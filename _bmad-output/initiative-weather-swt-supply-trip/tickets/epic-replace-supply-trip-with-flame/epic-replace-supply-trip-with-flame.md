---
type: epic
title: "Replace supply trip with flame short-on"
parent: initiative-weather-swt-supply-trip
covers: ["R11", "R12", "R1"]
sources:
  - _bmad-output/initiative-weather-swt-supply-trip/initiative-weather-swt-supply-trip.md
  - _bmad-output/initiative-weather-swt-supply-trip/forge-trv-valve-closure-anti-cycle/forge-trv-valve-closure-anti-cycle.md
companions: []
after: []
refined: false
risk: high
---

# Replace supply trip with flame short-on

## Description
Remove the supply rise-rate trip (`r_obs` / `r_max` / `boiler_water` trip path) from code, yaml, and tests, and replace it with a flame short-on SWT trip: under Plant on ∧ Heating Demand ∧ `ch_active` ∧ latch clear, if `flame_on` True duration &lt; `flame_on_min_s`, attempt SWT `0` and latch only after successful write. Clear on hold, zone rising-edge, plant-off, or successful idle write-0 (Decision C). While latched, weather curve is not applied; TRV soft-close from epic 4 keeps running.

## Outcome
Plant anti-cycle is flame short-on latching SWT to 0 (not supply rise-rate); after clear, demand SWT follows the weather curve again when gates allow.

## Done when
1. Supply rise-rate trip path is gone from App, config models, example yaml, and tests.
2. Flame observe gate + short-on duration trip latches SWT `0` only after successful write; while latched, demand keeps `0`.
3. Latch clears on hold, zone rising-edge, plant-off, or successful idle write-0; then R1 when gates allow.
4. TRV soft-close continues while flame-latched; house yaml commissions confirmed `flame_on` / `ch_active`.
5. Automated tests lock remove + flame latch/clear and interaction with weather-curve demand.

## Boundaries
Owns supply-trip removal and flame short-on observe/latch/clear on the SWT path, plus `flame_on` / `ch_active` / `flame_on_min_s` / `flame_trip_hold_s` yaml. Does not own TRV soft-close (epic 4) or ADR/docs (epic 6). Must not restore supply rise-rate trip.

- Touch point: `apps/ha_smart_hvac/` — remove supply trip; flame latch; gate CAP-8 FF writer; owner: this epic
- Touch point: `apps/apps.yaml` / `apps.yaml.example` — remove trip keys; add flame entities/defaults; owner: this epic
- Must not change: Exclusive Session; Heating Demand definition; TRV soft-close behavior from epic 4

## References
- parent — `_bmad-output/initiative-weather-swt-supply-trip/initiative-weather-swt-supply-trip.md`, Requirements R11–R12 and R1 latch; Constraints C1–C6
- source — `_bmad-output/initiative-weather-swt-supply-trip/forge-trv-valve-closure-anti-cycle/forge-trv-valve-closure-anti-cycle.md`
- sibling — `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-trv-idle-max-close/epic-trv-idle-max-close.md`

## Notes
- Waits on epic-trv-idle-max-close because: TRV soft-close primary anti-cycle must be live before supply trip is removed.
- Shared covers: R1 with epic 1 (weather formula there; flame latch gate here).
- Decision: Envelope approved thin (`refined: false`) — remove+flame one epic (2026-11-15); refine before stories.
