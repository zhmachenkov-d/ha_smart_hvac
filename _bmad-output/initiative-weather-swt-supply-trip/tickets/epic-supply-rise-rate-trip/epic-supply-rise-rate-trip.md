---
type: epic
title: "Supply rise-rate trip"
parent: initiative-weather-swt-supply-trip
covers: ["R5", "R6", "R7"]
sources:
  - _bmad-output/initiative-weather-swt-supply-trip/initiative-weather-swt-supply-trip.md
companions: []
after: []
refined: false
risk: high
---

# Supply rise-rate trip

## Description

Add a supply-water rise-rate trip on top of the restored weather-curve demand path: under Plant Management on and Heating Demand, on every supply temperature change compute `r_obs` (°C/min); if `r_obs > r_max` (yaml, default 2 °C/min) latch and write SWT `0` until the latch clears — the weather curve is not applied while latched. Clear when the yaml hold timer elapses (default 900 s) or when Heating Demand appears on a zone that previously had none. Supply entity is yaml-commissioned (`boiler_water` = house OpenTherm boiler water sensor, already decided).

## Outcome

When supply rises faster than `r_max` under demand, the App latches SWT to `0` until hold expiry or a zone rising-edge into Heating Demand restores the weather-curve path.

## Done when

1. Under Plant Management on and Heating Demand, every supply temperature change yields `r_obs`; `r_obs > r_max` latches and writes SWT `0`.
2. While latched under demand, the weather curve is not applied.
3. Latch clears after hold timer (default 900 s) or zone rising-edge Heating Demand; after clear, demand SWT follows the weather curve when gates allow.
4. Supply entity is yaml-commissioned; house entity id confirmed (`sensor.opentherm_bridge_boiler_water_temperature_degc`).
5. Automated tests lock trip latch, clear paths, and interaction with the weather-curve demand path.

## Boundaries

Owns supply rise-rate observation, latch/hold/clear, and supply yaml commission on the SWT path. Does not own weather-curve restore (epic 1) or ADR/domain-doc supersede / dead PID cleanup (epic 3). Critical Zone must not drive the trip. CAP-7 stays out.

- Touch point: `apps/ha_smart_hvac/` — supply listener, `r_obs`, latch state, hold timer, zone rising-edge clear; owner: this epic
- Touch point: `apps/apps.yaml` / `apps.yaml.example` — `boiler_water`, `r_max`, hold; owner: this epic
- Must not change: Exclusive Session; Heating Demand definition; weather-curve formula from epic 1
- Must not: drive trip from Critical Zone; restore CAP-7

## References

- parent — `_bmad-output/initiative-weather-swt-supply-trip/initiative-weather-swt-supply-trip.md`, Requirements R5–R7 (R7 supply); Constraints C1–C6
- sibling — `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-weather-curve-swt-restore/epic-weather-curve-swt-restore.md`

## Notes

- Waits on epic-weather-curve-swt-restore because: weather-curve demand SWT path and Outdoor control listener must be live under Plant/Demand gates before the trip layers on.
- Handoff: epic-supersede-pid-domain-docs waits on this epic’s shipped trip so ADR/CONTEXT/AGENTS match the App.
- Shared covers: R7 with epic 1 (supply entity here; Outdoor+FF there).
- Decision: Slice approved — trip is second epic after weather-curve restore (2026-11-11).
