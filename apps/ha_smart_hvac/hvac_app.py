"""HVAC App — fixed-gain PID Set Water Temperature loop."""

from __future__ import annotations

import math

import appdaemon.plugins.hass.hassapi as hass

from ha_smart_hvac.config import ConfigError, parse_config
from ha_smart_hvac.coordinator import has_heating_demand, select_max_error_demand_zone
from ha_smart_hvac.models import (
    HvacConfig,
    ThermostatReading,
    ZoneSnapshot,
    plant_management_enabled,
)
from ha_smart_hvac.pid import PidResult, evaluate_demand


class HvacApp(hass.Hass):
    def initialize(self) -> None:
        try:
            self._config: HvacConfig = parse_config(self.args)
        except ConfigError as exc:
            self.log(f"HVAC config error: {exc}", level="ERROR")
            return
        if self._config.ignored_keys:
            self.log(
                "HVAC config: ignoring legacy or unknown keys: "
                + ", ".join(self._config.ignored_keys),
                level="WARNING",
            )

        self._integral = 0.0

        self._register_control_listeners()
        self.run_every(
            self.control_tick,
            "now",
            self._config.control_interval,
        )
        self.log("HVAC fixed-gain PID app initialized")

    def _register_control_listeners(self) -> None:
        """Re-evaluate gate on plant / zone air / thermostat attrs."""
        config = self._config
        self.listen_state(self.control_event, config.plant_management)
        for zone in config.zones:
            self.listen_state(self.control_event, zone.temperature)
            for entity_id in zone.thermostats:
                self.listen_state(
                    self.control_event, entity_id, attribute="hvac_action"
                )
                self.listen_state(
                    self.control_event, entity_id, attribute="temperature"
                )

    def _clear_pid_ephemeral(self) -> None:
        self._integral = 0.0

    def _gate_prelude(self) -> list[ZoneSnapshot] | None:
        """Plant Management / Heating Demand prelude. Zones on demand, else None."""
        config = self._config

        if not plant_management_enabled(self.get_state(config.plant_management)):
            self._clear_pid_ephemeral()
            self._hands_off("Plant Management disabled")
            return None

        zones = self._read_zones(config)
        if not zones:
            self._go_idle("No zones with valid readings this tick")
            return None

        if not has_heating_demand(zones):
            self._go_idle("No heating demand; setpoint 0", level="INFO")
            return None

        return zones

    def control_tick(self, kwargs: dict) -> None:
        zones = self._gate_prelude()
        if zones is None:
            return
        self._run_demand(zones)

    def control_event(
        self,
        entity: str,
        attribute: str,
        old: object,
        new: object,
        kwargs: dict,
    ) -> None:
        """Event entry: shared prelude clears; demand is tick-owned (no write / ∫)."""
        # listen_state args ignored — re-read current Hass state in prelude.
        self._gate_prelude()

    def _run_demand(self, zones: list[ZoneSnapshot]) -> None:
        config = self._config
        pid = config.pid
        result = evaluate_demand(
            zones,
            integral=self._integral,
            kp=pid.kp,
            ki=pid.ki,
            base_water_temp=config.base_water_temp,
            setpoint_min=config.setpoint_min,
            setpoint_max=config.setpoint_max,
            i_term_min=pid.i_term_min,
            i_term_max=pid.i_term_max,
            dt_hours=config.control_interval / 3600.0,
        )
        if result is None:
            self._go_idle("Demand zone weights unusable; setpoint 0")
            return

        critical = select_max_error_demand_zone(zones)
        # R7: skip the plant call only when the plant already reads the command
        # (_write_setpoint); ∫ advances only when the plant entity is readable.
        if not self._write_setpoint(result.command):
            return
        self._integral = result.integral
        self._log_demand_success(result, critical)

    def _log_demand_success(
        self, result: PidResult, critical: ZoneSnapshot | None
    ) -> None:
        parts = [
            f"e={result.e:.2f}",
            f"u_pid={result.u_pid:.2f}",
            f"command={result.command}",
        ]
        if critical is not None:
            parts.append(f"critical_zone={critical.name}")
        self.log(", ".join(parts))

    def _hands_off(self, message: str) -> None:
        self.log(message, level="WARNING")

    def _go_idle(self, message: str, *, level: str = "WARNING") -> None:
        self._write_setpoint(0.0)
        self._clear_pid_ephemeral()
        self.log(message, level=level)

    def _read_zones(self, config: HvacConfig) -> list[ZoneSnapshot]:
        snapshots: list[ZoneSnapshot] = []
        for zone in config.zones:
            zone_temp = self._read_float(zone.temperature)
            if zone_temp is None:
                self.log(
                    f"Zone {zone.name}: temperature unavailable ({zone.temperature})",
                    level="WARNING",
                )
                continue

            thermostats: list[ThermostatReading] = []
            for entity_id in zone.thermostats:
                setpoint = self._read_setpoint(entity_id)
                if setpoint is None:
                    self.log(
                        f"Zone {zone.name}: thermostat unavailable ({entity_id})",
                        level="WARNING",
                    )
                    continue
                thermostats.append(
                    ThermostatReading(
                        entity_id=entity_id,
                        setpoint=setpoint,
                        hvac_action=self._read_hvac_action(entity_id),
                    )
                )

            if not thermostats:
                continue

            snapshots.append(
                ZoneSnapshot(
                    name=zone.name,
                    zone_temp=zone_temp,
                    thermostats=tuple(thermostats),
                    weight=zone.weight,
                )
            )
        return snapshots

    def _read_float(self, entity_id: str) -> float | None:
        state = self.get_state(entity_id)
        if state in (None, "unavailable", "unknown"):
            return None
        try:
            value = float(state)
        except (TypeError, ValueError):
            return None
        return value if math.isfinite(value) else None

    def _read_setpoint(self, entity_id: str) -> float | None:
        value = self.get_state(entity_id, attribute="temperature")
        if value in (None, "unavailable", "unknown"):
            return None
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return None
        return parsed if math.isfinite(parsed) else None

    def _read_hvac_action(self, entity_id: str) -> str | None:
        value = self.get_state(entity_id, attribute="hvac_action")
        if value in (None, "unavailable", "unknown"):
            return None
        return str(value)

    def _write_setpoint(self, value: float) -> bool:
        entity_id = self._config.plant_setpoint
        current = self._read_float(entity_id)
        if current is None:
            self.log(
                f"Plant setpoint unavailable: {entity_id}",
                level="WARNING",
            )
            return False
        if current == value:
            return True
        self.call_service(
            "number/set_value",
            entity_id=entity_id,
            value=value,
        )
        return True
