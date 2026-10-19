"""Validate and parse apps.yaml arguments."""

from __future__ import annotations

from typing import Any

from ha_smart_hvac.models import (
    AutoCorrectConfig,
    HvacConfig,
    WeatherFeedforwardConfig,
    ZoneConfig,
)


class ConfigError(ValueError):
    pass


def _require(mapping: dict[str, Any], key: str) -> Any:
    if key not in mapping:
        raise ConfigError(f"Missing required config key: {key}")
    return mapping[key]


def _parse_zone(raw: Any) -> ZoneConfig:
    if not isinstance(raw, dict):
        raise ConfigError("Each zone must be a mapping")
    name = _require(raw, "name")
    temperature = _require(raw, "temperature")
    thermostats = _require(raw, "thermostats")
    if not isinstance(name, str) or not name:
        raise ConfigError("Zone name must be a non-empty string")
    if not isinstance(temperature, str) or not temperature:
        raise ConfigError(f"Zone {name!r}: temperature must be a non-empty entity id")
    if not isinstance(thermostats, list) or not thermostats:
        raise ConfigError(f"Zone {name!r}: thermostats must be a non-empty list")
    for entity_id in thermostats:
        if not isinstance(entity_id, str) or not entity_id:
            raise ConfigError(f"Zone {name!r}: invalid thermostat entity id")
    return ZoneConfig(
        name=name, temperature=temperature, thermostats=tuple(thermostats)
    )


def _parse_auto_correct(raw: Any) -> AutoCorrectConfig:
    """Parse optional weather_feedforward.auto_correct nest; missing → E2 defaults."""
    if raw is None:
        return AutoCorrectConfig()
    if not isinstance(raw, dict):
        raise ConfigError("weather_feedforward.auto_correct must be a mapping")
    defaults = AutoCorrectConfig()
    r_expected = float(raw.get("r_expected_c_per_h", defaults.r_expected_c_per_h))
    e_sat = float(raw.get("e_sat_c_per_h", defaults.e_sat_c_per_h))
    if r_expected <= 0:
        raise ConfigError(
            "weather_feedforward.auto_correct.r_expected_c_per_h must be positive"
        )
    if e_sat <= 0:
        raise ConfigError(
            "weather_feedforward.auto_correct.e_sat_c_per_h must be positive"
        )
    return AutoCorrectConfig(
        outdoor_gate_delta_k=float(
            raw.get("outdoor_gate_delta_k", defaults.outdoor_gate_delta_k)
        ),
        r_expected_c_per_h=r_expected,
        near_setpoint_eps_k=float(
            raw.get("near_setpoint_eps_k", defaults.near_setpoint_eps_k)
        ),
        e_sat_c_per_h=e_sat,
    )


def _parse_weather_feedforward(
    raw: Any,
) -> tuple[WeatherFeedforwardConfig, AutoCorrectConfig]:
    if not isinstance(raw, dict):
        raise ConfigError("weather_feedforward must be a mapping")
    ff = WeatherFeedforwardConfig(
        base=float(_require(raw, "base")),
        slope=float(_require(raw, "slope")),
        comfort_ref=float(_require(raw, "comfort_ref")),
    )
    return ff, _parse_auto_correct(raw.get("auto_correct"))


def parse_config(args: dict[str, Any]) -> HvacConfig:
    """Parse AppDaemon app arguments into a validated HvacConfig."""
    outdoor_temperature = _require(args, "outdoor_temperature")
    plant_management = _require(args, "plant_management")
    plant_setpoint = _require(args, "plant_setpoint")
    if not isinstance(outdoor_temperature, str) or not outdoor_temperature:
        raise ConfigError("outdoor_temperature must be a non-empty entity id")
    if not isinstance(plant_management, str) or not plant_management:
        raise ConfigError("plant_management must be a non-empty entity id")
    if not isinstance(plant_setpoint, str) or not plant_setpoint:
        raise ConfigError("plant_setpoint must be a non-empty entity id")

    setpoint_min = float(_require(args, "setpoint_min"))
    setpoint_max = float(_require(args, "setpoint_max"))
    if setpoint_min >= setpoint_max:
        raise ConfigError("setpoint_min must be less than setpoint_max")

    control_interval = int(args.get("control_interval", 60))
    if control_interval <= 0:
        raise ConfigError("control_interval must be positive")

    zones_raw = _require(args, "zones")
    if not isinstance(zones_raw, list) or not zones_raw:
        raise ConfigError("zones must be a non-empty list")

    weather_feedforward, auto_correct = _parse_weather_feedforward(
        _require(args, "weather_feedforward")
    )
    return HvacConfig(
        outdoor_temperature=outdoor_temperature,
        plant_management=plant_management,
        plant_setpoint=plant_setpoint,
        setpoint_min=setpoint_min,
        setpoint_max=setpoint_max,
        control_interval=control_interval,
        weather_feedforward=weather_feedforward,
        auto_correct=auto_correct,
        zones=tuple(_parse_zone(z) for z in zones_raw),
    )
