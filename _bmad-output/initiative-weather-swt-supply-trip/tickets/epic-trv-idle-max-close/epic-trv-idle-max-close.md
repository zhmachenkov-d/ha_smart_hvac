---
type: epic
title: "TRV idle max-close soft-close"
parent: initiative-weather-swt-supply-trip
covers: ["R9", "R10"]
sources:
  - _bmad-output/initiative-weather-swt-supply-trip/initiative-weather-swt-supply-trip.md
  - _bmad-output/initiative-weather-swt-supply-trip/forge-trv-valve-closure-anti-cycle/forge-trv-valve-closure-anti-cycle.md
companions: []
after: []
refined: true
risk: high
---

# TRV idle max-close soft-close

## Description
Primary anti-cycle on commissioned Sonoff TRVs: AppDaemon writes only `valve_closure_degree` as idle max-close (yaml floor / overshoot 100 / clear to floor), and plant-off writes 100 on all commissioned Sonoff TRVs. Never writes `valve_opening_degree`. Explicit yaml wiring; house entity ids already confirmed on the initiative.

## Outcome
With Plant Management on, Sonoff TRV zones soft-close at the idle max-close floor (and fully close on overshoot); with Plant off, all commissioned Sonoff TRVs are at closure 100 — without the App owning heating max-open.

## Requirements
1. **R1 (parent R9):** Under Plant Management on, for every commissioned Sonoff TRV the App writes only `valve_closure_degree` as idle max-close: yaml `valve_closure_floor` (default **80**) by default; **100** when that TRV's zone `T_zone > setpoint + accuracy`; restore floor when `T_zone ≤ setpoint` — with or without Heating Demand.
2. **R2 (parent R10):** Under Plant Management off, the App writes `valve_closure_degree` = **100** on all commissioned Sonoff TRVs.

## Constraints
1. **C1 (parent C1):** Implementation stays inside the AppDaemon `ha_smart_hvac` App writing the existing HA plant Set Water Temperature entity and commissioned Sonoff TRV `valve_closure_degree` numbers.
2. **C2 (parent C2):** Exclusive Session (ADR 0001) and Heating Demand via thermostat `hvac_action=heating` are unchanged.
3. **C4 (parent C4):** Critical Zone must not drive Set Water Temperature, TRV soft-close, or the flame trip.
4. **C5 (parent C5):** Outdoor, `flame_on`, `ch_active`, and per-TRV closure/accuracy entity ids are yaml-commissioned; house entity ids are not hardcoded and house `apps.yaml` changes require owner confirmation.
5. **C7 (parent C7):** The App never writes `valve_opening_degree`; heating max-open stays with the TRV. TRV wiring is explicit yaml per Sonoff TRV (closure number + accuracy source) — no name guessing; generic thermostats have no TRV-law keys.

## Done when
1. Plant on: each commissioned Sonoff TRV holds floor or 100 on overshoot and restores floor when `T_zone ≤ setpoint`, with or without Heating Demand.
2. Plant off: all commissioned Sonoff TRVs receive `valve_closure_degree` = 100.
3. App never writes `valve_opening_degree`; generic thermostats have no TRV-law keys.
4. Example + house yaml wire the confirmed closure/accuracy entities; automated tests lock the law.

## Boundaries
Owns Sonoff TRV soft-close listeners/writes and yaml commission for closure/accuracy/floor. Does not own flame trip or supply-trip removal (epic 5) or ADR/docs amend (epic 6). Does not change Exclusive Session or Heating Demand.

- Touch point: `apps/ha_smart_hvac/` — TRV soft-close path; owner: this epic
- Touch point: `apps/apps.yaml` / `apps.yaml.example` — per-TRV closure + accuracy, `valve_closure_floor`; owner: this epic
- Must not: write `valve_opening_degree`; infer entities by naming convention

## References
- parent — `_bmad-output/initiative-weather-swt-supply-trip/initiative-weather-swt-supply-trip.md`, Requirements R9–R10; Constraints C1, C2, C4, C5, C7
- source — `_bmad-output/initiative-weather-swt-supply-trip/forge-trv-valve-closure-anti-cycle/forge-trv-valve-closure-anti-cycle.md`

## Notes
- Waits on epic-supersede-pid-domain-docs because: PID path/docs cleanup finished (3.4 dropped); weather-curve App stable before TRV soft-close.
- Decision: Envelope approved thin (`refined: false`) — re-slice 2026-11-15; refine before stories.
- Decision: Refine from parent covers only — no extra companions before stories (2026-11-15).
