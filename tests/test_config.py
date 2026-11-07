"""Config parse smoke: PID commission args; no outdoor / weather feedforward."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
import yaml

from ha_smart_hvac.config import ConfigError, parse_config

ROOT = Path(__file__).resolve().parents[1]


def _minimal_args() -> dict:
    return {
        "plant_management": "switch.pm",
        "plant_setpoint": "number.setpoint",
        "setpoint_min": 40,
        "setpoint_max": 55,
        "zones": [
            {
                "name": "living_room",
                "temperature": "sensor.temp",
                "thermostats": ["climate.thermostat"],
            }
        ],
    }


def test_parse_config_without_ladrc_or_tune_keys() -> None:
    config = parse_config(_minimal_args())
    assert not hasattr(config, "ladrc")
    assert not hasattr(config, "tune_state_path")
    assert config.setpoint_min == 40.0
    assert config.setpoint_max == 55.0
    assert len(config.zones) == 1
    assert config.zones[0].name == "living_room"


def test_parse_omitted_pid_defaults() -> None:
    config = parse_config(_minimal_args())
    assert config.control_interval == 300
    assert config.base_water_temp == pytest.approx(40.0)
    assert config.pid.kp == pytest.approx(1.0)
    assert config.pid.ki == pytest.approx(0.1)
    assert config.pid.integral_min == pytest.approx(-50.0)
    assert config.pid.integral_max == pytest.approx(50.0)
    assert config.zones[0].weight == pytest.approx(1.0)


def test_parse_pid_and_weight_overrides() -> None:
    args = _minimal_args()
    args["control_interval"] = 120
    args["base_water_temp"] = 42
    args["pid"] = {
        "kp": 2.0,
        "ki": 0.2,
        "integral_min": -10,
        "integral_max": 10,
    }
    args["zones"][0]["weight"] = 3.0
    config = parse_config(args)
    assert config.control_interval == 120
    assert config.base_water_temp == pytest.approx(42.0)
    assert config.pid.kp == pytest.approx(2.0)
    assert config.pid.ki == pytest.approx(0.2)
    assert config.pid.integral_min == pytest.approx(-10.0)
    assert config.pid.integral_max == pytest.approx(10.0)
    assert config.zones[0].weight == pytest.approx(3.0)


def test_parse_apps_yaml_example() -> None:
    """Real example file parses with PID commission defaults."""
    raw = yaml.safe_load((ROOT / "apps.yaml.example").read_text())
    assert isinstance(raw, dict) and "hvac" in raw
    args = dict(raw["hvac"])
    args.pop("module", None)
    args.pop("class", None)
    assert "ladrc" not in args
    assert "tune_state_path" not in args
    assert "outdoor_temperature" not in args
    assert "weather_feedforward" not in args
    config = parse_config(args)
    assert not hasattr(config, "ladrc")
    assert not hasattr(config, "tune_state_path")
    assert config.setpoint_min == 40.0
    assert config.control_interval == 300
    assert config.base_water_temp == pytest.approx(40.0)
    assert config.pid.kp == pytest.approx(1.0)
    assert config.zones[0].weight == pytest.approx(1.0)


def test_parse_rejects_setpoint_min_not_less_than_max() -> None:
    args = _minimal_args()
    args["setpoint_min"] = 55
    args["setpoint_max"] = 40
    with pytest.raises(ConfigError, match="setpoint_min must be less than"):
        parse_config(args)


def test_parse_rejects_integral_min_not_less_than_max() -> None:
    args = _minimal_args()
    args["pid"] = {"integral_min": 10, "integral_max": -10}
    with pytest.raises(ConfigError, match="integral_min must be less than"):
        parse_config(args)


def test_parse_rejects_negative_zone_weight() -> None:
    args = _minimal_args()
    args["zones"][0]["weight"] = -1
    with pytest.raises(ConfigError, match="weight must be >= 0"):
        parse_config(args)


def test_parse_rejects_non_numeric_zone_weight() -> None:
    args = _minimal_args()
    args["zones"][0]["weight"] = None
    with pytest.raises(ConfigError, match="weight must be a number"):
        parse_config(args)


@pytest.mark.parametrize("module", ["ha_smart_hvac.ladrc", "ha_smart_hvac.ladrc_tuner"])
def test_ladrc_modules_absent(module: str) -> None:
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module(module)


def test_critical_zone_swt_driver_symbols_absent() -> None:
    """Matrix: no select_critical_zone / ControlDecision on the package surface."""
    import ha_smart_hvac.coordinator as coordinator
    import ha_smart_hvac.models as models

    assert not hasattr(coordinator, "select_critical_zone")
    assert not hasattr(models, "ControlDecision")


@pytest.mark.parametrize(
    "module", ["ha_smart_hvac.feedforward", "ha_smart_hvac.ff_auto_correct"]
)
def test_weather_feedforward_modules_absent(module: str) -> None:
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module(module)


def test_config_has_no_outdoor_or_feedforward_fields() -> None:
    import ha_smart_hvac.models as models

    config = parse_config(_minimal_args())
    assert not hasattr(config, "outdoor_temperature")
    assert not hasattr(config, "weather_feedforward")
    assert not hasattr(config, "auto_correct")
    assert not hasattr(models, "WeatherFeedforwardConfig")
    assert not hasattr(models, "AutoCorrectConfig")


def test_legacy_outdoor_and_feedforward_keys_ignored() -> None:
    """Stale commissioning keys parse as unknown args, not as control inputs."""
    args = _minimal_args()
    args["outdoor_temperature"] = "sensor.outdoor"
    args["weather_feedforward"] = {
        "base": 25,
        "slope": 1.2,
        "comfort_ref": 20,
        "auto_correct": {"e_sat_c_per_h": 0},
    }
    config = parse_config(args)
    assert not hasattr(config, "outdoor_temperature")
    assert not hasattr(config, "weather_feedforward")
