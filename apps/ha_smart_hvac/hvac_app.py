"""HVAC App — outdoor weather-curve Set Water Temperature loop."""

from __future__ import annotations

import math
import time
from collections.abc import Callable

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

        self._monotonic: Callable[[], float] = time.monotonic
        self._supply_trip_latched = False
        self._supply_sample: tuple[float, float] | None = None
        self._trip_hold_handle: object | None = None
        self._trip_hold_token = 0
        self._zone_heating_prior: dict[str, bool] = {}

        self._register_control_listeners()
        self.listen_state(self.supply_event, self._config.boiler_water)
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
            # Empty read: leave per-zone Heating Demand prior unchanged.
            self._go_idle("No zones with valid readings this tick")
            return None

        had_edge = self._detect_and_update_zone_heating_prior(zones)

        if not has_heating_demand(zones):
            self._go_idle("No heating demand; setpoint 0", level="INFO")
            return None

        if had_edge and self._supply_trip_latched:
            self._clear_trip_state()

        return zones, outdoor

    def _detect_and_update_zone_heating_prior(self, zones: list[ZoneSnapshot]) -> bool:
        """Detect per-zone False→True Heating Demand; update prior.

        Missing snapshot for a configured zone → current False (Decision A).
        Empty prior → seed from currents and return False (no clear).
        Only prior keys already present with value False count as an edge.
        """
        by_name = {z.name: z for z in zones}
        current: dict[str, bool] = {}
        for zone in self._config.zones:
            snap = by_name.get(zone.name)
            current[zone.name] = (
                snap.has_heating_eligible if snap is not None else False
            )

        prior = self._zone_heating_prior
        if not prior:
            self._zone_heating_prior = current
            return False

        had_edge = any(current[name] and prior.get(name) is False for name in current)
        self._zone_heating_prior = current
        return had_edge

    def _plant_and_heating_demand(self) -> bool:
        """Plant on ∧ Heating Demand — no Outdoor read (supply path gate)."""
        config = self._config
        if not plant_management_enabled(self.get_state(config.plant_management)):
            return False
        zones = self._read_zones(config)
        if not zones:
            return False
        return has_heating_demand(zones)

    def _clear_trip_state(self) -> None:
        """Clear latch, supply samples, and hold timer (idempotent)."""
        self._supply_trip_latched = False
        self._disarm_trip_hold()

    def _disarm_trip_hold(self) -> None:
        """Cancel hold timer and wipe samples; invalidate pending hold callbacks."""
        self._supply_sample = None
        self._trip_hold_token += 1
        if self._trip_hold_handle is not None:
            self.cancel_timer(self._trip_hold_handle)
            self._trip_hold_handle = None

    def _trip_hold_expired(self, kwargs: dict) -> None:
        """Hold elapsed: clear trip RAM, then re-run Outdoor prelude + demand."""
        if kwargs.get("token") != self._trip_hold_token:
            return
        self._clear_trip_state()
        outcome = self._gate_prelude()
        if outcome is None:
            return
        zones, outdoor = outcome
        self._run_demand(zones, outdoor)

    def supply_event(
        self,
        entity: str,
        attribute: str,
        old: object,
        new: object,
        kwargs: dict,
    ) -> None:
        """Supply rise-rate trip — Plant∧Demand only; never Outdoor prelude."""
        if not self._plant_and_heating_demand():
            self._supply_sample = None
            return

        config = self._config
        supply = self._read_float(config.boiler_water)
        if supply is None:
            self.log(
                f"Supply temperature unreadable: {config.boiler_water}",
                level="WARNING",
            )
            return

        now = self._monotonic()
        prev = self._supply_sample
        if prev is not None:
            t_prev, temp_prev = prev
            dt_s = now - t_prev
            if dt_s <= 0:
                self.log(
                    "Supply rise-rate: non-positive sample interval; keeping latest",
                    level="WARNING",
                )
                self._supply_sample = (now, supply)
                return
            r_obs = (supply - temp_prev) / (dt_s / 60.0)
            if r_obs > config.r_max:
                if self._supply_trip_latched:
                    self._write_setpoint(0.0)
                    self._supply_sample = (now, supply)
                    return
                if self._write_setpoint(0.0):
                    self._supply_trip_latched = True
                    token = self._trip_hold_token + 1
                    self._trip_hold_token = token
                    self._trip_hold_handle = self.run_in(
                        self._trip_hold_expired, config.hold, token=token
                    )
                    self.log(
                        f"Supply rise-rate trip: r_obs={r_obs:.2f} °C/min > "
                        f"r_max={config.r_max:.2f} °C/min; latching SWT 0",
                        level="WARNING",
                    )
                    self._supply_sample = (now, supply)
                    return
                self.log(
                    f"Supply rise-rate trip: r_obs={r_obs:.2f} °C/min > "
                    f"r_max={config.r_max:.2f} °C/min; SWT write failed, "
                    "not latching",
                    level="WARNING",
                )
                return

        self._supply_sample = (now, supply)

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
        """Shared demand writer for tick and every eligible control_event."""
        config = self._config
        if self._supply_trip_latched:
            plant_current = self._read_float(config.plant_setpoint)
            if not self._write_setpoint(0.0, plant_reading=plant_current):
                return
            return

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
        self._clear_trip_state()
        self.log(message, level="WARNING")

    def _go_idle(self, message: str, *, level: str = "WARNING") -> None:
        self._disarm_trip_hold()
        if self._write_setpoint(0.0):
            self._supply_trip_latched = False
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
