"""Tests for outdoor weather-curve Set Water Temperature control loop."""

import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from ha_smart_hvac.config import parse_config
from ha_smart_hvac.hvac_app import HvacApp
from ha_smart_hvac.pid import quantize_command
from ha_smart_hvac.rls import (
    STATE_FILENAME,
    RlsState,
    copy_durable,
    durable_equal,
)

_SETPOINT_MIN = 40.0
_SETPOINT_MAX = 55.0
_CONTROL_INTERVAL = 300
_BASE = 40.0
_KP = 1.0
_KI = 1.0
_DT_HOURS = _CONTROL_INTERVAL / 3600.0
_FF_BASE = 37.0
_FF_SLOPE = 0.9
_FF_COMFORT_REF = 20.0
_OUTDOOR_TEMP = 10.0  # u_ff = 37 + 0.9*(20-10) = 46.0

_OUTDOOR = "sensor.outdoor"
_PLANT_MGMT = "switch.pm"
_PLANT_SETPOINT = "number.plant_setpoint"
_BOILER_WATER = "sensor.boiler_water"
_ZONE_TEMP = "sensor.zone_one_temp"
_CLIMATE = "climate.zone_one"
_ZONE_NAME = "zone_one"


def _tick_args() -> dict:
    return {
        "outdoor_temperature": _OUTDOOR,
        "plant_management": _PLANT_MGMT,
        "plant_setpoint": _PLANT_SETPOINT,
        "setpoint_min": _SETPOINT_MIN,
        "setpoint_max": _SETPOINT_MAX,
        "control_interval": _CONTROL_INTERVAL,
        "base_water_temp": _BASE,
        "weather_feedforward": {
            "base": _FF_BASE,
            "slope": _FF_SLOPE,
            "comfort_ref": _FF_COMFORT_REF,
        },
        "pid": {
            "kp": _KP,
            "ki": _KI,
            "i_term_min": -10,
            "i_term_max": 15,
        },
        "zones": [
            {
                "name": _ZONE_NAME,
                "temperature": _ZONE_TEMP,
                "thermostats": [_CLIMATE],
            }
        ],
    }


def _expected_command(*, outdoor: float = _OUTDOOR_TEMP) -> float:
    u_ff = _FF_BASE + _FF_SLOPE * (_FF_COMFORT_REF - outdoor)
    return quantize_command(u_ff, _SETPOINT_MIN, _SETPOINT_MAX)


def _u_ff(*, outdoor: float = _OUTDOOR_TEMP) -> float:
    return _FF_BASE + _FF_SLOPE * (_FF_COMFORT_REF - outdoor)


def _tick_app(
    *,
    plant_setpoint: object = 45.0,
    zone_temp: object = 20.0,
    setpoint: float = 22.0,
    hvac_action: str = "heating",
    plant_management: str = "on",
    outdoor: object = _OUTDOOR_TEMP,
    boiler_water: object = 50.0,
    args: dict | None = None,
    app_dir: str | Path | None = None,
) -> HvacApp:
    """Hass-stubbed HvacApp for control_tick (_config only)."""
    app = object.__new__(HvacApp)
    app._config = parse_config(args if args is not None else _tick_args())
    app._integral = 0.0
    app._rls = RlsState()
    app._rls_fallback_latched = False
    app._rls_fallback_reason = None
    app._rls_last_saved = copy_durable(app._rls)
    app._rls_force_rewrite = False
    app._rls_persist_fail_warned = False
    app.AD = SimpleNamespace(
        app_dir=Path(app_dir) if app_dir is not None else Path(tempfile.mkdtemp())
    )
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
        if entity_id == _BOILER_WATER:
            return boiler_water
        if entity_id == _CLIMATE:
            if attribute == "temperature":
                return setpoint
            if attribute == "hvac_action":
                return hvac_action
            return "heat"
        return None

    app.get_state = MagicMock(side_effect=get_state)
    return app


def _adaptive_args(
    *,
    kp_min: float = 0.0,
    kp_max: float = 100.0,
    ki_min: float = 0.0,
    ki_max: float = 10000.0,
) -> dict:
    args = _tick_args()
    args["boiler_water"] = _BOILER_WATER
    args["pid"] = {
        **args["pid"],
        "adaptive": True,
        "kp_min": kp_min,
        "kp_max": kp_max,
        "ki_min": ki_min,
        "ki_max": ki_max,
    }
    return args


def _set_value_writes(app: HvacApp) -> list[float]:
    return [
        c.kwargs["value"]
        for c in app.call_service.call_args_list
        if c.args and c.args[0] == "number/set_value"
    ]


def _info_msgs(app: HvacApp) -> list[str]:
    return [
        str(c.args[0])
        for c in app.log.call_args_list
        if c.args and (c.kwargs.get("level") is None or c.kwargs.get("level") == "INFO")
    ]


def _warn_msgs(app: HvacApp) -> list[str]:
    return [
        str(c.args[0])
        for c in app.log.call_args_list
        if c.kwargs.get("level") == "WARNING"
    ]


def _init_app(
    args: dict | None = None, *, app_dir: str | Path | None = None
) -> HvacApp:
    """Hass-stubbed app ready for initialize() (run_every + listen_state).

    Default plant-off so the explicit initialize control_tick is hands-off
    (∫ stays 0, no SWT write). Override get_state for gated-demand init tests.
    """
    app = object.__new__(HvacApp)
    app.args = args if args is not None else _tick_args()
    app.AD = SimpleNamespace(
        app_dir=Path(app_dir) if app_dir is not None else Path(tempfile.mkdtemp())
    )
    app.log = MagicMock()
    app.run_every = MagicMock()
    app.listen_state = MagicMock()
    app.call_service = MagicMock()

    def get_state(entity_id: str, attribute: str | None = None):
        if entity_id == _PLANT_MGMT:
            return "off"
        if entity_id == _OUTDOOR:
            return _OUTDOOR_TEMP
        if entity_id == _ZONE_TEMP:
            return 20.0
        if entity_id == _PLANT_SETPOINT:
            return 45.0
        if entity_id == _BOILER_WATER:
            return 50.0
        if entity_id == _CLIMATE:
            if attribute == "temperature":
                return 22.0
            if attribute == "hvac_action":
                return "heating"
            return "heat"
        return None

    app.get_state = MagicMock(side_effect=get_state)
    return app


def _init_gated_get_state(
    *,
    plant_management: str = "on",
    zone_temp: object = 20.0,
    setpoint: float = 22.0,
    hvac_action: str = "heating",
    plant_setpoint: object = 45.0,
    outdoor: object = _OUTDOOR_TEMP,
    boiler_water: object = 50.0,
):
    """get_state side_effect for initialize under gated demand."""

    def get_state(entity_id: str, attribute: str | None = None):
        if entity_id == _PLANT_MGMT:
            return plant_management
        if entity_id == _OUTDOOR:
            return outdoor
        if entity_id == _ZONE_TEMP:
            return zone_temp
        if entity_id == _PLANT_SETPOINT:
            return plant_setpoint
        if entity_id == _BOILER_WATER:
            return boiler_water
        if entity_id == _CLIMATE:
            if attribute == "temperature":
                return setpoint
            if attribute == "hvac_action":
                return hvac_action
            return "heat"
        return None

    return get_state


def _fire_control_event(app: HvacApp, entity: str = _PLANT_MGMT) -> None:
    app.control_event(entity, "state", None, "on", {})


def test_initialize_schedules_control_tick() -> None:
    app = _init_app()

    app.initialize()

    assert app._integral == 0.0
    assert _set_value_writes(app) == []
    app.run_every.assert_called_once()
    assert app.run_every.call_args.args[0].__func__ is HvacApp.control_tick
    assert app.run_every.call_args.args[1] == "now"
    assert app.run_every.call_args.args[2] == _CONTROL_INTERVAL


def test_initialize_under_demand_runs_first_tick() -> None:
    app = _init_app()
    app.get_state = MagicMock(side_effect=_init_gated_get_state())
    expected = _expected_command()

    app.initialize()

    assert _set_value_writes(app) == [expected]
    assert app._integral == pytest.approx(0.0)
    app.run_every.assert_called_once()
    assert app.run_every.call_args.args[1] == "now"
    assert app.run_every.call_args.args[2] == _CONTROL_INTERVAL


def test_initialize_under_demand_plant_unreadable_leaves_latch_false() -> None:
    app = _init_app()
    app.get_state = MagicMock(
        side_effect=_init_gated_get_state(plant_setpoint="unavailable")
    )

    app.initialize()

    assert _set_value_writes(app) == []
    assert app._integral == pytest.approx(0.0)


def _err_msgs(app: HvacApp) -> list[str]:
    return [
        str(c.args[0])
        for c in app.log.call_args_list
        if c.kwargs.get("level") == "ERROR"
    ]


def _bad_args(path: str, value: object) -> dict:
    args = _tick_args()
    if path.startswith("pid."):
        args["pid"][path.removeprefix("pid.")] = value
    elif path == "weight":
        args["zones"][0]["weight"] = value
    else:
        args[path] = value
    return args


@pytest.mark.parametrize(
    ("path", "value"),
    [
        pytest.param("setpoint_min", "abc", id="non-numeric"),
        pytest.param("pid.kp", float("nan"), id="non-finite"),
        pytest.param("pid.ki", -0.1, id="negative-gain"),
        pytest.param("control_interval", 60.7, id="fractional-interval"),
        pytest.param("control_interval", 1e15, id="interval-above-one-day"),
        pytest.param("pid.i_term_min", 1, id="i-term-excludes-zero"),
        pytest.param("base_water_temp", 55.1, id="base-out-of-bounds"),
        pytest.param("weight", float("inf"), id="non-finite-weight"),
        pytest.param("setpoint_max", 10**400, id="overflow"),
    ],
)
def test_initialize_logs_config_error_without_raising(path: str, value: object) -> None:
    app = _init_app(args=_bad_args(path, value))

    app.initialize()

    errors = _err_msgs(app)
    assert len(errors) == 1
    assert "HVAC config error" in errors[0]
    app.run_every.assert_not_called()
    app.listen_state.assert_not_called()


def test_initialize_warns_on_misspelled_zone_key() -> None:
    args = _tick_args()
    args["zones"] = [
        {
            "name": "living",
            "temperature": _ZONE_TEMP,
            "thermostats": [_CLIMATE],
            "weigth": 3,
        }
    ]
    app = _init_app(args=args)

    app.initialize()

    assert _warn_msgs(app) == [
        "HVAC config: ignoring legacy or unknown keys: zones[living].weigth",
        "Plant Management disabled",
    ]
    assert app._config.zones[0].weight == pytest.approx(1.0)
    app.run_every.assert_called_once()


def test_initialize_clean_args_no_warning() -> None:
    args = _tick_args()
    args.update({"module": "ha_smart_hvac", "class": "HvacApp", "name": "hvac"})
    app = _init_app(args=args)

    app.initialize()

    # No config warnings; plant-off initialize tick still hands-off.
    assert _warn_msgs(app) == ["Plant Management disabled"]
    app.run_every.assert_called_once()


def test_critical_zone_does_not_change_swt() -> None:
    """Max-error zone is logged only; SWT follows Outdoor FF only."""
    zone_two_temp = "sensor.zone_two_temp"
    climate_two = "climate.zone_two"
    args = _tick_args()
    args["zones"] = [
        {
            "name": "zone_one",
            "temperature": _ZONE_TEMP,
            "weight": 1.0,
            "thermostats": [_CLIMATE],
        },
        {
            "name": "zone_two",
            "temperature": zone_two_temp,
            "weight": 1.0,
            "thermostats": [climate_two],
        },
    ]
    expected = _expected_command()

    app = object.__new__(HvacApp)
    app._config = parse_config(args)
    app._integral = 0.0
    app._rls = RlsState()
    app._rls_fallback_latched = False
    app._rls_fallback_reason = None
    app.call_service = MagicMock()
    app.log = MagicMock()

    def get_state(entity_id: str, attribute: str | None = None):
        if entity_id == _PLANT_MGMT:
            return "on"
        if entity_id == _OUTDOOR:
            return _OUTDOOR_TEMP
        if entity_id == _ZONE_TEMP:
            return 21.5
        if entity_id == zone_two_temp:
            return 15.0
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
    joined = " ".join(_info_msgs(app))
    assert f"outdoor={_OUTDOOR_TEMP:.2f}" in joined
    assert f"u_ff={_u_ff():.2f}" in joined
    assert f"command={expected}" in joined
    assert "critical_zone=zone_two" in joined
    assert "u_pid=" not in joined


def test_partial_zone_skip_uses_successful_snapshots_only() -> None:
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
    app = object.__new__(HvacApp)
    app._config = parse_config(args)
    app._integral = 0.0
    app._rls = RlsState()
    app._rls_fallback_latched = False
    app._rls_fallback_reason = None
    app.call_service = MagicMock()
    app.log = MagicMock()

    def get_state(entity_id: str, attribute: str | None = None):
        if entity_id == _PLANT_MGMT:
            return "on"
        if entity_id == _OUTDOOR:
            return _OUTDOOR_TEMP
        if entity_id == _ZONE_TEMP:
            return 20.0
        if entity_id == zone_two_temp:
            return "unavailable"
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
    expected = _expected_command()

    app.control_tick({})

    assert _set_value_writes(app) == [expected]
    assert any("Zone zone_two: temperature unavailable" in m for m in _warn_msgs(app))


def test_partial_zone_skip_unavailable_thermostat_setpoint() -> None:
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
    app = object.__new__(HvacApp)
    app._config = parse_config(args)
    app._integral = 0.0
    app._rls = RlsState()
    app._rls_fallback_latched = False
    app._rls_fallback_reason = None
    app.call_service = MagicMock()
    app.log = MagicMock()

    def get_state(entity_id: str, attribute: str | None = None):
        if entity_id == _PLANT_MGMT:
            return "on"
        if entity_id == _OUTDOOR:
            return _OUTDOOR_TEMP
        if entity_id == _ZONE_TEMP:
            return 20.0
        if entity_id == zone_two_temp:
            return 19.0
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
                return "unavailable"
            if attribute == "hvac_action":
                return "heating"
            return "heat"
        return None

    app.get_state = MagicMock(side_effect=get_state)
    expected = _expected_command()

    app.control_tick({})

    assert _set_value_writes(app) == [expected]
    assert any("thermostat unavailable" in m for m in _warn_msgs(app))


def test_plant_on_idle_writes_zero_and_clears() -> None:
    app = _tick_app(zone_temp=22.0, setpoint=22.0, hvac_action="idle")
    app._integral = 12.0

    app.control_tick({})

    assert _set_value_writes(app) == [0.0]
    assert app._integral == 0.0
    assert "No heating demand; setpoint 0" in _info_msgs(app)
    assert not any("No heating demand" in m for m in _warn_msgs(app))


def test_idle_write_fail_still_clears() -> None:
    app = _tick_app(
        zone_temp=22.0,
        setpoint=22.0,
        hvac_action="idle",
        plant_setpoint="unavailable",
    )
    app._integral = 12.0

    app.control_tick({})

    assert _set_value_writes(app) == []
    assert app._integral == 0.0
    assert any("Plant setpoint unavailable" in m for m in _warn_msgs(app))


def test_plant_off_no_write_clears() -> None:
    app = _tick_app(plant_management="off")
    app._integral = 12.0

    app.control_tick({})

    assert _set_value_writes(app) == []
    app.call_service.assert_not_called()
    assert app._integral == 0.0


def test_no_valid_zones_writes_zero_and_clears() -> None:
    app = _tick_app(zone_temp="unavailable")
    app._integral = 5.0

    app.control_tick({})

    assert _set_value_writes(app) == [0.0]
    assert app._integral == 0.0
    assert any("No zones with valid readings this tick" in m for m in _warn_msgs(app))


def test_demand_fail_write_aborts_without_success_info() -> None:
    app = _tick_app(
        zone_temp=20.0,
        setpoint=22.0,
        plant_setpoint="unavailable",
    )

    app.control_tick({})

    assert _set_value_writes(app) == []
    assert not any("command=" in m for m in _info_msgs(app))
    assert any("Plant setpoint unavailable" in m for m in _warn_msgs(app))
    # R7: ∫ advances only when the plant entity is readable (written or already equal)
    assert app._integral == pytest.approx(0.0)


def test_event_plant_off_no_write_clears() -> None:
    app = _tick_app(plant_management="off")
    app._integral = 5.0

    _fire_control_event(app)

    assert _set_value_writes(app) == []
    assert app._integral == 0.0


def test_event_idle_writes_zero_clears() -> None:
    app = _tick_app(zone_temp=22.0, setpoint=22.0, hvac_action="idle")
    app._integral = 5.0

    _fire_control_event(app)

    assert _set_value_writes(app) == [0.0]
    assert app._integral == 0.0


def test_event_idle_write_fail_still_clears() -> None:
    app = _tick_app(
        zone_temp=22.0,
        setpoint=22.0,
        hvac_action="idle",
        plant_setpoint="unavailable",
    )
    app._integral = 5.0

    _fire_control_event(app)

    assert _set_value_writes(app) == []
    assert app._integral == 0.0
    assert any("Plant setpoint unavailable" in m for m in _warn_msgs(app))


def test_event_no_valid_zones_writes_zero_and_clears() -> None:
    app = _tick_app(zone_temp="unavailable")
    app._integral = 5.0

    _fire_control_event(app)

    assert _set_value_writes(app) == [0.0]
    assert app._integral == 0.0


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
    [None, "unavailable", "unknown", "not-a-float", object(), "nan", float("nan")],
)
def test_write_setpoint_fail_closed_when_entity_unreadable(raw_state):
    app = _write_stub(raw_state)

    ok = HvacApp._write_setpoint(app, 42.0)

    assert ok is False
    app.call_service.assert_not_called()


def test_non_finite_zone_temp_skips_zone_like_unavailable() -> None:
    app = _tick_app(zone_temp=float("nan"), plant_setpoint=45.0)
    app._integral = 5.0

    app.control_tick({})

    assert _set_value_writes(app) == [0.0]
    assert app._integral == 0.0


# --- RLS adaptive on control_tick (tracer) -----------------------------------


def test_initialize_creates_rls_state() -> None:
    app = _init_app()
    app.initialize()
    assert isinstance(app._rls, RlsState)
    assert app._rls.theta == [0.0, 0.0]
    assert app._rls_fallback_latched is False
    assert app._rls_fallback_reason is None


def test_initialize_logs_legacy_ki_warning_once() -> None:
    args = _tick_args()
    args["pid"]["ki"] = 0.2
    app = _init_app(args=args)
    app.initialize()
    warns = [m for m in _warn_msgs(app) if "legacy" in m and "pid.ki" in m]
    assert len(warns) == 1
    assert app._config.pid.legacy_ki_warning is True


def _count_rls_steps(monkeypatch: pytest.MonkeyPatch) -> dict[str, int]:
    stepped = {"n": 0}
    real_step = __import__("ha_smart_hvac.rls", fromlist=["rls_step"]).rls_step

    def _count(state, **kwargs) -> bool:
        stepped["n"] += 1
        return real_step(state, **kwargs)

    monkeypatch.setattr("ha_smart_hvac.hvac_app.rls_step", _count)
    return stepped


@pytest.mark.parametrize(
    ("clear_mode", "expect_zero_write"),
    [
        ("idle", True),
        ("plant_off", False),
        ("no_zones", True),
    ],
)
def test_clear_wipes_y_prev_keeps_rls_bookkeeping(
    clear_mode: str, expect_zero_write: bool
) -> None:
    kwargs: dict = {
        "zone_temp": 20.0,
        "setpoint": 22.0,
        "plant_setpoint": 45.0,
        "boiler_water": 50.0,
        "args": _adaptive_args(),
    }
    if clear_mode == "idle":
        kwargs["hvac_action"] = "idle"
    elif clear_mode == "plant_off":
        kwargs["plant_management"] = "off"
    else:
        kwargs["zone_temp"] = "unavailable"
    app = _tick_app(**kwargs)
    app._integral = 12.0
    app._rls.y_prev = 50.0
    app._rls.last_u = 42.0
    app._rls.theta = [0.8, 0.2]
    app._rls.p = [[1.0, 0.1], [0.1, 2.0]]
    app._rls.adapted_kp = 2.0
    app._rls.adapted_ki = 0.5

    app.control_tick({})

    assert app._rls.y_prev is None
    assert app._rls.last_u == pytest.approx(42.0)
    assert app._rls.theta == [0.8, 0.2]
    assert app._rls.p == [[1.0, 0.1], [0.1, 2.0]]
    assert app._rls.adapted_kp == pytest.approx(2.0)
    assert app._rls.adapted_ki == pytest.approx(0.5)
    assert app._integral == 0.0
    if expect_zero_write:
        assert _set_value_writes(app) == [0.0]
    else:
        assert _set_value_writes(app) == []


# --- RLS state JSON persistence ----------------------------------------------


def _rls_path(app: HvacApp) -> Path:
    return Path(app.app_dir) / STATE_FILENAME


def _write_valid_rls_json(
    path: Path,
    *,
    theta: list[float] | None = None,
    p: list[list[float]] | None = None,
    last_u: float | None = 45.0,
    adapted_kp: float | None = 1.5,
    adapted_ki: float | None = 12.0,
    extra: dict | None = None,
) -> None:
    payload = {
        "version": 1,
        "theta": theta if theta is not None else [0.9, 0.1],
        "p": p if p is not None else [[1.0, 0.0], [0.0, 1.0]],
        "last_u": last_u,
        "adapted_kp": adapted_kp,
        "adapted_ki": adapted_ki,
    }
    if extra:
        payload.update(extra)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_initialize_loads_valid_rls_state(tmp_path: Path) -> None:
    path = tmp_path / STATE_FILENAME
    _write_valid_rls_json(path)
    app = _init_app(args=_adaptive_args(), app_dir=tmp_path)
    app.initialize()

    assert app._rls.theta == [0.9, 0.1]
    assert app._rls.p == [[1.0, 0.0], [0.0, 1.0]]
    assert app._rls.last_u == pytest.approx(45.0)
    assert app._rls.adapted_kp == pytest.approx(1.5)
    assert app._rls.adapted_ki == pytest.approx(12.0)
    assert app._rls.y_prev is None
    assert app._rls_fallback_latched is False
    assert app._rls_force_rewrite is False
    assert durable_equal(app._rls_last_saved, copy_durable(app._rls))
    assert any("Loaded RLS state" in m for m in _info_msgs(app))


def test_initialize_missing_rls_state_silent_cold(tmp_path: Path) -> None:
    app = _init_app(args=_adaptive_args(), app_dir=tmp_path)
    app.initialize()

    assert app._rls.theta == [0.0, 0.0]
    assert app._rls_force_rewrite is False
    assert not any("RLS state" in m for m in _warn_msgs(app))
    assert not any("Loaded RLS state" in m for m in _info_msgs(app))


def test_initialize_corrupt_rls_sets_force(tmp_path: Path) -> None:
    path = tmp_path / STATE_FILENAME
    path.write_text("{not json", encoding="utf-8")
    app = _init_app(args=_adaptive_args(), app_dir=tmp_path)
    app.initialize()

    assert app._rls.theta == [0.0, 0.0]
    assert app._rls_force_rewrite is True
    assert any("unusable RLS state" in m for m in _warn_msgs(app))


def test_initialize_imc_invalid_theta_sets_force(tmp_path: Path) -> None:
    path = tmp_path / STATE_FILENAME
    _write_valid_rls_json(path, theta=[0.0, 0.1])  # a1 not in (0,1)
    app = _init_app(args=_adaptive_args(), app_dir=tmp_path)
    app.initialize()

    assert app._rls.theta == [0.0, 0.0]
    assert app._rls_force_rewrite is True
    assert any("IMC-invalid" in m for m in _warn_msgs(app))


def test_initialize_adapted_drop_reason_and_force(tmp_path: Path) -> None:
    path = tmp_path / STATE_FILENAME
    _write_valid_rls_json(path, adapted_kp=1.5, adapted_ki=None)
    app = _init_app(args=_adaptive_args(), app_dir=tmp_path)
    app.initialize()

    assert app._rls.theta == [0.9, 0.1]
    assert app._rls.adapted_kp is None
    assert app._rls.adapted_ki is None
    assert app._rls_force_rewrite is True
    assert app._rls_fallback_latched is False
    assert sum(1 for m in _warn_msgs(app) if "mismatch" in m) == 1
    assert any("Loaded RLS state" in m for m in _info_msgs(app))


def test_force_rewrite_stays_set_ff_demand_does_not_persist(
    tmp_path: Path,
) -> None:
    """FF demand path does not call persist; force flag and disk stay as after load."""
    path = tmp_path / STATE_FILENAME
    _write_valid_rls_json(path, adapted_kp=1.5, adapted_ki=None)
    before = path.read_text()
    app = _init_app(args=_adaptive_args(), app_dir=tmp_path)
    app.initialize()
    assert app._rls_force_rewrite is True
    assert app._rls.adapted_kp is None
    last_u_before = 42.0
    app._rls.last_u = last_u_before

    app.get_state = MagicMock(
        side_effect=lambda entity_id, attribute=None: {
            _PLANT_MGMT: "on",
            _OUTDOOR: _OUTDOOR_TEMP,
            _ZONE_TEMP: 20.04,
            _PLANT_SETPOINT: 42.0,
            _BOILER_WATER: 50.0,
            _CLIMATE: (
                22.0
                if attribute == "temperature"
                else ("heating" if attribute == "hvac_action" else "heat")
            ),
        }.get(entity_id)
    )
    app.call_service = MagicMock()

    app.control_tick({})

    assert app._rls_force_rewrite is True
    assert app._rls.last_u == last_u_before
    assert path.read_text() == before


def test_initialize_adapted_out_of_rail_drop(tmp_path: Path) -> None:
    path = tmp_path / STATE_FILENAME
    _write_valid_rls_json(path, adapted_kp=999.0, adapted_ki=1.0)
    app = _init_app(
        args=_adaptive_args(kp_min=0.0, kp_max=10.0, ki_min=0.0, ki_max=100.0),
        app_dir=tmp_path,
    )
    app.initialize()

    assert app._rls.adapted_kp is None
    assert app._rls_force_rewrite is True
    assert sum(1 for m in _warn_msgs(app) if "out_of_rail" in m) == 1


def test_initialize_unknown_keys_ignored(tmp_path: Path) -> None:
    path = tmp_path / STATE_FILENAME
    _write_valid_rls_json(path, extra={"y_prev": 50.0, "noise": True})
    app = _init_app(args=_adaptive_args(), app_dir=tmp_path)
    app.initialize()

    assert app._rls.y_prev is None
    assert app._rls.theta == [0.9, 0.1]
    assert any("Loaded RLS state" in m for m in _info_msgs(app))


def test_initialize_adaptive_off_skips_load(tmp_path: Path) -> None:
    path = tmp_path / STATE_FILENAME
    _write_valid_rls_json(path)
    app = _init_app(args=_tick_args(), app_dir=tmp_path)
    app.initialize()

    assert app._rls.theta == [0.0, 0.0]
    assert not any("Loaded RLS state" in m for m in _info_msgs(app))


def test_load_missing_race_after_is_file_is_silent_cold(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / STATE_FILENAME
    path.write_text("{}", encoding="utf-8")
    app = _init_app(args=_adaptive_args(), app_dir=tmp_path)

    real_is_file = Path.is_file
    seen = {"n": 0}

    def _is_file(self: Path) -> bool:
        if self == path:
            seen["n"] += 1
            if seen["n"] == 1:
                return True
            return False
        return real_is_file(self)

    monkeypatch.setattr(Path, "is_file", _is_file)
    monkeypatch.setattr("ha_smart_hvac.hvac_app.load_rls_state", lambda *_a, **_k: None)

    app.initialize()

    assert app._rls.theta == [0.0, 0.0]
    assert app._rls_force_rewrite is False
    assert not any("Ignoring unusable" in m for m in _warn_msgs(app))


def test_initialize_after_latched_restores_adapted_clears_latch(
    tmp_path: Path,
) -> None:
    path = tmp_path / STATE_FILENAME
    _write_valid_rls_json(path)
    app = _init_app(args=_adaptive_args(), app_dir=tmp_path)
    app.initialize()
    app._rls_fallback_latched = True
    app._rls_fallback_reason = "out_of_band"
    # Simulate App reload after a latched episode.
    app.initialize()
    assert app._rls_fallback_latched is False
    assert app._rls_fallback_reason is None
    assert app._rls.adapted_kp == pytest.approx(1.5)
    assert app._rls.adapted_ki == pytest.approx(12.0)


# --- Weather FF demand Behavior & acceptance (entry 1) ---


def test_demand_tick_writes_ff_command_no_integral_no_rls() -> None:
    app = _tick_app(plant_setpoint=45.0)
    app._integral = 1.5
    app._rls.last_u = 41.0
    app._rls.y_prev = 50.0
    expected = _expected_command()

    app.control_tick({})

    assert _set_value_writes(app) == [expected]
    assert app._integral == pytest.approx(1.5)
    assert app._rls.last_u == pytest.approx(41.0)
    assert app._rls.y_prev == pytest.approx(50.0)
    joined = " ".join(_info_msgs(app))
    assert f"outdoor={_OUTDOOR_TEMP:.2f}" in joined
    assert f"u_ff={_u_ff():.2f}" in joined
    assert f"command={expected}" in joined
    assert "u_pid=" not in joined
    assert ", e=" not in joined and not joined.startswith("e=")


def test_demand_tick_pins_mild_outdoor_to_example_min_rail() -> None:
    """Example rails 50/60: outdoor≈10 → u_ff≈46 pins command to 50.0."""
    args = _tick_args()
    args["setpoint_min"] = 50
    args["setpoint_max"] = 60
    args["base_water_temp"] = 51  # stay inside new rails (parse only)
    app = _tick_app(plant_setpoint=45.0, outdoor=10.0, args=args)

    app.control_tick({})

    assert _set_value_writes(app) == [50.0]
    joined = " ".join(_info_msgs(app))
    assert "u_ff=46.00" in joined
    assert "command=50.0" in joined


def test_demand_event_writes_ff_same_as_tick() -> None:
    app = _tick_app(plant_setpoint=45.0)
    expected = _expected_command()

    _fire_control_event(app)

    assert _set_value_writes(app) == [expected]
    assert app._integral == pytest.approx(0.0)


def test_outdoor_event_under_demand_refreshes_command() -> None:
    app = _tick_app(plant_setpoint=45.0, outdoor=10.0)
    app.control_tick({})
    assert _set_value_writes(app) == [_expected_command(outdoor=10.0)]

    app.call_service.reset_mock()
    app.log.reset_mock()
    # colder outdoor → higher u_ff
    app.get_state = MagicMock(
        side_effect=_init_gated_get_state(outdoor=0.0, plant_setpoint=45.0)
    )
    _fire_control_event(app, entity=_OUTDOOR)

    assert _set_value_writes(app) == [_expected_command(outdoor=0.0)]


def test_zone_air_event_under_held_demand_refreshes_ff() -> None:
    """Held demand: non-Outdoor control events still run the FF writer."""
    app = _tick_app(plant_setpoint=45.0, outdoor=10.0)
    app.control_tick({})
    app.call_service.reset_mock()
    # Change outdoor via get_state while firing zone-air event — FF uses re-read.
    app.get_state = MagicMock(
        side_effect=_init_gated_get_state(outdoor=5.0, plant_setpoint=45.0)
    )
    _fire_control_event(app, entity=_ZONE_TEMP)

    assert _set_value_writes(app) == [_expected_command(outdoor=5.0)]


def test_weights_unusable_under_demand_still_writes_ff() -> None:
    args = _tick_args()
    args["zones"] = [
        {
            "name": _ZONE_NAME,
            "temperature": _ZONE_TEMP,
            "weight": 0.0,
            "thermostats": [_CLIMATE],
        }
    ]
    app = _tick_app(plant_setpoint=45.0, args=args)
    expected = _expected_command()

    app.control_tick({})

    assert _set_value_writes(app) == [expected]
    assert app._integral == pytest.approx(0.0)


def test_outdoor_unavailable_goes_idle() -> None:
    app = _tick_app(plant_setpoint=45.0, outdoor="unavailable")
    app._integral = 3.0

    app.control_tick({})

    assert _set_value_writes(app) == [0.0]
    assert app._integral == 0.0
    assert any(
        f"Outdoor temperature unavailable: {_OUTDOOR}" in m for m in _warn_msgs(app)
    )


def test_outdoor_miss_plant_unreadable_clears_no_success_log() -> None:
    app = _tick_app(plant_setpoint="unavailable", outdoor="unavailable")
    app._integral = 3.0

    app.control_tick({})

    assert _set_value_writes(app) == []
    assert app._integral == 0.0
    assert any("Plant setpoint unavailable" in m for m in _warn_msgs(app))
    assert any(
        f"Outdoor temperature unavailable: {_OUTDOOR}" in m for m in _warn_msgs(app)
    )
    assert not any("command=" in m for m in _info_msgs(app))


def test_plant_off_outdoor_unavailable_no_write_no_outdoor_idle() -> None:
    app = _tick_app(plant_management="off", outdoor="unavailable")
    app._integral = 4.0

    app.control_tick({})

    assert _set_value_writes(app) == []
    assert app._integral == 0.0
    assert "Plant Management disabled" in _warn_msgs(app)
    assert all("Outdoor temperature unavailable" not in m for m in _warn_msgs(app))
    # plant-off must not read Outdoor
    assert all(
        (not c.args) or c.args[0] != _OUTDOOR for c in app.get_state.call_args_list
    )


def test_equal_float_ff_skip_still_logs_success() -> None:
    expected = _expected_command()
    app = _tick_app(plant_setpoint=expected)
    app._integral = 2.0
    app._rls.last_u = 40.0

    app.control_tick({})

    assert _set_value_writes(app) == []
    assert app._integral == pytest.approx(2.0)
    assert app._rls.last_u == pytest.approx(40.0)
    assert any(f"command={expected}" in m for m in _info_msgs(app))


def test_plant_unreadable_on_demand_no_success_log_holds_ephemeral() -> None:
    app = _tick_app(plant_setpoint="unavailable")
    app._integral = 0.5
    app._rls.last_u = 40.0

    app.control_tick({})

    assert _set_value_writes(app) == []
    assert app._integral == pytest.approx(0.5)
    assert app._rls.last_u == pytest.approx(40.0)
    assert any("Plant setpoint unavailable" in m for m in _warn_msgs(app))
    assert not any("command=" in m for m in _info_msgs(app))


def test_non_finite_u_ff_goes_idle(monkeypatch: pytest.MonkeyPatch) -> None:
    import ha_smart_hvac.hvac_app as hvac_mod

    monkeypatch.setattr(hvac_mod, "weather_feedforward", lambda *_a, **_k: float("nan"))
    app = _tick_app(plant_setpoint=45.0)
    app._integral = 2.0

    app.control_tick({})

    assert _set_value_writes(app) == [0.0]
    assert app._integral == 0.0
    assert any("Non-finite weather feedforward" in m for m in _warn_msgs(app))


def test_init_outdoor_unavailable_goes_idle() -> None:
    app = _init_app()
    app.get_state = MagicMock(side_effect=_init_gated_get_state(outdoor="unavailable"))

    app.initialize()

    assert _set_value_writes(app) == [0.0]
    assert app._integral == 0.0
    assert any(
        f"Outdoor temperature unavailable: {_OUTDOOR}" in m for m in _warn_msgs(app)
    )


def test_initialize_registers_outdoor_listener() -> None:
    app = _init_app()
    app.initialize()

    listens = app.listen_state.call_args_list
    entity_only = {
        c.args[1] for c in listens if len(c.args) >= 2 and not c.kwargs.get("attribute")
    }
    assert _OUTDOOR in entity_only
    assert _PLANT_MGMT in entity_only


def test_adaptive_ff_demand_does_not_step_or_persist_rls(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    args = _adaptive_args()
    app = _tick_app(plant_setpoint=45.0, args=args, app_dir=tmp_path)
    app._config = parse_config(args)
    app._rls.last_u = 40.0
    app._rls.y_prev = 48.0
    stepped = {"n": 0}
    persisted = {"n": 0}

    def boom(*_a, **_k):
        stepped["n"] += 1
        raise AssertionError("rls_step must not run on FF demand")

    monkeypatch.setattr(app, "_maybe_rls_step", boom)
    monkeypatch.setattr(
        app,
        "_maybe_persist_rls",
        lambda: persisted.__setitem__("n", persisted["n"] + 1),
    )

    app.control_tick({})

    assert stepped["n"] == 0
    assert persisted["n"] == 0
    assert app._rls.last_u == pytest.approx(40.0)
    assert not (tmp_path / STATE_FILENAME).exists()
