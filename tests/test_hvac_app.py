"""Tests for weather-curve Set Water Temperature control_tick (CAP-5)."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from ha_smart_hvac.config import parse_config
from ha_smart_hvac.feedforward import weather_feedforward
from ha_smart_hvac.hvac_app import HvacApp

_SETPOINT_MIN = 40.0
_SETPOINT_MAX = 55.0
_CONTROL_INTERVAL = 60

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


def _expected_ff_clamp(config, outdoor: float) -> float:
    u_ff = weather_feedforward(outdoor, config.weather_feedforward)
    return max(config.setpoint_min, min(config.setpoint_max, u_ff))


def _set_value_writes(app: HvacApp) -> list[float]:
    return [
        c.kwargs["value"]
        for c in app.call_service.call_args_list
        if c.args and c.args[0] == "number/set_value"
    ]


def _init_app(args: dict | None = None) -> HvacApp:
    """Hass-stubbed app ready for initialize() (run_every + listen_state)."""
    app = object.__new__(HvacApp)
    app.args = args if args is not None else _tick_args()
    app.log = MagicMock()
    app.run_every = MagicMock()
    app.listen_state = MagicMock()
    return app


def test_initialize_schedules_control_tick() -> None:
    app = _init_app()

    with patch.object(HvacApp, "app_dir", new_callable=PropertyMock) as mock_dir:
        mock_dir.return_value = Path("/tmp")
        app.initialize()

    assert not hasattr(app, "_ladrc")
    assert not hasattr(app, "_tuner")
    assert not hasattr(app, "_blow_up_latch")
    assert not hasattr(app, "_blow_up_warned")
    app.run_every.assert_called_once()
    assert app.run_every.call_args.args[0].__func__ is HvacApp.control_tick


def test_cap5_demand_writes_clamp_uff_only() -> None:
    """CAP-5(a): demand → clamp(u_ff) only; no water-path LADRC attrs."""
    outdoor = 10.0
    app = _tick_app(
        zone_temp=20.0,
        setpoint=22.0,
        outdoor=outdoor,
        plant_setpoint=45.0,
    )
    expected = _expected_ff_clamp(app._config, outdoor)

    app.control_tick({})

    assert _set_value_writes(app) == [expected]
    assert not hasattr(app, "_ladrc")
    assert not hasattr(app, "_tuner")
    assert not hasattr(app, "_blow_up_latch")
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


def test_cap5_heating_at_setpoint_still_writes_clamp_uff() -> None:
    """Heating Demand follows hvac_action: error ≤ 0 still takes demand path."""
    outdoor = 10.0
    app = _tick_app(
        zone_temp=22.0,
        setpoint=22.0,
        outdoor=outdoor,
        plant_setpoint=45.0,
        hvac_action="heating",
    )
    expected = _expected_ff_clamp(app._config, outdoor)

    app.control_tick({})

    assert _set_value_writes(app) == [expected]


def test_demand_fail_write_aborts_without_success_info() -> None:
    """Demand + unreadable plant setpoint: no set_value, no command= INFO."""
    app = _tick_app(
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


def test_cap5_plant_on_idle_writes_zero() -> None:
    """CAP-5(b): Plant-on idle → write 0; no water-path LADRC attrs."""
    app = _tick_app(zone_temp=22.0, setpoint=22.0, hvac_action="idle")

    app.control_tick({})

    assert _set_value_writes(app) == [0.0]
    assert not hasattr(app, "_ladrc")
    assert not hasattr(app, "_tuner")
    assert not hasattr(app, "_blow_up_latch")


def test_cap5_plant_off_no_write() -> None:
    """CAP-5(c): Plant-off → no Set Water Temperature write."""
    app = _tick_app(plant_management="off")

    app.control_tick({})

    assert _set_value_writes(app) == []
    app.call_service.assert_not_called()
    assert not hasattr(app, "_ladrc")
    assert not hasattr(app, "_tuner")
    assert not hasattr(app, "_blow_up_latch")


def test_cap5_flat_air_multi_tick_stays_at_ff_clamp() -> None:
    """CAP-5(d): flat near-setpoint air never climbs to max via tracking."""
    outdoor = 10.0
    app = _tick_app(
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
        assert writes[0] < app._config.setpoint_max


def test_cap5_max_error_zone_air_not_additive_on_swt() -> None:
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
    assert not hasattr(app, "_ladrc")
    assert not hasattr(app, "_tuner")


def test_matrix_outdoor_missing_goes_idle() -> None:
    """I/O matrix: outdoor unavailable → _go_idle write 0."""
    app = _tick_app(outdoor="unavailable")

    app.control_tick({})

    assert _set_value_writes(app) == [0.0]


def test_matrix_no_valid_zones_goes_idle() -> None:
    """I/O matrix: no valid zones → _go_idle write 0."""
    app = _tick_app(zone_temp="unavailable")

    app.control_tick({})

    assert _set_value_writes(app) == [0.0]


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
    [None, "unavailable", "unknown", "not-a-float", object()],
)
def test_write_setpoint_fail_closed_when_entity_unreadable(raw_state):
    app = _write_stub(raw_state)

    ok = HvacApp._write_setpoint(app, 42.0)

    assert ok is False
    app.call_service.assert_not_called()


# --- CAP-7 rise-rate auto-correct (Hass) ---


def _cap7_app(tmp_path: Path, **kwargs) -> HvacApp:
    """Tick app with corrector + app_dir under tmp_path for JSON isolation."""
    from ha_smart_hvac.ff_auto_correct import STATE_FILENAME

    app = _tick_app(**kwargs)
    app._ff_auto_correct = app._build_corrector()
    app._state_path = lambda: tmp_path / STATE_FILENAME  # type: ignore[method-assign]
    return app


def test_cap7_plant_off_clears_ephemeral_json_untouched(tmp_path: Path) -> None:
    from ha_smart_hvac.ff_auto_correct import STATE_FILENAME, save_ff_state

    state = tmp_path / STATE_FILENAME
    save_ff_state(state, 30.0, 1.5)
    before = state.read_text()

    app = _cap7_app(tmp_path, plant_management="off")
    app._ff_auto_correct._steady = 5
    app._ff_auto_correct._selected_zone_id = "zone_one"

    app.control_tick({})

    assert _set_value_writes(app) == []
    assert app._ff_auto_correct._steady == 0
    assert app._ff_auto_correct._selected_zone_id is None
    assert state.read_text() == before


def test_cap7_no_demand_clears_ephemeral_json_untouched(tmp_path: Path) -> None:
    from ha_smart_hvac.ff_auto_correct import STATE_FILENAME, save_ff_state

    state = tmp_path / STATE_FILENAME
    save_ff_state(state, 30.0, 1.5)
    before = state.read_text()

    app = _cap7_app(tmp_path, zone_temp=22.0, setpoint=22.0, hvac_action="idle")
    app._ff_auto_correct._steady = 5

    app.control_tick({})

    assert _set_value_writes(app) == [0.0]
    assert app._ff_auto_correct._steady == 0
    assert state.read_text() == before


def test_cap7_idle_outdoor_missing_clears_ephemeral_json_untouched(
    tmp_path: Path,
) -> None:
    from ha_smart_hvac.ff_auto_correct import STATE_FILENAME, save_ff_state

    state = tmp_path / STATE_FILENAME
    save_ff_state(state, 30.0, 1.5)
    before = state.read_text()

    app = _cap7_app(tmp_path, outdoor="unavailable")
    app._ff_auto_correct._steady = 3

    app.control_tick({})

    assert _set_value_writes(app) == [0.0]
    assert app._ff_auto_correct._steady == 0
    assert state.read_text() == before


def test_cap7_empty_zones_clears_ephemeral_json_untouched(tmp_path: Path) -> None:
    from ha_smart_hvac.ff_auto_correct import STATE_FILENAME, save_ff_state

    state = tmp_path / STATE_FILENAME
    save_ff_state(state, 30.0, 1.5)
    before = state.read_text()

    app = _cap7_app(tmp_path, zone_temp="unavailable")
    app._ff_auto_correct._steady = 4
    app._ff_auto_correct._selected_zone_id = "zone_one"

    app.control_tick({})

    assert _set_value_writes(app) == [0.0]
    assert app._ff_auto_correct._steady == 0
    assert app._ff_auto_correct._selected_zone_id is None
    assert state.read_text() == before


def test_cap7_write_fail_keeps_in_memory_no_json(tmp_path: Path) -> None:
    """2C: SWT write fail → keep in-memory nudge, no JSON."""
    from ha_smart_hvac.ff_auto_correct import STATE_FILENAME, WINDOW_SIZE

    outdoor = 18.0
    app = _cap7_app(
        tmp_path,
        zone_temp=20.0,
        setpoint=22.0,
        outdoor=outdoor,
        plant_setpoint=45.0,
    )
    for _ in range(WINDOW_SIZE - 1):
        app.control_tick({})
        app.call_service.reset_mock()

    base_before = app._ff_auto_correct.base
    original = app.get_state.side_effect

    def get_state_fail_plant(entity_id: str, attribute: str | None = None):
        if entity_id == _PLANT_SETPOINT:
            return "unavailable"
        return original(entity_id, attribute)

    app.get_state = MagicMock(side_effect=get_state_fail_plant)
    app.control_tick({})

    assert app._ff_auto_correct.base == pytest.approx(base_before + 0.1)
    assert not (tmp_path / STATE_FILENAME).exists()
    assert _set_value_writes(app) == []


def test_cap7_persist_fail_still_logs_command(tmp_path: Path, monkeypatch) -> None:
    """Persist OSError after SWT write: tick still logs; in-memory nudge kept."""
    from ha_smart_hvac.ff_auto_correct import WINDOW_SIZE

    outdoor = 18.0
    app = _cap7_app(
        tmp_path,
        zone_temp=20.0,
        setpoint=22.0,
        outdoor=outdoor,
        plant_setpoint=45.0,
    )
    for _ in range(WINDOW_SIZE - 1):
        app.control_tick({})
        app.call_service.reset_mock()
        app.log.reset_mock()

    monkeypatch.setattr(
        "ha_smart_hvac.hvac_app.save_ff_state",
        lambda *args, **kwargs: False,
    )
    base_before = app._ff_auto_correct.base
    app.control_tick({})

    assert app._ff_auto_correct.base == pytest.approx(base_before + 0.1)
    assert _set_value_writes(app)
    warn = [
        c
        for c in app.log.call_args_list
        if c.kwargs.get("level") == "WARNING"
        and "Failed to persist FF auto-correct state" in c.args[0]
    ]
    assert warn
    info = [
        c.args[0] for c in app.log.call_args_list if c.args and "command=" in c.args[0]
    ]
    assert info


def test_cap7_adapt_swt_equals_clamp_uff_not_additive(tmp_path: Path) -> None:
    """CAP-7: after adapt, SWT is clamp(u_ff) from post-nudge params only."""
    from ha_smart_hvac.feedforward import weather_feedforward
    from ha_smart_hvac.ff_auto_correct import STATE_FILENAME, WINDOW_SIZE, load_ff_state
    from ha_smart_hvac.models import WeatherFeedforwardConfig

    outdoor = 0.0  # far → slope knob
    app = _cap7_app(
        tmp_path,
        zone_temp=20.0,
        setpoint=22.0,
        outdoor=outdoor,
        plant_setpoint=45.0,
    )
    for _ in range(WINDOW_SIZE - 1):
        app.control_tick({})
        app.call_service.reset_mock()

    slope_before = app._ff_auto_correct.slope
    app.control_tick({})

    assert app._ff_auto_correct.slope != pytest.approx(slope_before)
    expected = max(
        app._config.setpoint_min,
        min(
            app._config.setpoint_max,
            weather_feedforward(
                outdoor,
                WeatherFeedforwardConfig(
                    base=app._ff_auto_correct.base,
                    slope=app._ff_auto_correct.slope,
                    comfort_ref=app._config.weather_feedforward.comfort_ref,
                ),
            ),
        ),
    )
    assert _set_value_writes(app) == [expected]
    yaml_slope = app._config.weather_feedforward.slope
    assert app._ff_auto_correct.slope != pytest.approx(yaml_slope)
    assert expected != pytest.approx(_expected_ff_clamp(app._config, outdoor))
    # Happy adapt 2C: JSON written only when params changed and SWT write ok
    loaded = load_ff_state(tmp_path / STATE_FILENAME)
    assert loaded == (app._ff_auto_correct.base, app._ff_auto_correct.slope)


def test_cap7_d_cmd_blocks_raise_at_max_no_json(tmp_path: Path) -> None:
    """D-cmd: raise blocked at setpoint_max → no mutate, no JSON."""
    from ha_smart_hvac.ff_auto_correct import STATE_FILENAME, WINDOW_SIZE

    # base high enough that u_ff sits at max for mild outdoor
    app = _cap7_app(
        tmp_path,
        zone_temp=20.0,
        setpoint=22.0,
        outdoor=20.0,
        plant_setpoint=55.0,
    )
    app._ff_auto_correct.base = 55.0
    app._ff_auto_correct.slope = 1.0
    for _ in range(WINDOW_SIZE):
        app.control_tick({})
        app.call_service.reset_mock()

    assert app._ff_auto_correct.base == pytest.approx(55.0)
    assert not (tmp_path / STATE_FILENAME).exists()


def test_cap7_d_cmd_blocks_lower_at_min_no_json(tmp_path: Path) -> None:
    """D-cmd: lower blocked at setpoint_min → no mutate, no JSON."""
    from ha_smart_hvac.ff_auto_correct import STATE_FILENAME, WINDOW_SIZE

    # base at min so u_ff = base at outdoor=comfort_ref; fast rise wants −base
    outdoor = 20.0
    temps = [20.0 + (0.1 * i / (WINDOW_SIZE - 1)) for i in range(WINDOW_SIZE)]
    zone_temp = {"t": temps[0]}
    app = _cap7_app(
        tmp_path,
        zone_temp=temps[0],
        setpoint=22.0,
        outdoor=outdoor,
        plant_setpoint=_SETPOINT_MIN,
    )
    app._ff_auto_correct.base = _SETPOINT_MIN
    app._ff_auto_correct.slope = 1.0

    def get_state(entity_id: str, attribute: str | None = None):
        if entity_id == _PLANT_MGMT:
            return "on"
        if entity_id == _OUTDOOR:
            return outdoor
        if entity_id == _ZONE_TEMP:
            return zone_temp["t"]
        if entity_id == _PLANT_SETPOINT:
            return _SETPOINT_MIN
        if entity_id == _CLIMATE:
            if attribute == "temperature":
                return 22.0
            if attribute == "hvac_action":
                return "heating"
            return "heat"
        return None

    app.get_state = MagicMock(side_effect=get_state)
    base0 = app._ff_auto_correct.base
    for temp in temps:
        zone_temp["t"] = temp
        app.control_tick({})
        app.call_service.reset_mock()

    assert app._ff_auto_correct.base == pytest.approx(base0)
    assert not (tmp_path / STATE_FILENAME).exists()


def test_cap7_initialize_overlays_valid_json(tmp_path: Path) -> None:
    from ha_smart_hvac.ff_auto_correct import STATE_FILENAME, save_ff_state

    save_ff_state(tmp_path / STATE_FILENAME, 30.0, 1.5)

    app = _init_app(args=_tick_args())

    with patch.object(HvacApp, "app_dir", new_callable=PropertyMock) as mock_dir:
        mock_dir.return_value = tmp_path
        app.initialize()

    assert app._ff_auto_correct.base == pytest.approx(30.0)
    assert app._ff_auto_correct.slope == pytest.approx(1.5)
    assert app._ff_auto_correct._previous is None
    assert app._ff_auto_correct._steady == 0


def test_cap7_initialize_corrupt_json_keeps_yaml(tmp_path: Path) -> None:
    from ha_smart_hvac.ff_auto_correct import STATE_FILENAME

    (tmp_path / STATE_FILENAME).write_text("{not json")

    app = _init_app(args=_tick_args())

    with patch.object(HvacApp, "app_dir", new_callable=PropertyMock) as mock_dir:
        mock_dir.return_value = tmp_path
        app.initialize()

    ff = app._config.weather_feedforward
    assert app._ff_auto_correct.base == pytest.approx(ff.base)
    assert app._ff_auto_correct.slope == pytest.approx(ff.slope)
    app.log.assert_any_call(
        f"Ignoring invalid FF auto-correct state: {tmp_path / STATE_FILENAME}",
        level="WARNING",
    )


# --- CAP-8 event-driven gate re-evaluation ---


def _fire_control_event(app: HvacApp) -> None:
    """Invoke control_event with dummy listen_state callback args (stub-only)."""
    app.control_event(_PLANT_MGMT, "state", None, "on", {})


def _ephemeral_snapshot(corrector) -> tuple[list[float], int, object]:
    return (list(corrector._window), corrector._steady, corrector._previous)


def test_cap8_initialize_registers_listeners() -> None:
    """CAP-8: listen_state for plant/outdoor/zone air/climate attrs; run_every."""
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

    with patch.object(HvacApp, "app_dir", new_callable=PropertyMock) as mock_dir:
        mock_dir.return_value = Path("/tmp")
        app.initialize()

    app.run_every.assert_called_once()
    assert app.run_every.call_args.args[0].__func__ is HvacApp.control_tick

    listens = app.listen_state.call_args_list
    # (callback, entity) or (callback, entity, attribute=...)
    entity_only = {
        c.args[1] for c in listens if len(c.args) >= 2 and not c.kwargs.get("attribute")
    }
    attr_listens = {
        (c.args[1], c.kwargs["attribute"]) for c in listens if c.kwargs.get("attribute")
    }
    assert entity_only == {_PLANT_MGMT, _OUTDOOR, _ZONE_TEMP, zone_two_temp}
    assert attr_listens == {
        (_CLIMATE, "hvac_action"),
        (_CLIMATE, "temperature"),
        (climate_two, "hvac_action"),
        (climate_two, "temperature"),
    }
    assert all(c.args[0].__func__ is HvacApp.control_event for c in listens)


def test_cap8_demand_writes_clamp_uff_no_process_demand(tmp_path: Path) -> None:
    """CAP-8 demand: clamp_uff write; process_demand not called."""
    outdoor = 10.0
    app = _cap7_app(
        tmp_path,
        zone_temp=20.0,
        setpoint=22.0,
        outdoor=outdoor,
        plant_setpoint=45.0,
    )
    expected = app._ff_auto_correct.clamp_uff(outdoor)

    with patch.object(
        app._ff_auto_correct,
        "process_demand",
        wraps=app._ff_auto_correct.process_demand,
    ) as mock_pd:
        _fire_control_event(app)
        mock_pd.assert_not_called()

    assert _set_value_writes(app) == [expected]


def test_cap8_outdoor_flip_writes_new_clamp(tmp_path: Path) -> None:
    """CAP-8 outdoor flip: new clamp_uff; CAP-7 untouched; no process_demand."""
    outdoor = {"t": 10.0}
    app = _cap7_app(
        tmp_path,
        zone_temp=20.0,
        setpoint=22.0,
        outdoor=10.0,
        plant_setpoint=45.0,
    )
    original = app.get_state.side_effect

    def get_state(entity_id: str, attribute: str | None = None):
        if entity_id == _OUTDOOR:
            return outdoor["t"]
        return original(entity_id, attribute)

    app.get_state = MagicMock(side_effect=get_state)
    corrector = app._ff_auto_correct
    corrector._window.extend([20.0, 20.1, 20.2])
    corrector._steady = 3
    corrector._previous = "base"
    before = _ephemeral_snapshot(corrector)
    clamp_before = corrector.clamp_uff(outdoor["t"])

    outdoor["t"] = 0.0
    expected = corrector.clamp_uff(outdoor["t"])
    assert expected != pytest.approx(clamp_before)

    with patch.object(
        corrector, "process_demand", wraps=corrector.process_demand
    ) as mock_pd:
        _fire_control_event(app)
        mock_pd.assert_not_called()

    assert _set_value_writes(app) == [expected]
    assert _ephemeral_snapshot(corrector) == before


def test_cap8_plant_off_no_write_clears_ephemeral(tmp_path: Path) -> None:
    """CAP-8 plant off: no setpoint write; ephemeral cleared."""
    app = _cap7_app(tmp_path, plant_management="off")
    app._ff_auto_correct._steady = 5
    app._ff_auto_correct._selected_zone_id = "zone_one"

    _fire_control_event(app)

    assert _set_value_writes(app) == []
    app.call_service.assert_not_called()
    assert app._ff_auto_correct._steady == 0
    assert app._ff_auto_correct._selected_zone_id is None


def test_cap8_idle_writes_zero_json_untouched(tmp_path: Path) -> None:
    """CAP-8 idle: write 0; ephemeral cleared; FF JSON untouched."""
    from ha_smart_hvac.ff_auto_correct import STATE_FILENAME, save_ff_state

    state = tmp_path / STATE_FILENAME
    save_ff_state(state, 30.0, 1.5)
    before = state.read_text()

    app = _cap7_app(tmp_path, zone_temp=22.0, setpoint=22.0, hvac_action="idle")
    app._ff_auto_correct._steady = 5

    _fire_control_event(app)

    assert _set_value_writes(app) == [0.0]
    assert app._ff_auto_correct._steady == 0
    assert state.read_text() == before


def test_cap8_outdoor_missing_writes_zero_clears(tmp_path: Path) -> None:
    """CAP-8 outdoor missing: write 0; ephemeral cleared; JSON untouched."""
    from ha_smart_hvac.ff_auto_correct import STATE_FILENAME, save_ff_state

    state = tmp_path / STATE_FILENAME
    save_ff_state(state, 30.0, 1.5)
    before = state.read_text()

    app = _cap7_app(tmp_path, outdoor="unavailable")
    app._ff_auto_correct._steady = 3

    _fire_control_event(app)

    assert _set_value_writes(app) == [0.0]
    assert app._ff_auto_correct._steady == 0
    assert state.read_text() == before


def test_cap8_no_valid_zones_writes_zero_clears(tmp_path: Path) -> None:
    """CAP-8 no valid zones: write 0; ephemeral cleared; JSON untouched."""
    from ha_smart_hvac.ff_auto_correct import STATE_FILENAME, save_ff_state

    state = tmp_path / STATE_FILENAME
    save_ff_state(state, 30.0, 1.5)
    before = state.read_text()

    app = _cap7_app(tmp_path, zone_temp="unavailable")
    app._ff_auto_correct._steady = 4
    app._ff_auto_correct._selected_zone_id = "zone_one"

    _fire_control_event(app)

    assert _set_value_writes(app) == [0.0]
    assert app._ff_auto_correct._steady == 0
    assert app._ff_auto_correct._selected_zone_id is None
    assert state.read_text() == before


def test_cap8_demand_does_not_advance_cap7_or_persist(tmp_path: Path) -> None:
    """CAP-8 demand: window/steady/previous unchanged; no FF persist from event."""
    from ha_smart_hvac.ff_auto_correct import STATE_FILENAME, save_ff_state

    state = tmp_path / STATE_FILENAME
    save_ff_state(state, 30.0, 1.5)
    before_json = state.read_text()

    outdoor = 10.0
    app = _cap7_app(
        tmp_path,
        zone_temp=20.0,
        setpoint=22.0,
        outdoor=outdoor,
        plant_setpoint=45.0,
    )
    corrector = app._ff_auto_correct
    corrector._window.extend([19.5, 19.6, 19.7])
    corrector._steady = 7
    corrector._previous = "slope"
    corrector._selected_zone_id = "zone_one"
    before = _ephemeral_snapshot(corrector)
    selected_before = corrector._selected_zone_id

    with patch(
        "ha_smart_hvac.hvac_app.save_ff_state", wraps=save_ff_state
    ) as mock_save:
        _fire_control_event(app)
        mock_save.assert_not_called()

    assert _ephemeral_snapshot(corrector) == before
    assert corrector._selected_zone_id == selected_before
    assert state.read_text() == before_json
    assert _set_value_writes(app) == [corrector.clamp_uff(outdoor)]


def test_cap8_seed_event_then_tick_advances_cap7(tmp_path: Path) -> None:
    """Seeded window → CAP-8 event (unchanged) → control_tick advances CAP-7."""
    outdoor = 10.0
    app = _cap7_app(
        tmp_path,
        zone_temp=20.0,
        setpoint=22.0,
        outdoor=outdoor,
        plant_setpoint=45.0,
    )
    corrector = app._ff_auto_correct
    corrector._window.extend([19.5, 19.6, 19.7])
    corrector._steady = 7
    corrector._previous = "base"
    corrector._selected_zone_id = "zone_one"
    before = _ephemeral_snapshot(corrector)

    _fire_control_event(app)
    assert _ephemeral_snapshot(corrector) == before

    app.call_service.reset_mock()
    app.control_tick({})

    assert corrector._steady == before[1] + 1
    assert len(corrector._window) == len(before[0]) + 1
    assert _set_value_writes(app)  # tick still writes on demand


def test_cap8_equal_setpoint_skips_set_value(tmp_path: Path) -> None:
    """CAP-8 equality skip: evaluation runs; no number/set_value when float equal."""
    outdoor = 10.0
    expected = _expected_ff_clamp(parse_config(_tick_args()), outdoor)
    app = _cap7_app(
        tmp_path,
        zone_temp=20.0,
        setpoint=22.0,
        outdoor=outdoor,
        plant_setpoint=expected,
    )
    assert app._ff_auto_correct.clamp_uff(outdoor) == pytest.approx(expected)

    _fire_control_event(app)

    assert _set_value_writes(app) == []
    app.call_service.assert_not_called()
    # Evaluation completed: demand path logged command=
    info_msgs = [
        str(c.args[0])
        for c in app.log.call_args_list
        if c.args and (c.kwargs.get("level") is None or c.kwargs.get("level") == "INFO")
    ]
    assert any("command=" in m for m in info_msgs)


def test_cap8_periodic_still_runs_process_demand(tmp_path: Path) -> None:
    """After listeners exist, control_tick on demand still runs process_demand."""
    outdoor = 10.0
    app = _cap7_app(
        tmp_path,
        zone_temp=20.0,
        setpoint=22.0,
        outdoor=outdoor,
        plant_setpoint=45.0,
    )

    with patch.object(
        app._ff_auto_correct,
        "process_demand",
        wraps=app._ff_auto_correct.process_demand,
    ) as mock_pd:
        app.control_tick({})
        mock_pd.assert_called_once()

    assert _set_value_writes(app) == [app._ff_auto_correct.clamp_uff(outdoor)]
