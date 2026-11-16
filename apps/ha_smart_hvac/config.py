"""Validate and parse apps.yaml arguments."""

from __future__ import annotations

import math
from typing import Any

from ha_smart_hvac.models import (
    HvacConfig,
    ThermostatConfig,
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

_DEFAULT_FLAME_ON_MIN_S = 300.0
_DEFAULT_FLAME_TRIP_HOLD_S = 900
_DEFAULT_VALVE_CLOSURE_FLOOR = 80.0

# Top-level keys parse_config reads.
_KNOWN_KEYS = frozenset(
    {
        "outdoor_temperature",
        "flame_on",
        "ch_active",
        "flame_on_min_s",
        "flame_trip_hold_s",
        "plant_management",
        "plant_setpoint",
        "setpoint_min",
        "setpoint_max",
        "control_interval",
        "weather_feedforward",
        "valve_closure_floor",
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


def _entity_id(raw: Any, *, label: str) -> str:
    if not isinstance(raw, str):
        raise ConfigError(f"{label} must be a non-empty entity id")
    stripped = raw.strip()
    if not stripped:
        raise ConfigError(f"{label} must be a non-empty entity id")
    return stripped


def _parse_thermostat(raw: Any, *, zone_name: str) -> ThermostatConfig:
    label = f"Zone {zone_name!r}"
    if isinstance(raw, str):
        return ThermostatConfig(climate=_entity_id(raw, label=f"{label}: thermostat"))
    if not isinstance(raw, dict):
        raise ConfigError(f"{label}: thermostat must be a string or mapping")
    climate = _entity_id(raw.get("climate"), label=f"{label}: climate")
    if "valve_closure" not in raw or "accuracy" not in raw:
        raise ConfigError(
            f"{label}: thermostat mapping requires valve_closure and accuracy"
        )
    valve_closure = _entity_id(
        raw.get("valve_closure"), label=f"{label}: valve_closure"
    )
    accuracy = _entity_id(raw.get("accuracy"), label=f"{label}: accuracy")
    return ThermostatConfig(
        climate=climate, valve_closure=valve_closure, accuracy=accuracy
    )


def _parse_zone(raw: Any) -> ZoneConfig:
    if not isinstance(raw, dict):
        raise ConfigError("Each zone must be a mapping")
    name = _require(raw, "name")
    temperature_raw = _require(raw, "temperature")
    thermostats = _require(raw, "thermostats")
    if not isinstance(name, str) or not name:
        raise ConfigError("Zone name must be a non-empty string")
    temperature = _entity_id(temperature_raw, label=f"Zone {name!r}: temperature")
    if not isinstance(thermostats, list) or not thermostats:
        raise ConfigError(f"Zone {name!r}: thermostats must be a non-empty list")
    parsed = tuple(_parse_thermostat(item, zone_name=name) for item in thermostats)
    weight = _number(raw, "weight", 1.0, label=f"Zone {name!r}: weight")
    if weight < 0:
        raise ConfigError(f"Zone {name!r}: weight must be >= 0")
    return ZoneConfig(
        name=name,
        temperature=temperature,
        thermostats=parsed,
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
    outdoor_temperature = _entity_id(
        _require(args, "outdoor_temperature"), label="outdoor_temperature"
    )
    flame_on = _entity_id(_require(args, "flame_on"), label="flame_on")
    ch_active = _entity_id(_require(args, "ch_active"), label="ch_active")
    plant_management = _entity_id(
        _require(args, "plant_management"), label="plant_management"
    )
    plant_setpoint = _entity_id(
        _require(args, "plant_setpoint"), label="plant_setpoint"
    )

    flame_on_min_s = _number(args, "flame_on_min_s", _DEFAULT_FLAME_ON_MIN_S)
    if flame_on_min_s <= 0:
        raise ConfigError("flame_on_min_s must be > 0")

    hold_raw = _number(args, "flame_trip_hold_s", _DEFAULT_FLAME_TRIP_HOLD_S)
    if hold_raw <= 0:
        raise ConfigError("flame_trip_hold_s must be > 0")
    flame_trip_hold_s = int(hold_raw)
    if flame_trip_hold_s < 1:
        raise ConfigError("flame_trip_hold_s must be >= 1")

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

    valve_closure_floor = _number(
        args, "valve_closure_floor", _DEFAULT_VALVE_CLOSURE_FLOOR
    )
    if not 0.0 <= valve_closure_floor <= 100.0:
        raise ConfigError("valve_closure_floor must be between 0 and 100")

    zones_raw = _require(args, "zones")
    if not isinstance(zones_raw, list) or not zones_raw:
        raise ConfigError("zones must be a non-empty list")

    return HvacConfig(
        outdoor_temperature=outdoor_temperature,
        flame_on=flame_on,
        ch_active=ch_active,
        plant_management=plant_management,
        plant_setpoint=plant_setpoint,
        setpoint_min=setpoint_min,
        setpoint_max=setpoint_max,
        control_interval=control_interval,
        flame_on_min_s=flame_on_min_s,
        flame_trip_hold_s=flame_trip_hold_s,
        weather_feedforward=weather_feedforward,
        zones=tuple(_parse_zone(z) for z in zones_raw),
        valve_closure_floor=valve_closure_floor,
        ignored_keys=_ignored_keys(args),
    )
