"""Validate and parse apps.yaml arguments."""

from __future__ import annotations

import math
from typing import Any

from ha_smart_hvac.models import (
    HvacConfig,
    WeatherFeedforwardConfig,
    ZoneConfig,
)


class ConfigError(ValueError):
    pass


_REQUIRED = object()

_DEFAULT_FF_BASE = 37.0
_DEFAULT_FF_SLOPE = 0.9
_DEFAULT_FF_COMFORT_REF = 20.0

# One day; also keeps run_every's timedelta from overflowing.
_MAX_CONTROL_INTERVAL = 86400

_DEFAULT_R_MAX = 2.0
_DEFAULT_HOLD = 900

# Top-level keys parse_config reads.
_KNOWN_KEYS = frozenset(
    {
        "outdoor_temperature",
        "boiler_water",
        "r_max",
        "hold",
        "plant_management",
        "plant_setpoint",
        "setpoint_min",
        "setpoint_max",
        "control_interval",
        "weather_feedforward",
        "zones",
    }
)

# Keys _parse_weather_feedforward reads under ``weather_feedforward``.
_FF_KEYS = frozenset({"base", "slope", "comfort_ref"})

# Keys _parse_zone reads under each zone mapping.
_ZONE_KEYS = frozenset({"name", "temperature", "thermostats", "weight"})

# AppDaemon 4.5.13 reserved app keys (BaseApp / AppConfig / GlobalModule aliases,
# plus the injected ``name``; ``global: false`` on an app stays in its args);
# any ``constrain_*`` key is also AppDaemon's.
# Hard-coded so this module imports without AppDaemon; a test guards drift.
_APPDAEMON_KEYS = frozenset(
    {
        "name",
        "config_path",
        "global",
        "module",
        "class",
        "dependencies",
        "global_dependencies",
        "disable",
        "priority",
        "pin_app",
        "pin_thread",
        "log",
        "log_level",
    }
)
_APPDAEMON_PREFIX = "constrain_"


def _require(mapping: dict[str, Any], key: str) -> Any:
    if key not in mapping:
        raise ConfigError(f"Missing required config key: {key}")
    return mapping[key]


def _number(
    mapping: dict[str, Any],
    key: str,
    default: Any = _REQUIRED,
    label: str | None = None,
) -> float:
    """Finite float from ``mapping[key]``; ConfigError on anything else.

    ``default`` applies only when ``key`` is absent; an explicit ``None`` is
    rejected. Booleans are rejected (``float(True) == 1.0`` would pass silently).
    """
    label = label or key
    if default is _REQUIRED:
        raw = _require(mapping, key)
    elif key in mapping:
        raw = mapping[key]
    else:
        return float(default)
    if isinstance(raw, bool):
        raise ConfigError(f"{label} must be a number")
    try:
        value = float(raw)
    except OverflowError as exc:
        raise ConfigError(f"{label} must be finite") from exc
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{label} must be a number") from exc
    if not math.isfinite(value):
        raise ConfigError(f"{label} must be finite")
    return value


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
    weight = _number(raw, "weight", 1.0, label=f"Zone {name!r}: weight")
    if weight < 0:
        raise ConfigError(f"Zone {name!r}: weight must be >= 0")
    return ZoneConfig(
        name=name,
        temperature=temperature,
        thermostats=tuple(thermostats),
        weight=weight,
    )


def _parse_weather_feedforward(raw: Any) -> WeatherFeedforwardConfig:
    """Require a mapping; omitted numerics → commission defaults; whitelist keys."""
    if not isinstance(raw, dict):
        raise ConfigError("weather_feedforward must be a mapping")
    unknown = sorted(str(k) for k in raw if str(k) not in _FF_KEYS)
    if unknown:
        raise ConfigError("weather_feedforward unknown keys: " + ", ".join(unknown))
    return WeatherFeedforwardConfig(
        base=_number(raw, "base", _DEFAULT_FF_BASE, label="weather_feedforward.base"),
        slope=_number(
            raw, "slope", _DEFAULT_FF_SLOPE, label="weather_feedforward.slope"
        ),
        comfort_ref=_number(
            raw,
            "comfort_ref",
            _DEFAULT_FF_COMFORT_REF,
            label="weather_feedforward.comfort_ref",
        ),
    )


def _is_appdaemon_key(key: str) -> bool:
    return key in _APPDAEMON_KEYS or key.startswith(_APPDAEMON_PREFIX)


def _ignored_keys(args: dict[Any, Any]) -> tuple[str, ...]:
    """Unknown top-level and zone sub-keys (AppDaemon keys excepted)."""
    ignored = [
        str(k)
        for k in args
        if str(k) not in _KNOWN_KEYS and not _is_appdaemon_key(str(k))
    ]
    zones_raw = args.get("zones")
    if isinstance(zones_raw, list):
        for index, zone in enumerate(zones_raw):
            if not isinstance(zone, dict):
                continue
            name = zone.get("name")
            label = str(name) if isinstance(name, str) and name else str(index)
            ignored.extend(
                f"zones[{label}].{str(k)}" for k in zone if str(k) not in _ZONE_KEYS
            )
    return tuple(sorted(ignored))


def parse_config(args: dict[str, Any]) -> HvacConfig:
    """Parse AppDaemon app arguments into a validated HvacConfig."""
    outdoor_temperature = _require(args, "outdoor_temperature")
    boiler_water = _require(args, "boiler_water")
    plant_management = _require(args, "plant_management")
    plant_setpoint = _require(args, "plant_setpoint")
    if not isinstance(outdoor_temperature, str) or not outdoor_temperature:
        raise ConfigError("outdoor_temperature must be a non-empty entity id")
    if not isinstance(boiler_water, str) or not boiler_water:
        raise ConfigError("boiler_water must be a non-empty entity id")
    if not isinstance(plant_management, str) or not plant_management:
        raise ConfigError("plant_management must be a non-empty entity id")
    if not isinstance(plant_setpoint, str) or not plant_setpoint:
        raise ConfigError("plant_setpoint must be a non-empty entity id")

    r_max = _number(args, "r_max", _DEFAULT_R_MAX)
    if r_max <= 0:
        raise ConfigError("r_max must be > 0")

    hold_raw = _number(args, "hold", _DEFAULT_HOLD)
    if hold_raw <= 0:
        raise ConfigError("hold must be > 0")
    hold = int(hold_raw)
    if hold < 1:
        raise ConfigError("hold must be >= 1")

    setpoint_min = _number(args, "setpoint_min")
    setpoint_max = _number(args, "setpoint_max")
    if setpoint_min >= setpoint_max:
        raise ConfigError("setpoint_min must be less than setpoint_max")

    interval = _number(args, "control_interval", 300)
    if not interval.is_integer():
        raise ConfigError("control_interval must be a whole number of seconds")
    control_interval = int(interval)
    if control_interval <= 0:
        raise ConfigError("control_interval must be positive")
    if control_interval > _MAX_CONTROL_INTERVAL:
        raise ConfigError(
            f"control_interval must be at most {_MAX_CONTROL_INTERVAL} seconds"
        )

    weather_feedforward = _parse_weather_feedforward(
        _require(args, "weather_feedforward")
    )

    zones_raw = _require(args, "zones")
    if not isinstance(zones_raw, list) or not zones_raw:
        raise ConfigError("zones must be a non-empty list")

    return HvacConfig(
        outdoor_temperature=outdoor_temperature,
        boiler_water=boiler_water,
        plant_management=plant_management,
        plant_setpoint=plant_setpoint,
        setpoint_min=setpoint_min,
        setpoint_max=setpoint_max,
        control_interval=control_interval,
        r_max=r_max,
        hold=hold,
        weather_feedforward=weather_feedforward,
        zones=tuple(_parse_zone(z) for z in zones_raw),
        ignored_keys=_ignored_keys(args),
    )
