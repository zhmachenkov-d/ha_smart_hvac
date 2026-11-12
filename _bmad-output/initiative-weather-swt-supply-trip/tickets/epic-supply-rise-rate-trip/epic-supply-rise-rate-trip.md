---
type: epic
title: "Supply rise-rate trip"
parent: initiative-weather-swt-supply-trip
covers: ["R5", "R6", "R7"]
sources:
  - _bmad-output/initiative-weather-swt-supply-trip/initiative-weather-swt-supply-trip.md
companions: []
after: []
refined: true
risk: high
---

# Supply rise-rate trip

## Description

Add a supply-water rise-rate trip on top of the restored weather-curve demand path: under Plant Management on and Heating Demand, on every supply temperature change compute `r_obs` (°C/min); if `r_obs > r_max` (yaml, default 2 °C/min) latch and write SWT `0` until the latch clears — the weather curve is not applied while latched. Clear when the yaml hold timer elapses (default 900 s) or when Heating Demand appears on a zone that previously had none. Supply entity is yaml-commissioned (`boiler_water` = house OpenTherm boiler water sensor, already decided). Idle / plant-off clear the latch and supply sample history (trip-state owns the clear that was vacuous after PID detach).

## Outcome

When supply rises faster than `r_max` under demand, the App latches SWT to `0` until hold expiry or a zone rising-edge into Heating Demand restores the weather-curve path.

## Requirements

1. **R5 (parent R5):** Under Plant Management on and Heating Demand, on every supply temperature change the App computes `r_obs` from supply (°C/min); if `r_obs > r_max` (yaml, default 2 °C/min) it latches and writes SWT `0` until the latch clears — the weather curve is not applied while latched.
2. **R6 (parent R6):** The latch clears when the yaml hold timer elapses (default 900 s) or when Heating Demand appears on a zone that previously had none (zone rising-edge); after clear, demand SWT again follows R1 when gates allow.
3. **R7 (parent R7):** Supply temperature is read from a yaml-commissioned entity; Outdoor Temperature returns to the weather-curve SWT path and commissioning.

## Constraints

1. **C1 (parent C1):** Implementation stays inside the AppDaemon `ha_smart_hvac` App writing the existing HA plant Set Water Temperature entity.
2. **C2 (parent C2):** Exclusive Session (ADR 0001) and Heating Demand via thermostat `hvac_action=heating` are unchanged.
3. **C3 (parent C3):** SWT uses round-to-0.1 and clamp into existing `setpoint_min` / `setpoint_max` only.
4. **C4 (parent C4):** Critical Zone must not drive Set Water Temperature or the supply rise-rate trip.
5. **C5 (parent C5):** Supply (and Outdoor) entity ids are yaml-commissioned; house entity ids are not hardcoded and house `apps.yaml` changes require owner confirmation.
6. **C6 (parent C6):** CAP-7 / adapting `base`/`slope` / `ff_auto_correct_state.json` are out of scope for this initiative.

## Done when

1. Under Plant Management on and Heating Demand, every supply temperature change with two successive valid samples yields `r_obs`; `r_obs > r_max` latches and writes SWT `0`.
2. While latched under demand, the weather curve is not applied; demand path keeps commanding `0` (equal-float plant readback skip remains the write throttle).
3. Latch clears after hold timer (default 900 s from latch moment) or zone rising-edge Heating Demand; idle write-`0` and plant-off (no write) also clear latch and supply sample history; after clear, demand SWT follows the weather curve when gates allow.
4. Supply entity is yaml-commissioned (`boiler_water`); house entity id confirmed (`sensor.opentherm_bridge_boiler_water_temperature_degc`); latch is RAM-only (reload clears it).
5. Automated tests lock trip latch, clear paths (hold, rising-edge, idle, plant-off), and interaction with the weather-curve demand path.

## Boundaries

Owns supply rise-rate observation, latch/hold/clear, trip-state clear on idle/plant-off, and supply yaml commission on the SWT path. Does not own weather-curve restore (epic 1) or ADR/domain-doc supersede / dead PID cleanup (epic 3). Critical Zone must not drive the trip. CAP-7 stays out.

- Touch point: `apps/ha_smart_hvac/` — supply listener, `r_obs`, latch state, hold timer, zone rising-edge clear, idle/plant-off trip clear; owner: this epic
- Touch point: `apps/apps.yaml` / `apps.yaml.example` — `boiler_water`, `r_max`, hold; owner: this epic
- Must not change: Exclusive Session; Heating Demand definition; weather-curve formula from epic 1; CAP-8 shared FF demand writer contract (trip gates it)
- Must not: drive trip from Critical Zone; restore CAP-7; persist latch to JSON

## References

- parent — `_bmad-output/initiative-weather-swt-supply-trip/initiative-weather-swt-supply-trip.md`, Requirements R5–R7 (R7 supply); Constraints C1–C6
- sibling — `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-weather-curve-swt-restore/epic-weather-curve-swt-restore.md`
- decision — `docs/decisions/adr-cap8-shared-ff-demand-writer.md` (trip must gate the shared FF writer)
- decision — `docs/decisions/adr-vacuous-clear-after-pid-detach.md` (this epic owns trip-state clear)

## Notes

- Waits on epic-weather-curve-swt-restore because: weather-curve demand SWT path and Outdoor control listener must be live under Plant/Demand gates before the trip layers on.
- Handoff: epic-supersede-pid-domain-docs waits on this epic’s shipped trip so ADR/CONTEXT/AGENTS match the App.
- Shared covers: R7 with epic 1 (supply entity here; Outdoor+FF there).
- Decision: Slice approved — trip is second epic after weather-curve restore (2026-11-11).
- Decision: Refine from parent covers only — no extra companions before stories (2026-11-12).
- Decision: R7 scope here — supply entity (`boiler_water`) commission and listener; Outdoor+FF already epic 1 (2026-11-12).
- Decision: Latch is RAM-only — no trip JSON; AppDaemon reload clears latch (2026-11-12).
- Decision: Idle write-`0` and plant-off (no write) clear latch and supply sample history (2026-11-12).
- Decision: `r_obs` needs two successive valid samples under gated demand; unreadable/non-finite supply → WARN, no trip, does not auto-clear an existing latch (2026-11-12).
- Decision: While latched under demand, demand path writes SWT `0` (equal-float skip); weather curve not applied (2026-11-12).
- Decision: Hold timer runs from latch moment; clear cancels it (2026-11-12).
- Decision: House HITL — entity already Q2-confirmed and present in house yaml; this epic commissions example + parse_config accept; house check that `boiler_water` is accepted (not ignored), no id change (2026-11-12).
- Decision: Stories approved — tracer = config + supply listener + r_obs + latch/hold + gate CAP-8 FF writer + example; rising-edge clear separate (least certain); house accept HITL; refactor sweep; no closing e2e suite (2026-11-12).
- Decision: Tracer bullet is entry 1 «Tracer: supply rise-rate trip» (2026-11-12).
- Decision: Yaml keys top-level `boiler_water`, `r_max` (default 2), `hold` (default 900) — not under `weather_feedforward` (2026-11-12).
- Decision: Shared R6 — entry 1 delivers hold/idle/plant-off clears; entry 2 delivers zone rising-edge clear (2026-11-12).
- Decision: Shared R7 — entry 1 delivers example + parse accept; entry 3 delivers house accept-check (2026-11-12).
