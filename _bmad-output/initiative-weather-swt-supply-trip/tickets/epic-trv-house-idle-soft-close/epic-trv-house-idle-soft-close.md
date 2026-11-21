---
type: epic
title: "TRV house-idle soft-close"
parent: initiative-weather-swt-supply-trip
covers: ["R9", "R10"]
sources:
  - _bmad-output/initiative-weather-swt-supply-trip/initiative-weather-swt-supply-trip.md
companions: []
after: []
refined: true
risk: high
---

# TRV house-idle soft-close
## Description
Replace the live plant-on floor + temperature-overshoot soft-close with house-idle soft-close: when no zone has Heating Demand, commissioned Sonoff TRVs get `valve_closure_degree` = yaml `valve_closure_floor` (default 80); after yaml `trv_soft_close_hold_s` (default 300) or any-zone Heating Demand, write 100. Plant-off still writes 100. App never writes `valve_opening_degree`. Amend example + house yaml and live docs to match.

## Outcome
Under Plant on, idle max-close soft-close follows house-wide idle → floor → hold-or-Heating-Demand → 100, matching updated parent R9 — without choking heating via mode-limit semantics.

## Requirements
1. **R1 (parent R9):** Under Plant Management on, when no zone has Heating Demand, the App writes `valve_closure_degree` = yaml `valve_closure_floor` (default **80**) on every commissioned Sonoff TRV; after yaml `trv_soft_close_hold_s` (default **300**) elapses, or when any zone has Heating Demand (cold start already heating, rising-edge, or sustained), the App writes `valve_closure_degree` = **100**. Temperature overshoot hysteresis is not part of the live soft-close law. (`valve_closure_degree` / `valve_opening_degree` are idle max-close / heating max-open limits, not stem position.)
2. **R2 (parent R10):** Under Plant Management off, the App writes `valve_closure_degree` = **100** on all commissioned Sonoff TRVs.

## Constraints
1. **C1 (parent C1):** Implementation stays inside the AppDaemon `ha_smart_hvac` App writing the existing HA plant Set Water Temperature entity and commissioned Sonoff TRV `valve_closure_degree` numbers.
2. **C2 (parent C2):** Exclusive Session (ADR 0001) and Heating Demand via thermostat `hvac_action=heating` are unchanged.
3. **C4 (parent C4):** Critical Zone must not drive Set Water Temperature, TRV soft-close, or the flame trip.
4. **C5 (parent C5):** Outdoor, `flame_on`, `ch_active`, per-TRV closure entity ids, `valve_closure_floor`, and `trv_soft_close_hold_s` are yaml-commissioned; house entity ids are not hardcoded and house `apps.yaml` changes require owner confirmation. Per-TRV `accuracy` is not required for the live soft-close law.
5. **C7 (parent C7):** The App never writes `valve_opening_degree`; heating max-open stays with the TRV. TRV wiring is explicit yaml per Sonoff TRV (closure number) — no name guessing; generic thermostats have no TRV-law keys.

## Done when
1. Plant on + no Heating Demand anywhere: commissioned Sonoff TRVs hold `valve_closure_floor`.
2. After `trv_soft_close_hold_s` or any zone Heating Demand: those TRVs receive closure 100.
3. Plant off: all commissioned Sonoff TRVs receive closure 100; App never writes `valve_opening_degree`.
4. Commissioned = closure entity only (`accuracy` not required); overshoot hysteresis and accuracy listeners are not live soft-close law.
5. Example + house yaml commission `trv_soft_close_hold_s` / floor (and drop accuracy where retired); ADR/CONTEXT/AGENTS/`knowledge/` match the new law.

## Boundaries
Owns the AppDaemon TRV soft-close law change, yaml commission for floor/hold/closure-only, and docs amend for updated R9. Does not own flame trip (epic 5). Does not own epic 6.3 CAP-8/deferred hygiene (unblocked after this epic). Does not change Exclusive Session or Heating Demand definition.

- Touch point: `apps/ha_smart_hvac/` — TRV soft-close path; owner: this epic
- Touch point: `apps/apps.yaml` / `apps.yaml.example` — `valve_closure_floor`, `trv_soft_close_hold_s`, per-TRV closure; owner: this epic
- Touch point: `docs/adr/`, `CONTEXT.md`, `AGENTS.md`, `knowledge/` — amend live soft-close law; owner: this epic
- Must not: write `valve_opening_degree`; restore temperature overshoot as live soft-close; require `accuracy` for commissioned TRV; infer TRV entities by naming

## References
- parent — `_bmad-output/initiative-weather-swt-supply-trip/initiative-weather-swt-supply-trip.md`, Requirements R9–R10; Constraints C1, C2, C4, C5, C7
- sibling — `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-trv-idle-max-close/epic-trv-idle-max-close.md` (historical floor+overshoot delivery)
- sibling — `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-docs-trv-flame-water-law/epic-docs-trv-flame-water-law.md`
- research — `_bmad-output/initiative-weather-swt-supply-trip/research-trv-soft-close-and-hold-timers/research-trv-soft-close-and-hold-timers.md`, §§1–6 (TRV soft-close, accuracy commission/listeners, flame hold timer, tests, accuracy history, call sites) @ 2ec1908

## Notes
- Waits on epic-docs-trv-flame-water-law because: prior docs epic landed; 6.3 remains blocked until this epic ships.
- covers: R9, R10 (R10 unchanged; R9 updated 2026-11-20).
- Decision: Envelope approved thin (`refined: false`) — re-slice 2026-11-20; refine before stories.
- Decision: Tracer = 7.1 "Tracer: TRV house-idle soft-close"; order 7.1 → (7.2 house yaml HITL ∥ 7.3 docs amend) → 7.4 Refactor sweep; docs one amend story; 7.2 config-only (no Exclusive Session); after 6.2 not 6.3 (2026-11-20).
- Decision: Refine from parent covers + settled picks — no PM/UX/architecture companions before stories (2026-11-20).
- Decision: Retire `accuracy` from commissioned TRV (closure-only yaml + no accuracy listeners); overshoot hysteresis removed with it — research §§2,5 (2026-11-20).
- Decision: Soft-close hold semantics — on house all-idle write floor and start `trv_soft_close_hold_s`; on hold expiry while still idle write 100; on any-zone Heating Demand (cold start / rising-edge / sustained) cancel hold and write 100; on return to all-idle restart floor+hold; plant-off cancel hold and write 100; equal-float write skip remains the throttle — research §3 flame hold pattern; tracer 7.1 Req 3 settles demand cancel beyond rising-edge-only (2026-11-20).
- Source conflict: R1 earlier said “heating rising-edge → 100”; tracer Req 3 / hold Decision above is any Heating Demand. Settled 2026-11-20 — R1 demand cancel follows tracer; docs story 7.3 SoT = tracer Reqs 1–7.
