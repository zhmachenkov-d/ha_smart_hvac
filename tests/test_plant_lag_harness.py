"""Closed-loop plant-lag multi-tick harness (decide-epic shared sim setup)."""

from __future__ import annotations

import math
from unittest.mock import patch

from ha_smart_hvac.hvac_app import advance_with_tracking_residue
from ha_smart_hvac.models import LadrcConfig, LadrcTuneConfig, WeatherFeedforwardConfig
from harness.runner import ClosedLoopSeries, run_closed_loop

_N = 40
_Y0 = 20.0
_T_R = 21.0
_ZONE = "living_room"
_OUTDOOR = 0.0
_PLANT_K = 0.45
_PLANT_T = 300.0
_PLANT_N = 3
_SETPOINT_MIN = 40.0
_SETPOINT_MAX = 55.0


def _example_aligned_config(*, u_track_max: float = 250.0) -> LadrcConfig:
    """Same b0/ωo/ωc/dt/u_track_max shape as apps.yaml.example / CAP-3(b)."""
    return LadrcConfig(
        b0=5e-4,
        omega_o=0.03,
        omega_c=0.03,
        omega_c_min=0.02,
        omega_c_max=0.15,
        tune=LadrcTuneConfig(
            ki=0.005,
            deadband=0.2,
            min_steady_ticks=5,
            max_rate_fraction=0.05,
        ),
        dt=60.0,
        u_track_max=u_track_max,
    )


def _ff_config() -> WeatherFeedforwardConfig:
    return WeatherFeedforwardConfig(base=25.0, slope=1.2, comfort_ref=20.0)


def _run(*, zero_uff: bool = False, u_track_max: float = 250.0) -> ClosedLoopSeries:
    return run_closed_loop(
        n_ticks=_N,
        y0=_Y0,
        reference=_T_R,
        critical_zone=_ZONE,
        outdoor=_OUTDOOR,
        plant_k=_PLANT_K,
        plant_t=_PLANT_T,
        plant_n=_PLANT_N,
        setpoint_min=_SETPOINT_MIN,
        setpoint_max=_SETPOINT_MAX,
        ladrc_config=_example_aligned_config(u_track_max=u_track_max),
        ff_config=_ff_config(),
        zero_uff=zero_uff,
    )


def _assert_finite_series(series: ClosedLoopSeries) -> None:
    assert len(series) == _N
    for name in ("command", "y", "u_track", "z1", "z2", "u_ff"):
        values = getattr(series, name)
        assert len(values) == _N
        assert all(math.isfinite(v) for v in values), name


def test_ff_on_series_length_and_finite():
    series = _run(zero_uff=False)
    _assert_finite_series(series)
    expected_uff = 25.0 + 1.2 * (20.0 - _OUTDOOR)
    assert all(u == expected_uff for u in series.u_ff)


def test_zero_uff_residue_is_command():
    applied: list[tuple[float, float, float]] = []
    real = advance_with_tracking_residue

    def _capture(ladrc, measured, command, u_ff, config):
        applied.append((command, u_ff, command - u_ff))
        real(ladrc, measured, command, u_ff, config)

    with patch("harness.runner.advance_with_tracking_residue", side_effect=_capture):
        series = _run(zero_uff=True)
    _assert_finite_series(series)
    assert all(u == 0.0 for u in series.u_ff)
    assert len(applied) == _N
    assert all(u_ff == 0.0 for _, u_ff, _ in applied)
    assert all(residue == command for command, _, residue in applied)


def test_back_to_back_modes_do_not_mutate_each_others_series():
    ff_on = _run(zero_uff=False)
    zero = _run(zero_uff=True)
    assert ff_on.u_ff is not zero.u_ff
    assert all(u != 0.0 for u in ff_on.u_ff)
    assert all(u == 0.0 for u in zero.u_ff)
    # Re-run FF-on; prior zero series must stay all-zero u_ff.
    _run(zero_uff=False)
    assert all(u == 0.0 for u in zero.u_ff)
    assert len(zero) == _N
    assert len(ff_on) == _N


def test_forced_guard_trip_clamps_to_uff_and_sticky_latch():
    series = _run(zero_uff=False, u_track_max=1.0)
    _assert_finite_series(series)
    expected_uff = 25.0 + 1.2 * (20.0 - _OUTDOOR)
    clamped = max(_SETPOINT_MIN, min(_SETPOINT_MAX, expected_uff))
    trip_idxs = [i for i, t in enumerate(series.tripped) if t]
    assert trip_idxs, "expected at least one magnitude trip with tiny u_track_max"
    i0 = trip_idxs[0]
    assert series.command[i0] == clamped
    assert series.latch[i0] is True


def test_sticky_latch_holds_in_decay_band_without_retrip():
    """CAP-4: after a trip, latch stays True when |u_track| in (0.8·max, max]."""
    u_track_max = 100.0
    # Trip, then in-band residue (no re-trip) so sticky hold is the only latch source.
    scripted = iter([150.0, 90.0])
    expected_uff = 25.0 + 1.2 * (20.0 - _OUTDOOR)
    clamped = max(_SETPOINT_MIN, min(_SETPOINT_MAX, expected_uff))

    with patch(
        "harness.runner.LadrcState.compute_tracking",
        side_effect=lambda *args, **kwargs: next(scripted),
    ):
        series = run_closed_loop(
            n_ticks=2,
            y0=_Y0,
            reference=_T_R,
            critical_zone=_ZONE,
            outdoor=_OUTDOOR,
            plant_k=_PLANT_K,
            plant_t=_PLANT_T,
            plant_n=_PLANT_N,
            setpoint_min=_SETPOINT_MIN,
            setpoint_max=_SETPOINT_MAX,
            ladrc_config=_example_aligned_config(u_track_max=u_track_max),
            ff_config=_ff_config(),
            zero_uff=False,
        )

    assert series.tripped[0] is True
    assert series.command[0] == clamped
    assert series.latch[0] is True
    assert series.tripped[1] is False
    assert abs(series.u_track[1]) == 90.0
    assert 0.8 * u_track_max < abs(series.u_track[1]) <= u_track_max
    assert series.latch[1] is True
