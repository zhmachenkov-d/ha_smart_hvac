"""Config parse smoke: Outdoor + weather feedforward + flame short-on."""

from __future__ import annotations

import importlib
import math
import re
from pathlib import Path

import pytest
import yaml

from ha_smart_hvac.config import _APPDAEMON_KEYS, ConfigError, parse_config

ROOT = Path(__file__).resolve().parents[1]


def _minimal_args() -> dict:
    return {
        "outdoor_temperature": "sensor.outdoor",
        "flame_on": "binary_sensor.flame_on",
        "ch_active": "binary_sensor.ch_active",
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


def test_parse_omitted_defaults() -> None:
    config = parse_config(_minimal_args())
    assert config.control_interval == 300
    assert config.outdoor_temperature == "sensor.outdoor"
    assert config.weather_feedforward.base == pytest.approx(37.0)
    assert config.weather_feedforward.slope == pytest.approx(0.9)
    assert config.weather_feedforward.comfort_ref == pytest.approx(20.0)
    assert config.valve_closure_floor == pytest.approx(80.0)
    assert config.zones[0].weight == pytest.approx(1.0)
    assert config.zones[0].thermostats[0].climate == "climate.thermostat"
    assert not config.zones[0].thermostats[0].commissioned


def test_parse_weight_override() -> None:
    args = _minimal_args()
    args["control_interval"] = 120
    args["zones"][0]["weight"] = 3.0
    config = parse_config(args)
    assert config.control_interval == 120
    assert config.zones[0].weight == pytest.approx(3.0)


def test_parse_apps_yaml_example() -> None:
    """Real example file parses Outdoor + FF + flame short-on commission."""
    example_text = (ROOT / "apps.yaml.example").read_text()
    raw = yaml.safe_load(example_text)
    assert isinstance(raw, dict) and "hvac" in raw
    args = dict(raw["hvac"])
    assert args["module"] == "ha_smart_hvac"
    assert args["class"] == "HvacApp"
    assert "ladrc" not in args
    assert "tune_state_path" not in args
    assert "pid" not in args
    assert "base_water_temp" not in args
    assert "boiler_water" not in args
    assert "r_max" not in args
    assert "hold" not in args
    assert "flame_on" in args
    assert "ch_active" in args
    assert "flame_on_min_s" in args
    assert "flame_trip_hold_s" in args
    assert "auto_correct" not in args.get("weather_feedforward", {})
    assert "ff_auto_correct" not in example_text
    assert "rls_state" not in example_text
    assert "pin" in example_text.lower() or "mild Outdoor" in example_text
    config = parse_config(args)
    assert not hasattr(config, "ladrc")
    assert not hasattr(config, "tune_state_path")
    assert not hasattr(config, "auto_correct")
    assert config.outdoor_temperature == "sensor.YOUR_OUTDOOR_TEMPERATURE"
    assert config.setpoint_min == 50.0
    assert config.setpoint_max == 60.0
    assert config.control_interval == 300
    assert config.weather_feedforward.base == pytest.approx(37.0)
    assert config.weather_feedforward.slope == pytest.approx(0.9)
    assert config.weather_feedforward.comfort_ref == pytest.approx(20.0)
    assert config.flame_on == "binary_sensor.YOUR_FLAME_ON"
    assert config.ch_active == "binary_sensor.YOUR_CH_ACTIVE"
    assert config.flame_on_min_s == pytest.approx(300.0)
    assert config.flame_trip_hold_s == 900
    assert config.valve_closure_floor == pytest.approx(80.0)
    assert "valve_closure_floor" not in config.ignored_keys
    assert config.zones[0].weight == pytest.approx(1.0)
    thermos = config.zones[0].thermostats
    assert len(thermos) == 2
    assert thermos[0].climate == "climate.YOUR_ZONE_ONE_SONOFF_TRV"
    assert thermos[0].valve_closure == (
        "number.YOUR_ZONE_ONE_SONOFF_TRV_VALVE_CLOSURE_DEGREE"
    )
    assert thermos[0].accuracy == (
        "number.YOUR_ZONE_ONE_SONOFF_TRV_TEMPERATURE_CONTROL_ACCURACY"
    )
    assert thermos[0].commissioned
    assert thermos[1].climate == "climate.YOUR_ZONE_ONE_GENERIC_THERMOSTAT"
    assert not thermos[1].commissioned
    assert config.ignored_keys == ()


def test_parse_flame_short_on_defaults() -> None:
    config = parse_config(_minimal_args())
    assert config.flame_on == "binary_sensor.flame_on"
    assert config.ch_active == "binary_sensor.ch_active"
    assert config.flame_on_min_s == pytest.approx(300.0)
    assert config.flame_trip_hold_s == 900


@pytest.mark.parametrize("key", ["flame_on", "ch_active"])
def test_parse_rejects_missing_flame_entities(key: str) -> None:
    args = _minimal_args()
    del args[key]
    with pytest.raises(ConfigError, match=key):
        parse_config(args)


@pytest.mark.parametrize("key", ["flame_on", "ch_active"])
def test_parse_rejects_empty_flame_entities(key: str) -> None:
    args = _minimal_args()
    args[key] = ""
    with pytest.raises(ConfigError, match=rf"{key} must be a non-empty"):
        parse_config(args)


@pytest.mark.parametrize("key", ["flame_on_min_s", "flame_trip_hold_s"])
@pytest.mark.parametrize("value", [0, -1, math.nan, math.inf])
def test_parse_rejects_non_positive_flame_scalars(key: str, value: object) -> None:
    args = _minimal_args()
    args[key] = value
    with pytest.raises(ConfigError, match=rf"^{re.escape(key)} must be"):
        parse_config(args)


def test_parse_accepts_flame_overrides() -> None:
    args = _minimal_args()
    args["flame_on_min_s"] = 120.5
    args["flame_trip_hold_s"] = 180
    config = parse_config(args)
    assert config.flame_on_min_s == pytest.approx(120.5)
    assert config.flame_trip_hold_s == 180


def test_parse_rejects_setpoint_min_not_less_than_max() -> None:
    args = _minimal_args()
    args["setpoint_min"] = 55
    args["setpoint_max"] = 40
    with pytest.raises(ConfigError, match="setpoint_min must be less than"):
        parse_config(args)


def test_parse_ignores_legacy_water_law_keys() -> None:
    """Leftover pid / base_water_temp / trip keys ignored; flame commissioned."""
    args = _minimal_args()
    args["pid"] = {"kp": 2.0, "integral_min": -10, "adaptive": True}
    args["base_water_temp"] = 42
    args["boiler_water"] = "sensor.legacy_boiler"
    args["r_max"] = 2
    args["hold"] = 900
    config = parse_config(args)
    assert config.ignored_keys == (
        "base_water_temp",
        "boiler_water",
        "hold",
        "pid",
        "r_max",
    )
    assert config.flame_on == "binary_sensor.flame_on"
    assert config.outdoor_temperature == "sensor.outdoor"
    assert config.weather_feedforward.base == pytest.approx(37.0)
    assert config.weather_feedforward.slope == pytest.approx(0.9)
    assert config.weather_feedforward.comfort_ref == pytest.approx(20.0)
    assert config.zones[0].name == "living_room"
    assert config.zones[0].weight == pytest.approx(1.0)


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


@pytest.mark.parametrize("key", ["flame_on", "ch_active"])
def test_flame_entities_reject_non_string(key: str) -> None:
    args = _minimal_args()
    args[key] = 42
    with pytest.raises(ConfigError, match=rf"{key} must be a non-empty"):
        parse_config(args)


def test_parse_rejects_flame_trip_hold_in_open_unit_interval() -> None:
    args = _minimal_args()
    args["flame_trip_hold_s"] = 0.5
    with pytest.raises(ConfigError, match="flame_trip_hold_s must be >= 1"):
        parse_config(args)


@pytest.mark.parametrize(("raw", "expected"), [(90.9, 90), (900.9, 900)])
def test_parse_flame_trip_hold_truncates_fractional_seconds(
    raw: float, expected: int
) -> None:
    args = _minimal_args()
    args["flame_trip_hold_s"] = raw
    assert parse_config(args).flame_trip_hold_s == expected


# --- Commission parse hardening ----------------------------------------------

_TOP_NUMERIC_KEYS = [
    "setpoint_min",
    "setpoint_max",
    "control_interval",
]


def _with_value(key: str, value: object) -> dict:
    args = _minimal_args()
    args[key] = value
    return args


_ALL_NUMERIC_KEYS = _TOP_NUMERIC_KEYS


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


def test_parse_reports_legacy_and_unknown_keys() -> None:
    args = _minimal_args()
    args["pid"] = {"integral_min": -10}
    args["foo"] = 1
    args["base_water_temp"] = 40
    config = parse_config(args)
    assert config.ignored_keys == (
        "base_water_temp",
        "foo",
        "pid",
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
    args["zones"][0][2] = "x"
    assert parse_config(args).ignored_keys == (
        "60",
        "zones[living_room].2",
    )


def test_appdaemon_keys_match_app_config_fields() -> None:
    """Drift guard both ways: reserved keys == AppConfig/GlobalModule keys + name."""
    from appdaemon.models.config.app import AppConfig, GlobalModule

    fields = AppConfig.model_fields | GlobalModule.model_fields
    expected = {field.alias or name for name, field in fields.items()} | {"name"}
    assert expected == _APPDAEMON_KEYS


def test_parse_valve_closure_floor_override() -> None:
    args = _minimal_args()
    args["valve_closure_floor"] = 85
    config = parse_config(args)
    assert config.valve_closure_floor == pytest.approx(85.0)
    assert "valve_closure_floor" not in config.ignored_keys


@pytest.mark.parametrize("value", [-0.1, 100.1, -1, 101])
def test_parse_rejects_valve_closure_floor_out_of_range(value: float) -> None:
    args = _minimal_args()
    args["valve_closure_floor"] = value
    with pytest.raises(
        ConfigError, match="valve_closure_floor must be between 0 and 100"
    ):
        parse_config(args)


@pytest.mark.parametrize("value", [0, 100, 0.0, 100.0])
def test_parse_accepts_valve_closure_floor_inclusive_bounds(value: float) -> None:
    args = _minimal_args()
    args["valve_closure_floor"] = value
    assert parse_config(args).valve_closure_floor == pytest.approx(float(value))


def test_parse_thermostat_mapping_commissioned() -> None:
    args = _minimal_args()
    args["zones"][0]["thermostats"] = [
        {
            "climate": "climate.trv",
            "valve_closure": "number.trv_closure",
            "accuracy": "number.trv_accuracy",
        },
        "climate.generic",
    ]
    config = parse_config(args)
    trv, generic = config.zones[0].thermostats
    assert trv.climate == "climate.trv"
    assert trv.valve_closure == "number.trv_closure"
    assert trv.accuracy == "number.trv_accuracy"
    assert trv.commissioned
    assert generic.climate == "climate.generic"
    assert not generic.commissioned


@pytest.mark.parametrize(
    "thermostat",
    [
        None,
        42,
        {"climate": "climate.trv", "valve_closure": "number.trv_closure"},
        {"climate": "climate.trv", "accuracy": "number.trv_accuracy"},
        {
            "climate": "climate.trv",
            "valve_closure": "",
            "accuracy": "number.trv_accuracy",
        },
        {
            "climate": "climate.trv",
            "valve_closure": "number.trv_closure",
            "accuracy": "",
        },
        {
            "climate": "climate.trv",
            "valve_closure": 12,
            "accuracy": "number.trv_accuracy",
        },
        {
            "climate": "climate.trv",
            "valve_closure": "number.trv_closure",
            "accuracy": 0.5,
        },
        {"climate": "climate.trv"},
        {
            "valve_closure": "number.trv_closure",
            "accuracy": "number.trv_accuracy",
        },
        {
            "climate": "",
            "valve_closure": "number.trv_closure",
            "accuracy": "number.trv_accuracy",
        },
        {
            "climate": 7,
            "valve_closure": "number.trv_closure",
            "accuracy": "number.trv_accuracy",
        },
    ],
)
def test_parse_rejects_partial_or_invalid_trv_fields(thermostat: object) -> None:
    args = _minimal_args()
    args["zones"][0]["thermostats"] = [thermostat]
    with pytest.raises(ConfigError):
        parse_config(args)


@pytest.mark.parametrize(
    "field_path",
    [
        ("outdoor_temperature",),
        ("flame_on",),
        ("ch_active",),
        ("plant_management",),
        ("plant_setpoint",),
        ("zones", 0, "temperature"),
        ("zones", 0, "thermostats", 0),
    ],
)
def test_parse_rejects_whitespace_only_entity_id(field_path: tuple) -> None:
    args = _minimal_args()
    target = args
    for key in field_path[:-1]:
        target = target[key]
    target[field_path[-1]] = "   "
    with pytest.raises(ConfigError, match="non-empty entity id"):
        parse_config(args)


def test_parse_rejects_whitespace_only_trv_entity_fields() -> None:
    args = _minimal_args()
    for field in ("climate", "valve_closure", "accuracy"):
        args = _minimal_args()
        thermo = {
            "climate": "climate.trv",
            "valve_closure": "number.trv_closure",
            "accuracy": "number.trv_accuracy",
        }
        thermo[field] = "\t  "
        args["zones"][0]["thermostats"] = [thermo]
        with pytest.raises(ConfigError, match="non-empty entity id"):
            parse_config(args)


def test_parse_strips_padded_entity_ids() -> None:
    args = _minimal_args()
    args["outdoor_temperature"] = "  sensor.outdoor  "
    args["flame_on"] = "\tbinary_sensor.flame_on\n"
    args["ch_active"] = " binary_sensor.ch_active "
    args["plant_management"] = " switch.pm "
    args["plant_setpoint"] = "  number.setpoint  "
    args["zones"] = [
        {
            "name": "living_room",
            "temperature": "  sensor.temp  ",
            "thermostats": [
                {
                    "climate": "  climate.trv  ",
                    "valve_closure": " number.trv_closure ",
                    "accuracy": "\tnumber.trv_accuracy\t",
                },
                "  climate.generic  ",
            ],
        }
    ]
    config = parse_config(args)
    assert config.outdoor_temperature == "sensor.outdoor"
    assert config.flame_on == "binary_sensor.flame_on"
    assert config.ch_active == "binary_sensor.ch_active"
    assert config.plant_management == "switch.pm"
    assert config.plant_setpoint == "number.setpoint"
    zone = config.zones[0]
    assert zone.temperature == "sensor.temp"
    trv, generic = zone.thermostats
    assert trv.climate == "climate.trv"
    assert trv.valve_closure == "number.trv_closure"
    assert trv.accuracy == "number.trv_accuracy"
    assert generic.climate == "climate.generic"
