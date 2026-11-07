"""Data models for HVAC control."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ZoneConfig:
    name: str
    temperature: str
    thermostats: tuple[str, ...]
    weight: float = 1.0


@dataclass(frozen=True)
class ThermostatReading:
    entity_id: str
    setpoint: float
    hvac_action: str | None = None


@dataclass(frozen=True)
class ZoneSnapshot:
    name: str
    zone_temp: float
    thermostats: tuple[ThermostatReading, ...]
    weight: float = 1.0

    def _eligible_thermostats(self) -> tuple[ThermostatReading, ...]:
        return tuple(t for t in self.thermostats if t.hvac_action == "heating")

    @property
    def has_heating_eligible(self) -> bool:
        return bool(self._eligible_thermostats())

    @property
    def heating_setpoint_max(self) -> float | None:
        """Max setpoint among heating thermostats; None if none eligible."""
        thermostats = self._eligible_thermostats()
        if not thermostats:
            return None
        return max(t.setpoint for t in thermostats)

    @property
    def zone_error(self) -> float:
        thermostats = self._eligible_thermostats()
        if not thermostats:
            return float("-inf")
        return max(t.setpoint - self.zone_temp for t in thermostats)


@dataclass(frozen=True)
class PidConfig:
    kp: float = 1.0
    ki: float = 0.1
    integral_min: float = -50.0
    integral_max: float = 50.0


def plant_management_enabled(switch_state: str | None) -> bool:
    return switch_state == "on"


@dataclass(frozen=True)
class HvacConfig:
    plant_management: str
    plant_setpoint: str
    setpoint_min: float
    setpoint_max: float
    control_interval: int
    base_water_temp: float
    pid: PidConfig
    zones: tuple[ZoneConfig, ...]
