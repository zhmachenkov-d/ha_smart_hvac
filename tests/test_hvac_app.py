"""Tests for fixed-gain PID Set Water Temperature control loop."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from ha_smart_hvac.config import parse_config
from ha_smart_hvac.ff_auto_correct import clamp
from ha_smart_hvac.hvac_app import HvacApp

_SETPOINT_MIN = 40.0
_SETPOINT_MAX = 55.0
_CONTROL_INTERVAL = 300
_BASE = 40.0
_KP = 1.0
_KI = 0.1

_OUTDOOR = "sensor.outdoor"
_PLANT_MGMT = "switch.pm"
_PLANT_SETPOINT = "number.plant_setpoint"
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
        "pid": {
            "kp": _KP,
            "ki": _KI,
            "integral_min": -50,
            "integral_max": 50,
        },
        "weather_feedforward": {
            "base": 25,
            "slope": 1.2,
            "comfort_ref": 20,
        },
        "zones": [
            {
                "name": _ZONE_NAME,
                "temperature": _ZONE_TEMP,
                "thermostats": [_CLIMATE],
            }
        ],
    }


def _expected_command(
    *,
    zone_temp: float,
    setpoint: float,
    integral: float = 0.0,
    base: float = _BASE,
    kp: float = _KP,
    ki: float = _KI,
) -> float:
    e = setpoint - zone_temp
    u_pid = kp * e + ki * integral
    raw = base + u_pid
    return round(clamp(raw, _SETPOINT_MIN, _SETPOINT_MAX), 1)


def _tick_app(
    *,
    plant_setpoint: object = 45.0,
    zone_temp: float = 20.0,
    setpoint: float = 22.0,
    outdoor: float = 0.0,
    hvac_action: str = "heating",
    plant_management: str = "on",
) -> HvacApp:
    """Hass-stubbed HvacApp for control_tick (_config only)."""
    app = object.__new__(HvacApp)
    app._config = parse_config(_tick_args())
    app._integral = 0.0
    app._last_commanded = None
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


def _init_app(args: dict | None = None) -> HvacApp:
    """Hass-stubbed app ready for initialize() (run_every + listen_state)."""
    app = object.__new__(HvacApp)
    app.args = args if args is not None else _tick_args()
    app.log = MagicMock()
    app.run_every = MagicMock()
    app.listen_state = MagicMock()
    return app


def _fire_control_event(app: HvacApp) -> None:
    app.control_event(_PLANT_MGMT, "state", None, "on", {})


def test_initialize_schedules_control_tick() -> None:
    app = _init_app()

    app.initialize()

    assert app._integral == 0.0
    assert app._last_commanded is None
    app.run_every.assert_called_once()
    assert app.run_every.call_args.args[0].__func__ is HvacApp.control_tick
    assert app.run_every.call_args.args[2] == _CONTROL_INTERVAL


def test_initialize_outdoor_not_among_listeners() -> None:
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
    app = _init_app(args=args)
    app.initialize()

    listens = app.listen_state.call_args_list
    entity_only = {
        c.args[1] for c in listens if len(c.args) >= 2 and not c.kwargs.get("attribute")
    }
    attr_listens = {
        (c.args[1], c.kwargs["attribute"]) for c in listens if c.kwargs.get("attribute")
    }
    assert _OUTDOOR not in entity_only
    assert entity_only == {_PLANT_MGMT, _ZONE_TEMP, zone_two_temp}
    assert attr_listens == {
        (_CLIMATE, "hvac_action"),
        (_CLIMATE, "temperature"),
        (climate_two, "hvac_action"),
        (climate_two, "temperature"),
    }
    assert all(c.args[0].__func__ is HvacApp.control_event for c in listens)


def test_demand_tick_writes_pid_command_and_advances_integral() -> None:
    app = _tick_app(zone_temp=20.0, setpoint=22.0, plant_setpoint=45.0)
    expected = _expected_command(zone_temp=20.0, setpoint=22.0)

    app.control_tick({})

    assert _set_value_writes(app) == [expected]
    # e=2, dt=300 → ∫ = clamp(600, ±50) = 50 (rail; dt wiring locked below)
    assert app._integral == pytest.approx(50.0)
    assert app._last_commanded == pytest.approx(expected)
    joined = " ".join(_info_msgs(app))
    assert "e=" in joined
    assert "u_pid=" in joined
    assert "command=" in joined
    assert "critical_zone=zone_one" in joined
    assert "u_ff=" not in joined
    assert "outdoor=" not in joined


def test_demand_tick_integral_uses_control_interval_as_dt() -> None:
    """In-range e·dt must equal control_interval (not legacy 60)."""
    app = _tick_app(zone_temp=21.9, setpoint=22.0, plant_setpoint=45.0)
    expected = _expected_command(zone_temp=21.9, setpoint=22.0)

    app.control_tick({})

    assert _set_value_writes(app) == [expected]
    # e=0.1, dt=300 → ∫ = 30 (inside ±50); dt=60 would yield 6
    assert app._integral == pytest.approx(0.1 * _CONTROL_INTERVAL)


def test_demand_event_no_write_no_integral_change() -> None:
    app = _tick_app(zone_temp=20.0, setpoint=22.0, plant_setpoint=45.0)

    _fire_control_event(app)

    assert _set_value_writes(app) == []
    assert app._integral == pytest.approx(0.0)
    assert app._last_commanded is None


def test_tick_then_demand_event_leaves_integral_and_last() -> None:
    app = _tick_app(zone_temp=20.0, setpoint=22.0, plant_setpoint=45.0)

    app.control_tick({})
    integral_after_tick = app._integral
    last_after_tick = app._last_commanded
    assert integral_after_tick == pytest.approx(50.0)
    assert last_after_tick is not None

    app.call_service.reset_mock()
    _fire_control_event(app)

    assert _set_value_writes(app) == []
    assert app._integral == pytest.approx(integral_after_tick)
    assert app._last_commanded == last_after_tick


def test_saturation_freeze_on_tick() -> None:
    """Large positive e with high base → sat high; ∫ does not advance."""
    args = _tick_args()
    args["base_water_temp"] = 50.0
    app = _tick_app(zone_temp=10.0, setpoint=30.0, plant_setpoint=45.0)
    app._config = parse_config(args)
    # e=20, u_pid=20, raw=70 > 55 → freeze

    app.control_tick({})

    assert _set_value_writes(app) == [55.0]
    assert app._integral == pytest.approx(0.0)


def test_heating_at_setpoint_still_writes_pid() -> None:
    app = _tick_app(
        zone_temp=22.0,
        setpoint=22.0,
        plant_setpoint=45.0,
        hvac_action="heating",
    )
    expected = _expected_command(zone_temp=22.0, setpoint=22.0)

    app.control_tick({})

    assert _set_value_writes(app) == [expected]


def test_critical_zone_does_not_change_swt() -> None:
    """Max-error zone is logged only; SWT uses weighted demand average."""
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
    config = parse_config(args)
    # zone_one: Tair=21.5 Tset=22 e_z=0.5; zone_two: Tair=15 Tset=22 e_z=7
    # equal weights → Tair_w=18.25, Tset_w=22, e=3.75
    # u_pid=3.75, raw=43.75, command=43.8
    expected = round(clamp(40.0 + 3.75, _SETPOINT_MIN, _SETPOINT_MAX), 1)

    app = object.__new__(HvacApp)
    app._config = config
    app._integral = 0.0
    app._last_commanded = None
    app.call_service = MagicMock()
    app.log = MagicMock()

    def get_state(entity_id: str, attribute: str | None = None):
        if entity_id == _PLANT_MGMT:
            return "on"
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
    assert "critical_zone=zone_two" in joined


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
    app._last_commanded = None
    app.call_service = MagicMock()
    app.log = MagicMock()

    def get_state(entity_id: str, attribute: str | None = None):
        if entity_id == _PLANT_MGMT:
            return "on"
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
    expected = _expected_command(zone_temp=20.0, setpoint=22.0)

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
    app._last_commanded = None
    app.call_service = MagicMock()
    app.log = MagicMock()

    def get_state(entity_id: str, attribute: str | None = None):
        if entity_id == _PLANT_MGMT:
            return "on"
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
    expected = _expected_command(zone_temp=20.0, setpoint=22.0)

    app.control_tick({})

    assert _set_value_writes(app) == [expected]
    assert any("thermostat unavailable" in m for m in _warn_msgs(app))


def test_outdoor_missing_still_runs_demand() -> None:
    app = _tick_app(
        zone_temp=20.0,
        setpoint=22.0,
        outdoor="unavailable",
        plant_setpoint=45.0,
    )
    expected = _expected_command(zone_temp=20.0, setpoint=22.0)

    app.control_tick({})

    assert _set_value_writes(app) == [expected]


def test_equal_rounded_skip_no_set_value() -> None:
    expected = _expected_command(zone_temp=20.0, setpoint=22.0)
    app = _tick_app(
        zone_temp=20.0,
        setpoint=22.0,
        plant_setpoint=45.0,
    )
    app._last_commanded = expected

    app.control_tick({})

    assert _set_value_writes(app) == []
    app.call_service.assert_not_called()
    assert any("command=" in m for m in _info_msgs(app))
    # equal skip still advances ∫ on tick (command treated as applied)
    assert app._integral == pytest.approx(50.0)
    assert app._last_commanded == pytest.approx(expected)


def test_plant_on_idle_writes_zero_and_clears() -> None:
    app = _tick_app(zone_temp=22.0, setpoint=22.0, hvac_action="idle")
    app._integral = 12.0
    app._last_commanded = 42.0

    app.control_tick({})

    assert _set_value_writes(app) == [0.0]
    assert app._integral == 0.0
    assert app._last_commanded is None


def test_idle_write_fail_still_clears() -> None:
    app = _tick_app(
        zone_temp=22.0,
        setpoint=22.0,
        hvac_action="idle",
        plant_setpoint="unavailable",
    )
    app._integral = 12.0
    app._last_commanded = 42.0

    app.control_tick({})

    assert _set_value_writes(app) == []
    assert app._integral == 0.0
    assert app._last_commanded is None
    assert any("Plant setpoint unavailable" in m for m in _warn_msgs(app))


def test_plant_off_no_write_clears() -> None:
    app = _tick_app(plant_management="off")
    app._integral = 12.0
    app._last_commanded = 42.0

    app.control_tick({})

    assert _set_value_writes(app) == []
    app.call_service.assert_not_called()
    assert app._integral == 0.0
    assert app._last_commanded is None


def test_no_valid_zones_writes_zero_and_clears() -> None:
    app = _tick_app(zone_temp="unavailable")
    app._integral = 5.0
    app._last_commanded = 41.0

    app.control_tick({})

    assert _set_value_writes(app) == [0.0]
    assert app._integral == 0.0
    assert app._last_commanded is None


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
    # decision A: ∫ advances only after successful write
    assert app._integral == pytest.approx(0.0)
    assert app._last_commanded is None


def test_zero_weight_sum_goes_idle() -> None:
    args = _tick_args()
    args["zones"] = [
        {
            "name": _ZONE_NAME,
            "temperature": _ZONE_TEMP,
            "weight": 0.0,
            "thermostats": [_CLIMATE],
        }
    ]
    app = _tick_app(zone_temp=20.0, setpoint=22.0, plant_setpoint=45.0)
    app._config = parse_config(args)
    app._integral = 3.0
    app._last_commanded = 42.0

    app.control_tick({})

    assert _set_value_writes(app) == [0.0]
    assert app._integral == 0.0
    assert app._last_commanded is None
    assert any("weights unusable" in m for m in _warn_msgs(app))


def test_event_plant_off_no_write_clears() -> None:
    app = _tick_app(plant_management="off")
    app._integral = 5.0
    app._last_commanded = 42.0

    _fire_control_event(app)

    assert _set_value_writes(app) == []
    assert app._integral == 0.0
    assert app._last_commanded is None


def test_event_idle_writes_zero_clears() -> None:
    app = _tick_app(zone_temp=22.0, setpoint=22.0, hvac_action="idle")
    app._integral = 5.0
    app._last_commanded = 42.0

    _fire_control_event(app)

    assert _set_value_writes(app) == [0.0]
    assert app._integral == 0.0
    assert app._last_commanded is None


def test_event_idle_write_fail_still_clears() -> None:
    app = _tick_app(
        zone_temp=22.0,
        setpoint=22.0,
        hvac_action="idle",
        plant_setpoint="unavailable",
    )
    app._integral = 5.0
    app._last_commanded = 42.0

    _fire_control_event(app)

    assert _set_value_writes(app) == []
    assert app._integral == 0.0
    assert app._last_commanded is None
    assert any("Plant setpoint unavailable" in m for m in _warn_msgs(app))


def test_event_no_valid_zones_writes_zero_and_clears() -> None:
    app = _tick_app(zone_temp="unavailable")
    app._integral = 5.0
    app._last_commanded = 41.0

    _fire_control_event(app)

    assert _set_value_writes(app) == [0.0]
    assert app._integral == 0.0
    assert app._last_commanded is None


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
    app._last_commanded = 41.0

    app.control_tick({})

    assert _set_value_writes(app) == [0.0]
    assert app._integral == 0.0
    assert app._last_commanded is None
