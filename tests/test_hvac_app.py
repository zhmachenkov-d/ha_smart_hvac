"""Tests for fixed-gain PID Set Water Temperature control loop."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from ha_smart_hvac.config import parse_config
from ha_smart_hvac.hvac_app import HvacApp
from ha_smart_hvac.pid import clamp

_SETPOINT_MIN = 40.0
_SETPOINT_MAX = 55.0
_CONTROL_INTERVAL = 300
_BASE = 40.0
_KP = 1.0
_KI = 1.0
_DT_HOURS = _CONTROL_INTERVAL / 3600.0

_OUTDOOR = "sensor.outdoor"
_PLANT_MGMT = "switch.pm"
_PLANT_SETPOINT = "number.plant_setpoint"
_ZONE_TEMP = "sensor.zone_one_temp"
_CLIMATE = "climate.zone_one"
_ZONE_NAME = "zone_one"


def _tick_args() -> dict:
    return {
        "plant_management": _PLANT_MGMT,
        "plant_setpoint": _PLANT_SETPOINT,
        "setpoint_min": _SETPOINT_MIN,
        "setpoint_max": _SETPOINT_MAX,
        "control_interval": _CONTROL_INTERVAL,
        "base_water_temp": _BASE,
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
    args["outdoor_temperature"] = _OUTDOOR
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
    # e=2, dt_hours=300/3600 → ∫ = 1/6 °C·h
    assert app._integral == pytest.approx(2.0 * _DT_HOURS)
    assert app._last_commanded == pytest.approx(expected)
    joined = " ".join(_info_msgs(app))
    assert "e=" in joined
    assert "u_pid=" in joined
    assert "command=" in joined
    assert "critical_zone=zone_one" in joined
    assert "u_ff=" not in joined
    assert "outdoor=" not in joined


def test_demand_tick_integral_uses_control_interval_in_hours() -> None:
    """∫ step is e·control_interval/3600 (°C·h), not e·seconds."""
    app = _tick_app(zone_temp=21.9, setpoint=22.0, plant_setpoint=45.0)
    expected = _expected_command(zone_temp=21.9, setpoint=22.0)

    app.control_tick({})

    assert _set_value_writes(app) == [expected]
    # e=0.1, dt_hours=300/3600 → ∫ = 0.1/12 °C·h
    assert app._integral == pytest.approx(0.1 * _DT_HOURS)


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
    assert integral_after_tick == pytest.approx(2.0 * _DT_HOURS)
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


def test_stale_outdoor_key_unavailable_still_runs_demand() -> None:
    app = _tick_app(zone_temp=20.0, setpoint=22.0, plant_setpoint=45.0)
    args = _tick_args()
    args["outdoor_temperature"] = _OUTDOOR
    app._config = parse_config(args)
    expected = _expected_command(zone_temp=20.0, setpoint=22.0)

    app.control_tick({})

    assert _set_value_writes(app) == [expected]
    assert all(c.args[0] != _OUTDOOR for c in app.get_state.call_args_list)


def test_equal_rounded_skip_no_set_value() -> None:
    """Off-grid raw 41.96 rounds to 42.0; plant already reads 42.0 → no call."""
    app = _tick_app(zone_temp=20.04, setpoint=22.0, plant_setpoint=42.0)
    assert app._last_commanded is None

    app.control_tick({})

    assert _set_value_writes(app) == []
    app.call_service.assert_not_called()
    assert any("command=42.0" in m for m in _info_msgs(app))
    # plant readable and at the command → ∫ advances
    assert app._integral == pytest.approx(1.96 * _DT_HOURS)
    assert app._last_commanded == pytest.approx(42.0)


def test_plant_drift_rewrites_command_despite_last_commanded() -> None:
    """R7: plant drifted to 50 after we commanded 42.0 → write 42.0 again."""
    app = _tick_app(zone_temp=20.0, setpoint=22.0, plant_setpoint=50.0)
    app._last_commanded = 42.0

    app.control_tick({})

    assert _set_value_writes(app) == [42.0]
    assert app._integral == pytest.approx(2.0 * _DT_HOURS)
    assert app._last_commanded == pytest.approx(42.0)


def test_plant_unavailable_equal_last_commanded_no_integral_step() -> None:
    """Plant unreadable: no write and ∫ held even if command == _last_commanded."""
    app = _tick_app(zone_temp=20.0, setpoint=22.0, plant_setpoint="unavailable")
    app._integral = 0.5
    expected = _expected_command(zone_temp=20.0, setpoint=22.0, integral=0.5)
    app._last_commanded = expected

    app.control_tick({})

    assert _set_value_writes(app) == []
    app.call_service.assert_not_called()
    assert app._integral == pytest.approx(0.5)
    assert app._last_commanded == pytest.approx(expected)
    assert any("Plant setpoint unavailable" in m for m in _warn_msgs(app))
    assert not any("command=" in m for m in _info_msgs(app))


def _echo_plant(app: HvacApp, initial: float) -> dict:
    """Plant entity reads back whatever number/set_value last wrote."""
    plant = {"value": initial}
    base_get_state = app.get_state.side_effect

    def get_state(entity_id: str, attribute: str | None = None):
        if entity_id == _PLANT_SETPOINT:
            return plant["value"]
        return base_get_state(entity_id, attribute)

    def call_service(service: str, **kwargs):
        if service == "number/set_value" and kwargs["entity_id"] == _PLANT_SETPOINT:
            plant["value"] = kwargs["value"]

    app.get_state.side_effect = get_state
    app.call_service.side_effect = call_service
    return plant


def test_integral_from_tick_one_appears_in_tick_two_command() -> None:
    app = _tick_app(zone_temp=20.0, setpoint=22.0, plant_setpoint=45.0)
    plant = _echo_plant(app, 45.0)

    app.control_tick({})

    assert _set_value_writes(app) == [42.0]
    assert plant["value"] == 42.0
    integral_after_one = app._integral
    assert integral_after_one == pytest.approx(2.0 * _DT_HOURS)

    app.control_tick({})

    expected_two = _expected_command(
        zone_temp=20.0, setpoint=22.0, integral=integral_after_one
    )
    assert expected_two == pytest.approx(42.2)
    assert _set_value_writes(app) == [42.0, expected_two]
    assert app._integral == pytest.approx(4.0 * _DT_HOURS)


def test_constant_error_ramps_about_one_twelfth_per_tick() -> None:
    """C4 defaults, e = 1 at 300 s: SWT ramps ~1/12 °C per tick, no rail jump."""
    app = _tick_app(zone_temp=21.0, setpoint=22.0, plant_setpoint=45.0)
    plant = _echo_plant(app, 45.0)

    readings = []
    for _ in range(12):
        app.control_tick({})
        readings.append(plant["value"])

    e = 1.0
    assert readings[0] == pytest.approx(_BASE + _KP * e)
    max_step = _KI * e * _DT_HOURS + 0.1 + 1e-9
    for prev, cur in zip(readings, readings[1:], strict=False):
        assert 0.0 <= cur - prev <= max_step
    assert app._integral == pytest.approx(e * 12 * _DT_HOURS)  # one hour: e·1 h
    assert readings[-1] == pytest.approx(
        round(_BASE + _KP * e + _KI * e * 11 * _DT_HOURS, 1)
    )


def test_distinct_gains_wire_kp_and_ki_into_tick() -> None:
    """kp ≠ ki at app level: swapped or merged gains change the written SWT."""
    args = _tick_args()
    args["pid"] = {**args["pid"], "kp": 2.0, "ki": 0.5}
    app = _tick_app(zone_temp=20.0, setpoint=22.0, plant_setpoint=45.0)
    app._config = parse_config(args)
    app._integral = 4.0  # I-term 0.5·4 = 2 °C

    app.control_tick({})

    # e=2: 40 + 2·2 + 0.5·4 = 46.0 (swap → 49.0; ki=kp → 52.0; kp=ki → 43.0)
    assert _set_value_writes(app) == [46.0]
    # ∫ step does not involve kp: 4 + e·dt_hours
    assert app._integral == pytest.approx(4.0 + 2.0 * _DT_HOURS)


@pytest.mark.parametrize("interval", [60, 300])
def test_one_hour_of_ticks_same_integral_at_any_interval(interval: int) -> None:
    """∫ is °C·h: one hour of ticks adds e·1 h for any control_interval (house: 60)."""
    args = _tick_args()
    args["control_interval"] = interval
    app = _tick_app(zone_temp=21.0, setpoint=22.0, plant_setpoint=45.0)
    app._config = parse_config(args)
    _echo_plant(app, 45.0)

    app.control_tick({})
    assert app._integral == pytest.approx(1.0 * interval / 3600.0)

    for _ in range(3600 // interval - 1):
        app.control_tick({})
    assert app._integral == pytest.approx(1.0)


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
    # R7: ∫ advances only when the plant entity is readable (written or already equal)
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
