"""Config parse smoke: PID commission args; no outdoor / weather feedforward."""

from __future__ import annotations

import importlib
import math
from dataclasses import replace
from pathlib import Path

import pytest
import yaml

from ha_smart_hvac.config import _APPDAEMON_KEYS, ConfigError, parse_config
from ha_smart_hvac.models import PidConfig

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
    assert config.pid.ki == pytest.approx(1.0)
    assert config.pid.i_term_min == pytest.approx(-10.0)
    assert config.pid.i_term_max == pytest.approx(15.0)
    assert config.zones[0].weight == pytest.approx(1.0)


def test_parse_pid_and_weight_overrides() -> None:
    args = _minimal_args()
    args["control_interval"] = 120
    args["base_water_temp"] = 42
    args["pid"] = {
        "kp": 2.0,
        "ki": 0.2,
        "i_term_min": -5,
        "i_term_max": 10,
    }
    args["zones"][0]["weight"] = 3.0
    config = parse_config(args)
    assert config.control_interval == 120
    assert config.base_water_temp == pytest.approx(42.0)
    assert config.pid.kp == pytest.approx(2.0)
    assert config.pid.ki == pytest.approx(0.2)
    assert config.pid.i_term_min == pytest.approx(-5.0)
    assert config.pid.i_term_max == pytest.approx(10.0)
    assert config.zones[0].weight == pytest.approx(3.0)


def test_parse_apps_yaml_example() -> None:
    """Real example file parses with PID commission defaults."""
    raw = yaml.safe_load((ROOT / "apps.yaml.example").read_text())
    assert isinstance(raw, dict) and "hvac" in raw
    args = dict(raw["hvac"])
    assert args["module"] == "ha_smart_hvac"
    assert args["class"] == "HvacApp"
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
    assert config.pid == PidConfig(kp=1.0, ki=1.0, i_term_min=-10.0, i_term_max=15.0)
    assert config.zones[0].weight == pytest.approx(1.0)
    assert config.ignored_keys == ()


def test_parse_rejects_setpoint_min_not_less_than_max() -> None:
    args = _minimal_args()
    args["setpoint_min"] = 55
    args["setpoint_max"] = 40
    with pytest.raises(ConfigError, match="setpoint_min must be less than"):
        parse_config(args)


def test_parse_rejects_i_term_min_not_less_than_max() -> None:
    args = _minimal_args()
    args["pid"] = {"i_term_min": 10, "i_term_max": -10}
    with pytest.raises(ConfigError, match="i_term_min must be less than i_term_max"):
        parse_config(args)


def test_parse_ignores_legacy_integral_keys() -> None:
    """Old integral_min / integral_max (∫ units) no longer affect parsed config."""
    args = _minimal_args()
    args["pid"] = {"integral_min": 10, "integral_max": -10}
    config = parse_config(args)
    assert config.pid == PidConfig()
    assert config.ignored_keys == ("pid.integral_max", "pid.integral_min")
    assert replace(config, ignored_keys=()) == parse_config(_minimal_args())


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
    assert config.ignored_keys == ("outdoor_temperature", "weather_feedforward")
    assert replace(config, ignored_keys=()) == parse_config(_minimal_args())


# --- C5 commission parse hardening (story 1.7) -------------------------------

_TOP_NUMERIC_KEYS = [
    "setpoint_min",
    "setpoint_max",
    "control_interval",
    "base_water_temp",
]
_PID_NUMERIC_KEYS = ["kp", "ki", "i_term_min", "i_term_max"]


def _with_value(key: str, value: object) -> dict:
    args = _minimal_args()
    if key.startswith("pid."):
        args["pid"] = {key.removeprefix("pid."): value}
    else:
        args[key] = value
    return args


_ALL_NUMERIC_KEYS = _TOP_NUMERIC_KEYS + [f"pid.{k}" for k in _PID_NUMERIC_KEYS]


@pytest.mark.parametrize("key", _ALL_NUMERIC_KEYS)
@pytest.mark.parametrize("value", ["abc", None, [1], True])
def test_parse_rejects_non_numeric(key: str, value: object) -> None:
    with pytest.raises(ConfigError, match=rf"^{key} must be a number$"):
        parse_config(_with_value(key, value))


@pytest.mark.parametrize("key", _ALL_NUMERIC_KEYS)
@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf, "nan", "inf"])
def test_parse_rejects_non_finite(key: str, value: object) -> None:
    with pytest.raises(ConfigError, match=rf"^{key} must be finite$"):
        parse_config(_with_value(key, value))


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_parse_rejects_non_finite_zone_weight(value: float) -> None:
    args = _minimal_args()
    args["zones"][0]["weight"] = value
    with pytest.raises(ConfigError, match="Zone 'living_room': weight must be finite"):
        parse_config(args)


@pytest.mark.parametrize("key", _ALL_NUMERIC_KEYS)
def test_parse_rejects_overflow(key: str) -> None:
    with pytest.raises(ConfigError, match=rf"^{key} must be finite$"):
        parse_config(_with_value(key, 10**400))


def test_parse_rejects_overflow_zone_weight() -> None:
    args = _minimal_args()
    args["zones"][0]["weight"] = 10**400
    with pytest.raises(ConfigError, match="weight must be finite"):
        parse_config(args)


@pytest.mark.parametrize(("key", "value"), [("kp", -1), ("ki", -0.1)])
def test_parse_rejects_negative_gain(key: str, value: float) -> None:
    args = _minimal_args()
    args["pid"] = {key: value}
    with pytest.raises(ConfigError, match=rf"pid\.{key} must be >= 0"):
        parse_config(args)


def test_parse_accepts_zero_gains() -> None:
    args = _minimal_args()
    args["pid"] = {"kp": 0, "ki": 0}
    config = parse_config(args)
    assert config.pid.kp == 0.0
    assert config.pid.ki == 0.0


@pytest.mark.parametrize("value", [60.7, 0.5])
def test_parse_rejects_fractional_control_interval(value: float) -> None:
    args = _minimal_args()
    args["control_interval"] = value
    with pytest.raises(
        ConfigError, match="control_interval must be a whole number of seconds"
    ):
        parse_config(args)


@pytest.mark.parametrize("value", [60.0, "60", " 60 ", "6_0", 60])
def test_parse_accepts_whole_control_interval(value: object) -> None:
    args = _minimal_args()
    args["control_interval"] = value
    config = parse_config(args)
    assert config.control_interval == 60
    assert isinstance(config.control_interval, int)


def test_parse_accepts_yaml_sexagesimal_control_interval() -> None:
    args = _minimal_args()
    args["control_interval"] = yaml.safe_load("v: 1:00")["v"]
    assert parse_config(args).control_interval == 60


@pytest.mark.parametrize("value", [0, -60])
def test_parse_rejects_non_positive_control_interval(value: int) -> None:
    args = _minimal_args()
    args["control_interval"] = value
    with pytest.raises(ConfigError, match="control_interval must be positive"):
        parse_config(args)


@pytest.mark.parametrize(("lo", "hi"), [(1, 5), (-5, -1)])
def test_parse_rejects_i_term_range_excluding_zero(lo: float, hi: float) -> None:
    args = _minimal_args()
    args["pid"] = {"i_term_min": lo, "i_term_max": hi}
    with pytest.raises(ConfigError, match="i_term_min must be <= 0"):
        parse_config(args)


@pytest.mark.parametrize(("lo", "hi"), [(0, 5), (-5, 0)])
def test_parse_accepts_i_term_range_with_zero_on_edge(lo: float, hi: float) -> None:
    args = _minimal_args()
    args["pid"] = {"i_term_min": lo, "i_term_max": hi}
    config = parse_config(args)
    assert (config.pid.i_term_min, config.pid.i_term_max) == (lo, hi)


@pytest.mark.parametrize("value", [39.9, 55.1])
def test_parse_rejects_explicit_base_outside_clamp(value: float) -> None:
    args = _minimal_args()
    args["base_water_temp"] = value
    with pytest.raises(ConfigError, match="base_water_temp must be within"):
        parse_config(args)


@pytest.mark.parametrize("value", [40, 55])
def test_parse_accepts_explicit_base_on_bound(value: float) -> None:
    args = _minimal_args()
    args["base_water_temp"] = value
    assert parse_config(args).base_water_temp == pytest.approx(value)


@pytest.mark.parametrize(
    ("lo", "hi", "expected"), [(42, 60, 42.0), (30, 35, 35.0), (40, 55, 40.0)]
)
def test_parse_omitted_base_is_default_clamped_into_bounds(
    lo: float, hi: float, expected: float
) -> None:
    args = _minimal_args()
    args["setpoint_min"] = lo
    args["setpoint_max"] = hi
    assert parse_config(args).base_water_temp == pytest.approx(expected)


def test_parse_reports_legacy_and_unknown_keys() -> None:
    args = _minimal_args()
    args["outdoor_temperature"] = "sensor.outdoor"
    args["weather_feedforward"] = {"base": 25}
    args["pid"] = {"integral_min": -10}
    args["foo"] = 1
    config = parse_config(args)
    assert config.ignored_keys == (
        "foo",
        "outdoor_temperature",
        "pid.integral_min",
        "weather_feedforward",
    )


def test_parse_appdaemon_reserved_keys_not_reported() -> None:
    raw = yaml.safe_load((ROOT / "apps.yaml.example").read_text())
    args = dict(raw["hvac"])
    args.update(
        {
            "name": "hvac",
            "priority": 50,
            "log_level": "DEBUG",
            "constrain_input_boolean": "input_boolean.x",
            "constrain_start_time": "06:00:00",
        }
    )
    assert parse_config(args).ignored_keys == ()


def test_parse_reports_non_string_keys_as_strings() -> None:
    args = _minimal_args()
    args[60] = "x"
    args["pid"] = {1: 2}
    assert parse_config(args).ignored_keys == ("60", "pid.1")


def test_appdaemon_keys_cover_app_config_fields() -> None:
    """Drift guard: every AppConfig key AppDaemon dumps into self.args is reserved."""
    from appdaemon.models.config.app import AppConfig

    for name, field in AppConfig.model_fields.items():
        assert (field.alias or name) in _APPDAEMON_KEYS, name
