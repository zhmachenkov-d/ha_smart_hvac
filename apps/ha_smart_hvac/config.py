"""Validate and parse apps.yaml arguments."""

from __future__ import annotations

import math
from typing import Any

from ha_smart_hvac.models import (
    HvacConfig,
    PidConfig,
    ZoneConfig,
)


class ConfigError(ValueError):
    pass


_REQUIRED = object()

_DEFAULT_BASE_WATER_TEMP = 40.0

# One day; also keeps run_every's timedelta from overflowing.
_MAX_CONTROL_INTERVAL = 86400

# Top-level keys parse_config reads.
_KNOWN_KEYS = frozenset(
    {
        "plant_management",
        "plant_setpoint",
        "setpoint_min",
        "setpoint_max",
        "control_interval",
        "base_water_temp",
        "pid",
        "zones",
    }
)

# Keys _parse_pid reads under ``pid``.
_PID_KEYS = frozenset({"kp", "ki", "i_term_min", "i_term_max"})

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


def _parse_pid(raw: Any) -> PidConfig:
    """Parse optional pid nest; missing keys → C4 starting commission defaults."""
    if raw is None:
        return PidConfig()
    if not isinstance(raw, dict):
        raise ConfigError("pid must be a mapping")
    defaults = PidConfig()
    kp = _number(raw, "kp", defaults.kp, label="pid.kp")
    ki = _number(raw, "ki", defaults.ki, label="pid.ki")
    i_term_min = _number(raw, "i_term_min", defaults.i_term_min, label="pid.i_term_min")
    i_term_max = _number(raw, "i_term_max", defaults.i_term_max, label="pid.i_term_max")
    if kp < 0:
        raise ConfigError("pid.kp must be >= 0")
    if ki < 0:
        raise ConfigError("pid.ki must be >= 0")
    if i_term_min >= i_term_max:
        raise ConfigError("pid.i_term_min must be less than i_term_max")
    if not i_term_min <= 0 <= i_term_max:
        raise ConfigError("pid.i_term_min must be <= 0 and pid.i_term_max must be >= 0")
    return PidConfig(kp=kp, ki=ki, i_term_min=i_term_min, i_term_max=i_term_max)


def _is_appdaemon_key(key: str) -> bool:
    return key in _APPDAEMON_KEYS or key.startswith(_APPDAEMON_PREFIX)


def _ignored_keys(args: dict[Any, Any]) -> tuple[str, ...]:
    """Unknown top-level and ``pid.*`` keys (AppDaemon reserved keys excepted)."""
    ignored = [
        str(k)
        for k in args
        if str(k) not in _KNOWN_KEYS and not _is_appdaemon_key(str(k))
    ]
    pid_raw = args.get("pid")
    if isinstance(pid_raw, dict):
        ignored.extend(f"pid.{k}" for k in pid_raw if str(k) not in _PID_KEYS)
    return tuple(sorted(ignored))


def parse_config(args: dict[str, Any]) -> HvacConfig:
    """Parse AppDaemon app arguments into a validated HvacConfig."""
    plant_management = _require(args, "plant_management")
    plant_setpoint = _require(args, "plant_setpoint")
    if not isinstance(plant_management, str) or not plant_management:
        raise ConfigError("plant_management must be a non-empty entity id")
    if not isinstance(plant_setpoint, str) or not plant_setpoint:
        raise ConfigError("plant_setpoint must be a non-empty entity id")

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

    if "base_water_temp" in args:
        base_water_temp = _number(args, "base_water_temp")
        if not setpoint_min <= base_water_temp <= setpoint_max:
            raise ConfigError(
                "base_water_temp must be within setpoint_min..setpoint_max "
                f"({setpoint_min:g}..{setpoint_max:g})"
            )
    else:
        base_water_temp = min(max(_DEFAULT_BASE_WATER_TEMP, setpoint_min), setpoint_max)
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
        ignored_keys=_ignored_keys(args),
    )
