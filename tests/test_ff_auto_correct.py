"""Pure CAP-7 rise-rate auto-correct law, guards, and B1 JSON."""

from __future__ import annotations

from pathlib import Path

import pytest

from ha_smart_hvac.ff_auto_correct import (
    BASE_MAX,
    MAX_RATE_BASE,
    MAX_RATE_SLOPE,
    RATE_ERROR_DEADBAND,
    WINDOW_SIZE,
    FfAutoCorrector,
    load_ff_state,
    save_ff_state,
)
from ha_smart_hvac.models import AutoCorrectConfig, ThermostatReading, ZoneSnapshot


def _zone(
    name: str,
    temp: float,
    *,
    setpoint: float = 22.0,
    hvac_action: str = "heating",
) -> ZoneSnapshot:
    return ZoneSnapshot(
        name=name,
        zone_temp=temp,
        thermostats=(ThermostatReading(f"climate.{name}", setpoint, hvac_action),),
    )


def _corrector(
    *,
    base: float = 25.0,
    slope: float = 1.2,
    comfort_ref: float = 20.0,
    outdoor_gate_delta_k: float = 12.0,
    setpoint_min: float = 20.0,
    setpoint_max: float = 55.0,
    control_interval: int = 60,
) -> FfAutoCorrector:
    return FfAutoCorrector(
        auto_correct=AutoCorrectConfig(outdoor_gate_delta_k=outdoor_gate_delta_k),
        control_interval=control_interval,
        base=base,
        slope=slope,
        comfort_ref=comfort_ref,
        setpoint_min=setpoint_min,
        setpoint_max=setpoint_max,
    )


def _run_window(
    corrector: FfAutoCorrector,
    outdoor: float,
    temps: list[float],
    *,
    name: str = "zone_a",
    setpoint: float = 22.0,
) -> None:
    assert len(temps) == WINDOW_SIZE
    for temp in temps:
        corrector.process_demand([_zone(name, temp, setpoint=setpoint)], outdoor)


def _flat_temps(temp: float) -> list[float]:
    return [temp] * WINDOW_SIZE


def _rise_temps(start: float, delta: float) -> list[float]:
    """Oldest=start, newest=start+delta → r_obs = delta / 0.25 at dt=60s."""
    return [start + (delta * i / (WINDOW_SIZE - 1)) for i in range(WINDOW_SIZE)]


# --- I1 / CS-base ---


def test_i1_cs_base_then_hysteresis_same_tick_selects_slope() -> None:
    """Restart + d ≥ gate+hyst → CS-base fill then slope same tick."""
    corrector = _corrector()
    outdoor = 0.0  # d=20 ≥ 14
    assert corrector._previous is None

    _run_window(corrector, outdoor, _flat_temps(20.0))

    assert corrector._previous == "slope"
    # Slow rise (flat) on slope → +slope
    assert corrector.slope == pytest.approx(1.2 + MAX_RATE_SLOPE)


def test_i1_stays_base_when_near_comfort() -> None:
    corrector = _corrector()
    outdoor = 18.0  # d=2 ≤ 10
    _run_window(corrector, outdoor, _flat_temps(20.0))
    assert corrector._previous == "base"
    assert corrector.base == pytest.approx(25.0 + MAX_RATE_BASE)


# --- G1 direction smoke ---


def test_g1_1_mild_slow_rise_raises_base() -> None:
    corrector = _corrector()
    _run_window(corrector, 18.0, _flat_temps(20.0))
    assert corrector.base > 25.0
    assert corrector.slope == pytest.approx(1.2)


def test_g1_2_mild_fast_rise_lowers_base() -> None:
    corrector = _corrector()
    # delta_T=0.1 → r_obs=0.4 > 0.35
    _run_window(corrector, 18.0, _rise_temps(20.0, 0.1))
    assert corrector.base < 25.0
    assert corrector.slope == pytest.approx(1.2)


def test_g1_3_far_slow_rise_raises_slope() -> None:
    corrector = _corrector()
    _run_window(corrector, 0.0, _flat_temps(20.0))
    assert corrector.slope > 1.2
    assert corrector.base == pytest.approx(25.0)


def test_g1_4_far_fast_rise_lowers_slope() -> None:
    corrector = _corrector()
    _run_window(corrector, 0.0, _rise_temps(20.0, 0.1))
    assert corrector.slope < 1.2
    assert corrector.base == pytest.approx(25.0)


def test_g1_5_warm_outdoor_i1_slope_skips() -> None:
    """Warm outdoor + I1 on slope → W-skip, no nudge."""
    corrector = _corrector()
    outdoor = 34.0  # d=14 → slope; comfort−T_out < 0
    base0, slope0 = corrector.base, corrector.slope
    _run_window(corrector, outdoor, _flat_temps(20.0))
    assert corrector._previous == "slope"
    assert corrector.base == pytest.approx(base0)
    assert corrector.slope == pytest.approx(slope0)


def test_g1_6_warm_outdoor_i1_base_slow_rise_allowed() -> None:
    """Warm outdoor + I1 on base + slow rise → base may nudge."""
    corrector = _corrector()
    outdoor = 25.0  # d=5 → base; comfort−T_out < 0
    _run_window(corrector, outdoor, _flat_temps(20.0))
    assert corrector._previous == "base"
    assert corrector.base == pytest.approx(25.0 + MAX_RATE_BASE)
    assert corrector.slope == pytest.approx(1.2)


# --- Append-on-freeze (1A) / incomplete W15 ---


def test_append_continues_on_near_setpoint_freeze() -> None:
    corrector = _corrector()
    outdoor = 18.0
    # error = 0.2 < ε=0.3 → freeze, but window still fills
    for temp in _flat_temps(21.8):
        corrector.process_demand([_zone("zone_a", temp, setpoint=22.0)], outdoor)
    assert len(corrector._window) == WINDOW_SIZE
    assert corrector.base == pytest.approx(25.0)
    assert corrector._previous == "base"  # I1 still advanced (3C)


def test_incomplete_w15_skips_adapt_without_er() -> None:
    corrector = _corrector()
    for _ in range(WINDOW_SIZE - 1):
        corrector.process_demand([_zone("zone_a", 20.0)], 18.0)
    assert len(corrector._window) == WINDOW_SIZE - 1
    assert corrector.base == pytest.approx(25.0)


def test_in_band_rate_freezes() -> None:
    """|e_r| ≤ δ freezes after W15 full."""
    corrector = _corrector()
    # r_obs ≈ 0.25 → e_r ≈ 0
    # delta_T = 0.25/4 = 0.0625
    temps = _rise_temps(20.0, 0.0625)
    r_obs = (temps[-1] - temps[0]) / 0.25
    assert abs(r_obs - 0.25) <= RATE_ERROR_DEADBAND
    _run_window(corrector, 18.0, temps)
    assert corrector.base == pytest.approx(25.0)


# --- Flush paths ---


def test_zone_switch_flushes_no_adapt() -> None:
    """Z1: both zones present, max-error selection changes → flush."""
    corrector = _corrector()
    outdoor = 18.0
    for _ in range(5):
        corrector.process_demand(
            [
                _zone("zone_a", 20.0, setpoint=22.0),  # error 2
                _zone("zone_b", 21.0, setpoint=22.0),  # error 1
            ],
            outdoor,
        )
    assert corrector._selected_zone_id == "zone_a"
    assert corrector._steady == 5

    result = corrector.process_demand(
        [
            _zone("zone_a", 21.0, setpoint=22.0),  # error 1
            _zone("zone_b", 18.0, setpoint=22.0),  # error 4
        ],
        outdoor,
    )
    assert corrector._steady == 0
    assert len(corrector._window) == 0
    assert corrector._previous is None
    assert corrector._selected_zone_id is None
    assert result.params_changed is False
    assert corrector.base == pytest.approx(25.0)


def test_4a_absent_zone_flushes() -> None:
    corrector = _corrector()
    outdoor = 18.0
    for _ in range(3):
        corrector.process_demand([_zone("zone_a", 20.0)], outdoor)
    # Previous selected absent from snapshots (only zone_b present)
    corrector.process_demand([_zone("zone_b", 18.0)], outdoor)
    assert corrector._steady == 0
    assert corrector._selected_zone_id is None


def test_m2_non_finite_zone_temp_flushes() -> None:
    corrector = _corrector()
    outdoor = 18.0
    for _ in range(3):
        corrector.process_demand([_zone("zone_a", 20.0)], outdoor)
    assert corrector._steady == 3

    result = corrector.process_demand([_zone("zone_a", float("nan"))], outdoor)
    assert corrector._steady == 0
    assert len(corrector._window) == 0
    assert corrector._selected_zone_id is None
    assert result.params_changed is False
    assert corrector.base == pytest.approx(25.0)


def test_empty_zones_flushes() -> None:
    corrector = _corrector()
    for _ in range(3):
        corrector.process_demand([_zone("zone_a", 20.0)], 18.0)
    result = corrector.process_demand([], 18.0)
    assert corrector._steady == 0
    assert len(corrector._window) == 0
    assert result.params_changed is False


def test_clear_ephemeral_resets_all() -> None:
    corrector = _corrector()
    _run_window(corrector, 18.0, _flat_temps(20.0))
    assert corrector._steady == WINDOW_SIZE
    corrector.clear_ephemeral()
    assert corrector._steady == 0
    assert len(corrector._window) == 0
    assert corrector._previous is None
    assert corrector._selected_zone_id is None
    # Runtime params untouched
    assert corrector.base == pytest.approx(25.0 + MAX_RATE_BASE)


# --- D-cmd / bounds ---


def test_d_cmd_blocks_raise_at_max() -> None:
    corrector = _corrector(base=40.0, slope=1.0, setpoint_min=20.0, setpoint_max=40.0)
    # outdoor=20 → u_ff=40 at max; slow rise wants +base
    outdoor = 20.0
    base0 = corrector.base
    _run_window(corrector, outdoor, _flat_temps(20.0), setpoint=22.0)
    assert corrector.base == pytest.approx(base0)
    assert corrector.clamp_uff(outdoor) == pytest.approx(40.0)


def test_d_cmd_allows_relieving_from_max() -> None:
    corrector = _corrector(base=40.0, slope=1.0, setpoint_min=20.0, setpoint_max=40.0)
    outdoor = 20.0  # at max; fast rise wants −base (relieving)
    _run_window(corrector, outdoor, _rise_temps(20.0, 0.1), setpoint=22.0)
    assert corrector.base < 40.0


def test_bounds_noop_no_params_changed() -> None:
    corrector = _corrector(base=BASE_MAX)
    outdoor = 18.0  # base knob; slow rise wants + but already at max
    result = None
    for temp in _flat_temps(20.0):
        result = corrector.process_demand([_zone("zone_a", temp)], outdoor)
    assert result is not None
    assert result.params_changed is False
    assert corrector.base == pytest.approx(BASE_MAX)


# --- B1 persistence helpers ---


def test_load_valid_json(tmp_path: Path) -> None:
    path = tmp_path / "ff_auto_correct_state.json"
    assert save_ff_state(path, 30.0, 1.5) is True
    assert load_ff_state(path) == (30.0, 1.5)
    assert not path.with_name(path.name + ".tmp").exists()


def test_save_ff_state_oserror_returns_false(tmp_path: Path) -> None:
    path = tmp_path / "ff_auto_correct_state.json"
    tmp_path.chmod(0o555)
    try:
        assert save_ff_state(path, 30.0, 1.5) is False
        assert not path.exists()
    finally:
        tmp_path.chmod(0o755)


def test_load_missing_returns_none(tmp_path: Path) -> None:
    assert load_ff_state(tmp_path / "missing.json") is None


def test_load_corrupt_returns_none(tmp_path: Path) -> None:
    path = tmp_path / "ff_auto_correct_state.json"
    path.write_text("{not json")
    assert load_ff_state(path) is None


@pytest.mark.parametrize(
    "payload",
    [
        '{"base": 14.9, "slope": 1.2}',
        '{"base": 40.1, "slope": 1.2}',
        '{"base": 25.0, "slope": 0.4}',
        '{"base": 25.0, "slope": 2.6}',
        '{"base": NaN, "slope": 1.2}',
        '{"base": 25.0, "slope": Infinity}',
    ],
)
def test_load_oob_returns_none(tmp_path: Path, payload: str) -> None:
    path = tmp_path / "ff_auto_correct_state.json"
    path.write_text(payload)
    assert load_ff_state(path) is None


def test_params_changed_false_when_frozen_mid_window() -> None:
    corrector = _corrector()
    result = corrector.process_demand([_zone("zone_a", 20.0)], 18.0)
    assert result.params_changed is False
    assert result.command == pytest.approx(corrector.clamp_uff(18.0))
