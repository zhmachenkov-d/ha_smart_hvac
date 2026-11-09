"""HVAC App — fixed-gain PID Set Water Temperature loop."""

from __future__ import annotations

import math
from pathlib import Path

import appdaemon.plugins.hass.hassapi as hass

from ha_smart_hvac.config import ConfigError, parse_config
from ha_smart_hvac.coordinator import has_heating_demand, select_max_error_demand_zone
from ha_smart_hvac.models import (
    HvacConfig,
    ThermostatReading,
    ZoneSnapshot,
    plant_management_enabled,
)
from ha_smart_hvac.pid import PidResult, evaluate_demand, weighted_error
from ha_smart_hvac.rls import (
    STATE_FILENAME,
    RlsDurableSnapshot,
    RlsState,
    copy_durable,
    durable_equal,
    gains_within_rails,
    imc_gains,
    load_rls_state,
    rls_step,
    save_rls_state,
)

# Sentinel: _write_setpoint re-reads plant when plant_reading is omitted.
_READ_PLANT = object()

# Latch reason codes (mutually exclusive; evaluation order in _maybe_rls_step).
_REASON_RLS_NOOP = "rls_noop"
_REASON_IMC_NONE = "imc_none"
_REASON_OUT_OF_BAND = "out_of_band"


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
        if self._config.pid.legacy_ki_warning:
            self.log(
                f"HVAC config: pid.ki={self._config.pid.ki:g} looks like legacy "
                "per-second scale (0 < ki < 1); expected 1/h — not auto-migrated",
                level="WARNING",
            )

        self._integral = 0.0
        self._rls = RlsState()
        self._rls_fallback_latched = False
        self._rls_fallback_reason: str | None = None
        self._rls_last_saved = copy_durable(self._rls)
        self._rls_force_rewrite = False
        self._rls_persist_fail_warned = False
        if self._config.pid.adaptive:
            self._load_rls_overlay()

        self._register_control_listeners()
        self.run_every(
            self.control_tick,
            "now",
            self._config.control_interval,
        )
        self.log("HVAC fixed-gain PID app initialized")

    def _state_path(self) -> Path:
        return Path(self.app_dir) / STATE_FILENAME

    def _seed_last_saved(self) -> None:
        self._rls_last_saved = copy_durable(self._rls)

    def _apply_loaded_adapted(self, loaded: RlsDurableSnapshot) -> None:
        """OQ6 B: overlay adapted or drop with reason WARNING + force."""
        pid = self._config.pid
        issue = loaded.adapted_issue
        kp, ki = loaded.adapted_kp, loaded.adapted_ki
        if issue is None and kp is not None and ki is not None:
            assert pid.kp_min is not None and pid.kp_max is not None
            assert pid.ki_min is not None and pid.ki_max is not None
            if not gains_within_rails(
                kp, ki, pid.kp_min, pid.kp_max, pid.ki_min, pid.ki_max
            ):
                issue = "out_of_rail"
                kp, ki = None, None
        if issue is not None:
            self._rls.adapted_kp = None
            self._rls.adapted_ki = None
            self._rls_force_rewrite = True
            self.log(
                f"RLS state adapted gains dropped on load ({issue})",
                level="WARNING",
            )
            return
        self._rls.adapted_kp = kp
        self._rls.adapted_ki = ki

    def _load_rls_overlay(self) -> None:
        """Adaptive-on initialize: overlay durable fields from rls_state.json."""
        path = self._state_path()
        if not path.is_file():
            self._seed_last_saved()
            return
        loaded = load_rls_state(path)
        if loaded is None:
            self.log(
                f"Ignoring unusable RLS state file: {path}",
                level="WARNING",
            )
            self._rls_force_rewrite = True
            self._seed_last_saved()
            return
        if (
            imc_gains(
                loaded.theta[0],
                loaded.theta[1],
                float(self._config.control_interval),
            )
            is None
        ):
            self.log(
                f"Ignoring RLS state with IMC-invalid theta: {path}",
                level="WARNING",
            )
            self._rls_force_rewrite = True
            self._seed_last_saved()
            return

        self._rls.theta = [loaded.theta[0], loaded.theta[1]]
        self._rls.p = [
            [loaded.p[0][0], loaded.p[0][1]],
            [loaded.p[1][0], loaded.p[1][1]],
        ]
        self._rls.last_u = loaded.last_u
        # y_prev stays None; latch stays False (process-local).
        self._apply_loaded_adapted(loaded)
        self.log(f"Loaded RLS state from {path}")
        self._seed_last_saved()

    def _maybe_persist_rls(self) -> None:
        """Save durable RLS after successful demand write when dirty or forced."""
        if not self._config.pid.adaptive:
            return
        snap = copy_durable(self._rls)
        if not self._rls_force_rewrite and durable_equal(snap, self._rls_last_saved):
            return
        path = self._state_path()
        if save_rls_state(path, self._rls):
            self._rls_last_saved = snap
            self._rls_force_rewrite = False
            self._rls_persist_fail_warned = False
            return
        if not self._rls_persist_fail_warned:
            self.log(
                f"Failed to persist RLS state: {path}",
                level="WARNING",
            )
            self._rls_persist_fail_warned = True

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
        # Wipe y_prev only among RLS bookkeeping; keep θ/P, last u, parked
        # adapted_*, and the fallback latch (parked gains ignored while latched).
        self._rls.y_prev = None

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

    def _gains_for_demand(self) -> tuple[float, float]:
        pid = self._config.pid
        # Latched unhealthy/OOB → YAML fixed until healthy in-band publish.
        if self._rls_fallback_latched:
            return pid.kp, pid.ki
        rls = self._rls
        if pid.adaptive and rls.adapted_kp is not None and rls.adapted_ki is not None:
            return rls.adapted_kp, rls.adapted_ki
        return pid.kp, pid.ki

    def _enter_rls_fallback(
        self,
        reason: str,
        *,
        proposed: tuple[float, float] | None = None,
    ) -> None:
        """Latch demand onto YAML fixed; WARN once on enter or reason change."""
        prior = self._rls_fallback_reason if self._rls_fallback_latched else None
        self._rls_fallback_latched = True
        self._rls_fallback_reason = reason
        if prior == reason:
            return
        pid = self._config.pid
        if reason == _REASON_OUT_OF_BAND and proposed is not None:
            kp, ki = proposed
            self.log(
                f"RLS fallback latched: {reason}; proposed kp={kp:g} ki={ki:g}; "
                f"rails kp=[{pid.kp_min:g},{pid.kp_max:g}] "
                f"ki=[{pid.ki_min:g},{pid.ki_max:g}]",
                level="WARNING",
            )
        else:
            self.log(
                f"RLS fallback latched: {reason}; using yaml fixed kp/ki",
                level="WARNING",
            )

    def _clear_rls_fallback(self) -> None:
        self._rls_fallback_latched = False
        self._rls_fallback_reason = None

    def _maybe_rls_step(self, *, plant_ok: bool) -> None:
        """Step RLS at most once on a demand tick when priors and y allow it."""
        config = self._config
        pid = config.pid
        entity_id = config.boiler_water
        assert entity_id is not None  # parse requires it when adaptive
        y = self._read_float(entity_id)
        if y is None:
            self.log(f"Boiler water unavailable: {entity_id}", level="WARNING")
            return

        rls = self._rls
        y_prev = rls.y_prev
        can_step = plant_ok and y_prev is not None and rls.last_u is not None
        if can_step:
            stepped = rls_step(rls, y=y, y_prev=y_prev, u_prev=rls.last_u)
            if not stepped:
                # Park adapted_* (leave as-is); latch → YAML fixed.
                self._enter_rls_fallback(_REASON_RLS_NOOP)
            else:
                # θ/P committed; accept adapted only when IMC finite + in-band.
                gains = imc_gains(
                    rls.theta[0], rls.theta[1], float(config.control_interval)
                )
                if (
                    gains is None
                    or not math.isfinite(gains[0])
                    or not math.isfinite(gains[1])
                ):
                    self._enter_rls_fallback(_REASON_IMC_NONE)
                else:
                    assert pid.kp_min is not None and pid.kp_max is not None
                    assert pid.ki_min is not None and pid.ki_max is not None
                    if not gains_within_rails(
                        gains[0],
                        gains[1],
                        pid.kp_min,
                        pid.kp_max,
                        pid.ki_min,
                        pid.ki_max,
                    ):
                        self._enter_rls_fallback(_REASON_OUT_OF_BAND, proposed=gains)
                    else:
                        rls.adapted_kp, rls.adapted_ki = gains
                        self._clear_rls_fallback()
        # Finite y always seeds/refreshes; plant-unreadable / missing u only skip step.
        # Skip-step paths do not enter or refresh the latch.
        rls.y_prev = y

    def _run_demand(self, zones: list[ZoneSnapshot]) -> None:
        config = self._config
        pid = config.pid
        # Weights-unusable clear must not step RLS (I/O matrix / AC).
        if weighted_error(zones) is None:
            self._go_idle("Demand zone weights unusable; setpoint 0")
            return
        # One plant snapshot per demand tick: RLS gate and write share it (no TOCTOU).
        plant_current = self._read_float(config.plant_setpoint)
        if pid.adaptive:
            self._maybe_rls_step(plant_ok=plant_current is not None)
        kp, ki = self._gains_for_demand()
        result = evaluate_demand(
            zones,
            integral=self._integral,
            kp=kp,
            ki=ki,
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
        if not self._write_setpoint(result.command, plant_reading=plant_current):
            return
        self._integral = result.integral
        # Last demand u: write True only (incl. equal-float skip); never idle 0.
        self._rls.last_u = result.command
        self._maybe_persist_rls()
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
