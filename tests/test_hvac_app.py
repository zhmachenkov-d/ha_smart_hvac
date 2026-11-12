"""Tests for outdoor weather-curve Set Water Temperature control loop."""

from __future__ import annotations

import ast
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

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
_BOILER_WATER = "sensor.boiler_water"
_PLANT_MGMT = "switch.pm"
_PLANT_SETPOINT = "number.plant_setpoint"
_ZONE_TEMP = "sensor.zone_one_temp"
_CLIMATE = "climate.zone_one"
_ZONE_NAME = "zone_one"

_HVAC_APP_PATH = (
    Path(__file__).resolve().parents[1] / "apps" / "ha_smart_hvac" / "hvac_app.py"
)
_PID_PATH = Path(__file__).resolve().parents[1] / "apps" / "ha_smart_hvac" / "pid.py"


def _tick_args() -> dict:
    return {
        "outdoor_temperature": _OUTDOOR,
        "boiler_water": _BOILER_WATER,
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
    app._supply_trip_latched = False
    app._supply_sample = None
    app._trip_hold_handle = None
    app._monotonic = MagicMock(return_value=0.0)

    def get_state(entity_id: str, attribute: str | None = None):
        if entity_id == _PLANT_MGMT:
            return plant_management
        if entity_id == _OUTDOOR:
            return outdoor
        if entity_id == _BOILER_WATER:
            return 40.0
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


def test_pid_does_not_reexport_clamp_or_quantize() -> None:
    """F6-B: pid may import clamp/quantize only as private aliases."""
    source = _PID_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        mod = node.module or ""
        ff = mod == "ha_smart_hvac.feedforward" or (
            node.level > 0 and (mod == "feedforward" or mod.startswith("feedforward."))
        )
        if not ff:
            continue
        for alias in node.names:
            if alias.name in {"clamp", "quantize_command"}:
                assert alias.asname is not None, (
                    f"{alias.name} must be imported as a private alias"
                )
                assert alias.asname.startswith("_"), (
                    f"{alias.name} alias {alias.asname!r} must be private"
                )


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
    """Leftover pid / base_water_temp → ignored_keys WARN; boiler_water commissioned."""
    args = _tick_args()
    args["pid"] = {"kp": 1.0, "adaptive": True}
    args["base_water_temp"] = 51
    app = _init_app(args=args)

    app.initialize()

    warns = _warn_msgs(app)
    assert warns[0].startswith("HVAC config: ignoring legacy or unknown keys:")
    assert "base_water_temp" in warns[0]
    assert "boiler_water" not in warns[0]
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
    app._supply_trip_latched = False

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
    app._supply_trip_latched = False

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
    app._supply_trip_latched = False

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


def test_initialize_registers_outdoor_and_supply_listeners() -> None:
    app = _init_app()
    app.initialize()

    listens = app.listen_state.call_args_list
    entity_only = {
        c.args[1] for c in listens if len(c.args) >= 2 and not c.kwargs.get("attribute")
    }
    assert _OUTDOOR in entity_only
    assert _BOILER_WATER in entity_only
    assert _PLANT_MGMT in entity_only
    boiler_listens = [
        c for c in listens if len(c.args) >= 2 and c.args[1] == _BOILER_WATER
    ]
    assert len(boiler_listens) == 1
    assert boiler_listens[0].args[0].__func__ is HvacApp.supply_event


def _demand_get_state(
    *,
    boiler_water: object = 40.0,
    outdoor: object = _OUTDOOR_TEMP,
    plant_management: str = "on",
    hvac_action: str = "heating",
):
    """get_state for supply trip tests under configurable gates."""

    def get_state(entity_id: str, attribute: str | None = None):
        if entity_id == _PLANT_MGMT:
            return plant_management
        if entity_id == _OUTDOOR:
            return outdoor
        if entity_id == _BOILER_WATER:
            return boiler_water
        if entity_id == _ZONE_TEMP:
            return 20.0
        if entity_id == _PLANT_SETPOINT:
            return 45.0
        if entity_id == _CLIMATE:
            if attribute == "temperature":
                return 22.0
            if attribute == "hvac_action":
                return hvac_action
            return "heat"
        return None

    return get_state


def _supply_trip_app(**kwargs) -> HvacApp:
    kwargs.setdefault("plant_management", "on")
    return _tick_app(**kwargs)


def test_supply_trip_latches_and_writes_zero() -> None:
    app = _supply_trip_app()
    times = [0.0, 60.0]
    app._monotonic = MagicMock(side_effect=times)

    app.supply_event(_BOILER_WATER, "state", 35.0, 40.0, {})
    assert app._supply_sample == (0.0, 40.0)
    assert not app._supply_trip_latched

    app.get_state = MagicMock(side_effect=_demand_get_state(boiler_water=50.0))
    app.supply_event(_BOILER_WATER, "state", 40.0, 50.0, {})

    assert app._supply_trip_latched
    assert _set_value_writes(app) == [0.0]
    app.run_in.assert_called_once()
    assert app.run_in.call_args.args[0].__func__ is HvacApp._trip_hold_expired
    assert app.run_in.call_args.args[1] == app._config.hold
    hold_cb = app.run_in.call_args.args[0]
    app.call_service.reset_mock()
    hold_cb({})
    assert not app._supply_trip_latched
    assert _set_value_writes(app) == [_expected_command()]


def test_latched_demand_writes_zero_no_ff() -> None:
    app = _supply_trip_app()
    app._supply_trip_latched = True
    app.control_tick({})
    assert _set_value_writes(app) == [0.0]
    assert not any("u_ff=" in m for m in _info_msgs(app))


def test_trip_hold_expiry_gated_runs_curve() -> None:
    app = _supply_trip_app(plant_setpoint=45.0)
    app._supply_trip_latched = True
    app._trip_hold_handle = "hold-handle"
    expected = _expected_command()

    app._trip_hold_expired({})

    assert not app._supply_trip_latched
    app.cancel_timer.assert_called_once_with("hold-handle")
    assert _set_value_writes(app) == [expected]


def test_trip_hold_expiry_closed_gate_clears_only() -> None:
    app = _supply_trip_app(plant_management="off")
    app._supply_trip_latched = True
    app._trip_hold_handle = "hold-handle"

    app._trip_hold_expired({})

    assert not app._supply_trip_latched
    assert _set_value_writes(app) == []


def test_idle_clears_trip_state() -> None:
    app = _supply_trip_app(
        zone_temp=22.0, setpoint=22.0, hvac_action="idle", plant_setpoint=0.0
    )
    app._supply_trip_latched = True
    app._supply_sample = (0.0, 40.0)
    app._trip_hold_handle = "hold-handle"

    app.control_tick({})

    assert not app._supply_trip_latched
    assert app._supply_sample is None
    app.cancel_timer.assert_called_once_with("hold-handle")


def test_plant_off_clears_trip_state() -> None:
    app = _supply_trip_app(plant_management="off")
    app._supply_trip_latched = True
    app._supply_sample = (0.0, 40.0)
    app._trip_hold_handle = "hold-handle"

    app.control_tick({})

    assert not app._supply_trip_latched
    assert app._supply_sample is None
    app.cancel_timer.assert_called_with("hold-handle")


def test_bad_supply_warns_without_trip() -> None:
    app = _supply_trip_app()
    app._supply_trip_latched = True
    app.get_state = MagicMock(side_effect=_demand_get_state(boiler_water="unavailable"))

    app.supply_event(_BOILER_WATER, "state", 40.0, None, {})

    assert app._supply_trip_latched
    assert any("Supply temperature unreadable" in m for m in _warn_msgs(app))


def test_supply_non_positive_dt_warns_keeps_latest() -> None:
    app = _supply_trip_app()
    app._supply_sample = (1.0, 40.0)
    app._monotonic = MagicMock(return_value=1.0)
    app.get_state = MagicMock(side_effect=_demand_get_state(boiler_water=41.0))

    app.supply_event(_BOILER_WATER, "state", 40.0, 41.0, {})

    assert not app._supply_trip_latched
    assert any("non-positive sample interval" in m for m in _warn_msgs(app))
    assert app._supply_sample == (1.0, 41.0)


def test_already_latched_does_not_restart_hold() -> None:
    app = _supply_trip_app()
    app._supply_trip_latched = True
    app._trip_hold_handle = "existing"
    app._supply_sample = (0.0, 40.0)
    app._monotonic = MagicMock(side_effect=[60.0, 120.0])
    app.get_state = MagicMock(side_effect=_demand_get_state(boiler_water=80.0))

    app.supply_event(_BOILER_WATER, "state", 40.0, 80.0, {})

    app.run_in.assert_not_called()


def test_supply_trip_under_demand_outdoor_unavailable() -> None:
    """supply_event gates on Plant∧Demand only — not Outdoor idle."""
    app = _supply_trip_app()
    times = [0.0, 60.0]
    app._monotonic = MagicMock(side_effect=times)
    app.get_state = MagicMock(
        side_effect=_demand_get_state(outdoor="unavailable", boiler_water=40.0)
    )

    app.supply_event(_BOILER_WATER, "state", 35.0, 40.0, {})
    app.get_state = MagicMock(
        side_effect=_demand_get_state(outdoor="unavailable", boiler_water=50.0)
    )
    app.supply_event(_BOILER_WATER, "state", 40.0, 50.0, {})

    assert app._supply_trip_latched
    assert _set_value_writes(app) == [0.0]
    app.run_in.assert_called_once()
    assert not any("Outdoor temperature unavailable" in m for m in _warn_msgs(app))


def test_supply_event_plant_off_does_not_trip() -> None:
    app = _supply_trip_app(plant_management="off")
    times = [0.0, 60.0]
    app._monotonic = MagicMock(side_effect=times)
    app.get_state = MagicMock(
        side_effect=_demand_get_state(plant_management="off", boiler_water=40.0)
    )

    app.supply_event(_BOILER_WATER, "state", 35.0, 40.0, {})
    app.get_state = MagicMock(
        side_effect=_demand_get_state(plant_management="off", boiler_water=50.0)
    )
    app.supply_event(_BOILER_WATER, "state", 40.0, 50.0, {})

    assert not app._supply_trip_latched
    app.run_in.assert_not_called()
    assert _set_value_writes(app) == []


def test_supply_event_no_heating_demand_does_not_trip() -> None:
    app = _supply_trip_app(hvac_action="idle")
    times = [0.0, 60.0]
    app._monotonic = MagicMock(side_effect=times)
    app.get_state = MagicMock(
        side_effect=_demand_get_state(hvac_action="idle", boiler_water=40.0)
    )

    app.supply_event(_BOILER_WATER, "state", 35.0, 40.0, {})
    app.get_state = MagicMock(
        side_effect=_demand_get_state(hvac_action="idle", boiler_water=50.0)
    )
    app.supply_event(_BOILER_WATER, "state", 40.0, 50.0, {})

    assert not app._supply_trip_latched
    app.run_in.assert_not_called()
    assert _set_value_writes(app) == []


def test_orphan_hold_callback_after_clear_no_demand_write() -> None:
    app = _supply_trip_app(plant_setpoint=45.0)
    app._supply_trip_latched = False
    app._trip_hold_handle = None

    app._trip_hold_expired({})

    assert _set_value_writes(app) == []
