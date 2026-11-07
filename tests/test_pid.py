"""Unit tests for fixed-gain PI Set Water Temperature law."""

from __future__ import annotations

import pytest

from ha_smart_hvac.models import ThermostatReading, ZoneSnapshot
from ha_smart_hvac.pid import evaluate_demand, weighted_error


def _zone(
    name: str,
    temp: float,
    setpoints: list[float],
    *,
    hvac_actions: list[str | None] | None = None,
    weight: float = 1.0,
) -> ZoneSnapshot:
    actions = hvac_actions or ["heating"] * len(setpoints)
    thermostats = tuple(
        ThermostatReading(f"climate.{name}_{i}", sp, actions[i])
        for i, sp in enumerate(setpoints)
    )
    return ZoneSnapshot(
        name=name, zone_temp=temp, thermostats=thermostats, weight=weight
    )


def _eval(
    zones: list[ZoneSnapshot],
    *,
    integral: float = 0.0,
    advance: bool = True,
    dt: float = 300.0,
    base: float = 40.0,
    kp: float = 1.0,
    ki: float = 0.1,
    lo: float = 40.0,
    hi: float = 55.0,
    integral_min: float = -50.0,
    integral_max: float = 50.0,
):
    return evaluate_demand(
        zones,
        integral=integral,
        kp=kp,
        ki=ki,
        base_water_temp=base,
        setpoint_min=lo,
        setpoint_max=hi,
        integral_min=integral_min,
        integral_max=integral_max,
        dt=dt,
        advance_integral=advance,
    )


def test_weighted_error_single_demand_zone() -> None:
    zones = [_zone("a", 20.0, [22.0])]
    assert weighted_error(zones) == pytest.approx(2.0)


def test_weighted_error_uses_max_heating_setpoint() -> None:
    zones = [_zone("a", 19.0, [20.0, 22.0], hvac_actions=["heating", "heating"])]
    assert weighted_error(zones) == pytest.approx(3.0)


def test_weighted_error_ignores_idle_thermostat_setpoint() -> None:
    zones = [_zone("a", 19.0, [20.0, 24.0], hvac_actions=["heating", "idle"])]
    assert weighted_error(zones) == pytest.approx(1.0)


def test_weighted_averages_normalize_weights() -> None:
    """Two demand zones, weights 1 and 3 → normalized Tair_w / Tset_w."""
    zones = [
        _zone("a", 20.0, [22.0], weight=1.0),
        _zone("b", 18.0, [24.0], weight=3.0),
    ]
    # Tair_w = (1*20 + 3*18)/4 = 18.5; Tset_w = (1*22 + 3*24)/4 = 23.5; e = 5.0
    assert weighted_error(zones) == pytest.approx(5.0)


def test_weighted_error_skips_non_demand_zones() -> None:
    zones = [
        _zone("idle", 10.0, [30.0], hvac_actions=["idle"], weight=10.0),
        _zone("heat", 20.0, [22.0], weight=1.0),
    ]
    assert weighted_error(zones) == pytest.approx(2.0)


def test_zero_weight_sum_returns_none() -> None:
    zones = [
        _zone("a", 20.0, [22.0], weight=0.0),
        _zone("b", 18.0, [24.0], weight=-1.0),
    ]
    assert weighted_error(zones) is None
    assert _eval(zones) is None


def test_unsaturated_tick_advances_integral_then_clamps() -> None:
    zones = [_zone("a", 20.0, [22.0])]
    result = _eval(zones, integral=0.0, advance=True, dt=300.0)
    assert result is not None
    assert result.e == pytest.approx(2.0)
    assert result.u_pid == pytest.approx(2.0)
    assert result.raw == pytest.approx(42.0)
    assert result.command == pytest.approx(42.0)
    # ∫ += 2*300 = 600 → clamp to 50
    assert result.integral == pytest.approx(50.0)


def test_no_advance_keeps_integral() -> None:
    zones = [_zone("a", 20.0, [22.0])]
    result = _eval(zones, integral=5.0, advance=False, dt=300.0)
    assert result is not None
    assert result.integral == pytest.approx(5.0)
    assert result.command == pytest.approx(round(40.0 + 1.0 * 2.0 + 0.1 * 5.0, 1))


def test_saturation_freeze_high_skips_integral_step() -> None:
    """raw > max and e > 0 → write clamp; do not apply ∫ += e·dt."""
    zones = [_zone("a", 10.0, [30.0])]  # e = 20
    # base + kp*e + ki*∫ = 40 + 20 + 0 = 60 > 55
    result = _eval(zones, integral=0.0, advance=True, base=40.0, lo=40.0, hi=55.0)
    assert result is not None
    assert result.raw > 55.0
    assert result.e > 0
    assert result.command == pytest.approx(55.0)
    assert result.integral == pytest.approx(0.0)


def test_saturation_freeze_low_skips_integral_step() -> None:
    """raw < min and e < 0 → freeze ∫."""
    zones = [_zone("a", 30.0, [20.0])]  # e = -10
    # base + u_pid = 40 - 10 = 30 < 40
    result = _eval(zones, integral=0.0, advance=True, base=40.0, lo=40.0, hi=55.0)
    assert result is not None
    assert result.raw < 40.0
    assert result.e < 0
    assert result.command == pytest.approx(40.0)
    assert result.integral == pytest.approx(0.0)


def test_no_freeze_when_sat_opposite_sign() -> None:
    """At high sat with e < 0, still advance (anti-windup freeze is same-sign only)."""
    zones = [_zone("a", 30.0, [20.0])]  # e = -10
    # ∫=300 → u_pid=20, raw=60 > max, but e < 0 → opposite sign → advance
    result = _eval(
        zones,
        integral=300.0,
        advance=True,
        base=40.0,
        lo=40.0,
        hi=55.0,
        dt=1.0,
        integral_min=-50.0,
        integral_max=50.0,
    )
    assert result is not None
    assert result.raw > 55.0
    assert result.e < 0
    assert result.integral == pytest.approx(50.0)  # 300 + (-10)*1 → clamp 50
