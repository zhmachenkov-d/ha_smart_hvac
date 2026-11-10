"""Tests for fixed-gain PID Set Water Temperature control loop."""

import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from ha_smart_hvac.config import parse_config
from ha_smart_hvac.hvac_app import HvacApp
from ha_smart_hvac.pid import clamp
from ha_smart_hvac.rls import (
    STATE_FILENAME,
    RlsState,
    copy_durable,
    durable_equal,
    load_rls_state,
)

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
_BOILER_WATER = "sensor.boiler_water"
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
    boiler_water: object = 50.0,
    args: dict | None = None,
    app_dir: str | Path | None = None,
) -> HvacApp:
    """Hass-stubbed HvacApp for control_tick (_config only)."""
    app = object.__new__(HvacApp)
    app._config = parse_config(args if args is not None else _tick_args())
    app._integral = 0.0
    # Mid-demand by default so existing event no-op tests stay no-ops.
    app._gated_demand = True
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
    boiler_water: object = 50.0,
):
    """get_state side_effect for initialize under gated demand."""

    def get_state(entity_id: str, attribute: str | None = None):
        if entity_id == _PLANT_MGMT:
            return plant_management
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


def _fire_control_event(app: HvacApp) -> None:
    app.control_event(_PLANT_MGMT, "state", None, "on", {})


def test_initialize_schedules_control_tick() -> None:
    app = _init_app()

    app.initialize()

    assert app._integral == 0.0
    assert app._gated_demand is False
    assert _set_value_writes(app) == []
    app.run_every.assert_called_once()
    assert app.run_every.call_args.args[0].__func__ is HvacApp.control_tick
    assert app.run_every.call_args.args[1] == "now"
    assert app.run_every.call_args.args[2] == _CONTROL_INTERVAL


def test_initialize_under_demand_runs_first_tick() -> None:
    app = _init_app()
    app.get_state = MagicMock(side_effect=_init_gated_get_state())
    expected = _expected_command(zone_temp=20.0, setpoint=22.0)

    app.initialize()

    assert _set_value_writes(app) == [expected]
    assert app._integral == pytest.approx(2.0 * _DT_HOURS)
    assert app._gated_demand is True
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
    assert app._gated_demand is False


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


def test_initialize_warns_once_on_legacy_keys() -> None:
    args = _tick_args()
    args["outdoor_temperature"] = _OUTDOOR
    args["weather_feedforward"] = {"base": 25}
    args["pid"]["integral_min"] = -10
    args["foo"] = 1
    app = _init_app(args=args)

    app.initialize()

    # Default _init_app plant-off → initialize tick hands-off WARNING.
    assert _warn_msgs(app) == [
        "HVAC config: ignoring legacy or unknown keys: "
        "foo, outdoor_temperature, pid.integral_min, weather_feedforward",
        "Plant Management disabled",
    ]
    app.run_every.assert_called_once()


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
    assert app._gated_demand is True

    _fire_control_event(app)

    assert _set_value_writes(app) == []
    assert app._integral == pytest.approx(0.0)
    assert app._gated_demand is True


def test_tick_then_demand_event_leaves_integral() -> None:
    app = _tick_app(zone_temp=20.0, setpoint=22.0, plant_setpoint=45.0)

    app.control_tick({})
    integral_after_tick = app._integral
    assert integral_after_tick == pytest.approx(2.0 * _DT_HOURS)
    assert app._gated_demand is True

    app.call_service.reset_mock()
    _fire_control_event(app)

    assert _set_value_writes(app) == []
    assert app._integral == pytest.approx(integral_after_tick)
    assert app._gated_demand is True


def test_rising_edge_idle_to_demand_writes_without_integral() -> None:
    app = _tick_app(zone_temp=20.0, setpoint=22.0, plant_setpoint=45.0)
    app._gated_demand = False
    app._integral = 0.5
    expected = _expected_command(zone_temp=20.0, setpoint=22.0, integral=0.5)

    _fire_control_event(app)

    assert _set_value_writes(app) == [expected]
    assert app._integral == pytest.approx(0.5)
    assert app._rls.last_u == pytest.approx(expected)
    assert app._gated_demand is True


def test_rising_edge_plant_on_with_demand_writes() -> None:
    """Plant-off → on while zones already heat: latch was False → edge write."""
    app = _tick_app(zone_temp=20.0, setpoint=22.0, plant_setpoint=45.0)
    app._gated_demand = False
    expected = _expected_command(zone_temp=20.0, setpoint=22.0)

    _fire_control_event(app)

    assert _set_value_writes(app) == [expected]
    assert app._integral == pytest.approx(0.0)
    assert app._gated_demand is True


def test_edge_equal_float_latches_and_updates_last_u() -> None:
    app = _tick_app(zone_temp=20.04, setpoint=22.0, plant_setpoint=42.0)
    app._gated_demand = False
    app._rls.last_u = 40.0

    _fire_control_event(app)

    assert _set_value_writes(app) == []
    assert app._integral == pytest.approx(0.0)
    assert app._rls.last_u == pytest.approx(42.0)
    assert app._gated_demand is True


def test_edge_plant_unreadable_keeps_latch_false() -> None:
    app = _tick_app(zone_temp=20.0, setpoint=22.0, plant_setpoint="unavailable")
    app._gated_demand = False
    app._integral = 0.5
    app._rls.last_u = 40.0

    _fire_control_event(app)

    assert _set_value_writes(app) == []
    assert app._integral == pytest.approx(0.5)
    assert app._rls.last_u == pytest.approx(40.0)
    assert app._gated_demand is False
    assert any("Plant setpoint unavailable" in m for m in _warn_msgs(app))


def test_edge_weights_unusable_clears_and_unlatches() -> None:
    args = _tick_args()
    args["zones"] = [
        {
            "name": _ZONE_NAME,
            "temperature": _ZONE_TEMP,
            "weight": 0.0,
            "thermostats": [_CLIMATE],
        }
    ]
    app = _tick_app(zone_temp=20.0, setpoint=22.0, plant_setpoint=45.0, args=args)
    app._gated_demand = False
    app._integral = 3.0

    _fire_control_event(app)

    assert _set_value_writes(app) == [0.0]
    assert app._integral == 0.0
    assert app._gated_demand is False


def test_tick_weights_unusable_unlatches() -> None:
    args = _tick_args()
    args["zones"] = [
        {
            "name": _ZONE_NAME,
            "temperature": _ZONE_TEMP,
            "weight": 0.0,
            "thermostats": [_CLIMATE],
        }
    ]
    app = _tick_app(zone_temp=20.0, setpoint=22.0, plant_setpoint=45.0, args=args)
    assert app._gated_demand is True
    app._integral = 3.0

    app.control_tick({})

    assert _set_value_writes(app) == [0.0]
    assert app._integral == 0.0
    assert app._gated_demand is False


def test_demand_edge_no_rls_no_persist(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    stepped = {"n": 0}
    real_step = __import__("ha_smart_hvac.rls", fromlist=["rls_step"]).rls_step

    def _count_step(state, **kwargs):
        stepped["n"] += 1
        return real_step(state, **kwargs)

    persisted = {"n": 0}

    def _count_save(*_a, **_k):
        persisted["n"] += 1
        return True

    monkeypatch.setattr("ha_smart_hvac.hvac_app.rls_step", _count_step)
    monkeypatch.setattr("ha_smart_hvac.hvac_app.save_rls_state", _count_save)
    app = _tick_app(
        zone_temp=20.0,
        setpoint=22.0,
        plant_setpoint=45.0,
        boiler_water=50.1,
        args=_adaptive_args(),
        app_dir=tmp_path,
    )
    app._gated_demand = False
    app._integral = 1.0
    app._rls.y_prev = 50.0
    app._rls.last_u = 40.0
    app._rls.theta = [0.9, 0.1]
    app._rls.p = [[1e-12, 0.0], [0.0, 1e-12]]
    expected = _expected_command(zone_temp=20.0, setpoint=22.0, integral=1.0)

    _fire_control_event(app)

    assert stepped["n"] == 0
    assert persisted["n"] == 0
    assert _set_value_writes(app) == [expected]
    assert app._integral == pytest.approx(1.0)
    assert app._rls.last_u == pytest.approx(expected)
    assert app._rls.y_prev == pytest.approx(50.0)
    assert app._gated_demand is True


def test_demand_edge_uses_adapted_gains() -> None:
    adapted_kp, adapted_ki = 2.0, 0.5
    app = _tick_app(
        zone_temp=20.0,
        setpoint=22.0,
        plant_setpoint=45.0,
        args=_adaptive_args(),
    )
    app._gated_demand = False
    app._integral = 1.0
    app._rls_fallback_latched = False
    app._rls.adapted_kp = adapted_kp
    app._rls.adapted_ki = adapted_ki
    expected = _expected_command(
        zone_temp=20.0,
        setpoint=22.0,
        integral=1.0,
        kp=adapted_kp,
        ki=adapted_ki,
    )

    _fire_control_event(app)

    assert _set_value_writes(app) == [expected]
    assert app._integral == pytest.approx(1.0)
    assert app._gated_demand is True


def test_tick_after_edge_advances_integral() -> None:
    app = _tick_app(zone_temp=20.0, setpoint=22.0, plant_setpoint=45.0)
    app._gated_demand = False

    _fire_control_event(app)
    assert app._integral == pytest.approx(0.0)
    assert app._gated_demand is True
    edge_command = _set_value_writes(app)[0]

    app.call_service.reset_mock()
    app.control_tick({})

    assert app._integral == pytest.approx(2.0 * _DT_HOURS)
    assert app._gated_demand is True
    # Full tick may rewrite (plant still at prior) or equal-skip; ∫ advanced once.
    assert edge_command == pytest.approx(
        _expected_command(zone_temp=20.0, setpoint=22.0)
    )


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


def test_two_decimal_setpoint_max_command_stays_inside_bound() -> None:
    """Grid snap must not write above setpoint_max when max has two decimals."""
    args = _tick_args()
    args["setpoint_max"] = 55.06
    args["base_water_temp"] = 50.0
    app = _tick_app(zone_temp=10.0, setpoint=30.0, plant_setpoint=45.0)
    app._config = parse_config(args)
    # e=20, raw=70 → quantize to 55.0 (≤ 55.06), not round(55.06)=55.1

    app.control_tick({})

    assert _set_value_writes(app) == [55.0]
    assert _set_value_writes(app)[0] <= 55.06


def test_off_grid_command_logged_without_one_decimal_rounding() -> None:
    """Success INFO must show the written off-grid command, not :.1f (55.0)."""
    args = _tick_args()
    args["setpoint_min"] = 55.01
    args["setpoint_max"] = 55.06
    args["base_water_temp"] = 55.03
    app = _tick_app(zone_temp=22.0, setpoint=22.0, plant_setpoint=45.0)
    app._config = parse_config(args)
    # e=0, raw=55.03 → no 0.1 grid point in bounds → clamp fallback 55.03

    app.control_tick({})

    assert _set_value_writes(app) == [pytest.approx(55.03)]
    assert any("command=55.03" in m for m in _info_msgs(app))


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
    app._rls = RlsState()
    app._rls_fallback_latched = False
    app._rls_fallback_reason = None
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
    app._rls = RlsState()
    app._rls_fallback_latched = False
    app._rls_fallback_reason = None
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
    app._rls = RlsState()
    app._rls_fallback_latched = False
    app._rls_fallback_reason = None
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

    app.control_tick({})

    assert _set_value_writes(app) == []
    app.call_service.assert_not_called()
    assert any("command=42.0" in m for m in _info_msgs(app))
    # plant readable and at the command → ∫ advances
    assert app._integral == pytest.approx(1.96 * _DT_HOURS)


def test_plant_drift_rewrites_command() -> None:
    """R7: plant drifted to 50 after we commanded 42.0 → write 42.0 again."""
    app = _tick_app(zone_temp=20.0, setpoint=22.0, plant_setpoint=50.0)

    app.control_tick({})

    assert _set_value_writes(app) == [42.0]
    assert app._integral == pytest.approx(2.0 * _DT_HOURS)


def test_plant_unavailable_no_integral_step() -> None:
    """Plant unreadable: no write and ∫ held."""
    app = _tick_app(zone_temp=20.0, setpoint=22.0, plant_setpoint="unavailable")
    app._integral = 0.5

    app.control_tick({})

    assert _set_value_writes(app) == []
    app.call_service.assert_not_called()
    assert app._integral == pytest.approx(0.5)
    assert app._gated_demand is False
    assert any("Plant setpoint unavailable" in m for m in _warn_msgs(app))
    assert not any("command=" in m for m in _info_msgs(app))


def test_tick_r7_then_event_edge_writes_without_integral() -> None:
    """Sticky-open: tick R7 leaves latch False; later event edge writes, ∫ frozen."""
    app = _tick_app(zone_temp=20.0, setpoint=22.0, plant_setpoint="unavailable")
    app._integral = 0.5

    app.control_tick({})
    assert app._gated_demand is False
    assert app._integral == pytest.approx(0.5)

    app.call_service.reset_mock()
    app.get_state = MagicMock(side_effect=_init_gated_get_state(plant_setpoint=45.0))
    expected = _expected_command(zone_temp=20.0, setpoint=22.0, integral=0.5)

    _fire_control_event(app)

    assert _set_value_writes(app) == [expected]
    assert app._integral == pytest.approx(0.5)
    assert app._gated_demand is True


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
    assert app._gated_demand is False


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

    app.control_tick({})

    assert _set_value_writes(app) == [0.0]
    assert app._integral == 0.0
    assert "Demand zone weights unusable; setpoint 0" in _warn_msgs(app)
    assert not any("weights unusable" in m for m in _info_msgs(app))


def test_overflowing_weights_go_idle_not_setpoint_max() -> None:
    zone_two_temp = "sensor.zone_two_temp"
    climate_two = "climate.zone_two"
    args = _tick_args()
    args["zones"] = [
        {
            "name": "zone_one",
            "temperature": _ZONE_TEMP,
            "weight": 1e308,
            "thermostats": [_CLIMATE],
        },
        {
            "name": "zone_two",
            "temperature": zone_two_temp,
            "weight": 1e308,
            "thermostats": [climate_two],
        },
    ]
    app = object.__new__(HvacApp)
    app._config = parse_config(args)
    app._integral = 3.0
    app._rls = RlsState()
    app._rls_fallback_latched = False
    app._rls_fallback_reason = None
    app.call_service = MagicMock()
    app.log = MagicMock()

    def get_state(entity_id: str, attribute: str | None = None):
        if entity_id == _PLANT_MGMT:
            return "on"
        if entity_id == _ZONE_TEMP:
            return 20.0
        if entity_id == zone_two_temp:
            return 18.0
        if entity_id == _PLANT_SETPOINT:
            return 45.0
        if entity_id in (_CLIMATE, climate_two):
            if attribute == "temperature":
                return 22.0
            if attribute == "hvac_action":
                return "heating"
            return "heat"
        return None

    app.get_state = MagicMock(side_effect=get_state)

    app.control_tick({})

    assert _set_value_writes(app) == [0.0]
    assert app._integral == 0.0
    assert "Demand zone weights unusable; setpoint 0" in _warn_msgs(app)
    assert _SETPOINT_MAX not in _set_value_writes(app)


def test_event_plant_off_no_write_clears() -> None:
    app = _tick_app(plant_management="off")
    app._integral = 5.0

    _fire_control_event(app)

    assert _set_value_writes(app) == []
    assert app._integral == 0.0
    assert app._gated_demand is False


def test_event_idle_writes_zero_clears() -> None:
    app = _tick_app(zone_temp=22.0, setpoint=22.0, hvac_action="idle")
    app._integral = 5.0

    _fire_control_event(app)

    assert _set_value_writes(app) == [0.0]
    assert app._integral == 0.0
    assert app._gated_demand is False


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
    assert app._gated_demand is False
    assert any("Plant setpoint unavailable" in m for m in _warn_msgs(app))


def test_event_no_valid_zones_writes_zero_and_clears() -> None:
    app = _tick_app(zone_temp="unavailable")
    app._integral = 5.0

    _fire_control_event(app)

    assert _set_value_writes(app) == [0.0]
    assert app._integral == 0.0
    assert app._gated_demand is False


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


def test_adaptive_off_never_steps_rls(monkeypatch: pytest.MonkeyPatch) -> None:
    stepped = {"n": 0}

    def _count(*_a, **_k):
        stepped["n"] += 1

    monkeypatch.setattr("ha_smart_hvac.hvac_app.rls_step", _count)
    app = _tick_app(zone_temp=20.0, setpoint=22.0, plant_setpoint=45.0)
    app._rls.y_prev = 50.0
    app._rls.last_u = 42.0

    app.control_tick({})

    assert stepped["n"] == 0
    assert _set_value_writes(app) == [_expected_command(zone_temp=20.0, setpoint=22.0)]


def test_adaptive_demand_tick_steps_and_uses_imc_gains(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prior u + y_prev + finite y → one RLS step; tiny P keeps IMC-valid θ."""
    from ha_smart_hvac.rls import imc_gains

    stepped = {"n": 0}
    real_step = __import__("ha_smart_hvac.rls", fromlist=["rls_step"]).rls_step

    def _counting_step(state, **kwargs):
        stepped["n"] += 1
        return real_step(state, **kwargs)

    monkeypatch.setattr("ha_smart_hvac.hvac_app.rls_step", _counting_step)
    app = _tick_app(
        zone_temp=20.0,
        setpoint=22.0,
        plant_setpoint=45.0,
        boiler_water=50.1,
        args=_adaptive_args(),
    )
    app._rls.theta = [0.9, 0.1]
    app._rls.p = [[1e-12, 0.0], [0.0, 1e-12]]
    app._rls.y_prev = 50.0
    app._rls.last_u = 45.0

    app.control_tick({})

    assert stepped["n"] == 1
    gains = imc_gains(app._rls.theta[0], app._rls.theta[1], float(_CONTROL_INTERVAL))
    assert gains is not None
    assert app._rls.adapted_kp == pytest.approx(gains[0])
    assert app._rls.adapted_ki == pytest.approx(gains[1])
    assert app._rls_fallback_latched is False
    expected = _expected_command(
        zone_temp=20.0, setpoint=22.0, kp=gains[0], ki=gains[1]
    )
    assert _set_value_writes(app) == [expected]
    assert app._rls.y_prev == pytest.approx(50.1)
    assert app._rls.last_u == pytest.approx(expected)


def _count_rls_steps(monkeypatch: pytest.MonkeyPatch) -> dict[str, int]:
    stepped = {"n": 0}
    real_step = __import__("ha_smart_hvac.rls", fromlist=["rls_step"]).rls_step

    def _count(state, **kwargs) -> bool:
        stepped["n"] += 1
        return real_step(state, **kwargs)

    monkeypatch.setattr("ha_smart_hvac.hvac_app.rls_step", _count)
    return stepped


def test_adaptive_seed_only_when_no_y_prev(monkeypatch: pytest.MonkeyPatch) -> None:
    stepped = _count_rls_steps(monkeypatch)
    app = _tick_app(
        zone_temp=20.0,
        setpoint=22.0,
        plant_setpoint=45.0,
        boiler_water=50.0,
        args=_adaptive_args(),
    )
    app._rls.last_u = 42.0
    assert app._rls.y_prev is None

    app.control_tick({})

    assert stepped["n"] == 0
    assert app._rls.y_prev == pytest.approx(50.0)
    assert _set_value_writes(app) == [_expected_command(zone_temp=20.0, setpoint=22.0)]


def test_adaptive_no_step_without_prior_u_refreshes_y_prev(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stepped = _count_rls_steps(monkeypatch)
    app = _tick_app(
        zone_temp=20.0,
        setpoint=22.0,
        plant_setpoint=45.0,
        boiler_water=51.0,
        args=_adaptive_args(),
    )
    app._rls.y_prev = 49.0
    assert app._rls.last_u is None

    app.control_tick({})

    assert stepped["n"] == 0
    assert app._rls.y_prev == pytest.approx(51.0)


def test_adaptive_boiler_water_unreadable_no_step_leaves_y_prev(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stepped = _count_rls_steps(monkeypatch)
    app = _tick_app(
        zone_temp=20.0,
        setpoint=22.0,
        plant_setpoint=45.0,
        boiler_water="unavailable",
        args=_adaptive_args(),
    )
    app._rls.y_prev = 50.0
    app._rls.last_u = 42.0

    app.control_tick({})

    assert stepped["n"] == 0
    assert app._rls.y_prev == pytest.approx(50.0)
    assert any("Boiler water unavailable" in m for m in _warn_msgs(app))
    assert app._integral == pytest.approx(2.0 * _DT_HOURS)


def test_adaptive_plant_unreadable_no_rls_no_integral(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stepped = _count_rls_steps(monkeypatch)
    app = _tick_app(
        zone_temp=20.0,
        setpoint=22.0,
        plant_setpoint="unavailable",
        boiler_water=51.0,
        args=_adaptive_args(),
    )
    app._rls.y_prev = 50.0
    app._rls.last_u = 42.0
    app._integral = 0.5

    app.control_tick({})

    assert stepped["n"] == 0
    assert app._integral == pytest.approx(0.5)
    assert app._rls.y_prev == pytest.approx(51.0)
    assert app._rls.last_u == pytest.approx(42.0)


def test_adaptive_control_event_no_rls_no_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stepped = _count_rls_steps(monkeypatch)
    app = _tick_app(
        zone_temp=20.0,
        setpoint=22.0,
        plant_setpoint=45.0,
        boiler_water=50.0,
        args=_adaptive_args(),
    )
    assert app._gated_demand is True
    app._rls.y_prev = 50.0
    app._rls.last_u = 42.0
    app._integral = 1.0

    _fire_control_event(app)

    assert stepped["n"] == 0
    assert _set_value_writes(app) == []
    assert app._integral == pytest.approx(1.0)
    assert app._gated_demand is True


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


def test_weights_unusable_clear_wipes_y_prev_keeps_last_u(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stepped = _count_rls_steps(monkeypatch)
    args = _adaptive_args()
    args["zones"][0]["weight"] = 0.0
    app = _tick_app(
        zone_temp=20.0,
        setpoint=22.0,
        plant_setpoint=45.0,
        boiler_water=50.0,
        args=args,
    )
    app._rls.y_prev = 50.0
    app._rls.last_u = 42.0
    app._rls.theta = [0.8, 0.2]
    app._rls.p = [[1.0, 0.1], [0.1, 2.0]]
    app._rls.adapted_kp = 2.0
    app._rls.adapted_ki = 0.5

    app.control_tick({})

    assert stepped["n"] == 0
    assert app._rls.y_prev is None
    assert app._rls.last_u == pytest.approx(42.0)
    assert app._rls.theta == [0.8, 0.2]
    assert app._rls.p == [[1.0, 0.1], [0.1, 2.0]]
    assert app._rls.adapted_kp == pytest.approx(2.0)
    assert _set_value_writes(app) == [0.0]


def test_adaptive_imc_invalid_latches_yaml_fixed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """True step + IMC None → θ/P kept; park adapted; latch → YAML fixed."""
    stepped = {"n": 0}
    real_step = __import__("ha_smart_hvac.rls", fromlist=["rls_step"]).rls_step

    def _counting_step(state, **kwargs):
        stepped["n"] += 1
        return real_step(state, **kwargs)

    monkeypatch.setattr("ha_smart_hvac.hvac_app.rls_step", _counting_step)
    monkeypatch.setattr("ha_smart_hvac.hvac_app.imc_gains", lambda *_a, **_k: None)
    app = _tick_app(
        zone_temp=20.0,
        setpoint=22.0,
        plant_setpoint=45.0,
        boiler_water=50.1,
        args=_adaptive_args(),
    )
    app._rls.theta = [0.9, 0.1]
    app._rls.p = [[1e-12, 0.0], [0.0, 1e-12]]
    app._rls.y_prev = 50.0
    app._rls.last_u = 45.0
    app._rls.adapted_kp = 2.0
    app._rls.adapted_ki = 0.5
    preview = RlsState()
    preview.theta = app._rls.theta[:]
    preview.p = [row[:] for row in app._rls.p]
    assert real_step(preview, y=50.1, y_prev=50.0, u_prev=45.0) is True

    app.control_tick({})

    assert stepped["n"] == 1
    # θ/P committed on True step even when IMC rejected.
    assert app._rls.theta[0] == pytest.approx(preview.theta[0])
    assert app._rls.theta[1] == pytest.approx(preview.theta[1])
    assert app._rls.p[0][0] == pytest.approx(preview.p[0][0])
    assert app._rls.p[1][1] == pytest.approx(preview.p[1][1])
    # Park leaves prior adapted; demand uses YAML (not parked 44.0).
    assert app._rls.adapted_kp == pytest.approx(2.0)
    assert app._rls.adapted_ki == pytest.approx(0.5)
    assert app._rls_fallback_latched is True
    assert app._rls_fallback_reason == "imc_none"
    # YAML kp=1, ki=1; e=2 → command 42.0
    assert _set_value_writes(app) == [42.0]
    assert sum(1 for m in _warn_msgs(app) if "imc_none" in m) == 1


def test_adaptive_rls_noop_latches_yaml_fixed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("ha_smart_hvac.hvac_app.rls_step", lambda *_a, **_k: False)
    app = _tick_app(
        zone_temp=20.0,
        setpoint=22.0,
        plant_setpoint=45.0,
        boiler_water=50.1,
        args=_adaptive_args(),
    )
    app._rls.theta = [0.9, 0.1]
    app._rls.p = [[1.0, 0.0], [0.0, 1.0]]
    app._rls.y_prev = 50.0
    app._rls.last_u = 45.0
    app._rls.adapted_kp = 2.0
    app._rls.adapted_ki = 0.5
    theta_before = app._rls.theta[:]
    p_before = [row[:] for row in app._rls.p]

    app.control_tick({})

    assert app._rls.theta == theta_before
    assert app._rls.p == p_before
    assert app._rls.adapted_kp == pytest.approx(2.0)
    assert app._rls_fallback_latched is True
    assert app._rls_fallback_reason == "rls_noop"
    assert _set_value_writes(app) == [42.0]
    assert sum(1 for m in _warn_msgs(app) if "rls_noop" in m) == 1

    # Same reason while latched → silent (no second WARNING).
    app.call_service.reset_mock()
    app.log.reset_mock()
    app._rls.y_prev = 50.0
    app.control_tick({})
    assert app._rls_fallback_reason == "rls_noop"
    assert not any("RLS fallback latched" in m for m in _warn_msgs(app))


def test_adaptive_out_of_band_latches_yaml_fixed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stepped = {"n": 0}
    real_step = __import__("ha_smart_hvac.rls", fromlist=["rls_step"]).rls_step

    def _counting_step(state, **kwargs):
        stepped["n"] += 1
        return real_step(state, **kwargs)

    monkeypatch.setattr("ha_smart_hvac.hvac_app.rls_step", _counting_step)
    monkeypatch.setattr(
        "ha_smart_hvac.hvac_app.imc_gains", lambda *_a, **_k: (50.0, 1.0)
    )
    app = _tick_app(
        zone_temp=20.0,
        setpoint=22.0,
        plant_setpoint=45.0,
        boiler_water=50.1,
        args=_adaptive_args(kp_min=0.0, kp_max=10.0, ki_min=0.0, ki_max=100.0),
    )
    app._rls.theta = [0.9, 0.1]
    app._rls.p = [[1e-12, 0.0], [0.0, 1e-12]]
    app._rls.y_prev = 50.0
    app._rls.last_u = 45.0
    app._rls.adapted_kp = 2.0
    app._rls.adapted_ki = 0.5
    preview = RlsState()
    preview.theta = app._rls.theta[:]
    preview.p = [row[:] for row in app._rls.p]
    assert real_step(preview, y=50.1, y_prev=50.0, u_prev=45.0) is True

    app.control_tick({})

    assert stepped["n"] == 1
    assert app._rls.theta[0] == pytest.approx(preview.theta[0])
    assert app._rls.theta[1] == pytest.approx(preview.theta[1])
    assert app._rls.p[0][0] == pytest.approx(preview.p[0][0])
    assert app._rls.p[1][1] == pytest.approx(preview.p[1][1])
    assert app._rls.adapted_kp == pytest.approx(2.0)  # not overwritten by 50
    assert app._rls_fallback_latched is True
    assert app._rls_fallback_reason == "out_of_band"
    assert _set_value_writes(app) == [42.0]
    oob_warns = [m for m in _warn_msgs(app) if "out_of_band" in m]
    assert len(oob_warns) == 1
    assert "kp=50" in oob_warns[0]


def test_adaptive_nonfinite_imc_latches_imc_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_step = __import__("ha_smart_hvac.rls", fromlist=["rls_step"]).rls_step
    monkeypatch.setattr("ha_smart_hvac.hvac_app.rls_step", real_step)
    monkeypatch.setattr(
        "ha_smart_hvac.hvac_app.imc_gains",
        lambda *_a, **_k: (float("nan"), 1.0),
    )
    app = _tick_app(
        zone_temp=20.0,
        setpoint=22.0,
        plant_setpoint=45.0,
        boiler_water=50.1,
        args=_adaptive_args(),
    )
    app._rls.theta = [0.9, 0.1]
    app._rls.p = [[1e-12, 0.0], [0.0, 1e-12]]
    app._rls.y_prev = 50.0
    app._rls.last_u = 45.0
    app._rls.adapted_kp = 2.0
    app._rls.adapted_ki = 0.5
    preview = RlsState()
    preview.theta = app._rls.theta[:]
    preview.p = [row[:] for row in app._rls.p]
    assert real_step(preview, y=50.1, y_prev=50.0, u_prev=45.0) is True

    app.control_tick({})

    assert app._rls.theta[0] == pytest.approx(preview.theta[0])
    assert app._rls.theta[1] == pytest.approx(preview.theta[1])
    assert app._rls.p[0][0] == pytest.approx(preview.p[0][0])
    assert app._rls.p[1][1] == pytest.approx(preview.p[1][1])
    assert app._rls.adapted_kp == pytest.approx(2.0)
    assert app._rls.adapted_ki == pytest.approx(0.5)
    assert app._rls_fallback_latched is True
    assert app._rls_fallback_reason == "imc_none"
    assert _set_value_writes(app) == [42.0]
    assert sum(1 for m in _warn_msgs(app) if "imc_none" in m) == 1


def test_adaptive_healthy_in_band_clears_latch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ha_smart_hvac.rls import imc_gains

    real_step = __import__("ha_smart_hvac.rls", fromlist=["rls_step"]).rls_step
    monkeypatch.setattr("ha_smart_hvac.hvac_app.rls_step", real_step)
    app = _tick_app(
        zone_temp=20.0,
        setpoint=22.0,
        plant_setpoint=45.0,
        boiler_water=50.1,
        args=_adaptive_args(),
    )
    app._rls.theta = [0.9, 0.1]
    app._rls.p = [[1e-12, 0.0], [0.0, 1e-12]]
    app._rls.y_prev = 50.0
    app._rls.last_u = 45.0
    app._rls_fallback_latched = True
    app._rls_fallback_reason = "imc_none"

    app.control_tick({})

    gains = imc_gains(app._rls.theta[0], app._rls.theta[1], float(_CONTROL_INTERVAL))
    assert gains is not None
    assert app._rls_fallback_latched is False
    assert app._rls_fallback_reason is None
    assert app._rls.adapted_kp == pytest.approx(gains[0])
    expected = _expected_command(
        zone_temp=20.0, setpoint=22.0, kp=gains[0], ki=gains[1]
    )
    assert _set_value_writes(app) == [expected]


def test_adaptive_latch_reason_change_rewarns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"n": 0}

    def _step(*_a, **_k) -> bool:
        calls["n"] += 1
        return False if calls["n"] == 1 else True

    monkeypatch.setattr("ha_smart_hvac.hvac_app.rls_step", _step)
    monkeypatch.setattr(
        "ha_smart_hvac.hvac_app.imc_gains", lambda *_a, **_k: (50.0, 1.0)
    )
    app = _tick_app(
        zone_temp=20.0,
        setpoint=22.0,
        plant_setpoint=45.0,
        boiler_water=50.1,
        args=_adaptive_args(kp_max=10.0),
    )
    app._rls.y_prev = 50.0
    app._rls.last_u = 45.0

    app.control_tick({})
    assert app._rls_fallback_reason == "rls_noop"
    assert sum(1 for m in _warn_msgs(app) if "rls_noop" in m) == 1

    app.call_service.reset_mock()
    app.log.reset_mock()
    app._rls.y_prev = 50.0  # keep priors for second step
    app.control_tick({})

    assert app._rls_fallback_reason == "out_of_band"
    assert sum(1 for m in _warn_msgs(app) if "out_of_band" in m) == 1
    assert sum(1 for m in _warn_msgs(app) if "rls_noop" in m) == 0


def test_adaptive_skip_step_does_not_enter_or_refresh_latch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stepped = _count_rls_steps(monkeypatch)
    app = _tick_app(
        zone_temp=20.0,
        setpoint=22.0,
        plant_setpoint=45.0,
        boiler_water=50.0,
        args=_adaptive_args(),
    )
    app._rls_fallback_latched = True
    app._rls_fallback_reason = "rls_noop"
    app._rls.adapted_kp = 2.0
    app._rls.adapted_ki = 0.5
    app._rls.last_u = 42.0
    assert app._rls.y_prev is None  # seed → skip step

    app.control_tick({})

    assert stepped["n"] == 0
    assert app._rls_fallback_latched is True
    assert app._rls_fallback_reason == "rls_noop"
    assert _set_value_writes(app) == [42.0]  # YAML, not parked 44
    assert not any("RLS fallback latched" in m for m in _warn_msgs(app))


def test_adaptive_skip_step_plant_unreadable_does_not_refresh_latch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stepped = _count_rls_steps(monkeypatch)
    app = _tick_app(
        zone_temp=20.0,
        setpoint=22.0,
        plant_setpoint="unavailable",
        boiler_water=51.0,
        args=_adaptive_args(),
    )
    app._rls_fallback_latched = True
    app._rls_fallback_reason = "out_of_band"
    app._rls.adapted_kp = 2.0
    app._rls.adapted_ki = 0.5
    app._rls.y_prev = 50.0
    app._rls.last_u = 42.0

    app.control_tick({})

    assert stepped["n"] == 0
    assert app._rls_fallback_latched is True
    assert app._rls_fallback_reason == "out_of_band"
    assert _set_value_writes(app) == []
    assert not any("RLS fallback latched" in m for m in _warn_msgs(app))


def test_adaptive_skip_step_boiler_unreadable_does_not_refresh_latch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stepped = _count_rls_steps(monkeypatch)
    app = _tick_app(
        zone_temp=20.0,
        setpoint=22.0,
        plant_setpoint=45.0,
        boiler_water="unavailable",
        args=_adaptive_args(),
    )
    app._rls_fallback_latched = True
    app._rls_fallback_reason = "rls_noop"
    app._rls.adapted_kp = 2.0
    app._rls.adapted_ki = 0.5
    app._rls.y_prev = 50.0
    app._rls.last_u = 42.0

    app.control_tick({})

    assert stepped["n"] == 0
    assert app._rls_fallback_latched is True
    assert app._rls_fallback_reason == "rls_noop"
    assert _set_value_writes(app) == [42.0]  # YAML fixed demand write
    assert not any("RLS fallback latched" in m for m in _warn_msgs(app))
    assert any("Boiler water unavailable" in m for m in _warn_msgs(app))


def test_adaptive_rail_edge_publishes_adapted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Inclusive rail edges must publish through `_maybe_rls_step`, not latch."""
    real_step = __import__("ha_smart_hvac.rls", fromlist=["rls_step"]).rls_step
    monkeypatch.setattr("ha_smart_hvac.hvac_app.rls_step", real_step)
    edge = (10.0, 100.0)
    monkeypatch.setattr("ha_smart_hvac.hvac_app.imc_gains", lambda *_a, **_k: edge)
    app = _tick_app(
        zone_temp=20.0,
        setpoint=22.0,
        plant_setpoint=45.0,
        boiler_water=50.1,
        args=_adaptive_args(kp_min=0.0, kp_max=10.0, ki_min=0.0, ki_max=100.0),
    )
    app._rls.theta = [0.9, 0.1]
    app._rls.p = [[1e-12, 0.0], [0.0, 1e-12]]
    app._rls.y_prev = 50.0
    app._rls.last_u = 45.0
    app._rls_fallback_latched = True
    app._rls_fallback_reason = "imc_none"

    app.control_tick({})

    assert app._rls_fallback_latched is False
    assert app._rls_fallback_reason is None
    assert app._rls.adapted_kp == pytest.approx(edge[0])
    assert app._rls.adapted_ki == pytest.approx(edge[1])
    expected = _expected_command(zone_temp=20.0, setpoint=22.0, kp=edge[0], ki=edge[1])
    assert _set_value_writes(app) == [expected]


def test_adaptive_latch_survives_clear_seed_uses_yaml(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stepped = _count_rls_steps(monkeypatch)
    app = _tick_app(
        zone_temp=20.0,
        setpoint=22.0,
        plant_setpoint=45.0,
        boiler_water=50.0,
        args=_adaptive_args(),
    )
    app._rls_fallback_latched = True
    app._rls_fallback_reason = "out_of_band"
    app._rls.adapted_kp = 2.0
    app._rls.adapted_ki = 0.5
    app._rls.last_u = 42.0
    app._rls.y_prev = 50.0
    app._integral = 12.0

    app._clear_pid_ephemeral()
    assert app._rls.y_prev is None
    assert app._rls_fallback_latched is True
    assert app._rls.adapted_kp == pytest.approx(2.0)

    app.control_tick({})

    assert stepped["n"] == 0  # seed only
    assert app._rls_fallback_latched is True
    assert app._rls_fallback_reason == "out_of_band"
    assert _set_value_writes(app) == [42.0]  # YAML fixed, not parked adapted


def test_adaptive_after_clear_seed_then_parked_gains_step(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ha_smart_hvac.rls import imc_gains

    stepped = _count_rls_steps(monkeypatch)
    app = _tick_app(
        zone_temp=20.0,
        setpoint=22.0,
        plant_setpoint=45.0,
        boiler_water=50.0,
        args=_adaptive_args(),
    )
    app._rls.last_u = 42.0
    app._rls.adapted_kp = 2.0
    app._rls.adapted_ki = 0.5
    app._rls.y_prev = None  # post-clear

    app.control_tick({})

    assert stepped["n"] == 0
    assert app._rls.y_prev == pytest.approx(50.0)
    assert app._rls_fallback_latched is False
    # e=2, u_pid = 2*2 + 0.5*0 = 4 → command 44.0
    assert _set_value_writes(app) == [44.0]

    app.call_service.reset_mock()
    app.control_tick({})

    assert stepped["n"] == 1
    gains = imc_gains(app._rls.theta[0], app._rls.theta[1], float(_CONTROL_INTERVAL))
    assert gains is not None
    assert app._rls_fallback_latched is False
    assert app._rls.adapted_kp == pytest.approx(gains[0])
    assert app._rls.adapted_ki == pytest.approx(gains[1])
    expected = _expected_command(
        zone_temp=20.0,
        setpoint=22.0,
        integral=2.0 * _DT_HOURS,
        kp=gains[0],
        ki=gains[1],
    )
    assert _set_value_writes(app) == [expected]


def test_equal_skip_demand_write_updates_last_u() -> None:
    app = _tick_app(
        zone_temp=20.04,
        setpoint=22.0,
        plant_setpoint=42.0,
        boiler_water=50.0,
        args=_adaptive_args(),
    )

    app.control_tick({})

    assert _set_value_writes(app) == []
    assert app._rls.last_u == pytest.approx(42.0)


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


def test_force_rewrite_after_adapted_drop_scrubs_disk(tmp_path: Path) -> None:
    path = tmp_path / STATE_FILENAME
    _write_valid_rls_json(path, adapted_kp=1.5, adapted_ki=None)
    app = _init_app(args=_adaptive_args(), app_dir=tmp_path)
    app.initialize()
    assert app._rls_force_rewrite is True
    assert app._rls.adapted_kp is None

    app.get_state = MagicMock(
        side_effect=lambda entity_id, attribute=None: {
            _PLANT_MGMT: "on",
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
    app._rls.last_u = 42.0
    app._rls_last_saved = copy_durable(app._rls)

    app.control_tick({})

    loaded = load_rls_state(path)
    assert loaded is not None
    assert loaded.adapted_kp is None
    assert loaded.adapted_ki is None
    assert app._rls_force_rewrite is False


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


def test_demand_persist_after_dirty_write(tmp_path: Path) -> None:
    app = _tick_app(
        zone_temp=20.0,
        setpoint=22.0,
        plant_setpoint=45.0,
        boiler_water=50.1,
        args=_adaptive_args(),
        app_dir=tmp_path,
    )
    app._rls.theta = [0.9, 0.1]
    app._rls.p = [[1e-12, 0.0], [0.0, 1e-12]]
    app._rls.y_prev = 50.0
    app._rls.last_u = 45.0
    app._rls_last_saved = copy_durable(app._rls)

    app.control_tick({})

    path = _rls_path(app)
    assert path.is_file()
    loaded = load_rls_state(path)
    assert loaded is not None
    assert durable_equal(loaded, copy_durable(app._rls))
    assert durable_equal(app._rls_last_saved, copy_durable(app._rls))
    assert app._rls_force_rewrite is False


def test_demand_no_rewrite_when_equal_and_not_forced(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = _tick_app(
        zone_temp=20.04,
        setpoint=22.0,
        plant_setpoint=42.0,
        boiler_water=50.0,
        args=_adaptive_args(),
        app_dir=tmp_path,
    )
    # Equal-float skip: command 42.0, last_u already 42 → snapshot can match.
    app._rls.last_u = 42.0
    app._rls_last_saved = copy_durable(app._rls)
    path = _rls_path(app)
    path.write_text("sentinel", encoding="utf-8")
    called = {"n": 0}

    def _count(*_a, **_k):
        called["n"] += 1
        return True

    monkeypatch.setattr("ha_smart_hvac.hvac_app.save_rls_state", _count)

    app.control_tick({})

    assert called["n"] == 0
    assert path.read_text(encoding="utf-8") == "sentinel"


def test_force_rewrite_after_corrupt_load(tmp_path: Path) -> None:
    path = tmp_path / STATE_FILENAME
    path.write_text("{bad", encoding="utf-8")
    app = _init_app(args=_adaptive_args(), app_dir=tmp_path)
    app.initialize()
    assert app._rls_force_rewrite is True

    # Demand tick with equal snapshot still rewrites when forced.
    app.get_state = MagicMock(
        side_effect=lambda entity_id, attribute=None: {
            _PLANT_MGMT: "on",
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
    app._rls.last_u = 42.0
    app._rls_last_saved = copy_durable(app._rls)

    app.control_tick({})

    assert path.is_file()
    assert load_rls_state(path) is not None
    assert app._rls_force_rewrite is False


def test_clear_paths_leave_file_and_latch(tmp_path: Path) -> None:
    path = tmp_path / STATE_FILENAME
    _write_valid_rls_json(path)
    prior = path.read_text(encoding="utf-8")

    zero_weight = _adaptive_args()
    zero_weight["zones"] = [
        {
            "name": _ZONE_NAME,
            "temperature": _ZONE_TEMP,
            "weight": 0.0,
            "thermostats": [_CLIMATE],
        }
    ]
    cases: list[dict] = [
        {"hvac_action": "idle"},
        {"plant_management": "off"},
        {"zone_temp": "unavailable"},
        {"args": zero_weight},
    ]

    for clear_kwargs in cases:
        tick_kwargs: dict = {
            "zone_temp": 20.0,
            "setpoint": 22.0,
            "plant_setpoint": 45.0,
            "boiler_water": 50.0,
            "args": _adaptive_args(),
            "app_dir": tmp_path,
        }
        tick_kwargs.update(clear_kwargs)
        app = _tick_app(**tick_kwargs)
        app._rls_fallback_latched = True
        app._rls_fallback_reason = "imc_none"
        app._rls.y_prev = 50.0
        app._integral = 3.0

        app.control_tick({})

        assert path.read_text(encoding="utf-8") == prior
        assert app._rls_fallback_latched is True
        assert app._rls.y_prev is None
        assert app._integral == 0.0


def test_persist_after_imc_reject_write_true(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Demand write True after IMC reject still persists dirty θ/P when dirty."""
    real_step = __import__("ha_smart_hvac.rls", fromlist=["rls_step"]).rls_step
    monkeypatch.setattr("ha_smart_hvac.hvac_app.imc_gains", lambda *_a, **_k: None)
    app = _tick_app(
        zone_temp=20.0,
        setpoint=22.0,
        plant_setpoint=45.0,
        boiler_water=50.1,
        args=_adaptive_args(),
        app_dir=tmp_path,
    )
    app._rls.theta = [0.9, 0.1]
    app._rls.p = [[1e-12, 0.0], [0.0, 1e-12]]
    app._rls.y_prev = 50.0
    app._rls.last_u = 45.0
    app._rls.adapted_kp = 2.0
    app._rls.adapted_ki = 0.5
    app._rls_last_saved = copy_durable(app._rls)
    preview = RlsState()
    preview.theta = app._rls.theta[:]
    preview.p = [row[:] for row in app._rls.p]
    assert real_step(preview, y=50.1, y_prev=50.0, u_prev=45.0) is True

    app.control_tick({})

    assert app._rls_fallback_latched is True
    assert _set_value_writes(app) == [42.0]
    path = _rls_path(app)
    assert path.is_file()
    loaded = load_rls_state(path)
    assert loaded is not None
    assert durable_equal(loaded, copy_durable(app._rls))
    assert loaded.theta[0] == pytest.approx(preview.theta[0])


def test_unsaved_dirty_lost_on_reload(tmp_path: Path) -> None:
    """Accepted loss: dirty RAM without a successful persist is gone on reload."""
    path = tmp_path / STATE_FILENAME
    _write_valid_rls_json(path, last_u=45.0, adapted_kp=1.5, adapted_ki=12.0)
    app = _init_app(args=_adaptive_args(), app_dir=tmp_path)
    app.initialize()
    app._rls.theta = [0.5, 0.5]
    app._rls.last_u = 99.0
    # No demand persist — simulate App stop with dirty RAM.
    app2 = _init_app(args=_adaptive_args(), app_dir=tmp_path)
    app2.initialize()
    assert app2._rls.theta == [0.9, 0.1]
    assert app2._rls.last_u == pytest.approx(45.0)
    assert app2._rls.adapted_kp == pytest.approx(1.5)


def test_adaptive_off_demand_does_not_save(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    called = {"n": 0}

    def _count(*_a, **_k):
        called["n"] += 1
        return True

    monkeypatch.setattr("ha_smart_hvac.hvac_app.save_rls_state", _count)
    app = _tick_app(
        zone_temp=20.0,
        setpoint=22.0,
        plant_setpoint=45.0,
        args=_tick_args(),
        app_dir=tmp_path,
    )
    app.control_tick({})
    assert called["n"] == 0
    assert not _rls_path(app).exists()


def test_persist_soft_fail_episode_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = _tick_app(
        zone_temp=20.0,
        setpoint=22.0,
        plant_setpoint=45.0,
        boiler_water=50.0,
        args=_adaptive_args(),
        app_dir=tmp_path,
    )
    app._rls.last_u = 99.0  # dirty vs cold last_saved
    monkeypatch.setattr(
        "ha_smart_hvac.hvac_app.save_rls_state", lambda *_a, **_k: False
    )

    app.control_tick({})
    warns1 = [m for m in _warn_msgs(app) if "Failed to persist RLS state" in m]
    assert len(warns1) == 1
    assert app._rls_force_rewrite is False
    assert app._rls_persist_fail_warned is True
    # Tick still wrote SWT.
    assert _set_value_writes(app) == [_expected_command(zone_temp=20.0, setpoint=22.0)]

    app.log.reset_mock()
    app.call_service.reset_mock()
    app.control_tick({})
    warns2 = [m for m in _warn_msgs(app) if "Failed to persist RLS state" in m]
    assert warns2 == []

    # Successful save ends episode; later fail re-WARNs.
    monkeypatch.setattr("ha_smart_hvac.hvac_app.save_rls_state", lambda *_a, **_k: True)
    app.control_tick({})
    assert app._rls_persist_fail_warned is False
    monkeypatch.setattr(
        "ha_smart_hvac.hvac_app.save_rls_state", lambda *_a, **_k: False
    )
    # Force dirty again after successful save updated last_saved.
    app._rls.adapted_kp = 3.0
    app._rls.adapted_ki = 4.0
    app.log.reset_mock()
    app.control_tick({})
    asserts = [m for m in _warn_msgs(app) if "Failed to persist RLS state" in m]
    assert len(asserts) == 1


def test_persist_soft_fail_keeps_force_and_last_saved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / STATE_FILENAME
    path.write_text("{bad", encoding="utf-8")
    app = _init_app(args=_adaptive_args(), app_dir=tmp_path)
    app.initialize()
    assert app._rls_force_rewrite is True

    app.get_state = MagicMock(
        side_effect=lambda entity_id, attribute=None: {
            _PLANT_MGMT: "on",
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
    app._rls.last_u = 42.0
    app._rls_last_saved = copy_durable(app._rls)
    pre_saved = copy_durable(app._rls_last_saved)
    calls = {"n": 0}

    def _fail(*_a, **_k):
        calls["n"] += 1
        return False

    monkeypatch.setattr("ha_smart_hvac.hvac_app.save_rls_state", _fail)

    app.control_tick({})
    assert calls["n"] == 1
    assert app._rls_force_rewrite is True
    assert durable_equal(app._rls_last_saved, pre_saved)
    assert any("Failed to persist RLS state" in m for m in _warn_msgs(app))

    app.log.reset_mock()
    app.call_service.reset_mock()
    app.control_tick({})
    assert calls["n"] == 2
    assert app._rls_force_rewrite is True
    assert durable_equal(app._rls_last_saved, pre_saved)


def test_persist_unsavable_warns_distinct_from_io(tmp_path: Path) -> None:
    app = _tick_app(
        zone_temp=20.0,
        setpoint=22.0,
        plant_setpoint=45.0,
        boiler_water=50.0,
        args=_adaptive_args(),
        app_dir=tmp_path,
    )
    app._rls.last_u = 99.0
    app._rls.theta = [float("nan"), 0.1]
    # Let real save_rls_state reject unsavable fields.
    app.control_tick({})
    unsavable = [m for m in _warn_msgs(app) if "unsavable" in m]
    io_fail = [m for m in _warn_msgs(app) if "Failed to persist RLS state" in m]
    assert len(unsavable) == 1
    assert io_fail == []
    assert app._rls_persist_fail_warned is True


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


def test_write_false_after_rls_does_not_persist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    stepped = {"n": 0}
    real_step = __import__("ha_smart_hvac.rls", fromlist=["rls_step"]).rls_step

    def _counting_step(state, **kwargs):
        stepped["n"] += 1
        return real_step(state, **kwargs)

    called = {"n": 0}

    def _count_save(*_a, **_k):
        called["n"] += 1
        return True

    monkeypatch.setattr("ha_smart_hvac.hvac_app.rls_step", _counting_step)
    monkeypatch.setattr("ha_smart_hvac.hvac_app.save_rls_state", _count_save)
    monkeypatch.setattr(HvacApp, "_write_setpoint", lambda *_a, **_k: False)
    app = _tick_app(
        zone_temp=20.0,
        setpoint=22.0,
        plant_setpoint=45.0,
        boiler_water=50.1,
        args=_adaptive_args(),
        app_dir=tmp_path,
    )
    app._rls.theta = [0.9, 0.1]
    app._rls.p = [[1e-12, 0.0], [0.0, 1e-12]]
    app._rls.y_prev = 50.0
    app._rls.last_u = 45.0

    app.control_tick({})

    assert stepped["n"] == 1
    assert called["n"] == 0
    assert not _rls_path(app).exists()


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
