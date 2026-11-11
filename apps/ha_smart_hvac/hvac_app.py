"""HVAC App — outdoor weather-curve Set Water Temperature loop."""

from __future__ import annotations

import math

import appdaemon.plugins.hass.hassapi as hass

from ha_smart_hvac.config import ConfigError, parse_config
from ha_smart_hvac.coordinator import has_heating_demand, select_max_error_demand_zone
from ha_smart_hvac.feedforward import quantize_command, weather_feedforward
from ha_smart_hvac.models import (
    HvacConfig,
    ThermostatReading,
    ZoneSnapshot,
    plant_management_enabled,
)

# Sentinel: _write_setpoint re-reads plant when plant_reading is omitted.
_READ_PLANT = object()


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

        self._register_control_listeners()
        self.run_every(
            self.control_tick,
            "now",
            self._config.control_interval,
        )
        # Explicit first tick: AD "now" schedules the first periodic fire at
        # now+interval, not immediately.
        self.control_tick({})
        self.log("HVAC weather-curve SWT app initialized")

    def _register_control_listeners(self) -> None:
        """Re-evaluate gate on plant / outdoor / zone air / thermostat attrs."""
        config = self._config
        self.listen_state(self.control_event, config.plant_management)
        self.listen_state(self.control_event, config.outdoor_temperature)
        for zone in config.zones:
            self.listen_state(self.control_event, zone.temperature)
            for entity_id in zone.thermostats:
                self.listen_state(
                    self.control_event, entity_id, attribute="hvac_action"
                )
                self.listen_state(
                    self.control_event, entity_id, attribute="temperature"
                )

    def _gate_prelude(self) -> tuple[list[ZoneSnapshot], float] | None:
        """Plant / Outdoor / Heating Demand prelude. (zones, outdoor) or None."""
        config = self._config

        if not plant_management_enabled(self.get_state(config.plant_management)):
            self._hands_off("Plant Management disabled")
            return None

        outdoor = self._read_float(config.outdoor_temperature)
        if outdoor is None:
            self._go_idle(
                f"Outdoor temperature unavailable: {config.outdoor_temperature}"
            )
            return None

        zones = self._read_zones(config)
        if not zones:
            self._go_idle("No zones with valid readings this tick")
            return None

        if not has_heating_demand(zones):
            self._go_idle("No heating demand; setpoint 0", level="INFO")
            return None

        return zones, outdoor

    def control_tick(self, kwargs: dict) -> None:
        outcome = self._gate_prelude()
        if outcome is None:
            return
        zones, outdoor = outcome
        self._run_demand(zones, outdoor)

    def control_event(
        self,
        entity: str,
        attribute: str,
        old: object,
        new: object,
        kwargs: dict,
    ) -> None:
        """Event entry: shared prelude + FF demand writer (no sticky latch)."""
        # listen_state args ignored — re-read current Hass state in prelude.
        outcome = self._gate_prelude()
        if outcome is None:
            return
        zones, outdoor = outcome
        self._run_demand(zones, outdoor)

    def _run_demand(self, zones: list[ZoneSnapshot], outdoor: float) -> None:
        """Shared FF demand writer for tick and every eligible control_event."""
        config = self._config
        u_ff = weather_feedforward(outdoor, config.weather_feedforward)
        if not math.isfinite(u_ff):
            self._go_idle(f"Non-finite weather feedforward u_ff for outdoor={outdoor}")
            return

        command = quantize_command(u_ff, config.setpoint_min, config.setpoint_max)
        plant_current = self._read_float(config.plant_setpoint)
        # R7: skip plant call when equal; no PID / RLS on FF demand path.
        if not self._write_setpoint(command, plant_reading=plant_current):
            return
        critical = select_max_error_demand_zone(zones)
        self._log_demand_success(outdoor, u_ff, command, critical)

    def _log_demand_success(
        self,
        outdoor: float,
        u_ff: float,
        command: float,
        critical: ZoneSnapshot | None,
    ) -> None:
        parts = [
            f"outdoor={outdoor:.2f}",
            f"u_ff={u_ff:.2f}",
            f"command={command}",
        ]
        if critical is not None:
            parts.append(f"critical_zone={critical.name}")
        self.log(", ".join(parts))

    def _hands_off(self, message: str) -> None:
        self.log(message, level="WARNING")

    def _go_idle(self, message: str, *, level: str = "WARNING") -> None:
        self._write_setpoint(0.0)
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

    def _write_setpoint(
        self, value: float, *, plant_reading: object = _READ_PLANT
    ) -> bool:
        """Write plant setpoint; pass ``plant_reading`` to reuse a demand snapshot."""
        entity_id = self._config.plant_setpoint
        current = (
            self._read_float(entity_id)
            if plant_reading is _READ_PLANT
            else plant_reading  # float | None from caller snapshot
        )
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
