"""Config parse smoke: weather-curve args without ladrc/tune keys."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
import yaml

from ha_smart_hvac.config import ConfigError, parse_config

ROOT = Path(__file__).resolve().parents[1]


def _minimal_args() -> dict:
    return {
        "outdoor_temperature": "sensor.outdoor",
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
        "weather_feedforward": {
            "base": 25,
            "slope": 1.2,
            "comfort_ref": 20,
        },
    }


def test_parse_config_without_ladrc_or_tune_keys() -> None:
    config = parse_config(_minimal_args())
    assert not hasattr(config, "ladrc")
    assert not hasattr(config, "tune_state_path")
    assert config.setpoint_min == 40.0
    assert config.setpoint_max == 55.0
    assert config.weather_feedforward.base == pytest.approx(25.0)
    assert config.weather_feedforward.slope == pytest.approx(1.2)
    assert config.weather_feedforward.comfort_ref == pytest.approx(20.0)
    assert len(config.zones) == 1
    assert config.zones[0].name == "living_room"


def test_parse_apps_yaml_example() -> None:
    """Real example file parses with no ladrc/tune fields."""
    raw = yaml.safe_load((ROOT / "apps.yaml.example").read_text())
    assert isinstance(raw, dict) and "hvac" in raw
    args = dict(raw["hvac"])
    args.pop("module", None)
    args.pop("class", None)
    assert "ladrc" not in args
    assert "tune_state_path" not in args
    config = parse_config(args)
    assert not hasattr(config, "ladrc")
    assert not hasattr(config, "tune_state_path")
    assert config.setpoint_min == 40.0
    assert config.weather_feedforward.base == pytest.approx(25.0)


def test_parse_rejects_setpoint_min_not_less_than_max() -> None:
    args = _minimal_args()
    args["setpoint_min"] = 55
    args["setpoint_max"] = 40
    with pytest.raises(ConfigError, match="setpoint_min must be less than"):
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
