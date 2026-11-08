---
type: epic
title: "PID domain language and ADR"
parent: initiative-pid
covers: ["R4", "R10"]
sources:
  - _bmad-output/initiative-pid/initiative-pid.md
companions: []
after: []
refined: true
risk: medium
status: done
---

# PID domain language and ADR

## Description

R4 docs only: write a new ADR that supersedes ADR 0004 and update AGENTS, CONTEXT and the `knowledge/` concept pages so domain language matches the shipped fixed-PID SWT App (tick vs event, no weather/CAP-7, Critical Zone diagnostics-only).

## Outcome

Operators and agents read one coherent law — `clamp(base + u_pid)` — with ADR 0004 superseded and no leftover weather-curve commissioning story.

## Requirements

1. **R1 (parent R4):** Outdoor Temperature, Weather Feedforward, CAP-7 rise-rate auto-correct, and `ff_auto_correct_state.json` are removed from the SWT path and commissioning; CONTEXT/AGENTS and a new ADR supersede ADR 0004.
2. **R2 (parent R10):** Critical Zone selection is retained for diagnostics/logging only and must not drive Set Water Temperature; CONTEXT/AGENTS state diagnostics-only after CAP-7 removal.

## Constraints

1. **C1 (parent C3):** Fixed PID ships before RLS; they are not one mixed delivery — docs describe the shipped fixed-PID law; RLS stays planned (epic 3), not current commissioning.

## Done when

1. A new ADR supersedes ADR 0004 for the live SWT law.
2. CONTEXT, AGENTS and the `knowledge/` concept pages (set-water-temperature, outdoor-temperature, adrc, critical-zone, multi-zone-coordinator, index) describe the PID path, tick/event split, and Critical Zone as diagnostics-only, with no weather/CAP-7 on the water path.
3. Language matches the App from epic 1 (no contradictory CAP-7 / Outdoor commissioning instructions).

## Boundaries

Owns `docs/adr/`, `CONTEXT.md`, `AGENTS.md`, and `knowledge/` language for this change. Does not change App runtime (epic 1) or deliver RLS (epic 3).

- Touch point: `docs/adr/`, `CONTEXT.md`, `AGENTS.md`, `knowledge/` concept pages — supersede 0004; owner: this epic
- Must not change: Exclusive Session (ADR 0001) semantics

## References

- parent — `_bmad-output/initiative-pid/initiative-pid.md`, Requirements R4, R10; Constraint C3
- sibling — `_bmad-output/initiative-pid/tickets/epic-fixed-pid-swt/epic-fixed-pid-swt.md`
- adr — `docs/adr/0004-weather-curve-swt.md` (to supersede)

## Notes

- Waits on epic-fixed-pid-swt because: live SWT path must be clamp(base + fixed u_pid) with Outdoor/FF/CAP-7 and ff JSON removed before language locks.
- Decision: Operator HITL — do not commission live Exclusive Session on the new yaml until this epic closes (2026-11-07).
- Decision: From the epic-fixed-pid-swt retrospective (initiative D17, D18): `knowledge/` concept pages are in scope (SR5); the AGENTS.md conventions are this epic's first change, since AGENTS.md loads into every agent session (PL2) (2026-11-07).
- Decision: Inputs for the ADR superseding 0004, from the epic-1 plans and retrospective: (1) demand SWT is written and ∫ advanced only on `control_tick`, events only clear (1.2 plan, `b0e1b6a`); (2) accepted consequence — an event clear (TRV idle flap, sensor blip, plant-off) may hold the plant at 0 until the next tick (≤ `control_interval`) and resets ∫ (SR3, D17); (3) anti-windup = I-term clamps plus same-sign SWT-saturation freeze (1.1 plan C2, `f09eb2c`); (4) ∫ and skip rule as revised by R7 / D22 (skip when the plant already reads the command; no ∫ advance while the plant is unavailable); (5) ∫ in °C·h with I-term limits in °C (D15) (2026-11-07).
- Decision: Refine — Requirements from parent R4 + R10 only (no John / architecture / spike); `covers` adds R10; ADR number and `knowledge/` adrc/outdoor reframes left to stories; `refined: true` (2026-11-08).
- Decision: Tracer bullet = entry 1 (AGENTS.md only — deliberate full-layer tracer deviation per D18/PL2); sequence 1 → 2 → {3 ∥ 4} → 5; R2 also in ADR (entry 2); Operator Exclusive Session HITL stays epic note, not story `hitl`; no closing e2e — sweep verify is repo search; `house-calibration.md` not primary (already PID; leftovers → sweep) (2026-11-08).
