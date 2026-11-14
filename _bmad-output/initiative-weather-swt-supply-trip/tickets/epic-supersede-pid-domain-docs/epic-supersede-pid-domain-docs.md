---
type: epic
title: "Supersede PID domain docs"
parent: initiative-weather-swt-supply-trip
covers: ["R4"]
sources:
  - _bmad-output/initiative-weather-swt-supply-trip/initiative-weather-swt-supply-trip.md
companions: []
after: []
refined: true
risk: medium
---

# Supersede PID domain docs

## Description

Align domain language with the shipped weather-curve + supply rise-rate trip water law: a new ADR supersedes ADR 0005 / 0006; CONTEXT, AGENTS, and `knowledge/` describe `clamp(u_ff)`, the supply trip latch/clear, gates, and Critical Zone as diagnostics-only. Remove dead fixed-PID / RLS modules and `pid` commissioning nests left after the path swap. CAP-7 / `ff_auto_correct_state.json` remain absent.

## Outcome

Operators and agents read one water law — weather curve plus supply trip — matching the App; PID/RLS language is gone from live docs and dead code.

## Requirements

1. **R4 (parent R4):** Fixed PID (`base_water_temp + u_pid`, ∫), optional RLS adaptive gains, and `rls_state.json` are removed from the live SWT path and commissioning; domain docs and a new ADR supersede ADR 0005 / 0006 for this water law.

## Constraints

1. **C1 (parent C1):** Implementation stays inside the AppDaemon `ha_smart_hvac` App writing the existing HA plant Set Water Temperature entity.
2. **C2 (parent C2):** Exclusive Session (ADR 0001) and Heating Demand via thermostat `hvac_action=heating` are unchanged.
3. **C3 (parent C3):** SWT uses round-to-0.1 and clamp into existing `setpoint_min` / `setpoint_max` only.
4. **C4 (parent C4):** Critical Zone must not drive Set Water Temperature or the supply rise-rate trip.
5. **C5 (parent C5):** Supply (and Outdoor) entity ids are yaml-commissioned; house entity ids are not hardcoded and house `apps.yaml` changes require owner confirmation.
6. **C6 (parent C6):** CAP-7 / adapting `base`/`slope` / `ff_auto_correct_state.json` are out of scope for this initiative.

## Done when

1. A new ADR supersedes ADR 0005 / 0006 for this water law (curve + trip; CAP-7 still out).
2. CONTEXT, AGENTS, and `knowledge/` match the shipped App (gates, `u_ff`, trip latch/clear, Critical Zone diagnostics-only).
3. Dead PID/RLS modules and `pid` / RLS commissioning are removed from the codebase and example yaml.
4. CAP-7 / `ff_auto_correct_state.json` remain absent.

## Boundaries

Owns ADR/CONTEXT/AGENTS/`knowledge/` supersede and final PID/RLS dead-code cleanup. Does not change the live weather-curve or trip behavior owned by epics 1–2 except to delete unused modules after the path no longer imports them. Must not restore CAP-7.

- Touch point: `docs/adr/`, `CONTEXT.md`, `AGENTS.md`, `knowledge/` — supersede fixed-PID live law; owner: this epic
- Touch point: `apps/ha_smart_hvac/` — delete unused `pid`/`rls` modules after path swap; owner: this epic
- Must not change: Exclusive Session; Heating Demand definition; trip/curve runtime behavior from epics 1–2
- Must not restore: CAP-7 / `ff_auto_correct_state.json`

## References

- parent — `_bmad-output/initiative-weather-swt-supply-trip/initiative-weather-swt-supply-trip.md`, Requirement R4 (docs/cleanup); Constraints C1–C6
- adr — `docs/adr/0005-fixed-pid-swt.md` (to supersede)
- adr — `docs/adr/0006-optional-rls-adaptive-pid.md` (to supersede)
- sibling — `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-weather-curve-swt-restore/epic-weather-curve-swt-restore.md`
- sibling — `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-supply-rise-rate-trip/epic-supply-rise-rate-trip.md`

## Notes

- Waits on epic-supply-rise-rate-trip because: weather-curve demand path and supply rise-rate trip must be shipped so docs match the App.
- Shared covers: R4 with epic 1 (docs/cleanup here; path/commissioning there).
- Decision: Slice approved — docs/cleanup is third epic after trip (2026-11-11).
- Decision: Refine from parent covers only — no extra companions before stories (2026-11-14).
- Decision: R4 scope here — ADR 0007 as live law (weather curve + supply trip; CAP-7 out); supersede ADR 0005 / 0006; ADR 0004 stays historical; CONTEXT / AGENTS / knowledge live pages match App; dead `pid`/`rls` modules and remaining `pid` commissioning nests removed; path swap already epic 1 (2026-11-14).
- Decision: knowledge/ — live SWT and related concept pages describe curve + trip; PID/RLS concept pages demoted to historical prior art (like LADRC), not live law (2026-11-14).
- Decision: House apps.yaml — example yaml cleanup in this epic; house HITL only if a `pid` nest remains (2026-11-14).
- Decision: Story slice approved — tracer bullet is 3.1 (ADR 0007 + AGENTS/CONTEXT); then 3.2 knowledge live curve+trip + demote PID/RLS (least-certain); then 3.3 delete dead pid/rls modules; 3.4 Refactor sweep. Skip house HITL (no pid nest in house apps.yaml or example). No opening refactor; no closing e2e suite; ADR written in-story (not toolsmith). 3.2 and 3.3 both after 3.1 (2026-11-14).
