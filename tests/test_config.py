"""Config parse smoke: Outdoor + weather feedforward + PID commission args."""

from __future__ import annotations

import importlib
import math
import re
from dataclasses import replace
from pathlib import Path

import pytest
import yaml

from ha_smart_hvac.config import _APPDAEMON_KEYS, ConfigError, parse_config
from ha_smart_hvac.models import PidConfig

ROOT = Path(__file__).resolve().parents[1]


def _minimal_args() -> dict:
    return {
        "outdoor_temperature": "sensor.outdoor",
        "plant_management": "switch.pm",
        "plant_setpoint": "number.setpoint",
        "setpoint_min": 40,
        "setpoint_max": 55,
        "weather_feedforward": {},
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
    assert config.outdoor_temperature == "sensor.outdoor"
    assert config.weather_feedforward.base == pytest.approx(37.0)
    assert config.weather_feedforward.slope == pytest.approx(0.9)
    assert config.weather_feedforward.comfort_ref == pytest.approx(20.0)
    assert config.pid.kp == pytest.approx(1.0)
    assert config.pid.ki == pytest.approx(1.0)
    assert config.pid.i_term_min == pytest.approx(-10.0)
    assert config.pid.i_term_max == pytest.approx(15.0)
    assert config.pid.adaptive is False
    assert config.boiler_water is None
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
    """Real example file parses with Outdoor + FF + PID commission defaults."""
    example_text = (ROOT / "apps.yaml.example").read_text()
    raw = yaml.safe_load(example_text)
    assert isinstance(raw, dict) and "hvac" in raw
    args = dict(raw["hvac"])
    assert args["module"] == "ha_smart_hvac"
    assert args["class"] == "HvacApp"
    assert "ladrc" not in args
    assert "tune_state_path" not in args
    assert "auto_correct" not in args.get("weather_feedforward", {})
    assert "ff_auto_correct" not in example_text
    assert "pin" in example_text.lower() or "mild Outdoor" in example_text
    config = parse_config(args)
    assert not hasattr(config, "ladrc")
    assert not hasattr(config, "tune_state_path")
    assert not hasattr(config, "auto_correct")
    assert config.outdoor_temperature == "sensor.YOUR_OUTDOOR_TEMPERATURE"
    assert config.setpoint_min == 50.0
    assert config.setpoint_max == 60.0
    assert config.control_interval == 300
    assert config.base_water_temp == pytest.approx(51.0)
    assert config.weather_feedforward.base == pytest.approx(37.0)
    assert config.weather_feedforward.slope == pytest.approx(0.9)
    assert config.weather_feedforward.comfort_ref == pytest.approx(20.0)
    assert config.pid == PidConfig(
        kp=1.0, ki=1.0, i_term_min=-10.0, i_term_max=15.0, adaptive=False
    )
    assert config.boiler_water is None
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


@pytest.mark.parametrize("value", [None, "abc", [1], True, False])
def test_parse_rejects_non_numeric_zone_weight(value: object) -> None:
    args = _minimal_args()
    args["zones"][0]["weight"] = value
    with pytest.raises(
        ConfigError, match="Zone 'living_room': weight must be a number"
    ):
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


def test_feedforward_module_present_auto_correct_absent() -> None:
    importlib.import_module("ha_smart_hvac.feedforward")
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("ha_smart_hvac.ff_auto_correct")


def test_config_has_outdoor_and_feedforward_fields() -> None:
    import ha_smart_hvac.models as models

    config = parse_config(_minimal_args())
    assert config.outdoor_temperature == "sensor.outdoor"
    assert config.weather_feedforward.base == pytest.approx(37.0)
    assert not hasattr(config, "auto_correct")
    assert hasattr(models, "WeatherFeedforwardConfig")
    assert not hasattr(models, "AutoCorrectConfig")


def test_weather_feedforward_overrides() -> None:
    args = _minimal_args()
    args["weather_feedforward"] = {"base": 25, "slope": 1.2, "comfort_ref": 18}
    config = parse_config(args)
    assert config.weather_feedforward.base == pytest.approx(25.0)
    assert config.weather_feedforward.slope == pytest.approx(1.2)
    assert config.weather_feedforward.comfort_ref == pytest.approx(18.0)


def test_weather_feedforward_accepts_negative_slope() -> None:
    args = _minimal_args()
    args["weather_feedforward"] = {"slope": -0.5}
    assert parse_config(args).weather_feedforward.slope == pytest.approx(-0.5)


@pytest.mark.parametrize("key", ["base", "slope", "comfort_ref"])
@pytest.mark.parametrize(
    "value", [math.nan, math.inf, -math.inf, "nan", None, True, "x"]
)
def test_weather_feedforward_rejects_bad_numerics(key: str, value: object) -> None:
    args = _minimal_args()
    args["weather_feedforward"] = {key: value}
    with pytest.raises(ConfigError, match=rf"weather_feedforward\.{key} must be"):
        parse_config(args)


def test_weather_feedforward_rejects_unknown_subkeys() -> None:
    args = _minimal_args()
    args["weather_feedforward"] = {"base": 37, "auto_correct": {}}
    with pytest.raises(ConfigError, match="weather_feedforward unknown keys"):
        parse_config(args)


def test_missing_outdoor_or_feedforward_raises() -> None:
    args = _minimal_args()
    del args["outdoor_temperature"]
    with pytest.raises(ConfigError, match="outdoor_temperature"):
        parse_config(args)
    args = _minimal_args()
    del args["weather_feedforward"]
    with pytest.raises(ConfigError, match="weather_feedforward"):
        parse_config(args)


def test_empty_outdoor_entity_rejected() -> None:
    args = _minimal_args()
    args["outdoor_temperature"] = ""
    with pytest.raises(ConfigError, match="outdoor_temperature must be a non-empty"):
        parse_config(args)


def test_weather_feedforward_rejects_non_mapping() -> None:
    args = _minimal_args()
    args["weather_feedforward"] = "not-a-mapping"
    with pytest.raises(ConfigError, match="weather_feedforward must be a mapping"):
        parse_config(args)


def test_outdoor_temperature_rejects_non_string() -> None:
    args = _minimal_args()
    args["outdoor_temperature"] = 42
    with pytest.raises(ConfigError, match="outdoor_temperature must be a non-empty"):
        parse_config(args)


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
    with pytest.raises(ConfigError, match=rf"^{re.escape(key)} must be a number$"):
        parse_config(_with_value(key, value))


@pytest.mark.parametrize("key", _ALL_NUMERIC_KEYS)
@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf, "nan", "inf"])
def test_parse_rejects_non_finite(key: str, value: object) -> None:
    with pytest.raises(ConfigError, match=rf"^{re.escape(key)} must be finite$"):
        parse_config(_with_value(key, value))


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_parse_rejects_non_finite_zone_weight(value: float) -> None:
    args = _minimal_args()
    args["zones"][0]["weight"] = value
    with pytest.raises(ConfigError, match="Zone 'living_room': weight must be finite"):
        parse_config(args)


@pytest.mark.parametrize("key", _ALL_NUMERIC_KEYS)
def test_parse_rejects_overflow(key: str) -> None:
    with pytest.raises(ConfigError, match=rf"^{re.escape(key)} must be finite$"):
        parse_config(_with_value(key, 10**400))


def test_parse_rejects_overflow_zone_weight() -> None:
    args = _minimal_args()
    args["zones"][0]["weight"] = 10**400
    with pytest.raises(ConfigError, match="Zone 'living_room': weight must be finite"):
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
    assert config.pid.legacy_ki_warning is False


def test_parse_explicit_ki_one_no_legacy_warning() -> None:
    args = _minimal_args()
    args["pid"] = {"ki": 1.0}
    config = parse_config(args)
    assert config.pid.ki == pytest.approx(1.0)
    assert config.pid.legacy_ki_warning is False


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


@pytest.mark.parametrize("value", [86401, 1e15])
def test_parse_rejects_control_interval_above_one_day(value: float) -> None:
    args = _minimal_args()
    args["control_interval"] = value
    with pytest.raises(
        ConfigError, match="control_interval must be at most 86400 seconds"
    ):
        parse_config(args)


def test_parse_accepts_control_interval_of_one_day() -> None:
    args = _minimal_args()
    args["control_interval"] = 86400
    assert parse_config(args).control_interval == 86400


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
    args["pid"] = {"integral_min": -10}
    args["foo"] = 1
    config = parse_config(args)
    assert config.ignored_keys == (
        "foo",
        "pid.integral_min",
    )


def test_parse_reports_unknown_zone_sub_keys() -> None:
    args = _minimal_args()
    args["zones"][0]["weigth"] = 3
    config = parse_config(args)
    assert config.ignored_keys == ("zones[living_room].weigth",)
    assert config.zones[0].weight == pytest.approx(1.0)


def test_parse_reports_unknown_zone_sub_keys_on_second_zone() -> None:
    args = _minimal_args()
    args["zones"].append(
        {
            "name": "zone_two",
            "temperature": "sensor.temp_two",
            "thermostats": ["climate.thermostat_two"],
            "weigth": 3,
        }
    )
    config = parse_config(args)
    assert config.ignored_keys == ("zones[zone_two].weigth",)
    assert config.zones[1].weight == pytest.approx(1.0)


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
    args["zones"][0][2] = "x"
    assert parse_config(args).ignored_keys == (
        "60",
        "pid.1",
        "zones[living_room].2",
    )


def test_appdaemon_keys_match_app_config_fields() -> None:
    """Drift guard both ways: reserved keys == AppConfig/GlobalModule keys + name."""
    from appdaemon.models.config.app import AppConfig, GlobalModule

    fields = AppConfig.model_fields | GlobalModule.model_fields
    expected = {field.alias or name for name, field in fields.items()} | {"name"}
    assert expected == _APPDAEMON_KEYS


# --- RLS adaptive commission (tracer) ----------------------------------------


def test_parse_adaptive_false_allows_omitted_boiler_water() -> None:
    args = _minimal_args()
    args["pid"] = {"adaptive": False}
    config = parse_config(args)
    assert config.pid.adaptive is False
    assert config.boiler_water is None


def _adaptive_pid(**overrides: object) -> dict:
    pid: dict = {
        "adaptive": True,
        "kp_min": 0.0,
        "kp_max": 10.0,
        "ki_min": 0.0,
        "ki_max": 100.0,
    }
    pid.update(overrides)
    return pid


def test_parse_adaptive_true_with_boiler_water() -> None:
    args = _minimal_args()
    args["pid"] = _adaptive_pid()
    args["boiler_water"] = "  sensor.boiler_water  "
    config = parse_config(args)
    assert config.pid.adaptive is True
    assert config.boiler_water == "sensor.boiler_water"
    assert config.pid.kp_min == pytest.approx(0.0)
    assert config.pid.kp_max == pytest.approx(10.0)
    assert config.pid.ki_min == pytest.approx(0.0)
    assert config.pid.ki_max == pytest.approx(100.0)


def test_parse_adaptive_true_missing_boiler_water_raises() -> None:
    args = _minimal_args()
    args["pid"] = _adaptive_pid()
    with pytest.raises(ConfigError, match="boiler_water must be a non-empty entity id"):
        parse_config(args)


@pytest.mark.parametrize("value", ["", "   ", None, 1, True])
def test_parse_adaptive_true_invalid_boiler_water_raises(value: object) -> None:
    args = _minimal_args()
    args["pid"] = _adaptive_pid()
    args["boiler_water"] = value
    with pytest.raises(ConfigError, match="boiler_water must be a non-empty entity id"):
        parse_config(args)


@pytest.mark.parametrize("value", ["true", "false", 1, 0, None, "yes"])
def test_parse_rejects_non_bool_adaptive(value: object) -> None:
    args = _minimal_args()
    args["pid"] = {"adaptive": value}
    with pytest.raises(ConfigError, match="pid.adaptive must be a boolean"):
        parse_config(args)


def test_parse_adaptive_off_whitespace_boiler_water_omitted() -> None:
    args = _minimal_args()
    args["pid"] = {"adaptive": False}
    args["boiler_water"] = "   "
    config = parse_config(args)
    assert config.boiler_water is None


@pytest.mark.parametrize("missing", ["kp_min", "kp_max", "ki_min", "ki_max"])
def test_parse_adaptive_true_missing_rail_raises(missing: str) -> None:
    args = _minimal_args()
    args["boiler_water"] = "sensor.boiler_water"
    pid = _adaptive_pid()
    del pid[missing]
    args["pid"] = pid
    with pytest.raises(ConfigError, match=f"pid\\.{missing} is required"):
        parse_config(args)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("kp_min", -0.1),
        ("kp_max", -1.0),
        ("ki_min", -0.01),
        ("ki_max", -5.0),
    ],
)
def test_parse_adaptive_true_negative_rail_raises(key: str, value: float) -> None:
    args = _minimal_args()
    args["boiler_water"] = "sensor.boiler_water"
    args["pid"] = _adaptive_pid(**{key: value})
    with pytest.raises(ConfigError, match=f"pid\\.{key} must be >= 0"):
        parse_config(args)


@pytest.mark.parametrize(
    ("overrides", "match"),
    [
        ({"kp_min": 5.0, "kp_max": 1.0}, "pid.kp_min must be <= pid.kp_max"),
        ({"ki_min": 5.0, "ki_max": 1.0}, "pid.ki_min must be <= pid.ki_max"),
    ],
)
def test_parse_adaptive_true_rail_min_gt_max_raises(
    overrides: dict, match: str
) -> None:
    args = _minimal_args()
    args["boiler_water"] = "sensor.boiler_water"
    args["pid"] = _adaptive_pid(**overrides)
    with pytest.raises(ConfigError, match=match):
        parse_config(args)


def test_parse_adaptive_true_rail_min_eq_max_ok() -> None:
    args = _minimal_args()
    args["boiler_water"] = "sensor.boiler_water"
    args["pid"] = _adaptive_pid(kp_min=2.0, kp_max=2.0, ki_min=3.0, ki_max=3.0)
    config = parse_config(args)
    assert config.pid.kp_min == pytest.approx(2.0)
    assert config.pid.kp_max == pytest.approx(2.0)
    assert config.pid.ki_min == pytest.approx(3.0)
    assert config.pid.ki_max == pytest.approx(3.0)


def test_parse_explicit_legacy_scale_ki_sets_warning_flag() -> None:
    args = _minimal_args()
    args["pid"] = {"ki": 0.2}
    config = parse_config(args)
    assert config.pid.ki == pytest.approx(0.2)
    assert config.pid.legacy_ki_warning is True


def test_parse_omitted_ki_no_legacy_warning() -> None:
    config = parse_config(_minimal_args())
    assert config.pid.legacy_ki_warning is False


def test_parse_adaptive_off_may_omit_rails() -> None:
    args = _minimal_args()
    args["pid"] = {"adaptive": False}
    config = parse_config(args)
    assert config.pid.kp_min is None
    assert config.pid.kp_max is None
    assert config.pid.ki_min is None
    assert config.pid.ki_max is None
