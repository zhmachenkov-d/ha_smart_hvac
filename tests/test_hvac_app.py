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


def test_initialize_schedules_control_tick() -> None:
    app = object.__new__(HvacApp)
    app.args = _tick_args()
    app.log = MagicMock()
    app.run_every = MagicMock()

    with patch.object(HvacApp, "app_dir", new_callable=PropertyMock) as mock_dir:
        mock_dir.return_value = Path("/tmp")
        app.initialize()

    assert not hasattr(app, "_ladrc")
    assert not hasattr(app, "_tuner")
    assert not hasattr(app, "_blow_up_latch")
    assert not hasattr(app, "_blow_up_warned")
    app.run_every.assert_called_once()


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
    app = _tick_app(zone_temp=22.0, setpoint=22.0)

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

    app = _cap7_app(tmp_path, zone_temp=22.0, setpoint=22.0)
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


def test_cap7_initialize_overlays_valid_json(tmp_path: Path) -> None:
    from ha_smart_hvac.ff_auto_correct import STATE_FILENAME, save_ff_state

    save_ff_state(tmp_path / STATE_FILENAME, 30.0, 1.5)

    app = object.__new__(HvacApp)
    app.args = _tick_args()
    app.log = MagicMock()
    app.run_every = MagicMock()

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

    app = object.__new__(HvacApp)
    app.args = _tick_args()
    app.log = MagicMock()
    app.run_every = MagicMock()

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
