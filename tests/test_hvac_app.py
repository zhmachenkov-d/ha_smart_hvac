"""Tests for outdoor weather-curve Set Water Temperature control loop."""

from __future__ import annotations

import ast
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from ha_smart_hvac.config import parse_config
from ha_smart_hvac.feedforward import quantize_command
from ha_smart_hvac.hvac_app import HvacApp

_RLS_STATE_FILENAME = "rls_state.json"

_SETPOINT_MIN = 40.0
_SETPOINT_MAX = 55.0
_CONTROL_INTERVAL = 300
_FF_BASE = 37.0
_FF_SLOPE = 0.9
_FF_COMFORT_REF = 20.0
_OUTDOOR_TEMP = 10.0  # u_ff = 37 + 0.9*(20-10) = 46.0

_OUTDOOR = "sensor.outdoor"
_FLAME_ON = "binary_sensor.flame_on"
_CH_ACTIVE = "binary_sensor.ch_active"
_PLANT_MGMT = "switch.pm"
_PLANT_SETPOINT = "number.plant_setpoint"
_ZONE_TEMP = "sensor.zone_one_temp"
_CLIMATE = "climate.zone_one"
_ZONE_NAME = "zone_one"
_TRV_CLOSURE = "number.zone_one_trv_closure"
_TRV_ACCURACY = "number.zone_one_trv_accuracy"
_CLIMATE_GENERIC = "climate.zone_one_generic"
_TRV_CLOSURE_2 = "number.zone_two_trv_closure"
_TRV_ACCURACY_2 = "number.zone_two_trv_accuracy"
_ZONE_TEMP_2 = "sensor.zone_two_temp"
_CLIMATE_2 = "climate.zone_two_trv"

_HVAC_APP_PATH = (
    Path(__file__).resolve().parents[1] / "apps" / "ha_smart_hvac" / "hvac_app.py"
)


def _tick_args() -> dict:
    return {
        "outdoor_temperature": _OUTDOOR,
        "flame_on": _FLAME_ON,
        "ch_active": _CH_ACTIVE,
        "plant_management": _PLANT_MGMT,
        "plant_setpoint": _PLANT_SETPOINT,
        "setpoint_min": _SETPOINT_MIN,
        "setpoint_max": _SETPOINT_MAX,
        "control_interval": _CONTROL_INTERVAL,
        "weather_feedforward": {
            "base": _FF_BASE,
            "slope": _FF_SLOPE,
            "comfort_ref": _FF_COMFORT_REF,
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
    args: dict | None = None,
    app_dir: str | Path | None = None,
) -> HvacApp:
    """Hass-stubbed HvacApp for control_tick (_config only)."""
    app = object.__new__(HvacApp)
    app._config = parse_config(args if args is not None else _tick_args())
    app.AD = SimpleNamespace(
        app_dir=Path(app_dir) if app_dir is not None else Path(tempfile.mkdtemp())
    )
    app.call_service = MagicMock()
    app.log = MagicMock()
    app.set_state = MagicMock()
    app.run_in = MagicMock(return_value="hold-handle")
    app.cancel_timer = MagicMock()
    app._flame_trip_latched = False
    app._flame_on_since = None
    app._flame_trip_hold_handle = None
    app._flame_trip_hold_token = 0
    app._zone_heating_prior = {}
    app._trv_overshoot_latched = set()
    app._monotonic = MagicMock(return_value=0.0)

    def get_state(entity_id: str, attribute: str | None = None):
        if entity_id == _PLANT_MGMT:
            return plant_management
        if entity_id == _OUTDOOR:
            return outdoor
        if entity_id == _FLAME_ON:
            return "off"
        if entity_id == _CH_ACTIVE:
            return "on"
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


def _set_value_writes(app: HvacApp) -> list[float]:
    return [
        c.kwargs["value"]
        for c in app.call_service.call_args_list
        if c.args and c.args[0] == "number/set_value"
    ]


def _set_value_by_entity(app: HvacApp) -> list[tuple[str, float]]:
    return [
        (c.kwargs["entity_id"], c.kwargs["value"])
        for c in app.call_service.call_args_list
        if c.args and c.args[0] == "number/set_value"
    ]


def _trv_tick_args() -> dict:
    args = _tick_args()
    args["zones"] = [
        {
            "name": _ZONE_NAME,
            "temperature": _ZONE_TEMP,
            "thermostats": [
                {
                    "climate": _CLIMATE,
                    "valve_closure": _TRV_CLOSURE,
                    "accuracy": _TRV_ACCURACY,
                },
                _CLIMATE_GENERIC,
            ],
        }
    ]
    return args


def _trv_app(
    *,
    plant_management: str = "on",
    zone_temp: object = 20.0,
    setpoint: object = 22.0,
    accuracy: object = 0.5,
    closure: object = 50.0,
    hvac_action: str = "heating",
    plant_setpoint: object = 45.0,
    outdoor: object = _OUTDOOR_TEMP,
    valve_closure_floor: float | None = None,
) -> HvacApp:
    args = _trv_tick_args()
    if valve_closure_floor is not None:
        args["valve_closure_floor"] = valve_closure_floor
    app = _tick_app(
        plant_management=plant_management,
        zone_temp=zone_temp,
        setpoint=setpoint,
        hvac_action=hvac_action,
        plant_setpoint=plant_setpoint,
        outdoor=outdoor,
        args=args,
    )
    base_get = app.get_state.side_effect

    def get_state(entity_id: str, attribute: str | None = None):
        if entity_id == _TRV_CLOSURE:
            return closure
        if entity_id == _TRV_ACCURACY:
            return accuracy
        if entity_id == _CLIMATE_GENERIC:
            if attribute == "temperature":
                return setpoint
            if attribute == "hvac_action":
                return hvac_action
            return "heat"
        return base_get(entity_id, attribute)

    app.get_state = MagicMock(side_effect=get_state)
    return app


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
    (no SWT write). Override get_state for plant-on demand init tests.
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
    app.run_in = MagicMock(return_value="hold-handle")
    app.cancel_timer = MagicMock()

    def get_state(entity_id: str, attribute: str | None = None):
        if entity_id == _PLANT_MGMT:
            return "off"
        if entity_id == _OUTDOOR:
            return _OUTDOOR_TEMP
        if entity_id == _ZONE_TEMP:
            return 20.0
        if entity_id == _PLANT_SETPOINT:
            return 45.0
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
):
    """get_state side_effect for initialize under plant-on demand."""

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

    return get_state


def _fire_control_event(app: HvacApp, entity: str = _PLANT_MGMT) -> None:
    app.control_event(entity, "state", None, "on", {})


def test_hvac_app_does_not_import_rls_or_pid_quantize() -> None:
    """Import-lock: live App must not pull rls or pid (quantize/clamp or module)."""
    source = _HVAC_APP_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name != "ha_smart_hvac.rls"
                assert not alias.name.startswith("ha_smart_hvac.rls.")
                assert alias.name != "rls"
                assert alias.name != "ha_smart_hvac.pid"
                assert not alias.name.startswith("ha_smart_hvac.pid.")
                assert alias.name != "pid"
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            names = {alias.name for alias in node.names}
            # Absolute: ha_smart_hvac.rls[.*]; relative: from .rls / from ..rls
            rls_mod = mod == "ha_smart_hvac.rls" or mod.startswith("ha_smart_hvac.rls.")
            rls_rel = node.level > 0 and (mod == "rls" or mod.startswith("rls."))
            if rls_mod or rls_rel:
                raise AssertionError(
                    f"rls import forbidden: from {mod!r} level={node.level}"
                )
            # from ha_smart_hvac import rls; from . import rls
            if "rls" in names and (
                mod == "ha_smart_hvac" or (node.level > 0 and mod == "")
            ):
                raise AssertionError("rls import forbidden: import rls from package")
            pid_mod = (
                mod == "ha_smart_hvac.pid"
                or mod.startswith("ha_smart_hvac.pid.")
                or (node.level > 0 and (mod == "pid" or mod.startswith("pid.")))
            )
            if pid_mod:
                raise AssertionError(
                    f"pid import forbidden: from {mod!r} level={node.level}"
                )
            if "pid" in names and (
                mod == "ha_smart_hvac" or (node.level > 0 and mod == "")
            ):
                raise AssertionError("pid import forbidden: import pid from package")


def test_initialize_schedules_control_tick(tmp_path: Path) -> None:
    app = _init_app(app_dir=tmp_path)

    app.initialize()

    assert _set_value_writes(app) == []
    app.run_every.assert_called_once()
    assert app.run_every.call_args.args[0].__func__ is HvacApp.control_tick
    assert app.run_every.call_args.args[1] == "now"
    assert app.run_every.call_args.args[2] == _CONTROL_INTERVAL
    assert any(
        "HVAC weather-curve SWT app initialized" in str(c.args[0])
        for c in app.log.call_args_list
        if c.args
    )
    assert not (tmp_path / _RLS_STATE_FILENAME).exists()


def test_initialize_under_demand_runs_first_tick(tmp_path: Path) -> None:
    app = _init_app(app_dir=tmp_path)
    app.get_state = MagicMock(side_effect=_init_gated_get_state())
    expected = _expected_command()

    app.initialize()

    assert _set_value_writes(app) == [expected]
    app.run_every.assert_called_once()
    assert app.run_every.call_args.args[1] == "now"
    assert app.run_every.call_args.args[2] == _CONTROL_INTERVAL
    assert not (tmp_path / _RLS_STATE_FILENAME).exists()


def test_initialize_under_demand_plant_unreadable_skips_write() -> None:
    app = _init_app()
    app.get_state = MagicMock(
        side_effect=_init_gated_get_state(plant_setpoint="unavailable")
    )

    app.initialize()

    assert _set_value_writes(app) == []


def _err_msgs(app: HvacApp) -> list[str]:
    return [
        str(c.args[0])
        for c in app.log.call_args_list
        if c.kwargs.get("level") == "ERROR"
    ]


def _bad_args(path: str, value: object) -> dict:
    args = _tick_args()
    if path == "weight":
        args["zones"][0]["weight"] = value
    else:
        args[path] = value
    return args


@pytest.mark.parametrize(
    ("path", "value"),
    [
        pytest.param("setpoint_min", "abc", id="non-numeric"),
        pytest.param("control_interval", 60.7, id="fractional-interval"),
        pytest.param("control_interval", 1e15, id="interval-above-one-day"),
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

    assert _warn_msgs(app) == ["Plant Management disabled"]
    app.run_every.assert_called_once()


def test_initialize_warns_on_legacy_water_law_keys() -> None:
    """Leftover pid / base_water_temp / supply-trip keys → ignored_keys WARN."""
    args = _tick_args()
    args["pid"] = {"kp": 1.0, "adaptive": True}
    args["base_water_temp"] = 51
    args["boiler_water"] = "sensor.legacy"
    app = _init_app(args=args)

    app.initialize()

    warns = _warn_msgs(app)
    assert warns[0].startswith("HVAC config: ignoring legacy or unknown keys:")
    assert "base_water_temp" in warns[0]
    assert "boiler_water" in warns[0]
    assert "pid" in warns[0]
    assert "Plant Management disabled" in warns
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
    app.call_service = MagicMock()
    app.log = MagicMock()
    app._flame_trip_latched = False
    app._flame_on_since = None
    app._flame_trip_hold_handle = None
    app._flame_trip_hold_token = 0
    app._zone_heating_prior = {}
    app._trv_overshoot_latched = set()

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
    app.call_service = MagicMock()
    app.log = MagicMock()
    app._flame_trip_latched = False
    app._flame_on_since = None
    app._flame_trip_hold_handle = None
    app._flame_trip_hold_token = 0
    app._zone_heating_prior = {}
    app._trv_overshoot_latched = set()

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
    app.call_service = MagicMock()
    app.log = MagicMock()
    app._flame_trip_latched = False
    app._flame_on_since = None
    app._flame_trip_hold_handle = None
    app._flame_trip_hold_token = 0
    app._zone_heating_prior = {}
    app._trv_overshoot_latched = set()

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


def test_plant_on_idle_writes_zero() -> None:
    app = _tick_app(zone_temp=22.0, setpoint=22.0, hvac_action="idle")

    app.control_tick({})

    assert _set_value_writes(app) == [0.0]
    assert "No heating demand; setpoint 0" in _info_msgs(app)
    assert not any("No heating demand" in m for m in _warn_msgs(app))


def test_idle_write_fail_still_logs() -> None:
    app = _tick_app(
        zone_temp=22.0,
        setpoint=22.0,
        hvac_action="idle",
        plant_setpoint="unavailable",
    )

    app.control_tick({})

    assert _set_value_writes(app) == []
    assert "No heating demand; setpoint 0" in _info_msgs(app)
    assert any("Plant setpoint unavailable" in m for m in _warn_msgs(app))


def test_plant_off_no_write() -> None:
    app = _tick_app(plant_management="off")

    app.control_tick({})

    assert _set_value_writes(app) == []
    app.call_service.assert_not_called()
    assert "Plant Management disabled" in _warn_msgs(app)


def test_no_valid_zones_writes_zero() -> None:
    app = _tick_app(zone_temp="unavailable")

    app.control_tick({})

    assert _set_value_writes(app) == [0.0]
    assert any("No zones with valid readings" in m for m in _warn_msgs(app))


def test_demand_fail_write_aborts_without_success_info() -> None:
    app = _tick_app(plant_setpoint="unavailable")

    app.control_tick({})

    assert _set_value_writes(app) == []
    assert any("Plant setpoint unavailable" in m for m in _warn_msgs(app))
    assert not any("command=" in m for m in _info_msgs(app))


def test_event_plant_off_no_write() -> None:
    app = _tick_app(plant_management="off")

    _fire_control_event(app)

    assert _set_value_writes(app) == []
    assert "Plant Management disabled" in _warn_msgs(app)


def test_event_idle_writes_zero() -> None:
    app = _tick_app(zone_temp=22.0, setpoint=22.0, hvac_action="idle")

    _fire_control_event(app)

    assert _set_value_writes(app) == [0.0]
    assert "No heating demand; setpoint 0" in _info_msgs(app)


def test_event_idle_write_fail_still_logs() -> None:
    app = _tick_app(
        zone_temp=22.0,
        setpoint=22.0,
        hvac_action="idle",
        plant_setpoint="unavailable",
    )

    _fire_control_event(app)

    assert _set_value_writes(app) == []
    assert "No heating demand; setpoint 0" in _info_msgs(app)
    assert any("Plant setpoint unavailable" in m for m in _warn_msgs(app))


def test_event_no_valid_zones_writes_zero() -> None:
    app = _tick_app(zone_temp="unavailable")

    _fire_control_event(app)

    assert _set_value_writes(app) == [0.0]
    assert any("No zones with valid readings" in m for m in _warn_msgs(app))


@pytest.mark.parametrize("raw_state", [45.0, "45.0", 45])
def test_write_setpoint_skips_set_value_when_entity_float_equals(raw_state):
    app = _tick_app(plant_setpoint=raw_state)
    assert app._write_setpoint(45.0) is True
    assert _set_value_writes(app) == []
    assert not any(
        c.args and c.args[0] == "number/set_value"
        for c in app.call_service.call_args_list
    )


def test_write_setpoint_calls_set_value_when_entity_float_differs():
    app = _tick_app(plant_setpoint=40.0)
    assert app._write_setpoint(45.0) is True
    calls = [
        {"entity_id": c.kwargs["entity_id"], "value": c.kwargs["value"]}
        for c in app.call_service.call_args_list
        if c.args and c.args[0] == "number/set_value"
    ]
    assert calls == [{"entity_id": _PLANT_SETPOINT, "value": 45.0}]


@pytest.mark.parametrize(
    "raw_state",
    [None, "unavailable", "unknown", "nan", "abc", float("nan"), object()],
)
def test_write_setpoint_fail_closed_when_entity_unreadable(raw_state):
    app = _tick_app(plant_setpoint=raw_state)
    assert app._write_setpoint(45.0) is False
    assert _set_value_writes(app) == []
    assert not any(
        c.args and c.args[0] == "number/set_value"
        for c in app.call_service.call_args_list
    )


def test_non_finite_zone_temp_skips_zone_like_unavailable() -> None:
    app = _tick_app(zone_temp=float("nan"))

    app.control_tick({})

    assert _set_value_writes(app) == [0.0]
    assert any("No zones with valid readings" in m for m in _warn_msgs(app))


def test_demand_tick_writes_ff_command_no_rls_state(tmp_path: Path) -> None:
    app = _tick_app(plant_setpoint=45.0, app_dir=tmp_path)
    expected = _expected_command()

    app.control_tick({})

    assert _set_value_writes(app) == [expected]
    joined = " ".join(_info_msgs(app))
    assert f"outdoor={_OUTDOOR_TEMP:.2f}" in joined
    assert f"u_ff={_u_ff():.2f}" in joined
    assert f"command={expected}" in joined
    assert "u_pid=" not in joined
    assert ", e=" not in joined and not joined.startswith("e=")
    assert not (tmp_path / _RLS_STATE_FILENAME).exists()


def test_demand_tick_pins_mild_outdoor_to_example_min_rail() -> None:
    """Example rails 50/60: outdoor≈10 → u_ff≈46 pins command to 50.0."""
    args = _tick_args()
    args["setpoint_min"] = 50
    args["setpoint_max"] = 60
    app = _tick_app(plant_setpoint=45.0, outdoor=10.0, args=args)

    app.control_tick({})

    assert _set_value_writes(app) == [50.0]
    joined = " ".join(_info_msgs(app))
    assert "u_ff=46.00" in joined
    assert "command=50.0" in joined


def test_demand_tick_pins_cold_outdoor_to_max_rail() -> None:
    """Fixture rails 40/55: outdoor=-20 → u_ff=73 pins command to 55.0."""
    app = _tick_app(plant_setpoint=45.0, outdoor=-20.0)

    app.control_tick({})

    assert _set_value_writes(app) == [55.0]
    joined = " ".join(_info_msgs(app))
    assert "u_ff=73.00" in joined
    assert "command=55.0" in joined


def test_demand_event_writes_ff_same_as_tick(tmp_path: Path) -> None:
    app = _tick_app(plant_setpoint=45.0, app_dir=tmp_path)
    expected = _expected_command()

    _fire_control_event(app)

    assert _set_value_writes(app) == [expected]
    joined = " ".join(_info_msgs(app))
    assert f"outdoor={_OUTDOOR_TEMP:.2f}" in joined
    assert f"u_ff={_u_ff():.2f}" in joined
    assert f"command={expected}" in joined
    assert "u_pid=" not in joined
    assert ", e=" not in joined and not joined.startswith("e=")
    assert not (tmp_path / _RLS_STATE_FILENAME).exists()


def test_outdoor_event_under_demand_refreshes_command() -> None:
    app = _tick_app(plant_setpoint=45.0, outdoor=10.0)
    app.control_tick({})
    assert _set_value_writes(app) == [_expected_command(outdoor=10.0)]

    app.call_service.reset_mock()
    app.log.reset_mock()

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


def test_outdoor_unavailable_goes_idle() -> None:
    app = _tick_app(plant_setpoint=45.0, outdoor="unavailable")

    app.control_tick({})

    assert _set_value_writes(app) == [0.0]
    assert any(
        f"Outdoor temperature unavailable: {_OUTDOOR}" in m for m in _warn_msgs(app)
    )


def test_outdoor_miss_plant_unreadable_clears_no_success_log() -> None:
    app = _tick_app(plant_setpoint="unavailable", outdoor="unavailable")

    app.control_tick({})

    assert _set_value_writes(app) == []
    assert any("Plant setpoint unavailable" in m for m in _warn_msgs(app))
    assert any(
        f"Outdoor temperature unavailable: {_OUTDOOR}" in m for m in _warn_msgs(app)
    )
    assert not any("command=" in m for m in _info_msgs(app))


def test_plant_off_outdoor_unavailable_no_write_no_outdoor_idle() -> None:
    app = _tick_app(plant_management="off", outdoor="unavailable")

    app.control_tick({})

    assert _set_value_writes(app) == []
    assert "Plant Management disabled" in _warn_msgs(app)
    assert all("Outdoor temperature unavailable" not in m for m in _warn_msgs(app))

    assert all(
        (not c.args) or c.args[0] != _OUTDOOR for c in app.get_state.call_args_list
    )


def test_equal_float_ff_skip_still_logs_success() -> None:
    expected = _expected_command()
    app = _tick_app(plant_setpoint=expected)

    app.control_tick({})

    assert _set_value_writes(app) == []
    assert any(f"command={expected}" in m for m in _info_msgs(app))


def test_plant_unreadable_on_demand_no_success_log() -> None:
    app = _tick_app(plant_setpoint="unavailable")

    app.control_tick({})

    assert _set_value_writes(app) == []
    assert any("Plant setpoint unavailable" in m for m in _warn_msgs(app))
    assert not any("command=" in m for m in _info_msgs(app))


def test_non_finite_u_ff_goes_idle(monkeypatch: pytest.MonkeyPatch) -> None:
    import ha_smart_hvac.hvac_app as hvac_mod

    monkeypatch.setattr(hvac_mod, "weather_feedforward", lambda *_a, **_k: float("nan"))
    app = _tick_app(plant_setpoint=45.0)

    app.control_tick({})

    assert _set_value_writes(app) == [0.0]
    assert any("Non-finite weather feedforward" in m for m in _warn_msgs(app))


def test_init_outdoor_unavailable_goes_idle() -> None:
    app = _init_app()
    app.get_state = MagicMock(side_effect=_init_gated_get_state(outdoor="unavailable"))

    app.initialize()

    assert _set_value_writes(app) == [0.0]
    assert any(
        f"Outdoor temperature unavailable: {_OUTDOOR}" in m for m in _warn_msgs(app)
    )


def test_initialize_registers_outdoor_and_flame_listeners() -> None:
    app = _init_app()
    app.initialize()

    listens = app.listen_state.call_args_list
    entity_only = {
        c.args[1] for c in listens if len(c.args) >= 2 and not c.kwargs.get("attribute")
    }
    assert _OUTDOOR in entity_only
    assert _FLAME_ON in entity_only
    assert _CH_ACTIVE in entity_only
    assert _PLANT_MGMT in entity_only
    flame_listens = [c for c in listens if len(c.args) >= 2 and c.args[1] == _FLAME_ON]
    ch_listens = [c for c in listens if len(c.args) >= 2 and c.args[1] == _CH_ACTIVE]
    assert len(flame_listens) == 1
    assert flame_listens[0].args[0].__func__ is HvacApp.flame_event
    assert len(ch_listens) == 1
    assert ch_listens[0].args[0].__func__ is HvacApp.ch_active_event


def _demand_get_state(
    *,
    flame_on: object = "off",
    ch_active: object = "on",
    outdoor: object = _OUTDOOR_TEMP,
    plant_management: str = "on",
    hvac_action: str = "heating",
    plant_setpoint: object = 45.0,
):
    """get_state for flame short-on tests under configurable gates."""

    def get_state(entity_id: str, attribute: str | None = None):
        if entity_id == _PLANT_MGMT:
            return plant_management
        if entity_id == _OUTDOOR:
            return outdoor
        if entity_id == _FLAME_ON:
            return flame_on
        if entity_id == _CH_ACTIVE:
            return ch_active
        if entity_id == _ZONE_TEMP:
            return 20.0
        if entity_id == _PLANT_SETPOINT:
            return plant_setpoint
        if entity_id == _CLIMATE:
            if attribute == "temperature":
                return 22.0
            if attribute == "hvac_action":
                return hvac_action
            return "heat"
        return None

    return get_state


def _flame_trip_app(**kwargs) -> HvacApp:
    ch_active = kwargs.pop("ch_active", "on")
    flame_on = kwargs.pop("flame_on", "off")
    app = _tick_app(**kwargs)
    gate_kwargs = {
        "plant_management": kwargs.get("plant_management", "on"),
        "hvac_action": kwargs.get("hvac_action", "heating"),
        "plant_setpoint": kwargs.get("plant_setpoint", 45.0),
        "outdoor": kwargs.get("outdoor", _OUTDOOR_TEMP),
        "ch_active": ch_active,
        "flame_on": flame_on,
    }
    app.get_state = MagicMock(side_effect=_demand_get_state(**gate_kwargs))
    return app


def _fire_flame(app: HvacApp, *, old: object, new: object) -> None:
    app.flame_event(_FLAME_ON, "state", old, new, {})


def test_flame_short_on_latches_and_writes_zero() -> None:
    app = _flame_trip_app()
    times = iter([100.0, 150.0])
    app._monotonic = MagicMock(side_effect=lambda: next(times))

    _fire_flame(app, old="off", new="on")
    assert app._flame_on_since == 100.0
    assert not app._flame_trip_latched

    _fire_flame(app, old="on", new="off")
    assert app._flame_on_since is None
    assert app._flame_trip_latched
    assert _set_value_writes(app) == [0.0]
    app.run_in.assert_called_once()
    assert app.run_in.call_args.args[0].__func__ is HvacApp._flame_trip_hold_expired
    assert app.run_in.call_args.args[1] == app._config.flame_trip_hold_s
    assert app._flame_trip_hold_handle == app.run_in.return_value
    assert app.run_in.call_args.kwargs.get("token") == app._flame_trip_hold_token


def test_flame_commissioned_min_and_hold_used_by_app() -> None:
    """Non-default yaml min/hold drive latch threshold and run_in delay."""
    args = _tick_args()
    args["flame_on_min_s"] = 60
    args["flame_trip_hold_s"] = 180
    app = _flame_trip_app(args=args)
    assert app._config.flame_on_min_s == 60
    assert app._config.flame_trip_hold_s == 180

    # duration 100 >= 60 → no latch
    times = iter([0.0, 100.0])
    app._monotonic = MagicMock(side_effect=lambda: next(times))
    _fire_flame(app, old="off", new="on")
    _fire_flame(app, old="on", new="off")
    assert not app._flame_trip_latched
    app.run_in.assert_not_called()
    assert _set_value_writes(app) == []

    # duration 50 < 60 → latch with hold 180
    app.call_service.reset_mock()
    app.run_in.reset_mock()
    times = iter([0.0, 50.0])
    app._monotonic = MagicMock(side_effect=lambda: next(times))
    _fire_flame(app, old="off", new="on")
    _fire_flame(app, old="on", new="off")
    assert app._flame_trip_latched
    assert _set_value_writes(app) == [0.0]
    assert app.run_in.call_args.args[1] == 180


def test_flame_short_on_hold_expiry_runs_curve_e2e() -> None:
    """Short-on latch via flame_event then hold expiry ADV8 → weather-curve demand."""
    app = _flame_trip_app(plant_setpoint=45.0)
    times = iter([100.0, 150.0])
    app._monotonic = MagicMock(side_effect=lambda: next(times))
    order: list[str] = []
    real_trv = app._apply_trv_law
    real_prelude = app._gate_prelude

    def trv_tracking():
        order.append("trv")
        return real_trv()

    def prelude_tracking():
        order.append("prelude")
        return real_prelude()

    app._apply_trv_law = trv_tracking  # type: ignore[method-assign]
    app._gate_prelude = prelude_tracking  # type: ignore[method-assign]

    _fire_flame(app, old="off", new="on")
    _fire_flame(app, old="on", new="off")
    assert app._flame_trip_latched
    token = app._flame_trip_hold_token
    handle = app._flame_trip_hold_handle

    app._flame_trip_hold_expired({"token": token})

    assert not app._flame_trip_latched
    assert app._flame_trip_hold_handle is None
    app.cancel_timer.assert_called_with(handle)
    assert order[:2] == ["trv", "prelude"]
    assert _set_value_writes(app) == [0.0, _expected_command()]


def test_flame_long_on_does_not_latch() -> None:
    app = _flame_trip_app()
    times = iter([0.0, 301.0])
    app._monotonic = MagicMock(side_effect=lambda: next(times))

    _fire_flame(app, old="off", new="on")
    _fire_flame(app, old="on", new="off")

    assert app._flame_on_since is None
    assert not app._flame_trip_latched
    app.run_in.assert_not_called()
    assert _set_value_writes(app) == []


def test_flame_write_fail_does_not_latch_clears_since() -> None:
    app = _flame_trip_app(plant_setpoint="unavailable")
    times = iter([0.0, 10.0])
    app._monotonic = MagicMock(side_effect=lambda: next(times))
    app.get_state = MagicMock(
        side_effect=_demand_get_state(plant_setpoint="unavailable")
    )

    _fire_flame(app, old="off", new="on")
    assert app._flame_on_since == 0.0
    _fire_flame(app, old="on", new="off")

    assert app._flame_on_since is None
    assert not app._flame_trip_latched
    app.run_in.assert_not_called()
    assert _set_value_writes(app) == []
    assert any("SWT write failed, not latching" in m for m in _warn_msgs(app))


def test_flame_fall_gate_closed_wipes_since_no_latch() -> None:
    """Armed under open gate; demand lost before fall → wipe since, no latch."""
    app = _flame_trip_app()
    times = iter([0.0, 10.0])
    app._monotonic = MagicMock(side_effect=lambda: next(times))

    _fire_flame(app, old="off", new="on")
    assert app._flame_on_since == 0.0

    app.get_state = MagicMock(side_effect=_demand_get_state(hvac_action="idle"))
    _fire_flame(app, old="on", new="off")

    assert app._flame_on_since is None
    assert not app._flame_trip_latched
    app.run_in.assert_not_called()
    assert _set_value_writes(app) == []


def test_flame_ch_active_off_before_fall_wipes_since() -> None:
    app = _flame_trip_app()
    times = iter([0.0, 10.0])
    app._monotonic = MagicMock(side_effect=lambda: next(times))

    _fire_flame(app, old="off", new="on")
    assert app._flame_on_since == 0.0

    app.get_state = MagicMock(side_effect=_demand_get_state(ch_active="off"))
    _fire_flame(app, old="on", new="off")

    assert app._flame_on_since is None
    assert not app._flame_trip_latched
    assert _set_value_writes(app) == []


def test_ch_active_listener_wipes_since_without_latch() -> None:
    app = _flame_trip_app()
    app._flame_on_since = 42.0
    app.get_state = MagicMock(side_effect=_demand_get_state(ch_active="off"))

    app.ch_active_event(_CH_ACTIVE, "state", "on", "off", {})

    assert app._flame_on_since is None
    assert not app._flame_trip_latched
    assert _set_value_writes(app) == []


def test_ch_active_open_gate_preserves_armed_since() -> None:
    app = _flame_trip_app()
    times = iter([100.0])
    app._monotonic = MagicMock(side_effect=lambda: next(times))
    _fire_flame(app, old="off", new="on")
    assert app._flame_on_since == 100.0

    app.ch_active_event(_CH_ACTIVE, "state", "on", "on", {})

    assert app._flame_on_since == 100.0
    assert not app._flame_trip_latched
    assert _set_value_writes(app) == []


def test_ch_active_off_event_wipes_even_when_current_state_on() -> None:
    """Queued CH-off must wipe even if get_state already bounced back to on."""
    app = _flame_trip_app()
    app._flame_on_since = 42.0
    app.get_state = MagicMock(side_effect=_demand_get_state(ch_active="on"))

    app.ch_active_event(_CH_ACTIVE, "state", "on", "off", {})

    assert app._flame_on_since is None
    assert not app._flame_trip_latched
    assert _set_value_writes(app) == []


def test_open_gate_fall_without_since_does_not_latch() -> None:
    app = _flame_trip_app()
    app._flame_on_since = None

    _fire_flame(app, old="on", new="off")

    assert app._flame_on_since is None
    assert not app._flame_trip_latched
    app.run_in.assert_not_called()
    assert _set_value_writes(app) == []


def test_closed_gate_arm_does_not_set_since() -> None:
    app = _flame_trip_app(plant_management="off")

    _fire_flame(app, old="off", new="on")

    assert app._flame_on_since is None
    assert not app._flame_trip_latched


def test_flame_short_on_under_demand_outdoor_unavailable() -> None:
    """Observe gate never requires Outdoor."""
    app = _flame_trip_app()
    times = iter([0.0, 10.0])
    app._monotonic = MagicMock(side_effect=lambda: next(times))
    app.get_state = MagicMock(side_effect=_demand_get_state(outdoor="unavailable"))

    _fire_flame(app, old="off", new="on")
    _fire_flame(app, old="on", new="off")

    assert app._flame_trip_latched
    assert _set_value_writes(app) == [0.0]


def test_flame_none_to_on_does_not_arm() -> None:
    app = _flame_trip_app()
    app._monotonic = MagicMock(return_value=5.0)

    _fire_flame(app, old=None, new="on")

    assert app._flame_on_since is None
    assert not app._flame_trip_latched


@pytest.mark.parametrize("old", ["unavailable", "unknown"])
def test_flame_unreadable_to_on_does_not_arm(old: str) -> None:
    app = _flame_trip_app()
    app._monotonic = MagicMock(return_value=5.0)

    _fire_flame(app, old=old, new="on")

    assert app._flame_on_since is None
    assert not app._flame_trip_latched
    assert _set_value_writes(app) == []


@pytest.mark.parametrize("new", ["unavailable", "unknown", None])
def test_flame_on_to_unreadable_wipes_since_no_latch(new: object) -> None:
    app = _flame_trip_app()
    times = iter([0.0, 10.0])
    app._monotonic = MagicMock(side_effect=lambda: next(times))

    _fire_flame(app, old="off", new="on")
    assert app._flame_on_since == 0.0

    _fire_flame(app, old="on", new=new)

    assert app._flame_on_since is None
    assert not app._flame_trip_latched
    app.run_in.assert_not_called()
    assert _set_value_writes(app) == []


def test_flame_duration_equal_min_does_not_latch() -> None:
    app = _flame_trip_app()
    times = iter([0.0, app._config.flame_on_min_s])
    app._monotonic = MagicMock(side_effect=lambda: next(times))

    _fire_flame(app, old="off", new="on")
    _fire_flame(app, old="on", new="off")

    assert app._flame_on_since is None
    assert not app._flame_trip_latched
    app.run_in.assert_not_called()
    assert _set_value_writes(app) == []


def test_ch_active_off_to_on_while_flame_already_on_does_not_arm() -> None:
    """CH rising while flame already on must not invent a since or latch."""
    app = _flame_trip_app()
    app.get_state = MagicMock(
        side_effect=_demand_get_state(flame_on="on", ch_active="on")
    )
    app._flame_on_since = None

    app.ch_active_event(_CH_ACTIVE, "state", "off", "on", {})

    assert app._flame_on_since is None
    assert not app._flame_trip_latched
    assert _set_value_writes(app) == []


def test_latched_demand_writes_zero_no_ff() -> None:
    app = _flame_trip_app()
    app._flame_trip_latched = True
    app.control_tick({})
    assert _set_value_writes(app) == [0.0]
    assert not any("u_ff=" in m for m in _info_msgs(app))


def test_flame_hold_expiry_gated_runs_trv_then_curve() -> None:
    """ADV8: hold expiry clears, applies TRV, then Outdoor prelude + demand."""
    app = _flame_trip_app(plant_setpoint=45.0)
    app._flame_trip_latched = True
    app._flame_trip_hold_handle = "hold-handle"
    app._flame_trip_hold_token = 7
    order: list[str] = []
    real_trv = app._apply_trv_law
    real_prelude = app._gate_prelude

    def trv_tracking():
        order.append("trv")
        return real_trv()

    def prelude_tracking():
        order.append("prelude")
        return real_prelude()

    app._apply_trv_law = trv_tracking  # type: ignore[method-assign]
    app._gate_prelude = prelude_tracking  # type: ignore[method-assign]

    app._flame_trip_hold_expired({"token": 7})

    assert not app._flame_trip_latched
    app.cancel_timer.assert_called_once_with("hold-handle")
    assert order[:2] == ["trv", "prelude"]
    assert _set_value_writes(app) == [_expected_command()]


def test_flame_hold_expiry_closed_gate_clears_only() -> None:
    app = _flame_trip_app(plant_management="off")
    app._flame_trip_latched = True
    app._flame_trip_hold_handle = "hold-handle"
    app._flame_trip_hold_token = 3
    trv = MagicMock(wraps=app._apply_trv_law)
    app._apply_trv_law = trv  # type: ignore[method-assign]

    app._flame_trip_hold_expired({"token": 3})

    assert not app._flame_trip_latched
    assert _set_value_writes(app) == []
    trv.assert_called_once()


def test_idle_clears_flame_trip_state() -> None:
    app = _flame_trip_app(zone_temp=22.0, setpoint=22.0, hvac_action="idle")
    app.get_state = MagicMock(
        side_effect=_demand_get_state(hvac_action="idle", plant_setpoint=45.0)
    )
    app._flame_trip_latched = True
    app._flame_on_since = 1.0
    app._flame_trip_hold_handle = "hold-handle"

    app.control_tick({})

    assert not app._flame_trip_latched
    assert app._flame_on_since is None
    app.cancel_timer.assert_called_once_with("hold-handle")
    assert _set_value_writes(app) == [0.0]


def test_plant_off_clears_flame_trip_state() -> None:
    app = _flame_trip_app(plant_management="off")
    app.get_state = MagicMock(side_effect=_demand_get_state(plant_management="off"))
    app._flame_trip_latched = True
    app._flame_on_since = 1.0
    app._flame_trip_hold_handle = "hold-handle"

    app.control_tick({})

    assert not app._flame_trip_latched
    assert app._flame_on_since is None
    app.cancel_timer.assert_called_with("hold-handle")
    assert _set_value_writes(app) == []


def test_plant_off_wipes_armed_since_without_latch() -> None:
    """Plant-off mid-burn wipes armed since; no latch and no SWT write."""
    app = _flame_trip_app(plant_management="off")
    app.get_state = MagicMock(side_effect=_demand_get_state(plant_management="off"))
    app._flame_trip_latched = False
    app._flame_on_since = 42.0
    app._flame_trip_hold_handle = None

    app.control_tick({})

    assert not app._flame_trip_latched
    assert app._flame_on_since is None
    assert _set_value_writes(app) == []


def test_idle_wipes_armed_since_without_latch() -> None:
    """Idle mid-burn disarms since; successful idle write-0; never latched."""
    app = _flame_trip_app(zone_temp=22.0, setpoint=22.0, hvac_action="idle")
    app.get_state = MagicMock(
        side_effect=_demand_get_state(hvac_action="idle", plant_setpoint=45.0)
    )
    app._flame_trip_latched = False
    app._flame_on_since = 42.0

    app.control_tick({})

    assert not app._flame_trip_latched
    assert app._flame_on_since is None
    assert _set_value_writes(app) == [0.0]


def test_already_latched_flame_observe_wipes_since_no_reassert() -> None:
    """Latched observer never re-asserts or restarts hold."""
    app = _flame_trip_app()
    app._flame_trip_latched = True
    app._flame_trip_hold_handle = "existing"
    app._flame_on_since = 1.0
    app._monotonic = MagicMock(return_value=50.0)

    _fire_flame(app, old="off", new="on")
    assert app._flame_on_since is None

    _fire_flame(app, old="on", new="off")
    assert app._flame_on_since is None
    assert app._flame_trip_latched
    assert app._flame_trip_hold_handle == "existing"
    app.run_in.assert_not_called()
    assert _set_value_writes(app) == []


def test_orphan_hold_callback_after_clear_no_demand_write() -> None:
    app = _flame_trip_app(plant_setpoint=45.0)
    app._flame_trip_latched = False
    app._flame_trip_hold_handle = None
    app._flame_trip_hold_token = 2

    app._flame_trip_hold_expired({"token": 1})

    assert not app._flame_trip_latched
    assert app._flame_trip_hold_handle is None
    assert app._flame_trip_hold_token == 2
    assert _set_value_writes(app) == []


def test_orphan_hold_callback_after_retrip_does_not_clear_new_latch() -> None:
    app = _flame_trip_app(plant_setpoint=45.0)
    app._flame_trip_latched = True
    app._flame_trip_hold_handle = "new-handle"
    app._flame_trip_hold_token = 5

    app._flame_trip_hold_expired({"token": 4})

    assert app._flame_trip_latched
    assert app._flame_trip_hold_handle == "new-handle"
    assert _set_value_writes(app) == []


def test_latched_demand_equal_float_skips_set_value() -> None:
    app = _flame_trip_app(plant_setpoint=0.0)
    app.get_state = MagicMock(side_effect=_demand_get_state(plant_setpoint=0.0))
    app._flame_trip_latched = True
    app.control_tick({})
    assert _set_value_writes(app) == []
    assert app._flame_trip_latched


def test_idle_write_fail_keeps_latch_disarms_hold() -> None:
    app = _flame_trip_app(
        zone_temp=22.0, setpoint=22.0, hvac_action="idle", plant_setpoint="unavailable"
    )
    app.get_state = MagicMock(
        side_effect=_demand_get_state(hvac_action="idle", plant_setpoint="unavailable")
    )
    app._flame_trip_latched = True
    app._flame_on_since = 1.0
    app._flame_trip_hold_handle = "hold-handle"
    app._flame_trip_hold_token = 1

    app.control_tick({})

    assert app._flame_trip_latched
    assert app._flame_on_since is None
    assert app._flame_trip_hold_handle is None
    app.cancel_timer.assert_called_once_with("hold-handle")


def test_ungated_flame_event_wipes_since() -> None:
    app = _flame_trip_app(plant_management="off")
    app.get_state = MagicMock(side_effect=_demand_get_state(plant_management="off"))
    app._flame_on_since = 1.0

    _fire_flame(app, old="on", new="off")

    assert app._flame_on_since is None
    assert not app._flame_trip_latched


def _two_zone_trip_args() -> dict:
    args = _tick_args()
    args["zones"] = [
        {
            "name": "zone_one",
            "temperature": _ZONE_TEMP,
            "thermostats": [_CLIMATE],
        },
        {
            "name": "zone_two",
            "temperature": "sensor.zone_two_temp",
            "thermostats": ["climate.zone_two"],
        },
    ]
    return args


def _two_zone_get_state(
    *,
    zone_one_action: str = "heating",
    zone_two_action: str = "idle",
    zone_two_temp: object = 19.0,
    plant_setpoint: object = 45.0,
    plant_management: str = "on",
    outdoor: object = _OUTDOOR_TEMP,
):
    def get_state(entity_id: str, attribute: str | None = None):
        if entity_id == _PLANT_MGMT:
            return plant_management
        if entity_id == _OUTDOOR:
            return outdoor
        if entity_id == _FLAME_ON:
            return "off"
        if entity_id == _CH_ACTIVE:
            return "on"
        if entity_id == _ZONE_TEMP:
            return 20.0
        if entity_id == "sensor.zone_two_temp":
            return zone_two_temp
        if entity_id == _PLANT_SETPOINT:
            return plant_setpoint
        if entity_id == _CLIMATE:
            if attribute == "temperature":
                return 22.0
            if attribute == "hvac_action":
                return zone_one_action
            return "heat"
        if entity_id == "climate.zone_two":
            if attribute == "temperature":
                return 22.0
            if attribute == "hvac_action":
                return zone_two_action
            return "heat"
        return None

    return get_state


def _two_zone_app(**kwargs) -> HvacApp:
    plant_setpoint = kwargs.pop("plant_setpoint", 45.0)
    app = _tick_app(args=_two_zone_trip_args(), plant_setpoint=plant_setpoint)
    app.get_state = MagicMock(
        side_effect=_two_zone_get_state(plant_setpoint=plant_setpoint, **kwargs)
    )
    return app


def test_empty_zone_read_leaves_prior_unchanged() -> None:
    """Empty `_read_zones` → prior unchanged (no seed, no edge)."""
    app = _two_zone_app(zone_one_action="heating", zone_two_temp="unavailable")
    # Force both zones unreadable: zone_one temp unavailable too.
    base = _two_zone_get_state(zone_one_action="heating", zone_two_temp="unavailable")

    def get_state(entity_id: str, attribute: str | None = None):
        if entity_id == _ZONE_TEMP:
            return "unavailable"
        return base(entity_id, attribute)

    app.get_state = MagicMock(side_effect=get_state)
    prior = {"zone_one": True, "zone_two": False}
    app._zone_heating_prior = dict(prior)

    app.control_tick({})

    assert app._zone_heating_prior == prior
    assert any("No zones with valid readings" in m for m in _warn_msgs(app))


def test_plant_off_leaves_zone_heating_prior_unchanged() -> None:
    """Plant-off: no zone read → prior unchanged; `_hands_off` clear unchanged."""
    app = _two_zone_app(plant_management="off")
    prior = {"zone_one": True, "zone_two": False}
    app._zone_heating_prior = dict(prior)
    app._flame_trip_latched = True
    app._flame_on_since = 1.0
    app._flame_trip_hold_handle = "hold-handle"

    app.control_tick({})

    assert app._zone_heating_prior == prior
    assert not app._flame_trip_latched
    assert app._flame_on_since is None
    app.cancel_timer.assert_called_with("hold-handle")
    assert "Plant Management disabled" in _warn_msgs(app)


def test_outdoor_miss_leaves_zone_heating_prior_unchanged() -> None:
    """Outdoor unavailable before zone read → prior unchanged; idle clear path."""
    app = _two_zone_app(outdoor="unavailable")
    prior = {"zone_one": True, "zone_two": False}
    app._zone_heating_prior = dict(prior)
    app._flame_trip_latched = True
    app._flame_on_since = 1.0
    app._flame_trip_hold_handle = "hold-handle"

    app.control_tick({})

    assert app._zone_heating_prior == prior
    assert not app._flame_trip_latched
    assert app._flame_on_since is None
    app.cancel_timer.assert_called_with("hold-handle")
    assert any(
        f"Outdoor temperature unavailable: {_OUTDOOR}" in m for m in _warn_msgs(app)
    )


def test_rising_edge_clears_latch_and_writes_curve() -> None:
    """Latched; prior A=True B=False; B idle→heating → clear + weather-curve SWT."""
    app = _two_zone_app(zone_one_action="heating", zone_two_action="idle")
    app._flame_trip_latched = True
    app._flame_on_since = 1.0
    app._flame_trip_hold_handle = "hold-handle"
    app._zone_heating_prior = {"zone_one": True, "zone_two": False}
    expected = _expected_command()

    app.get_state = MagicMock(
        side_effect=_two_zone_get_state(
            zone_one_action="heating", zone_two_action="heating"
        )
    )
    app.control_tick({})

    assert not app._flame_trip_latched
    assert app._flame_on_since is None
    app.cancel_timer.assert_called_once_with("hold-handle")
    assert _set_value_writes(app) == [expected]
    assert app._zone_heating_prior == {"zone_one": True, "zone_two": True}
    assert any("u_ff=" in m for m in _info_msgs(app))


def test_latched_no_new_edge_keeps_latch_and_writes_zero() -> None:
    """Latched; same zones still heating → latch stays; SWT 0."""
    app = _two_zone_app(zone_one_action="heating", zone_two_action="heating")
    app._flame_trip_latched = True
    app._flame_on_since = 1.0
    app._flame_trip_hold_handle = "hold-handle"
    app._zone_heating_prior = {"zone_one": True, "zone_two": True}

    app.control_tick({})

    assert app._flame_trip_latched
    assert app._flame_on_since == 1.0
    assert app._flame_trip_hold_handle == "hold-handle"
    app.cancel_timer.assert_not_called()
    assert _set_value_writes(app) == [0.0]
    assert not any("u_ff=" in m for m in _info_msgs(app))
    assert app._zone_heating_prior == {"zone_one": True, "zone_two": True}


def test_latched_one_zone_falls_idle_keeps_latch() -> None:
    """Latched; one zone falls idle, another still heats → latch stays."""
    app = _two_zone_app(zone_one_action="heating", zone_two_action="idle")
    app._flame_trip_latched = True
    app._zone_heating_prior = {"zone_one": True, "zone_two": True}

    app.control_tick({})

    assert app._flame_trip_latched
    assert _set_value_writes(app) == [0.0]
    assert app._zone_heating_prior == {"zone_one": True, "zone_two": False}


def test_latched_missing_prior_key_is_not_edge() -> None:
    """Missing prior key ≠ False→True edge; latch stays; prior is filled in."""
    app = _two_zone_app(zone_one_action="heating", zone_two_action="heating")
    app._flame_trip_latched = True
    app._flame_trip_hold_handle = "hold-handle"
    app._zone_heating_prior = {"zone_one": True}  # zone_two key absent

    app.control_tick({})

    assert app._flame_trip_latched
    assert app._flame_trip_hold_handle == "hold-handle"
    assert _set_value_writes(app) == [0.0]
    assert app._zone_heating_prior == {"zone_one": True, "zone_two": True}


def test_rising_edge_clear_via_control_event() -> None:
    """Rising-edge clear also runs on control_event (same prelude path)."""
    app = _two_zone_app(zone_one_action="heating", zone_two_action="idle")
    app._flame_trip_latched = True
    app._flame_on_since = 1.0
    app._flame_trip_hold_handle = "hold-handle"
    app._zone_heating_prior = {"zone_one": True, "zone_two": False}
    expected = _expected_command()

    app.get_state = MagicMock(
        side_effect=_two_zone_get_state(
            zone_one_action="heating", zone_two_action="heating"
        )
    )
    _fire_control_event(app, entity="climate.zone_two")

    assert not app._flame_trip_latched
    assert app._flame_on_since is None
    app.cancel_timer.assert_called_once_with("hold-handle")
    assert _set_value_writes(app) == [expected]
    assert app._zone_heating_prior == {"zone_one": True, "zone_two": True}


def test_latched_no_new_edge_via_control_event() -> None:
    """Latched; same zones still heating on control_event → latch stays; SWT 0."""
    app = _two_zone_app(zone_one_action="heating", zone_two_action="heating")
    app._flame_trip_latched = True
    app._flame_on_since = 1.0
    app._flame_trip_hold_handle = "hold-handle"
    app._zone_heating_prior = {"zone_one": True, "zone_two": True}

    _fire_control_event(app, entity="climate.zone_two")

    assert app._flame_trip_latched
    assert app._flame_on_since == 1.0
    assert app._flame_trip_hold_handle == "hold-handle"
    app.cancel_timer.assert_not_called()
    assert _set_value_writes(app) == [0.0]
    assert app._zone_heating_prior == {"zone_one": True, "zone_two": True}
    assert not any("u_ff=" in m for m in _info_msgs(app))


def test_rising_edge_not_latched_updates_prior_and_writes_curve() -> None:
    """Not latched; zone rises → prior updates; weather-curve path unchanged."""
    app = _two_zone_app(zone_one_action="heating", zone_two_action="idle")
    app._zone_heating_prior = {"zone_one": True, "zone_two": False}
    expected = _expected_command()

    app.get_state = MagicMock(
        side_effect=_two_zone_get_state(
            zone_one_action="heating", zone_two_action="heating"
        )
    )
    app.control_tick({})

    assert not app._flame_trip_latched
    assert _set_value_writes(app) == [expected]
    assert app._zone_heating_prior == {"zone_one": True, "zone_two": True}
    assert any("u_ff=" in m for m in _info_msgs(app))


def test_latched_empty_prior_seeds_without_clear() -> None:
    """Prior empty while latched and zones heating → seed prior; latch stays."""
    app = _two_zone_app(zone_one_action="heating", zone_two_action="heating")
    app._flame_trip_latched = True
    app._zone_heating_prior = {}
    app._flame_trip_hold_handle = "hold-handle"

    app.control_tick({})

    assert app._flame_trip_latched
    assert app._flame_trip_hold_handle == "hold-handle"
    assert _set_value_writes(app) == [0.0]
    assert app._zone_heating_prior == {"zone_one": True, "zone_two": True}
    assert not any("u_ff=" in m for m in _info_msgs(app))


def test_latched_all_false_prior_rising_edge_clears() -> None:
    """Non-empty all-False prior (not empty seed) + heating → clear + curve SWT."""
    app = _two_zone_app(zone_one_action="heating", zone_two_action="heating")
    app._flame_trip_latched = True
    app._flame_on_since = 1.0
    app._flame_trip_hold_handle = "hold-handle"
    app._zone_heating_prior = {"zone_one": False, "zone_two": False}
    expected = _expected_command()

    app.control_tick({})

    assert not app._flame_trip_latched
    assert app._flame_on_since is None
    app.cancel_timer.assert_called_once_with("hold-handle")
    assert _set_value_writes(app) == [expected]
    assert app._zone_heating_prior == {"zone_one": True, "zone_two": True}
    assert any("u_ff=" in m for m in _info_msgs(app))


def test_idle_no_demand_updates_prior_all_false() -> None:
    """Zones read; none heating → update prior (all false); then idle 0 path."""
    app = _two_zone_app(zone_one_action="idle", zone_two_action="idle")
    app._zone_heating_prior = {"zone_one": True, "zone_two": False}

    app.control_tick({})

    assert _set_value_writes(app) == [0.0]
    assert "No heating demand; setpoint 0" in _info_msgs(app)
    assert app._zone_heating_prior == {"zone_one": False, "zone_two": False}


def test_skip_then_return_rising_edge_clears_latch() -> None:
    """Decision A: skipped zone forced False in prior; later heating → clear."""
    app = _two_zone_app(zone_one_action="heating", zone_two_temp="unavailable")
    app._flame_trip_latched = True
    app._flame_on_since = 1.0
    app._flame_trip_hold_handle = "hold-handle"
    # Seed via prelude while zone_two skipped → prior zone_two False (Decision A).
    app.control_tick({})
    assert app._flame_trip_latched
    assert app._zone_heating_prior == {"zone_one": True, "zone_two": False}
    app.call_service.reset_mock()
    app.cancel_timer.reset_mock()

    expected = _expected_command()
    app.get_state = MagicMock(
        side_effect=_two_zone_get_state(
            zone_one_action="heating",
            zone_two_action="heating",
            zone_two_temp=19.0,
        )
    )
    app.control_tick({})

    assert not app._flame_trip_latched
    assert app._flame_on_since is None
    app.cancel_timer.assert_called_once_with("hold-handle")
    assert _set_value_writes(app) == [expected]
    assert app._zone_heating_prior == {"zone_one": True, "zone_two": True}


def test_rising_edge_clear_does_not_use_critical_zone() -> None:
    """Rising-edge clear uses _clear_flame_trip_state; CZ stays diagnostics."""
    app = _two_zone_app(zone_one_action="heating", zone_two_action="idle")
    app._flame_trip_latched = True
    app._zone_heating_prior = {"zone_one": True, "zone_two": False}

    # Rising zone_two (small error); CZ would be zone_one if used for clear.
    def get_state(entity_id: str, attribute: str | None = None):
        if entity_id == _PLANT_MGMT:
            return "on"
        if entity_id == _OUTDOOR:
            return _OUTDOOR_TEMP
        if entity_id == _FLAME_ON:
            return "off"
        if entity_id == _CH_ACTIVE:
            return "on"
        if entity_id == _ZONE_TEMP:
            return 15.0  # error 7 → Critical Zone
        if entity_id == "sensor.zone_two_temp":
            return 21.0  # error 1 → rising zone
        if entity_id == _PLANT_SETPOINT:
            return 45.0
        if entity_id == _CLIMATE:
            if attribute == "temperature":
                return 22.0
            if attribute == "hvac_action":
                return "heating"
            return "heat"
        if entity_id == "climate.zone_two":
            if attribute == "temperature":
                return 22.0
            if attribute == "hvac_action":
                return "heating"
            return "heat"
        return None

    app.get_state = MagicMock(side_effect=get_state)
    clear = MagicMock(wraps=app._clear_flame_trip_state)
    app._clear_flame_trip_state = clear  # type: ignore[method-assign]

    app.control_tick({})

    clear.assert_called_once()
    assert not app._flame_trip_latched
    assert _set_value_writes(app) == [_expected_command()]
    joined = " ".join(_info_msgs(app))
    assert "critical_zone=zone_one" in joined
    assert "u_ff=" in joined


def test_latched_trip_path_does_not_use_critical_zone() -> None:
    """Latched demand writes SWT 0 without consulting Critical Zone."""
    app = _two_zone_app(zone_one_action="heating", zone_two_action="heating")

    # zone_one colder → would be Critical Zone if select_max_error ran.
    def get_state(entity_id: str, attribute: str | None = None):
        if entity_id == _PLANT_MGMT:
            return "on"
        if entity_id == _OUTDOOR:
            return _OUTDOOR_TEMP
        if entity_id == _FLAME_ON:
            return "off"
        if entity_id == _CH_ACTIVE:
            return "on"
        if entity_id == _ZONE_TEMP:
            return 15.0
        if entity_id == "sensor.zone_two_temp":
            return 21.0
        if entity_id == _PLANT_SETPOINT:
            return 45.0
        if entity_id == _CLIMATE:
            if attribute == "temperature":
                return 22.0
            if attribute == "hvac_action":
                return "heating"
            return "heat"
        if entity_id == "climate.zone_two":
            if attribute == "temperature":
                return 22.0
            if attribute == "hvac_action":
                return "heating"
            return "heat"
        return None

    app.get_state = MagicMock(side_effect=get_state)
    app._flame_trip_latched = True
    app._zone_heating_prior = {"zone_one": True, "zone_two": True}

    with patch("ha_smart_hvac.hvac_app.select_max_error_demand_zone") as select_cz:
        app.control_tick({})
        select_cz.assert_not_called()

    assert app._flame_trip_latched
    assert _set_value_writes(app) == [0.0]
    joined = " ".join(_info_msgs(app))
    assert "critical_zone=" not in joined
    assert "u_ff=" not in joined


def test_trv_runs_while_flame_latched() -> None:
    """TRV soft-close still applies on tick while flame-latched; SWT stays 0."""
    app = _trv_app(zone_temp=20.0, setpoint=22.0, accuracy=0.5, closure=10.0)
    app._flame_trip_latched = True
    app.control_tick({})
    writes = _set_value_by_entity(app)
    assert (_TRV_CLOSURE, app._config.valve_closure_floor) in writes
    assert (_PLANT_SETPOINT, 0.0) in writes
    assert not any("u_ff=" in m for m in _info_msgs(app))
    assert not any("critical_zone=" in m for m in _info_msgs(app))


def test_trv_at_or_below_setpoint_writes_floor() -> None:
    app = _trv_app(zone_temp=22.0, setpoint=22.0, accuracy=0.5, closure=10.0)
    app.control_tick({})
    assert (_TRV_CLOSURE, 80.0) in _set_value_by_entity(app)
    assert _TRV_CLOSURE not in app._trv_overshoot_latched
    assert not any(
        "valve_opening" in str(c.kwargs.get("entity_id", ""))
        for c in app.call_service.call_args_list
    )


def test_trv_overshoot_writes_100_and_latches() -> None:
    app = _trv_app(zone_temp=23.0, setpoint=22.0, accuracy=0.5, closure=80.0)
    app.control_tick({})
    assert (_TRV_CLOSURE, 100.0) in _set_value_by_entity(app)
    assert _TRV_CLOSURE in app._trv_overshoot_latched


def test_trv_dead_band_keeps_100_while_latched() -> None:
    app = _trv_app(zone_temp=22.3, setpoint=22.0, accuracy=0.5, closure=80.0)
    app._trv_overshoot_latched.add(_TRV_CLOSURE)
    app.control_tick({})
    assert (_TRV_CLOSURE, 100.0) in _set_value_by_entity(app)
    assert _TRV_CLOSURE in app._trv_overshoot_latched


def test_trv_clear_writes_floor_and_unlatches() -> None:
    app = _trv_app(zone_temp=21.5, setpoint=22.0, accuracy=0.5, closure=100.0)
    app._trv_overshoot_latched.add(_TRV_CLOSURE)
    app.control_tick({})
    assert (_TRV_CLOSURE, 80.0) in _set_value_by_entity(app)
    assert _TRV_CLOSURE not in app._trv_overshoot_latched


def test_trv_unreadable_skips_latch_mutate() -> None:
    app = _trv_app(zone_temp=23.0, setpoint=22.0, accuracy="unavailable", closure=80.0)
    app.control_tick({})
    assert all(eid != _TRV_CLOSURE for eid, _ in _set_value_by_entity(app))
    assert _TRV_CLOSURE not in app._trv_overshoot_latched


def test_trv_plant_off_writes_100_no_plant_setpoint() -> None:
    app = _trv_app(
        plant_management="off",
        zone_temp=20.0,
        setpoint=22.0,
        closure=80.0,
    )
    app.control_tick({})
    writes = _set_value_by_entity(app)
    assert (_TRV_CLOSURE, 100.0) in writes
    assert all(eid != _PLANT_SETPOINT for eid, _ in writes)


def test_trv_plain_string_thermostats_no_closure_write() -> None:
    app = _tick_app(plant_management="off")
    app.control_tick({})
    assert _set_value_by_entity(app) == []


def test_trv_independent_of_heating_demand() -> None:
    app = _trv_app(
        zone_temp=23.0,
        setpoint=22.0,
        accuracy=0.5,
        closure=80.0,
        hvac_action="idle",
    )
    app.control_tick({})
    assert (_TRV_CLOSURE, 100.0) in _set_value_by_entity(app)
    assert _TRV_CLOSURE in app._trv_overshoot_latched
    # Idle demand → SWT 0, not weather curve
    assert (_PLANT_SETPOINT, 0.0) in _set_value_by_entity(app)


def test_trv_never_uses_write_setpoint_for_closure() -> None:
    app = _trv_app(zone_temp=20.0, setpoint=22.0, closure=10.0)
    with (
        patch.object(app, "_write_setpoint", wraps=app._write_setpoint) as plant_spy,
        patch.object(app, "_write_number", wraps=app._write_number) as num_spy,
    ):
        app.control_tick({})
    assert any(c.args == (_TRV_CLOSURE, 80.0) for c in num_spy.call_args_list)
    plant_values = [c.args[0] for c in plant_spy.call_args_list]
    assert 80.0 not in plant_values
    assert (_TRV_CLOSURE, 80.0) in _set_value_by_entity(app)


def test_trv_equal_float_skips_set_value() -> None:
    app = _trv_app(zone_temp=20.0, setpoint=22.0, closure=80.0)
    app.control_tick({})
    assert all(eid != _TRV_CLOSURE for eid, _ in _set_value_by_entity(app))


def test_trv_control_event_applies_law() -> None:
    app = _trv_app(zone_temp=23.0, setpoint=22.0, accuracy=0.5, closure=50.0)
    _fire_control_event(app)
    assert (_TRV_CLOSURE, 100.0) in _set_value_by_entity(app)
    assert _TRV_CLOSURE in app._trv_overshoot_latched


def test_trv_floor_override_used() -> None:
    app = _trv_app(
        zone_temp=20.0, setpoint=22.0, closure=10.0, valve_closure_floor=85.0
    )
    app.control_tick({})
    assert (_TRV_CLOSURE, 85.0) in _set_value_by_entity(app)


def test_trv_overshoot_closure_unavailable_does_not_latch() -> None:
    app = _trv_app(zone_temp=23.0, setpoint=22.0, accuracy=0.5, closure="unavailable")
    app.control_tick({})
    assert all(eid != _TRV_CLOSURE for eid, _ in _set_value_by_entity(app))
    assert _TRV_CLOSURE not in app._trv_overshoot_latched


def test_trv_clear_closure_unavailable_keeps_latch() -> None:
    app = _trv_app(zone_temp=21.5, setpoint=22.0, accuracy=0.5, closure="unavailable")
    app._trv_overshoot_latched.add(_TRV_CLOSURE)
    app.control_tick({})
    assert all(eid != _TRV_CLOSURE for eid, _ in _set_value_by_entity(app))
    assert _TRV_CLOSURE in app._trv_overshoot_latched


def test_trv_equal_float_clear_discards_latch() -> None:
    app = _trv_app(zone_temp=21.5, setpoint=22.0, accuracy=0.5, closure=80.0)
    app._trv_overshoot_latched.add(_TRV_CLOSURE)
    app.control_tick({})
    assert all(eid != _TRV_CLOSURE for eid, _ in _set_value_by_entity(app))
    assert _TRV_CLOSURE not in app._trv_overshoot_latched


def test_initialize_trv_mapping_listens_on_climate_attrs() -> None:
    app = _init_app(args=_trv_tick_args())

    def get_state(entity_id: str, attribute: str | None = None):
        if entity_id == _PLANT_MGMT:
            return "off"
        if entity_id == _TRV_CLOSURE:
            return 80.0
        if entity_id == _TRV_ACCURACY:
            return 0.5
        if entity_id == _ZONE_TEMP:
            return 20.0
        if entity_id == _OUTDOOR:
            return _OUTDOOR_TEMP
        if entity_id == _PLANT_SETPOINT:
            return 45.0
        if entity_id in (_CLIMATE, _CLIMATE_GENERIC):
            if attribute == "temperature":
                return 22.0
            if attribute == "hvac_action":
                return "heating"
            return "heat"
        return None

    app.get_state = MagicMock(side_effect=get_state)
    app.initialize()

    attr_listens = [
        (c.args[1], c.kwargs.get("attribute"))
        for c in app.listen_state.call_args_list
        if c.kwargs.get("attribute") in ("hvac_action", "temperature")
    ]
    assert (_CLIMATE, "hvac_action") in attr_listens
    assert (_CLIMATE, "temperature") in attr_listens
    assert (_CLIMATE_GENERIC, "hvac_action") in attr_listens
    assert (_CLIMATE_GENERIC, "temperature") in attr_listens
    assert all(
        entity not in (_TRV_CLOSURE, _TRV_ACCURACY) for entity, _ in attr_listens
    )
    entity_listens = [
        (c.args[0], c.args[1])
        for c in app.listen_state.call_args_list
        if len(c.args) >= 2 and c.kwargs.get("attribute") is None
    ]
    assert (app.control_event, _TRV_ACCURACY) in entity_listens
    assert all(entity != _TRV_CLOSURE for _, entity in entity_listens)
    assert not any(
        len(c.args) >= 2 and c.args[1] == _TRV_CLOSURE
        for c in app.listen_state.call_args_list
    )
    assert (_TRV_CLOSURE, 100.0) in _set_value_by_entity(app)


def test_trv_clear_at_exact_setpoint_unlatches() -> None:
    app = _trv_app(zone_temp=22.0, setpoint=22.0, accuracy=0.5, closure=100.0)
    app._trv_overshoot_latched.add(_TRV_CLOSURE)
    app.control_tick({})
    assert (_TRV_CLOSURE, 80.0) in _set_value_by_entity(app)
    assert _TRV_CLOSURE not in app._trv_overshoot_latched


def test_trv_exact_overshoot_threshold_writes_floor() -> None:
    app = _trv_app(zone_temp=22.5, setpoint=22.0, accuracy=0.5, closure=10.0)
    app.control_tick({})
    assert (_TRV_CLOSURE, 80.0) in _set_value_by_entity(app)
    assert _TRV_CLOSURE not in app._trv_overshoot_latched


def test_trv_zone_temp_unreadable_skips() -> None:
    app = _trv_app(zone_temp="unavailable", setpoint=22.0, accuracy=0.5, closure=80.0)
    app.control_tick({})
    assert all(eid != _TRV_CLOSURE for eid, _ in _set_value_by_entity(app))
    assert _TRV_CLOSURE not in app._trv_overshoot_latched


def test_trv_setpoint_unreadable_skips() -> None:
    app = _trv_app(zone_temp=23.0, setpoint="unavailable", accuracy=0.5, closure=80.0)
    app.control_tick({})
    assert all(eid != _TRV_CLOSURE for eid, _ in _set_value_by_entity(app))
    assert _TRV_CLOSURE not in app._trv_overshoot_latched


def test_trv_latched_accuracy_unavailable_still_clears() -> None:
    app = _trv_app(zone_temp=21.5, setpoint=22.0, accuracy="unavailable", closure=100.0)
    app._trv_overshoot_latched.add(_TRV_CLOSURE)
    app.control_tick({})
    assert (_TRV_CLOSURE, 80.0) in _set_value_by_entity(app)
    assert _TRV_CLOSURE not in app._trv_overshoot_latched


def test_trv_latched_accuracy_unavailable_keeps_100() -> None:
    app = _trv_app(zone_temp=22.3, setpoint=22.0, accuracy="unavailable", closure=80.0)
    app._trv_overshoot_latched.add(_TRV_CLOSURE)
    app.control_tick({})
    assert (_TRV_CLOSURE, 100.0) in _set_value_by_entity(app)
    assert _TRV_CLOSURE in app._trv_overshoot_latched


def test_trv_plant_off_via_control_event() -> None:
    app = _trv_app(
        plant_management="off",
        zone_temp=20.0,
        setpoint=22.0,
        closure=80.0,
    )
    _fire_control_event(app)
    writes = _set_value_by_entity(app)
    assert (_TRV_CLOSURE, 100.0) in writes
    assert all(eid != _PLANT_SETPOINT for eid, _ in writes)


def test_trv_no_valve_opening_degree_entity_writes() -> None:
    source = _HVAC_APP_PATH.read_text(encoding="utf-8")
    assert "valve_opening_degree" not in source


def test_trv_accuracy_state_change_reapplies_law() -> None:
    """Plant on; accuracy-only control_event re-applies floor/100."""
    app = _trv_app(zone_temp=20.0, setpoint=22.0, accuracy=0.5, closure=10.0)
    _fire_control_event(app, entity=_TRV_ACCURACY)
    assert (_TRV_CLOSURE, 80.0) in _set_value_by_entity(app)
    assert _TRV_CLOSURE not in app._trv_overshoot_latched


def test_trv_outdoor_fail_still_applies_before_prelude() -> None:
    app = _trv_app(
        zone_temp=20.0,
        setpoint=22.0,
        accuracy=0.5,
        closure=10.0,
        outdoor="unavailable",
    )
    with patch.object(app, "_apply_trv_law", wraps=app._apply_trv_law) as trv_spy:
        app.control_tick({})
    trv_spy.assert_called()
    assert (_TRV_CLOSURE, 80.0) in _set_value_by_entity(app)
    assert (_PLANT_SETPOINT, 0.0) in _set_value_by_entity(app)
    assert any(
        f"Outdoor temperature unavailable: {_OUTDOOR}" in m for m in _warn_msgs(app)
    )


def test_trv_empty_zone_prelude_still_runs_law() -> None:
    app = _trv_app(
        zone_temp="unavailable",
        setpoint=22.0,
        accuracy=0.5,
        closure=10.0,
    )
    with patch.object(app, "_apply_trv_law", wraps=app._apply_trv_law) as trv_spy:
        app.control_tick({})
    trv_spy.assert_called()
    # Own zone T unreadable → per-TRV skip; prelude still idles SWT.
    assert all(eid != _TRV_CLOSURE for eid, _ in _set_value_by_entity(app))
    assert (_PLANT_SETPOINT, 0.0) in _set_value_by_entity(app)
    assert any("No zones with valid readings" in m for m in _warn_msgs(app))


def test_trv_sibling_zone_temp_unreadable_own_reads_still_write() -> None:
    args = _tick_args()
    args["zones"] = [
        {
            "name": _ZONE_NAME,
            "temperature": _ZONE_TEMP,
            "thermostats": [
                {
                    "climate": _CLIMATE,
                    "valve_closure": _TRV_CLOSURE,
                    "accuracy": _TRV_ACCURACY,
                }
            ],
        },
        {
            "name": "zone_two",
            "temperature": _ZONE_TEMP_2,
            "thermostats": [
                {
                    "climate": _CLIMATE_2,
                    "valve_closure": _TRV_CLOSURE_2,
                    "accuracy": _TRV_ACCURACY_2,
                }
            ],
        },
    ]
    app = _tick_app(plant_setpoint=45.0, zone_temp=20.0, setpoint=22.0, args=args)
    base = app.get_state.side_effect

    def get_state(entity_id: str, attribute: str | None = None):
        if entity_id == _TRV_CLOSURE:
            return 10.0
        if entity_id == _TRV_ACCURACY:
            return 0.5
        if entity_id == _ZONE_TEMP_2:
            return "unavailable"
        if entity_id == _TRV_CLOSURE_2:
            return 10.0
        if entity_id == _TRV_ACCURACY_2:
            return 0.5
        if entity_id == _CLIMATE_2:
            if attribute == "temperature":
                return 22.0
            if attribute == "hvac_action":
                return "heating"
            return "heat"
        return base(entity_id, attribute)

    app.get_state = MagicMock(side_effect=get_state)
    app.control_tick({})
    writes = _set_value_by_entity(app)
    assert (_TRV_CLOSURE, 80.0) in writes
    assert all(eid != _TRV_CLOSURE_2 for eid, _ in writes)


def test_trv_multi_independent_latches_and_mixed_plain_skipped() -> None:
    args = _tick_args()
    args["zones"] = [
        {
            "name": _ZONE_NAME,
            "temperature": _ZONE_TEMP,
            "thermostats": [
                {
                    "climate": _CLIMATE,
                    "valve_closure": _TRV_CLOSURE,
                    "accuracy": _TRV_ACCURACY,
                },
                _CLIMATE_GENERIC,
                {
                    "climate": _CLIMATE_2,
                    "valve_closure": _TRV_CLOSURE_2,
                    "accuracy": _TRV_ACCURACY_2,
                },
            ],
        }
    ]
    app = _tick_app(plant_setpoint=45.0, zone_temp=23.0, setpoint=22.0, args=args)
    base = app.get_state.side_effect

    def get_state(entity_id: str, attribute: str | None = None):
        if entity_id == _TRV_CLOSURE:
            return 10.0
        if entity_id == _TRV_ACCURACY:
            return 0.5
        if entity_id == _TRV_CLOSURE_2:
            return 100.0
        if entity_id == _TRV_ACCURACY_2:
            return 0.5
        if entity_id == _CLIMATE_GENERIC:
            if attribute == "temperature":
                return 22.0
            if attribute == "hvac_action":
                return "heating"
            return "heat"
        if entity_id == _CLIMATE_2:
            if attribute == "temperature":
                return 22.0
            if attribute == "hvac_action":
                return "heating"
            return "heat"
        return base(entity_id, attribute)

    # Phase 1: shared T=21.5 — TRV1 unlatched → floor; latched TRV2 → clear.
    app._trv_overshoot_latched.add(_TRV_CLOSURE_2)

    def get_state_clear(entity_id: str, attribute: str | None = None):
        if entity_id == _ZONE_TEMP:
            return 21.5
        return get_state(entity_id, attribute)

    app.get_state = MagicMock(side_effect=get_state_clear)
    app.control_tick({})
    writes = _set_value_by_entity(app)
    assert (_TRV_CLOSURE, 80.0) in writes
    assert (_TRV_CLOSURE_2, 80.0) in writes
    assert _TRV_CLOSURE not in app._trv_overshoot_latched
    assert _TRV_CLOSURE_2 not in app._trv_overshoot_latched
    assert all(not str(eid).startswith("climate.") for eid, _ in writes)

    # Phase 2: overshoot latches TRV1 only; TRV2 high setpoint stays at floor.
    app.call_service.reset_mock()
    app._trv_overshoot_latched.clear()

    def get_state_overshoot(entity_id: str, attribute: str | None = None):
        if entity_id == _ZONE_TEMP:
            return 23.0
        if entity_id == _TRV_CLOSURE_2:
            return 10.0
        if entity_id == _CLIMATE_2:
            if attribute == "temperature":
                return 30.0  # high setpoint → no overshoot for TRV2
            if attribute == "hvac_action":
                return "heating"
            return "heat"
        return get_state(entity_id, attribute)

    app.get_state = MagicMock(side_effect=get_state_overshoot)
    app.control_tick({})
    writes = _set_value_by_entity(app)
    assert (_TRV_CLOSURE, 100.0) in writes
    assert _TRV_CLOSURE in app._trv_overshoot_latched
    assert (_TRV_CLOSURE_2, 80.0) in writes
    assert _TRV_CLOSURE_2 not in app._trv_overshoot_latched
    assert all(not str(eid).startswith("climate.") for eid, _ in writes)


def test_trv_cold_start_overshoot_latches_on_initialize() -> None:
    app = _init_app(args=_trv_tick_args())

    def get_state(entity_id: str, attribute: str | None = None):
        if entity_id == _PLANT_MGMT:
            return "on"
        if entity_id == _TRV_CLOSURE:
            return 80.0
        if entity_id == _TRV_ACCURACY:
            return 0.5
        if entity_id == _ZONE_TEMP:
            return 23.0
        if entity_id == _OUTDOOR:
            return _OUTDOOR_TEMP
        if entity_id == _PLANT_SETPOINT:
            return 45.0
        if entity_id in (_CLIMATE, _CLIMATE_GENERIC):
            if attribute == "temperature":
                return 22.0
            if attribute == "hvac_action":
                return "heating"
            return "heat"
        return None

    app.get_state = MagicMock(side_effect=get_state)
    app.initialize()
    assert (_TRV_CLOSURE, 100.0) in _set_value_by_entity(app)
    assert _TRV_CLOSURE in app._trv_overshoot_latched
