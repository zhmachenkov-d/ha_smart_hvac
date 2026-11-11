---
type: epic
title: "Supersede PID domain docs"
parent: initiative-weather-swt-supply-trip
covers: ["R4"]
sources:
  - _bmad-output/initiative-weather-swt-supply-trip/initiative-weather-swt-supply-trip.md
companions: []
after: []
refined: false
risk: medium
---

# Supersede PID domain docs

## Description

Align domain language with the shipped weather-curve + supply rise-rate trip water law: a new ADR supersedes ADR 0005 / 0006; CONTEXT, AGENTS, and `knowledge/` describe `clamp(u_ff)`, the supply trip latch/clear, gates, and Critical Zone as diagnostics-only. Remove dead fixed-PID / RLS modules and `pid` commissioning nests left after the path swap. CAP-7 / `ff_auto_correct_state.json` remain absent.

## Outcome

Operators and agents read one water law — weather curve plus supply trip — matching the App; PID/RLS language is gone from live docs and dead code.

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
