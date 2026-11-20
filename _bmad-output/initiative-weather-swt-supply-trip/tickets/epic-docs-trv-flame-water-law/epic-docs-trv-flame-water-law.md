---
type: epic
title: "Docs: TRV + flame water law"
parent: initiative-weather-swt-supply-trip
covers: ["R4", "R7", "R8"]
sources:
  - _bmad-output/initiative-weather-swt-supply-trip/initiative-weather-swt-supply-trip.md
companions: []
after: []
refined: true
risk: medium
---

# Docs: TRV + flame water law

## Description
Align ADR, CONTEXT, AGENTS, and `knowledge/` with the shipped weather-curve + TRV soft-close + flame short-on water law. A new ADR supersedes ADR 0007 for live water law (0007 becomes historical supply-trip era); remove live supply rise-rate trip language; keep CAP-7 out. Does not change runtime behavior owned by epics 4–5.

## Outcome
Operators and agents read one water law — weather curve, TRV idle max-close, flame short-on trip — matching the App.

## Requirements
1. **R1 (parent R4):** Fixed PID (`base_water_temp + u_pid`, ∫), optional RLS adaptive gains, and `rls_state.json` are removed from the live SWT path and commissioning; domain docs and a new ADR supersede ADR 0005 / 0006 for this water law.
2. **R2 (parent R7):** Outdoor Temperature is yaml-commissioned on the weather-curve SWT path and commissioning; anti-cycle no longer requires a supply rise-rate entity.
3. **R3 (parent R8):** Critical Zone remains diagnostics/logging only and does not drive Set Water Temperature, TRV soft-close, or the flame trip; CAP-7 rise-rate auto-correct of `base`/`slope` and `ff_auto_correct_state.json` are not restored in this initiative.

## Constraints
1. **C1 (parent C1):** Implementation stays inside the AppDaemon `ha_smart_hvac` App writing the existing HA plant Set Water Temperature entity and commissioned Sonoff TRV `valve_closure_degree` numbers.
2. **C2 (parent C2):** Exclusive Session (ADR 0001) and Heating Demand via thermostat `hvac_action=heating` are unchanged.
3. **C3 (parent C3):** SWT uses round-to-0.1 and clamp into existing `setpoint_min` / `setpoint_max` only.
4. **C4 (parent C4):** Critical Zone must not drive Set Water Temperature, TRV soft-close, or the flame trip.
5. **C5 (parent C5):** Outdoor, `flame_on`, `ch_active`, and per-TRV closure/accuracy entity ids are yaml-commissioned; house entity ids are not hardcoded and house `apps.yaml` changes require owner confirmation.
6. **C6 (parent C6):** CAP-7 / adapting `base`/`slope` / `ff_auto_correct_state.json` are out of scope for this initiative.
7. **C7 (parent C7):** The App never writes `valve_opening_degree`; heating max-open stays with the TRV. TRV wiring is explicit yaml per Sonoff TRV (closure number + accuracy source) — no name guessing; generic thermostats have no TRV-law keys.

## Done when
1. A new ADR is the live water law (weather curve + TRV soft-close + flame short-on; CAP-7 out); ADR 0007 is historical (supply-trip era); live docs no longer point at supply rise-rate trip as anti-cycle.
2. CONTEXT and AGENTS match the shipped App: Outdoor-gated weather-curve demand, TRV soft-close (including accuracy as a `control_event` listen where applicable), flame observe/latch/clear, Critical Zone diagnostics-only for SWT / TRV / flame.
3. `knowledge/` live pages match that law; supply-trip-only material is historical or removed from live law.
4. CAP-7 / `ff_auto_correct_state.json` remain absent from live commissioning language; anti-cycle docs do not require a supply rise-rate entity.

## Boundaries
Owns domain-doc amend after TRV + flame ship. Does not own TRV or flame runtime (epics 4–5). Must not restore CAP-7 or supply rise-rate as live law. Does not own code remediation (e.g. `control_event` docstring) deferred outside this epic.

- Touch point: `docs/adr/`, `CONTEXT.md`, `AGENTS.md`, `knowledge/` — owner: this epic
- Must not change: Exclusive Session; runtime from epics 4–5 except doc accuracy

## References
- parent — `_bmad-output/initiative-weather-swt-supply-trip/initiative-weather-swt-supply-trip.md`, Requirements R4, R7, R8; Constraints C1–C7
- adr — `docs/adr/0007-weather-curve-supply-trip-swt.md` (supersede for live law; keep as historical)
- sibling — `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-trv-idle-max-close/epic-trv-idle-max-close.md`
- sibling — `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-replace-supply-trip-with-flame/epic-replace-supply-trip-with-flame.md`

## Notes
- Waits on epic-replace-supply-trip-with-flame because: TRV soft-close and flame short-on must be shipped so docs match the App.
- Shared covers: R4 with epic 1/3 (path/prior docs there; this epic amends live docs for TRV+flame); R7/R8 wording refresh here.
- Decision: Envelope approved thin (`refined: false`) — re-slice 2026-11-15; refine before stories.
- Decision: Refine from parent covers only — no extra companions before stories (2026-11-17).
- Decision: New ADR supersedes ADR 0007 for live water law (curve + TRV soft-close + flame; CAP-7 out); 0007 historical supply-trip era — declined in-place amend of 0007 (2026-11-17).
- Decision: `knowledge/` page structure left to stories; live pages must match App; supply-trip-only → historical (2026-11-17).
- Decision: Stale `deferred-work.md` epic-3 bullets are hygiene in tracer/sweep, not a refine blocker; `control_event` docstring remediation stays out of this epic (2026-11-17).
- Decision: Story slice approved — tracer bullet is 6.1 (new ADR + AGENTS/CONTEXT + live pointers / zombie supply decisions); then 6.2 knowledge live curve+TRV+flame + demote supply-trip (least-certain); then 6.3 Refactor sweep. Declined separate closing e2e suite; ADR written in-story (not toolsmith). No opening refactor. (2026-11-17).
- Decision: Replan 2026-11-20 — story 6.3 blocked until new TRV house-idle soft-close epic; live R9 no longer overshoot hysteresis; docs amend follows that epic.
