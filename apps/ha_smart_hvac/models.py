"""Data models for HVAC control."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ZoneConfig:
    name: str
    temperature: str
    thermostats: tuple[str, ...]


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

    def _eligible_thermostats(self) -> tuple[ThermostatReading, ...]:
        return tuple(t for t in self.thermostats if t.hvac_action == "heating")

    @property
    def zone_error(self) -> float:
        thermostats = self._eligible_thermostats()
        if not thermostats:
            return float("-inf")
        return max(t.setpoint - self.zone_temp for t in thermostats)

    def reference_setpoint(self) -> float:
        """Setpoint of the thermostat with the largest error in this zone."""
        thermostats = self._eligible_thermostats()
        if not thermostats:
            raise ValueError("Zone has no eligible heating thermostats")
        best = max(
            thermostats,
            key=lambda t: t.setpoint - self.zone_temp,
        )
        return best.setpoint


@dataclass(frozen=True)
class WeatherFeedforwardConfig:
    base: float
    slope: float
    comfort_ref: float


@dataclass(frozen=True)
class AutoCorrectConfig:
    outdoor_gate_delta_k: float = 12.0
    r_expected_c_per_h: float = 0.25
    near_setpoint_eps_k: float = 0.3
    e_sat_c_per_h: float = 0.25


def plant_management_enabled(switch_state: str | None) -> bool:
    return switch_state == "on"


@dataclass(frozen=True)
class HvacConfig:
    outdoor_temperature: str
    plant_management: str
    plant_setpoint: str
    setpoint_min: float
    setpoint_max: float
    control_interval: int
    weather_feedforward: WeatherFeedforwardConfig
    auto_correct: AutoCorrectConfig
    zones: tuple[ZoneConfig, ...]
