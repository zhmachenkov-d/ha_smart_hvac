"""HVAC App — 60 s weather-curve Set Water Temperature loop."""

from __future__ import annotations

from pathlib import Path

import appdaemon.plugins.hass.hassapi as hass

from ha_smart_hvac.config import ConfigError, parse_config
from ha_smart_hvac.coordinator import has_heating_demand
from ha_smart_hvac.feedforward import weather_feedforward
from ha_smart_hvac.ff_auto_correct import (
    STATE_FILENAME,
    FfAutoCorrector,
    load_ff_state,
    save_ff_state,
)
from ha_smart_hvac.models import (
    HvacConfig,
    ThermostatReading,
    ZoneSnapshot,
    plant_management_enabled,
)


class HvacApp(hass.Hass):
    def initialize(self) -> None:
        try:
            self._config: HvacConfig = parse_config(self.args)
        except ConfigError as exc:
            self.log(f"HVAC config error: {exc}", level="ERROR")
            return

        self._ff_auto_correct = self._build_corrector()
        self._load_ff_overlay()

        self.run_every(
            self.control_tick,
            "now",
            self._config.control_interval,
        )
        self.log("HVAC weather-curve app initialized")

    def control_tick(self, kwargs: dict) -> None:
        config = self._config
        corrector = self._ensure_corrector()

        if not plant_management_enabled(self.get_state(config.plant_management)):
            corrector.clear_ephemeral()
            self._hands_off("Plant Management disabled")
            return

        outdoor = self._read_float(config.outdoor_temperature)
        if outdoor is None:
            corrector.clear_ephemeral()
            self._go_idle(
                f"Outdoor temperature unavailable: {config.outdoor_temperature}"
            )
            return

        zones = self._read_zones(config)
        if not zones:
            corrector.clear_ephemeral()
            self._go_idle("No zones with valid readings this tick")
            return

        if not has_heating_demand(zones):
            corrector.clear_ephemeral()
            self._write_setpoint(0.0)
            self.log("No heating demand; setpoint 0")
            return

        result = corrector.process_demand(zones, outdoor)
        write_ok = self._write_setpoint(result.command)
        if result.params_changed and write_ok:
            self._persist_ff_state()
        if not write_ok:
            return
        u_ff = weather_feedforward(outdoor, corrector.ff_config())
        self.log(
            f"outdoor={outdoor:.2f} °C, u_ff={u_ff:.2f}, command={result.command:.2f}"
        )

    def _build_corrector(self) -> FfAutoCorrector:
        config = self._config
        ff = config.weather_feedforward
        return FfAutoCorrector(
            auto_correct=config.auto_correct,
            control_interval=config.control_interval,
            base=ff.base,
            slope=ff.slope,
            comfort_ref=ff.comfort_ref,
            setpoint_min=config.setpoint_min,
            setpoint_max=config.setpoint_max,
        )

    def _ensure_corrector(self) -> FfAutoCorrector:
        if not hasattr(self, "_ff_auto_correct"):
            self._ff_auto_correct = self._build_corrector()
        return self._ff_auto_correct

    def _state_path(self) -> Path:
        return Path(self.app_dir) / STATE_FILENAME

    def _load_ff_overlay(self) -> None:
        path = self._state_path()
        loaded = load_ff_state(path)
        if loaded is None:
            if path.exists():
                self.log(
                    f"Ignoring invalid FF auto-correct state: {path}",
                    level="WARNING",
                )
            else:
                self.log(
                    f"FF auto-correct state missing ({path}); using yaml commission",
                    level="WARNING",
                )
            return
        base, slope = loaded
        self._ff_auto_correct.base = base
        self._ff_auto_correct.slope = slope
        self.log(f"Loaded FF auto-correct overlay from {path}")

    def _persist_ff_state(self) -> None:
        corrector = self._ff_auto_correct
        save_ff_state(self._state_path(), corrector.base, corrector.slope)

    def _hands_off(self, message: str) -> None:
        self.log(message, level="WARNING")

    def _go_idle(self, message: str) -> None:
        self._write_setpoint(0.0)
        self.log(message, level="WARNING")

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
                )
            )
        return snapshots

    def _read_float(self, entity_id: str) -> float | None:
        state = self.get_state(entity_id)
        if state in (None, "unavailable", "unknown"):
            return None
        try:
            return float(state)
        except (TypeError, ValueError):
            return None

    def _read_setpoint(self, entity_id: str) -> float | None:
        value = self.get_state(entity_id, attribute="temperature")
        if value in (None, "unavailable", "unknown"):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

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
