---
type: epic
title: "TRV house-idle soft-close"
parent: initiative-weather-swt-supply-trip
covers: ["R9", "R10"]
sources:
  - _bmad-output/initiative-weather-swt-supply-trip/initiative-weather-swt-supply-trip.md
companions: []
after: []
refined: false
risk: high
---

# TRV house-idle soft-close
## Description
Replace the live plant-on floor + temperature-overshoot soft-close with house-idle soft-close: when no zone has Heating Demand, commissioned Sonoff TRVs get `valve_closure_degree` = yaml `valve_closure_floor` (default 80); after yaml `trv_soft_close_hold_s` (default 300) or any-zone heating rising-edge, write 100. Plant-off still writes 100. App never writes `valve_opening_degree`. Amend example + house yaml and live docs to match.

## Outcome
Under Plant on, idle max-close soft-close follows house-wide idle → floor → hold-or-heating-edge → 100, matching updated parent R9 — without choking heating via mode-limit semantics.

## Done when
1. Plant on + no Heating Demand anywhere: commissioned Sonoff TRVs hold `valve_closure_floor`.
2. After `trv_soft_close_hold_s` or any zone heating rising-edge: those TRVs receive closure 100.
3. Plant off: all commissioned Sonoff TRVs receive closure 100; App never writes `valve_opening_degree`.
4. Example + house yaml commission `trv_soft_close_hold_s` / floor; ADR/CONTEXT/AGENTS/`knowledge/` match the new law; temperature overshoot hysteresis is not live soft-close law.

## Boundaries
Owns the AppDaemon TRV soft-close law change, yaml commission for floor/hold, and docs amend for updated R9. Does not own flame trip (epic 5). Does not own epic 6.3 CAP-8/deferred hygiene (unblocked after this epic). Does not change Exclusive Session or Heating Demand definition.

- Touch point: `apps/ha_smart_hvac/` — TRV soft-close path; owner: this epic
- Touch point: `apps/apps.yaml` / `apps.yaml.example` — `valve_closure_floor`, `trv_soft_close_hold_s`, per-TRV closure; owner: this epic
- Touch point: `docs/adr/`, `CONTEXT.md`, `AGENTS.md`, `knowledge/` — amend live soft-close law; owner: this epic
- Must not: write `valve_opening_degree`; restore temperature overshoot as live soft-close; infer TRV entities by naming

## References
- parent — `_bmad-output/initiative-weather-swt-supply-trip/initiative-weather-swt-supply-trip.md`, Requirements R9–R10; Constraints C1, C2, C4, C5, C7
- sibling — `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-trv-idle-max-close/epic-trv-idle-max-close.md` (historical floor+overshoot delivery)
- sibling — `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-docs-trv-flame-water-law/epic-docs-trv-flame-water-law.md`

## Notes
- Waits on epic-docs-trv-flame-water-law because: prior docs epic landed; 6.3 remains blocked until this epic ships.
- covers: R9, R10 (R10 unchanged; R9 updated 2026-11-20).
- Decision: Envelope approved thin (`refined: false`) — re-slice 2026-11-20; refine before stories.
- Decision: Proposed story shape at re-slice (not yet planned): tracer law+tests+example → house yaml HITL → docs amend → refactor sweep (2026-11-20).
