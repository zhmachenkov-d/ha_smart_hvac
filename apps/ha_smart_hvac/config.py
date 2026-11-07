"""Validate and parse apps.yaml arguments."""

from __future__ import annotations

from typing import Any

from ha_smart_hvac.models import (
    HvacConfig,
    PidConfig,
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
    if "weight" in raw:
        try:
            weight = float(raw["weight"])
        except (TypeError, ValueError) as exc:
            raise ConfigError(f"Zone {name!r}: weight must be a number") from exc
        if weight < 0:
            raise ConfigError(f"Zone {name!r}: weight must be >= 0")
    else:
        weight = 1.0
    return ZoneConfig(
        name=name,
        temperature=temperature,
        thermostats=tuple(thermostats),
        weight=weight,
    )


def _parse_pid(raw: Any) -> PidConfig:
    """Parse optional pid nest; missing keys → C4 starting commission defaults."""
    if raw is None:
        return PidConfig()
    if not isinstance(raw, dict):
        raise ConfigError("pid must be a mapping")
    defaults = PidConfig()
    integral_min = float(raw.get("integral_min", defaults.integral_min))
    integral_max = float(raw.get("integral_max", defaults.integral_max))
    if integral_min >= integral_max:
        raise ConfigError("pid.integral_min must be less than integral_max")
    return PidConfig(
        kp=float(raw.get("kp", defaults.kp)),
        ki=float(raw.get("ki", defaults.ki)),
        integral_min=integral_min,
        integral_max=integral_max,
    )


def parse_config(args: dict[str, Any]) -> HvacConfig:
    """Parse AppDaemon app arguments into a validated HvacConfig."""
    plant_management = _require(args, "plant_management")
    plant_setpoint = _require(args, "plant_setpoint")
    if not isinstance(plant_management, str) or not plant_management:
        raise ConfigError("plant_management must be a non-empty entity id")
    if not isinstance(plant_setpoint, str) or not plant_setpoint:
        raise ConfigError("plant_setpoint must be a non-empty entity id")

    setpoint_min = float(_require(args, "setpoint_min"))
    setpoint_max = float(_require(args, "setpoint_max"))
    if setpoint_min >= setpoint_max:
        raise ConfigError("setpoint_min must be less than setpoint_max")

    control_interval = int(args.get("control_interval", 300))
    if control_interval <= 0:
        raise ConfigError("control_interval must be positive")

    base_water_temp = float(args.get("base_water_temp", 40.0))
    pid = _parse_pid(args.get("pid"))

    zones_raw = _require(args, "zones")
    if not isinstance(zones_raw, list) or not zones_raw:
        raise ConfigError("zones must be a non-empty list")

    return HvacConfig(
        plant_management=plant_management,
        plant_setpoint=plant_setpoint,
        setpoint_min=setpoint_min,
        setpoint_max=setpoint_max,
        control_interval=control_interval,
        base_water_temp=base_water_temp,
        pid=pid,
        zones=tuple(_parse_zone(z) for z in zones_raw),
    )
