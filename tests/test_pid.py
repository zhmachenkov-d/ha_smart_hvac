"""Unit tests for fixed-gain PI Set Water Temperature law."""

from __future__ import annotations

import pytest

from ha_smart_hvac.models import ThermostatReading, ZoneSnapshot
from ha_smart_hvac.pid import clamp, evaluate_demand, quantize_command, weighted_error


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


_DT_HOURS = 300.0 / 3600.0
_KI = 1.0  # C4 default ki (1/h); _eval's default


def _eval(
    zones: list[ZoneSnapshot],
    *,
    integral: float = 0.0,
    dt_hours: float = _DT_HOURS,
    base: float = 40.0,
    kp: float = 1.0,
    ki: float = _KI,
    lo: float = 40.0,
    hi: float = 55.0,
    i_term_min: float = -10.0,
    i_term_max: float = 15.0,
):
    return evaluate_demand(
        zones,
        integral=integral,
        kp=kp,
        ki=ki,
        base_water_temp=base,
        setpoint_min=lo,
        setpoint_max=hi,
        i_term_min=i_term_min,
        i_term_max=i_term_max,
        dt_hours=dt_hours,
    )


def _run_ticks(zones: list[ZoneSnapshot], ticks: int, *, integral: float = 0.0, **kw):
    """Feed each tick's stepped ∫ into the next; return per-tick results."""
    results = []
    for _ in range(ticks):
        result = _eval(zones, integral=integral, **kw)
        assert result is not None
        results.append(result)
        integral = result.integral
    return results


@pytest.mark.parametrize(
    "value,expected",
    [(39.9, 40.0), (40.0, 40.0), (47.5, 47.5), (55.0, 55.0), (55.1, 55.0)],
)
def test_clamp_bounds(value: float, expected: float) -> None:
    assert clamp(value, 40.0, 55.0) == expected


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


def test_non_finite_weighted_error_returns_none() -> None:
    """Overflowing weights → non-finite e → None (idle path), not clamp(nan)."""
    zones = [
        _zone("a", 20.0, [22.0], weight=1e308),
        _zone("b", 18.0, [24.0], weight=1e308),
    ]
    assert weighted_error(zones) is None
    assert _eval(zones) is None


@pytest.mark.parametrize(
    ("raw", "lo", "hi", "expected"),
    [
        (60.0, 40.0, 55.06, 55.0),  # max with 2 decimals → ≤ hi
        (30.0, 42.04, 55.0, 42.1),  # min with 2 decimals → ≥ lo
        (41.96, 40.0, 55.0, 42.0),  # on-grid bounds unchanged
        (55.03, 55.01, 55.06, 55.03),  # no grid point → clamp(raw) off-grid
    ],
)
def test_quantize_command_grid_snap(
    raw: float, lo: float, hi: float, expected: float
) -> None:
    assert quantize_command(raw, lo, hi) == pytest.approx(expected)


def test_unsaturated_tick_advances_integral_in_degree_hours() -> None:
    zones = [_zone("a", 20.0, [22.0])]
    result = _eval(zones, integral=0.0)
    assert result is not None
    assert result.e == pytest.approx(2.0)
    assert result.u_pid == pytest.approx(2.0)
    assert result.raw == pytest.approx(42.0)
    assert result.command == pytest.approx(42.0)
    # ∫ += e·dt_hours = 2 * 300/3600 = 1/6 °C·h (inside the I-term rails)
    assert result.integral == pytest.approx(2.0 / 12.0)


def test_saturation_freeze_high_skips_integral_step() -> None:
    """raw > max and e > 0 → write clamp; do not apply ∫ += e·dt."""
    zones = [_zone("a", 10.0, [30.0])]  # e = 20
    # base + kp*e + ki*∫ = 40 + 20 + 0 = 60 > 55
    result = _eval(zones, integral=0.0, base=40.0, lo=40.0, hi=55.0)
    assert result is not None
    assert result.raw > 55.0
    assert result.e > 0
    assert result.command == pytest.approx(55.0)
    assert result.integral == pytest.approx(0.0)


def test_saturation_freeze_low_skips_integral_step() -> None:
    """raw < min and e < 0 → freeze ∫."""
    zones = [_zone("a", 30.0, [20.0])]  # e = -10
    # base + u_pid = 40 - 10 = 30 < 40
    result = _eval(zones, integral=0.0, base=40.0, lo=40.0, hi=55.0)
    assert result is not None
    assert result.raw < 40.0
    assert result.e < 0
    assert result.command == pytest.approx(40.0)
    assert result.integral == pytest.approx(0.0)


def test_no_freeze_when_sat_opposite_sign() -> None:
    """At high sat with e < 0, still advance (anti-windup freeze is same-sign only)."""
    zones = [_zone("a", 21.0, [20.0])]  # e = -1
    # ∫=5 → u_pid = -1 + 5 = 4, raw = 58 > max, but e < 0 → opposite sign → advance
    result = _eval(zones, integral=5.0, base=54.0, lo=40.0, hi=55.0)
    assert result is not None
    assert result.raw > 55.0
    assert result.e < 0
    assert result.command == pytest.approx(55.0)
    assert result.integral == pytest.approx(5.0 - 1.0 / 12.0)  # 4.9167


def test_small_error_three_ticks_i_term() -> None:
    """Matrix row 1: e = 0.2, 300 s, ki 1.0 → I-term 0.05 °C after 3 steps."""
    zones = [_zone("a", 21.8, [22.0])]
    results = _run_ticks(zones, 3)
    assert results[-1].e == pytest.approx(0.2)
    assert _KI * results[-1].integral == pytest.approx(0.05)


def test_full_hour_i_term_one_degree_no_rail() -> None:
    """Matrix row 2: e = 1 for 12 ticks → I-term +1.0 °C; no tick hits a rail."""
    zones = [_zone("a", 21.0, [22.0])]
    results = _run_ticks(zones, 12)
    i_terms = [_KI * r.integral for r in results]
    assert i_terms[-1] == pytest.approx(1.0)
    assert all(-10.0 < i < 15.0 for i in i_terms)
    steps = [b - a for a, b in zip([0.0, *i_terms], i_terms, strict=False)]
    assert all(step == pytest.approx(_KI * 1.0 * _DT_HOURS) for step in steps)


@pytest.mark.parametrize("ki", [1.0, 2.0])
def test_lower_rail_i_term_stops_at_i_term_min(ki: float) -> None:
    """Matrix row 3: sustained e < 0, not saturated low → I-term stops at min."""
    zones = [_zone("a", 23.0, [22.0])]  # e = -1
    seed = -9.95 / ki  # I-term just above i_term_min
    # base 52 keeps raw = 52 - 1 + I ≥ 41 > setpoint_min → no low freeze
    results = _run_ticks(zones, 5, integral=seed, ki=ki, base=52.0, lo=40.0, hi=60.0)
    for result in results:
        assert result.raw > 40.0
        assert ki * result.integral >= -10.0 - 1e-9
    assert ki * results[-1].integral == pytest.approx(-10.0)


def test_ki_zero_keeps_integral_and_i_term_zero() -> None:
    """Matrix row 4: ki = 0 → ∫ and I-term stay 0 for any e."""
    for temp in (20.0, 21.9, 22.0, 23.0):
        zones = [_zone("a", temp, [22.0])]
        results = _run_ticks(zones, 5, ki=0.0, base=48.0)
        for result in results:
            assert result.integral == 0.0
            assert result.u_pid == pytest.approx(result.e)


def test_kp_scales_proportional_term() -> None:
    zones = [_zone("a", 20.0, [22.0])]  # e = 2
    unit = _eval(zones, kp=1.0)
    double = _eval(zones, kp=2.0)
    assert unit is not None and double is not None
    assert unit.u_pid == pytest.approx(2.0)
    assert double.u_pid == pytest.approx(4.0)
    assert double.command == pytest.approx(44.0)
    # Kp does not enter the ∫ step
    assert double.integral == pytest.approx(unit.integral)


@pytest.mark.parametrize(
    "lo,hi,expected_command,expected_i_term,reaches_i_term_max",
    [
        (40.0, 55.0, 55.0, 14.0, False),  # example bounds: SWT-saturation freeze
        (42.0, 60.0, 58.0, 15.0, True),  # high bounds: I-term rail
    ],
)
def test_multi_tick_trace_constant_error(
    lo: float,
    hi: float,
    expected_command: float,
    expected_i_term: float,
    reaches_i_term_max: bool,
) -> None:
    """C4 defaults, e = 1, 200 ticks at 300 s: ramp by ~1/12 °C per tick."""
    zones = [_zone("a", 21.0, [22.0])]
    results = _run_ticks(zones, 200, base=lo, lo=lo, hi=hi)
    commands = [r.command for r in results]
    final_i_term = _KI * results[-1].integral
    i_term_step = _KI * 1.0 * _DT_HOURS  # ki·e·dt_hours

    max_step = i_term_step + 0.1 + 1e-9
    for prev, cur in zip(commands, commands[1:], strict=False):
        assert abs(cur - prev) <= max_step
    assert all(lo <= c <= hi for c in commands)
    assert commands[-1] == pytest.approx(expected_command)
    if reaches_i_term_max:
        assert final_i_term == pytest.approx(15.0)
    else:
        assert final_i_term == pytest.approx(expected_i_term, abs=0.1)
        assert final_i_term < 15.0
        # freeze needs raw = 41 + I strictly > 55: in exact arithmetic I = 14
        # gives raw == 55 and steps once more, so allow one step past 14.
        max_i_term = max(_KI * r.integral for r in results)
        upper = expected_i_term + i_term_step + 1e-6
        assert expected_i_term - 1e-6 <= max_i_term <= upper
