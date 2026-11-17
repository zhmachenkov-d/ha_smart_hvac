# Demo: Story 6.1 Intent — ADR 0008 ↔ App
Generated: 2026-11-17T09:21:00+00:00

Offline spot-read (no Exclusive Session). Intent AC: ADR 0008 matches shipped App for gates / TRV / flame / Decision C; live pointers retargeted.

## 1. Live ADR + historical 0007

- [0008-weather-curve-trv-flame-swt.md](../../../../docs/adr/0008-weather-curve-trv-flame-swt.md) — `status: accepted`; agent-law MUST-floor (curve + TRV + flame; CAP-7 out).
- [0007-weather-curve-supply-trip-swt.md](../../../../docs/adr/0007-weather-curve-supply-trip-swt.md) — `status: superseded by ADR-0008`; historical supply-trip era + live-pointer.
- [0004](../../../../docs/adr/0004-weather-curve-swt.md) / [house-calibration.md](../../../../docs/house-calibration.md) — Live water law → ADR-0008; calibration L1 includes flame / `ch_active` / TRV.

## 2. Latched demand keeps SWT 0 (no curve)

ADR Clear / SWT gates: latched `_run_demand` writes `0` (no curve / no CZ select-log).

App:

```263:270:apps/ha_smart_hvac/hvac_app.py
    def _run_demand(self, zones: list[ZoneSnapshot], outdoor: float) -> None:
        """Shared demand writer for tick and every eligible control_event."""
        config = self._config
        if self._flame_trip_latched:
            plant_current = self._read_float(config.plant_setpoint)
            if not self._write_setpoint(0.0, plant_reading=plant_current):
                return
            return
```

**Match.**

## 3. Dual-gate: Outdoor prelude vs flame observe (never Outdoor)

ADR Dual-gate + Flame trip latch: `_flame_observe_gate` = Plant∧Demand∧`ch_active`∧¬latch — never Outdoor.

App:

```133:145:apps/ha_smart_hvac/hvac_app.py
    def _flame_observe_gate(self) -> bool:
        """Plant on ∧ Heating Demand ∧ ch_active on ∧ ¬latch — no Outdoor."""
        ...
        return has_heating_demand(zones)
```

Tick / event: TRV then Outdoor prelude (ADR CAP-8 / TRV soft-close):

```238:261:apps/ha_smart_hvac/hvac_app.py
    def control_tick(self, kwargs: dict) -> None:
        self._apply_trv_law()
        outcome = self._gate_prelude()
        ...
        self._run_demand(zones, outdoor)

    def control_event(...):
        self._apply_trv_law()
        outcome = self._gate_prelude()
        ...
        self._run_demand(zones, outdoor)
```

**Match.**

## 4. Hold expiry = clear → TRV → prelude → demand (zones only)

ADR Clear paths: hold expiry clears, `_apply_trv_law`, then Outdoor prelude + `_run_demand` when prelude returns zones.

App:

```160:170:apps/ha_smart_hvac/hvac_app.py
    def _flame_trip_hold_expired(self, kwargs: dict) -> None:
        """Hold elapsed: clear, TRV law, then Outdoor prelude + demand (ADV8)."""
        if kwargs.get("token") != self._flame_trip_hold_token:
            return
        self._clear_flame_trip_state()
        self._apply_trv_law()
        outcome = self._gate_prelude()
        if outcome is None:
            return
        zones, outdoor = outcome
        self._run_demand(zones, outdoor)
```

AGENTS/CONTEXT post-patch: «when prelude returns zones». **Match.**

## 5. Rising-edge clear = `_clear_flame_trip_state` (disarm + clear)

ADR Clear paths + cite `adr-zone-rising-edge-decision-a.md` (now in opening inventory).

App:

```104:105:apps/ha_smart_hvac/hvac_app.py
        if had_edge and self._flame_trip_latched:
            self._clear_flame_trip_state()
```

```147:150:apps/ha_smart_hvac/hvac_app.py
    def _clear_flame_trip_state(self) -> None:
        """Clear latch, flame-on timer, and hold (idempotent)."""
        self._flame_trip_latched = False
        self._disarm_flame_trip_hold()
```

AGENTS/CONTEXT post-patch name the helper on rising-edge. **Match.**

## 6. Decision C idle clear (live note)

ADR Idle clear + [adr-idle-flame-clear-after-write.md](../../../../docs/decisions/adr-idle-flame-clear-after-write.md): always `_disarm_flame_trip_hold`; clear latch only after successful idle write `0`.

App:

```305:309:apps/ha_smart_hvac/hvac_app.py
    def _go_idle(self, message: str, *, level: str = "WARNING") -> None:
        self._disarm_flame_trip_hold()
        if self._write_setpoint(0.0):
            self._flame_trip_latched = False
        self.log(message, level=level)
```

Plant-off: `_hands_off` → `_clear_flame_trip_state` (no SWT write) — ADR SWT gates. **Match.**

Historical supply-era idle note banners + forward link to live Decision C — [adr-idle-trip-clear-after-write.md](../../../../docs/decisions/adr-idle-trip-clear-after-write.md).

## Verdict

Intent spot-read: ADR 0008 MUST-floor aligns with `hvac_app.py` for latched demand, dual-gate, hold expiry, rising-edge clear, Decision C, and plant-off. Live pointers / historical banners / post-patch AGENTS·CONTEXT wording consistent with that law. No Exclusive Session / runtime exercise (docs-only story).
