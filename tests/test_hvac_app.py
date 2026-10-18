"""Tests for hvac_app known-input wiring (tracking residue) and blow-up guard."""

import inspect
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from ha_smart_hvac.config import parse_config
from ha_smart_hvac.feedforward import weather_feedforward
from ha_smart_hvac.hvac_app import (
    LATCH_DECAY_U_TRACK_FRACTION,
    HvacApp,
    advance_with_tracking_residue,
    format_blow_up_warning,
    guard_u_track,
    latch_after_zone_change,
    latch_decay_residue_holds,
    next_decayed_omega_c,
    should_apply_omega_c,
    sticky_blow_up_latch,
)
from ha_smart_hvac.ladrc import LadrcState
from ha_smart_hvac.ladrc_tuner import LadrcTuner
from ha_smart_hvac.models import LadrcConfig, LadrcTuneConfig

# Locked CAP-5 thermal band (same numbers as tests/test_ladrc.py _thermal_config).
_THERMAL_B0 = 5e-4
_THERMAL_OMEGA_O = 0.03
_THERMAL_OMEGA_C = 0.01
_THERMAL_DT = 60.0

_SETPOINT_MIN = 40.0
_SETPOINT_MAX = 55.0
_U_TRACK_MAX = 100.0


def _config() -> LadrcConfig:
    return LadrcConfig(
        b0=_THERMAL_B0,
        omega_o=_THERMAL_OMEGA_O,
        omega_c=_THERMAL_OMEGA_C,
        omega_c_min=0.02,
        omega_c_max=0.15,
        tune=LadrcTuneConfig(
            ki=0.005,
            deadband=0.2,
            min_steady_ticks=5,
            max_rate_fraction=0.05,
        ),
        dt=_THERMAL_DT,
        u_track_max=_U_TRACK_MAX,
    )


def _run_guard(
    *,
    u_track: float,
    u_ff: float = 40.0,
    latch_in: bool = False,
    u_track_max: float = _U_TRACK_MAX,
):
    return guard_u_track(
        u_track,
        u_ff,
        u_track_max,
        _SETPOINT_MIN,
        _SETPOINT_MAX,
        latch_in,
    )


def test_residue_known_input_differs_behaviorally_from_absolute():
    """Residue vs absolute SWT must move the ESO differently (no private field)."""
    config = _config()
    measured = 21.0
    command = 55.0
    u_ff = 40.0

    via_residue = LadrcState()
    via_absolute = LadrcState()
    via_residue.reset(measured)
    via_absolute.reset(measured)

    advance_with_tracking_residue(via_residue, measured, command, u_ff, config)
    via_absolute.advance(measured, command, config)

    assert via_residue.z1 != via_absolute.z1


def test_advance_with_tracking_residue_uses_command_minus_uff():
    """ESO known input is post-clamp (command − u_ff), not absolute SWT."""
    state = LadrcState()
    config = _config()
    state.reset(21.0)
    command = 55.0  # absolute clamped plant write
    u_ff = 40.0

    advance_with_tracking_residue(state, 21.0, command, u_ff, config)

    assert state._last_u_applied == command - u_ff
    assert state._last_u_applied != command


def test_advance_with_tracking_residue_zero_when_command_equals_uff():
    state = LadrcState()
    config = _config()
    state.reset(21.0)
    u_ff = 40.0
    command = 40.0  # clamp at min with u_track ≈ 0

    advance_with_tracking_residue(state, 21.0, command, u_ff, config)

    assert state._last_u_applied == 0.0


def test_advance_with_tracking_residue_mid_band():
    """Residue when command sits between plant limits (not only clamp edges)."""
    state = LadrcState()
    config = _config()
    state.reset(21.0)
    u_ff = 45.0
    command = 50.0

    advance_with_tracking_residue(state, 21.0, command, u_ff, config)

    assert state._last_u_applied == 5.0


def test_advance_with_tracking_residue_negative_when_command_below_uff():
    """Post-clamp residue can be negative when command < u_ff."""
    state = LadrcState()
    config = _config()
    state.reset(21.0)
    u_ff = 50.0
    command = 40.0

    advance_with_tracking_residue(state, 21.0, command, u_ff, config)

    assert state._last_u_applied == -10.0


# --- CAP-3(c): blow-up guard seam (Hass-free) ---


def test_guard_healthy_clamps_sum_no_trip():
    u_ff = 42.0
    u_track = 5.0

    result = _run_guard(u_track=u_track, u_ff=u_ff)

    assert result.command == u_ff + u_track
    assert result.tripped is False
    assert result.should_warn is False
    assert result.latch_out is False
    assert result.reason is None


def test_guard_magnitude_trip_ff_only_no_eso_mutate():
    """Seam returns ff-only; does not reset ESO (AI-6: reset after write)."""
    ladrc = LadrcState()
    ladrc.reset(21.0)
    ladrc.z2 = 1.0
    u_ff = 42.0
    u_track = 150.0

    result = _run_guard(u_track=u_track, u_ff=u_ff)

    assert result.tripped is True
    assert result.should_warn is True
    assert result.latch_out is True
    assert result.reason == "magnitude"
    assert result.command == u_ff
    assert ladrc.z1 == 21.0
    assert ladrc.z2 == 1.0


def test_guard_trip_clamps_out_of_band_uff():
    """AI-7 / F-V2: trip command is clamp(u_ff), not raw u_ff."""
    low = _run_guard(u_track=200.0, u_ff=30.0)  # below setpoint_min
    assert low.tripped is True
    assert low.command == _SETPOINT_MIN

    high = _run_guard(u_track=200.0, u_ff=70.0)  # above setpoint_max
    assert high.tripped is True
    assert high.command == _SETPOINT_MAX


def test_guard_non_finite_trip():
    for bad in (float("nan"), float("inf"), float("-inf")):
        result = _run_guard(u_track=bad, u_ff=45.0)
        assert result.tripped is True
        assert result.should_warn is True
        assert result.latch_out is True
        assert result.reason == "non-finite"
        assert result.command == 45.0


def test_guard_consecutive_trips_warn_only_first():
    latch = False
    warns = []
    for _ in range(3):
        result = _run_guard(u_track=200.0, latch_in=latch)
        warns.append(result.should_warn)
        latch = result.latch_out
        assert result.tripped is True
        assert result.command == 40.0

    assert warns == [True, False, False]


def test_guard_latch_clears_on_healthy_then_warns_again():
    trip1 = _run_guard(u_track=200.0, latch_in=False)
    assert trip1.should_warn is True

    healthy = _run_guard(u_track=1.0, latch_in=trip1.latch_out)
    assert healthy.tripped is False
    assert healthy.latch_out is False
    assert healthy.should_warn is False

    trip2 = _run_guard(u_track=200.0, latch_in=healthy.latch_out)
    assert trip2.should_warn is True


def test_guard_poisoned_z2_via_compute_tracking():
    """CAP-3(c)+AI-6: trip → ff-only; reset then advance (post-write order)."""
    config = _config()
    ladrc = LadrcState()
    measured = 21.0
    ladrc.reset(measured)
    ladrc.critical_zone = "zone_one"
    ladrc.z2 = 1e12

    u_track = ladrc.compute_tracking(
        measured=measured,
        reference=22.0,
        config=config,
        critical_zone="zone_one",
    )
    assert abs(u_track) > config.u_track_max

    u_ff = 40.0
    result = _run_guard(
        u_track=u_track,
        u_ff=u_ff,
        u_track_max=config.u_track_max,
    )

    assert result.tripped is True
    assert result.command == u_ff
    assert ladrc.z2 == 1e12  # seam does not reset

    ladrc.reset(measured)
    assert ladrc.z2 == 0.0
    advance_with_tracking_residue(ladrc, measured, result.command, u_ff, config)
    assert ladrc._last_u_applied == 0.0


def test_format_blow_up_warning_floor_fields():
    mag = format_blow_up_warning("magnitude", 150.0, 100.0, "zone_one")
    assert "magnitude" in mag
    assert "150" in mag
    assert "100" in mag
    assert "zone_one" in mag

    for value, token in (
        (float("nan"), "nan"),
        (float("inf"), "inf"),
        (float("-inf"), "-inf"),
    ):
        msg = format_blow_up_warning("non-finite", value, 100.0, "zone_two")
        assert "non-finite" in msg
        assert token in msg
        assert "100" in msg
        assert "zone_two" in msg


def test_latch_after_zone_change_matrix():
    assert latch_after_zone_change("A", "B", True) is False
    assert latch_after_zone_change("A", "A", True) is True
    assert latch_after_zone_change(None, "B", True) is True
    assert latch_after_zone_change("A", "B", False) is False
    assert latch_after_zone_change("A", "A", False) is False
    assert latch_after_zone_change(None, "B", False) is False


def test_idle_paths_clear_blow_up_latch():
    hands = inspect.getsource(HvacApp._hands_off)
    idle = inspect.getsource(HvacApp._go_idle)
    tick = inspect.getsource(HvacApp.control_tick)
    assert "_blow_up_latch = False" in hands
    assert "_blow_up_warned = False" in hands
    assert "_blow_up_latch = False" in idle
    assert "_blow_up_warned = False" in idle
    # no-demand path clears latch with clear()
    no_demand = tick.split("if not has_heating_demand(zones):")[1].split("return")[0]
    assert "_blow_up_latch = False" in no_demand
    assert "_blow_up_warned = False" in no_demand


@pytest.mark.parametrize(
    ("proposed", "current", "tripped", "command", "expected"),
    [
        (None, 0.05, False, 47.0, False),  # no proposal
        (0.06, 0.05, True, 47.0, False),  # guard tripped
        (0.06, 0.05, False, _SETPOINT_MAX, False),  # max + ωc↑
        (0.04, 0.05, False, _SETPOINT_MAX, True),  # max + ωc↓
        (0.04, 0.05, False, _SETPOINT_MIN, False),  # min + ωc↓
        (0.06, 0.05, False, _SETPOINT_MIN, True),  # min + ωc↑
        (0.06, 0.05, False, 47.0, True),  # interior
    ],
)
def test_should_apply_omega_c_matrix(
    proposed: float | None,
    current: float,
    tripped: bool,
    command: float,
    expected: bool,
) -> None:
    """CAP-6(a): directional clamp + guard trip matrix."""
    assert (
        should_apply_omega_c(
            proposed,
            current,
            guard_tripped=tripped,
            command=command,
            setpoint_min=_SETPOINT_MIN,
            setpoint_max=_SETPOINT_MAX,
        )
        is expected
    )


def test_saturated_upward_proposal_does_not_ratchet_applied_or_committed() -> None:
    """CAP-6(b): Hass-free loop — write-path applied and committed ωc never rise."""
    config = _config()
    ladrc = LadrcState()
    measured = 21.0
    reference = 22.0
    zone = "zone_one"
    ladrc.reset(measured)
    ladrc.critical_zone = zone

    committed_omega = config.omega_c
    # Positive u_track + u_ff at max → healthy command clamped at setpoint_max.
    u_ff = _SETPOINT_MAX

    for step in range(10):
        proposed = committed_omega * (1.0 + 0.05 * (step + 1))
        assert proposed > committed_omega

        proposed_cfg = config.with_omega_c(proposed)
        provisional_u = ladrc.compute_tracking(
            measured=measured,
            reference=reference,
            config=proposed_cfg,
            critical_zone=zone,
        )
        provisional = _run_guard(
            u_track=provisional_u,
            u_ff=u_ff,
            u_track_max=proposed_cfg.u_track_max,
        )
        assert provisional.command >= _SETPOINT_MAX

        apply_proposed = should_apply_omega_c(
            proposed,
            committed_omega,
            guard_tripped=provisional.tripped,
            command=provisional.command,
            setpoint_min=_SETPOINT_MIN,
            setpoint_max=_SETPOINT_MAX,
        )
        if apply_proposed:
            write_cfg = proposed_cfg
        else:
            write_cfg = config.with_omega_c(committed_omega)

        applied_omega = write_cfg.omega_c
        assert applied_omega == committed_omega
        assert applied_omega == config.omega_c

        if apply_proposed:
            committed_omega = proposed

        assert committed_omega == config.omega_c


# --- CAP-4 / CAP-6(e): latch decay + skip adapt ---


def _decay_config(*, omega_c: float = 0.10) -> LadrcConfig:
    """Config with headroom above omega_c_min so decay steps are observable."""
    return LadrcConfig(
        b0=_THERMAL_B0,
        omega_o=_THERMAL_OMEGA_O,
        omega_c=omega_c,
        omega_c_min=0.02,
        omega_c_max=0.15,
        tune=LadrcTuneConfig(
            ki=0.005,
            deadband=0.2,
            min_steady_ticks=5,
            max_rate_fraction=0.05,
        ),
        dt=_THERMAL_DT,
        u_track_max=_U_TRACK_MAX,
    )


@pytest.mark.parametrize(
    ("u_track", "u_track_max", "expected"),
    [
        (81.0, 100.0, True),  # just above 0.8·max
        (80.0, 100.0, False),  # at band
        (50.0, 100.0, False),  # below band
        (100.0, 100.0, True),  # at trip magnitude
        (150.0, 100.0, True),  # above trip
        (float("nan"), 100.0, True),
        (float("inf"), 100.0, True),
        (float("-inf"), 100.0, True),
    ],
)
def test_latch_decay_residue_holds_matrix(
    u_track: float, u_track_max: float, expected: bool
) -> None:
    assert latch_decay_residue_holds(u_track, u_track_max) is expected


def test_latch_decay_fraction_constant() -> None:
    assert LATCH_DECAY_U_TRACK_FRACTION == 0.8


def test_next_decayed_omega_c_step_and_floor() -> None:
    assert next_decayed_omega_c(0.10, 0.05, 0.02) == pytest.approx(0.095)
    # Floor at omega_c_min.
    assert next_decayed_omega_c(0.021, 0.05, 0.02) == pytest.approx(0.02)
    assert next_decayed_omega_c(0.02, 0.05, 0.02) == pytest.approx(0.02)


@pytest.mark.parametrize(
    ("latch_in", "tripped", "u_track", "expected"),
    [
        (False, True, 150.0, True),  # trip sets
        (True, False, 90.0, True),  # hold in (0.8·max, max]
        (True, False, 100.0, True),  # hold at max (not tripped; abs==max)
        (True, False, 80.0, False),  # clear at ≤ band
        (True, False, 50.0, False),  # clear below band
        (False, False, 90.0, False),  # no latch_in, not tripped
        (True, True, 150.0, True),  # trip while already latched
        (True, False, float("nan"), True),  # non-finite holds
    ],
)
def test_sticky_blow_up_latch_matrix(
    latch_in: bool, tripped: bool, u_track: float, expected: bool
) -> None:
    """CAP-4 sticky latch: trip sets; holds in (0.8·max, max]; clears at ≤ band."""
    assert sticky_blow_up_latch(latch_in, tripped, u_track, _U_TRACK_MAX) is expected


def _mirror_decay_tick(
    *,
    tuner: LadrcTuner,
    config: LadrcConfig,
    latch: bool,
    u_track: float,
    u_ff: float = 40.0,
    write_ok: bool = True,
) -> bool:
    """Hass-free mirror of control_tick sticky+decay after a plant write attempt.

    When write_ok is False, matches fail-write early return: latch and ωc unchanged.
    """
    latch_in = latch
    guard = guard_u_track(
        u_track,
        u_ff,
        config.u_track_max,
        _SETPOINT_MIN,
        _SETPOINT_MAX,
        latch_in,
    )
    if not write_ok:
        return latch_in
    latch_out = sticky_blow_up_latch(
        latch_in, guard.tripped, u_track, config.u_track_max
    )
    if latch_out and latch_decay_residue_holds(u_track, config.u_track_max):
        tuner.commit_omega_c(
            next_decayed_omega_c(
                tuner.omega_c,
                config.tune.max_rate_fraction,
                config.omega_c_min,
            )
        )
    return latch_out


def test_multi_tick_decay_persists_until_omega_c_min(tmp_path: Path) -> None:
    """CAP-6(e): latched ticks with |u_track| above band decay persisted ωc to floor."""
    config = _decay_config(omega_c=0.10)
    state_path = tmp_path / "ladrc_tune_state.json"
    tuner = LadrcTuner(config, state_path)
    assert tuner.omega_c == pytest.approx(0.10)

    # Residue in (0.8·max, max]: not tripped, sticky holds, decay runs.
    u_track = 90.0
    latch = True
    for _ in range(200):
        latch = _mirror_decay_tick(
            tuner=tuner, config=config, latch=latch, u_track=u_track
        )
        if tuner.omega_c <= config.omega_c_min + 1e-12:
            break

    assert latch is True
    assert tuner.omega_c == pytest.approx(config.omega_c_min)
    persisted = json.loads(state_path.read_text(encoding="utf-8"))["omega_c"]
    assert persisted == pytest.approx(config.omega_c_min)
    reloaded = LadrcTuner(config, state_path)
    assert reloaded.omega_c == pytest.approx(config.omega_c_min)


def test_decay_stops_when_residue_at_or_below_band(tmp_path: Path) -> None:
    """Finite |u_track| ≤ 0.8·u_track_max clears sticky latch and skips decay."""
    config = _decay_config(omega_c=0.10)
    state_path = tmp_path / "ladrc_tune_state.json"
    tuner = LadrcTuner(config, state_path)

    latch = True
    latch = _mirror_decay_tick(tuner=tuner, config=config, latch=latch, u_track=90.0)
    assert latch is True
    after_decay = tuner.omega_c
    assert after_decay < 0.10

    latch = _mirror_decay_tick(tuner=tuner, config=config, latch=latch, u_track=80.0)
    assert latch is False
    assert tuner.omega_c == pytest.approx(after_decay)
    persisted = json.loads(state_path.read_text(encoding="utf-8"))["omega_c"]
    assert persisted == pytest.approx(after_decay)


def test_non_finite_u_track_decay_persists(tmp_path: Path) -> None:
    """CAP-6(e): latched + non-finite u_track steps ωc down via real commit_omega_c."""
    config = _decay_config(omega_c=0.10)
    state_path = tmp_path / "ladrc_tune_state.json"
    tuner = LadrcTuner(config, state_path)
    expected = next_decayed_omega_c(
        0.10, config.tune.max_rate_fraction, config.omega_c_min
    )

    latch = _mirror_decay_tick(
        tuner=tuner, config=config, latch=True, u_track=float("nan")
    )

    assert latch is True
    assert tuner.omega_c == pytest.approx(expected)
    persisted = json.loads(state_path.read_text(encoding="utf-8"))["omega_c"]
    assert persisted == pytest.approx(expected)


def test_trip_edge_decay_persists_despite_guard_trip(tmp_path: Path) -> None:
    """CAP-6(e): trip-edge latches and decay-persists; normal commit still skips."""
    config = _decay_config(omega_c=0.10)
    state_path = tmp_path / "ladrc_tune_state.json"
    tuner = LadrcTuner(config, state_path)
    current = tuner.omega_c
    u_track = 150.0
    u_ff = 40.0

    # Latch inactive at start (trip-edge); adapt may have proposed — commit blocked.
    guard = guard_u_track(
        u_track,
        u_ff,
        config.u_track_max,
        _SETPOINT_MIN,
        _SETPOINT_MAX,
        False,
    )
    assert guard.tripped is True
    assert (
        should_apply_omega_c(
            0.11,
            current,
            guard_tripped=guard.tripped,
            command=guard.command,
            setpoint_min=_SETPOINT_MIN,
            setpoint_max=_SETPOINT_MAX,
        )
        is False
    )

    expected = next_decayed_omega_c(
        current, config.tune.max_rate_fraction, config.omega_c_min
    )
    latch = _mirror_decay_tick(
        tuner=tuner, config=config, latch=False, u_track=u_track, u_ff=u_ff
    )

    assert latch is True
    assert tuner.omega_c == pytest.approx(expected)
    persisted = json.loads(state_path.read_text(encoding="utf-8"))["omega_c"]
    assert persisted == pytest.approx(expected)
    reloaded = LadrcTuner(config, state_path)
    assert reloaded.omega_c == pytest.approx(expected)


def test_single_decay_step_matches_max_rate_fraction(tmp_path: Path) -> None:
    """Acceptance: one latched high-residue tick decreases persisted ωc by one step."""
    config = _decay_config(omega_c=0.10)
    state_path = tmp_path / "ladrc_tune_state.json"
    tuner = LadrcTuner(config, state_path)
    expected = next_decayed_omega_c(
        0.10, config.tune.max_rate_fraction, config.omega_c_min
    )

    _mirror_decay_tick(tuner=tuner, config=config, latch=True, u_track=90.0)

    assert tuner.omega_c == pytest.approx(expected)
    persisted = json.loads(state_path.read_text(encoding="utf-8"))["omega_c"]
    assert persisted == pytest.approx(expected)


def test_fail_write_leaves_latch_and_omega_c_unchanged(tmp_path: Path) -> None:
    """Fail-write early return: sticky/decay must not run (sticky-after-write)."""
    config = _decay_config(omega_c=0.10)
    state_path = tmp_path / "ladrc_tune_state.json"
    tuner = LadrcTuner(config, state_path)

    # Latched + gray-band residue would decay if write succeeded.
    latch = _mirror_decay_tick(
        tuner=tuner, config=config, latch=True, u_track=90.0, write_ok=False
    )
    assert latch is True
    assert tuner.omega_c == pytest.approx(0.10)

    # Trip-edge would sticky+decay on success; fail keeps latch False.
    latch = _mirror_decay_tick(
        tuner=tuner, config=config, latch=False, u_track=150.0, write_ok=False
    )
    assert latch is False
    assert tuner.omega_c == pytest.approx(0.10)
    assert not state_path.is_file()


# --- Package C: Hass-stubbed control_tick (AI-1 / AI-2 / AI-3) ---

_OUTDOOR = "sensor.outdoor"
_PLANT_MGMT = "switch.pm"
_PLANT_SETPOINT = "number.plant_setpoint"
_ZONE_TEMP = "sensor.zone_one_temp"
_CLIMATE = "climate.zone_one"
_ZONE_NAME = "zone_one"


def _tick_args(
    *,
    omega_c: float = 0.10,
    u_track_max: float = _U_TRACK_MAX,
) -> dict:
    """Thermal b0/ωo/tune args for parse_config (omega_c valid; not package A)."""
    return {
        "outdoor_temperature": _OUTDOOR,
        "plant_management": _PLANT_MGMT,
        "plant_setpoint": _PLANT_SETPOINT,
        "setpoint_min": _SETPOINT_MIN,
        "setpoint_max": _SETPOINT_MAX,
        "control_interval": int(_THERMAL_DT),
        "tune_state_path": "ladrc_tune_state.json",
        "weather_feedforward": {
            "base": 25,
            "slope": 1.2,
            "comfort_ref": 20,
        },
        "ladrc": {
            "b0": _THERMAL_B0,
            "omega_o": _THERMAL_OMEGA_O,
            "omega_c": omega_c,
            "omega_c_min": 0.02,
            "omega_c_max": 0.15,
            "u_track_max": u_track_max,
            "tune": {
                "ki": 0.005,
                "deadband": 0.2,
                "min_steady_ticks": 5,
                "max_rate_fraction": 0.05,
            },
        },
        "zones": [
            {
                "name": _ZONE_NAME,
                "temperature": _ZONE_TEMP,
                "thermostats": [_CLIMATE],
            }
        ],
    }


def _tick_app(
    tmp_path: Path,
    *,
    omega_c: float = 0.10,
    u_track_max: float = _U_TRACK_MAX,
    plant_setpoint: object = 45.0,
    zone_temp: float = 20.0,
    setpoint: float = 22.0,
    outdoor: float = 0.0,
    hvac_action: str = "heating",
    plant_management: str = "on",
    blow_up_latch: bool = False,
    blow_up_warned: bool = False,
) -> HvacApp:
    """Hass-stubbed HvacApp for control_tick (Package C recipe)."""
    config = parse_config(_tick_args(omega_c=omega_c, u_track_max=u_track_max))
    state_path = tmp_path / config.tune_state_path
    app = object.__new__(HvacApp)
    app._config = config
    app._ladrc = LadrcState()
    app._tuner = LadrcTuner(config.ladrc, state_path)
    app._blow_up_latch = blow_up_latch
    app._blow_up_warned = blow_up_warned
    app.call_service = MagicMock()
    app.log = MagicMock()
    app.set_state = MagicMock()

    def get_state(entity_id: str, attribute: str | None = None):
        if entity_id == _PLANT_MGMT:
            return plant_management
        if entity_id == _OUTDOOR:
            return outdoor
        if entity_id == _ZONE_TEMP:
            return zone_temp
        if entity_id == _PLANT_SETPOINT:
            return plant_setpoint
        if entity_id == _CLIMATE:
            if attribute == "temperature":
                return setpoint
            if attribute == "hvac_action":
                return hvac_action
            return "heat"
        return None

    app.get_state = MagicMock(side_effect=get_state)
    return app


def test_initialize_sets_blow_up_flags_false(tmp_path: Path) -> None:
    """initialize pins latch + warned false (stubs must not be the only assign site)."""
    app = object.__new__(HvacApp)
    app.args = _tick_args(omega_c=0.10)
    app.log = MagicMock()
    app.run_every = MagicMock()
    assert not hasattr(app, "_blow_up_latch")
    assert not hasattr(app, "_blow_up_warned")

    with patch.object(HvacApp, "app_dir", new_callable=PropertyMock) as mock_dir:
        mock_dir.return_value = tmp_path
        app.initialize()

    assert app._blow_up_latch is False
    assert app._blow_up_warned is False
    app.run_every.assert_called_once()


def test_idle_paths_clear_blow_up_warned(tmp_path: Path) -> None:
    """_go_idle / _hands_off / no-demand clear _blow_up_warned with the latch."""
    app = _tick_app(tmp_path, blow_up_warned=True, blow_up_latch=True)
    HvacApp._hands_off(app, "hands off")
    assert app._blow_up_warned is False
    assert app._blow_up_latch is False

    app._blow_up_warned = True
    app._blow_up_latch = True
    HvacApp._go_idle(app, "idle")
    assert app._blow_up_warned is False
    assert app._blow_up_latch is False

    app = _tick_app(
        tmp_path,
        blow_up_warned=True,
        blow_up_latch=True,
        zone_temp=22.0,
        setpoint=22.0,  # zone_error == 0 → no demand
    )
    app.control_tick({})
    assert app._blow_up_warned is False
    assert app._blow_up_latch is False


# --- CAP-5: weather-curve-only SWT law ---


def _expected_ff_clamp(config, outdoor: float) -> float:
    u_ff = weather_feedforward(outdoor, config.weather_feedforward)
    return max(config.setpoint_min, min(config.setpoint_max, u_ff))


def _set_value_writes(app: HvacApp) -> list[float]:
    return [
        c.kwargs["value"]
        for c in app.call_service.call_args_list
        if c.args and c.args[0] == "number/set_value"
    ]


def test_cap5_demand_writes_clamp_uff_only(tmp_path: Path) -> None:
    """CAP-5(a): demand → clamp(u_ff) only; no tracking / publish_sensor."""
    outdoor = 10.0
    app = _tick_app(
        tmp_path,
        zone_temp=20.0,
        setpoint=22.0,
        outdoor=outdoor,
        plant_setpoint=45.0,
    )
    expected = _expected_ff_clamp(app._config, outdoor)
    with (
        patch.object(
            app._ladrc, "compute_tracking", wraps=app._ladrc.compute_tracking
        ) as track,
        patch.object(
            app._tuner, "publish_sensor", wraps=app._tuner.publish_sensor
        ) as publish,
        patch.object(app._tuner, "maybe_adapt", wraps=app._tuner.maybe_adapt) as adapt,
    ):
        app.control_tick({})

    assert _set_value_writes(app) == [expected]
    track.assert_not_called()
    publish.assert_not_called()
    adapt.assert_not_called()
    info_msgs = [
        str(c.args[0])
        for c in app.log.call_args_list
        if c.kwargs.get("level") is None or c.kwargs.get("level") == "INFO"
    ]
    joined = " ".join(info_msgs)
    assert "u_ff=" in joined
    assert "command=" in joined
    assert "Critical zone" not in joined
    assert "u_track=" not in joined


def test_demand_fail_write_aborts_without_success_info(tmp_path: Path) -> None:
    """Demand + unreadable plant setpoint: no set_value, no command= INFO."""
    app = _tick_app(
        tmp_path,
        zone_temp=20.0,
        setpoint=22.0,
        outdoor=10.0,
        plant_setpoint="unavailable",
    )

    app.control_tick({})

    assert _set_value_writes(app) == []
    app.call_service.assert_not_called()
    warn_msgs = [
        str(c.args[0])
        for c in app.log.call_args_list
        if c.kwargs.get("level") == "WARNING"
    ]
    assert any("Plant setpoint unavailable" in m for m in warn_msgs)
    info_msgs = [
        str(c.args[0])
        for c in app.log.call_args_list
        if c.kwargs.get("level") is None or c.kwargs.get("level") == "INFO"
    ]
    assert not any("command=" in m for m in info_msgs)


def test_cap5_plant_on_idle_writes_zero_and_clears(tmp_path: Path) -> None:
    """CAP-5(b): Plant-on idle → write 0 + clear water-path state."""
    app = _tick_app(
        tmp_path,
        zone_temp=22.0,
        setpoint=22.0,
        blow_up_latch=True,
        blow_up_warned=True,
    )
    app._ladrc.reset(22.0)
    app._ladrc.z2 = 1.0
    app._tuner._steady_ticks = 3

    app.control_tick({})

    assert _set_value_writes(app) == [0.0]
    assert app._blow_up_latch is False
    assert app._blow_up_warned is False
    assert app._ladrc.z2 == 0.0
    assert app._tuner._steady_ticks == 0


def test_cap5_plant_off_no_write_and_clears(tmp_path: Path) -> None:
    """CAP-5(c): Plant-off → no Set Water Temperature write + clear."""
    app = _tick_app(
        tmp_path,
        plant_management="off",
        blow_up_latch=True,
        blow_up_warned=True,
    )
    app._ladrc.reset(20.0)
    app._ladrc.z2 = 1.0

    app.control_tick({})

    assert _set_value_writes(app) == []
    app.call_service.assert_not_called()
    assert app._blow_up_latch is False
    assert app._blow_up_warned is False
    assert app._ladrc.z2 == 0.0


def test_cap5_flat_air_multi_tick_stays_at_ff_clamp(tmp_path: Path) -> None:
    """CAP-5(d): flat near-setpoint air never climbs to max via tracking."""
    outdoor = 10.0
    app = _tick_app(
        tmp_path,
        zone_temp=21.8,
        setpoint=22.0,
        outdoor=outdoor,
        plant_setpoint=45.0,
    )
    expected = _expected_ff_clamp(app._config, outdoor)
    assert expected < app._config.setpoint_max

    for _ in range(5):
        app.call_service.reset_mock()
        app.control_tick({})
        writes = _set_value_writes(app)
        assert writes == [expected]
        assert writes[0] == expected
        assert writes[0] < app._config.setpoint_max


def test_cap5_max_error_zone_air_not_additive_on_swt(tmp_path: Path) -> None:
    """CAP-5(e): distinct max-error zone air is not an additive term on SWT."""
    outdoor = 10.0
    zone_two_temp = "sensor.zone_two_temp"
    climate_two = "climate.zone_two"
    args = _tick_args()
    args["zones"] = [
        {
            "name": "zone_one",
            "temperature": _ZONE_TEMP,
            "thermostats": [_CLIMATE],
        },
        {
            "name": "zone_two",
            "temperature": zone_two_temp,
            "thermostats": [climate_two],
        },
    ]
    config = parse_config(args)
    expected = _expected_ff_clamp(config, outdoor)

    app = object.__new__(HvacApp)
    app._config = config
    app._ladrc = LadrcState()
    app._tuner = LadrcTuner(config.ladrc, tmp_path / config.tune_state_path)
    app._blow_up_latch = False
    app._blow_up_warned = False
    app.call_service = MagicMock()
    app.log = MagicMock()
    app.set_state = MagicMock()

    def get_state(entity_id: str, attribute: str | None = None):
        if entity_id == _PLANT_MGMT:
            return "on"
        if entity_id == _OUTDOOR:
            return outdoor
        if entity_id == _ZONE_TEMP:
            return 21.5  # small error
        if entity_id == zone_two_temp:
            return 15.0  # max-error zone, distinct air
        if entity_id == _PLANT_SETPOINT:
            return 45.0
        if entity_id == _CLIMATE:
            if attribute == "temperature":
                return 22.0
            if attribute == "hvac_action":
                return "heating"
            return "heat"
        if entity_id == climate_two:
            if attribute == "temperature":
                return 22.0
            if attribute == "hvac_action":
                return "heating"
            return "heat"
        return None

    app.get_state = MagicMock(side_effect=get_state)
    app.control_tick({})

    assert _set_value_writes(app) == [expected]


def test_matrix_outdoor_missing_goes_idle(tmp_path: Path) -> None:
    """I/O matrix: outdoor unavailable → _go_idle write 0 + clear."""
    app = _tick_app(
        tmp_path,
        outdoor="unavailable",
        blow_up_latch=True,
        blow_up_warned=True,
    )
    app._ladrc.reset(20.0)
    app._ladrc.z2 = 1.0
    app._tuner._steady_ticks = 2

    app.control_tick({})

    assert _set_value_writes(app) == [0.0]
    assert app._blow_up_latch is False
    assert app._blow_up_warned is False
    assert app._ladrc.z2 == 0.0
    assert app._tuner._steady_ticks == 0


def test_matrix_no_valid_zones_goes_idle(tmp_path: Path) -> None:
    """I/O matrix: no valid zones → _go_idle write 0 + clear."""
    app = _tick_app(
        tmp_path,
        zone_temp="unavailable",
        blow_up_latch=True,
        blow_up_warned=True,
    )
    app._ladrc.reset(20.0)
    app._ladrc.z2 = 1.0

    app.control_tick({})

    assert _set_value_writes(app) == [0.0]
    assert app._blow_up_latch is False
    assert app._blow_up_warned is False
    assert app._ladrc.z2 == 0.0


# --- CAP-6 (c)(d): write-on-change vs fail-closed ---


def _write_stub(raw_state: object) -> HvacApp:
    """Minimal Hass surface for HvacApp._write_setpoint / _read_float."""
    app = object.__new__(HvacApp)
    app._config = SimpleNamespace(plant_setpoint=_PLANT_SETPOINT)
    app.get_state = MagicMock(return_value=raw_state)
    app.call_service = MagicMock()
    app.log = MagicMock()
    return app


@pytest.mark.parametrize(
    "raw_state",
    [42.0, "42.0", 42],
)
def test_write_setpoint_skips_set_value_when_entity_float_equals(raw_state):
    """CAP-6(c): identical entity float skips set_value; returns success."""
    app = _write_stub(raw_state)

    ok = HvacApp._write_setpoint(app, 42.0)

    assert ok is True
    app.call_service.assert_not_called()


def test_write_setpoint_calls_set_value_when_entity_float_differs():
    app = _write_stub(40.0)

    ok = HvacApp._write_setpoint(app, 42.0)

    assert ok is True
    app.call_service.assert_called_once_with(
        "number/set_value",
        entity_id=_PLANT_SETPOINT,
        value=42.0,
    )


@pytest.mark.parametrize(
    "raw_state",
    [None, "unavailable", "unknown", "not-a-float", object()],
)
def test_write_setpoint_fail_closed_when_entity_unreadable(raw_state):
    """CAP-6(d): unreadable/unparseable → no set_value, false (tick abort)."""
    app = _write_stub(raw_state)

    ok = HvacApp._write_setpoint(app, 42.0)

    assert ok is False
    app.call_service.assert_not_called()
