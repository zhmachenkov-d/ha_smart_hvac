---
type: epic
title: "Startup tick and demand-edge SWT"
parent: initiative-pid
covers: ["R5", "R6"]
sources:
  - _bmad-output/initiative-pid/initiative-pid.md
companions: []
after: []
refined: true
risk: high
---

# Startup tick and demand-edge SWT

## Description

Close the comfort lag after App reload and after the house enters gated Heating Demand: run one full control tick at initialize, and on rising-edge into gated demand write demand Set Water Temperature without advancing PID ∫ or stepping RLS. Mid-demand zone air and setpoint events stay no-op; idle / plant-off / fail clears stay as today. Align AGENTS, ADR 0005, and CONTEXT with the revised R5/R6.

## Outcome

After App start or entry into gated demand (Plant Management on and Heating Demand) the plant receives a demand SWT command without waiting up to a full `control_interval`, while ∫ and RLS still advance only on the periodic tick (and the initialize first tick for ∫ / full tick path).

## Requirements

1. **R1 (parent R5):** Periodic `control_interval` (default 300s) advances PID ∫ and issues a demand-path SWT write; `initialize` also runs one full `control_tick` (write + ∫ advance when gates allow; RLS steps per ADR 0006 when adaptive on) so the first demand command does not wait a full interval. The `control_interval` schedule is not reset by demand-edge writes.
2. **R2 (parent R6):** Event listeners may clear immediately on idle / plant-off / fail paths. Rising-edge into **gated demand** (transition into Plant Management on **and** Heating Demand — including plant turning on while zones already demand) may write demand SWT **without** advancing PID ∫ and **without** stepping RLS (current gains only). Other demand-path events (zone air / setpoint while already in gated demand) must not write demand SWT or advance ∫. Weights-unusable on the demand-edge path takes the same fail path as a tick: write `0` and clear ∫.

## Constraints

1. **C1 (parent C1):** SWT clamp uses existing `setpoint_min` / `setpoint_max` only.
2. **C2 (parent C2):** Implementation stays inside the AppDaemon `ha_smart_hvac` App writing the existing HA plant entity.
3. **C3 (D29):** RLS model update remains `control_tick`-only (ADR 0006); demand-edge must not call the RLS step.

## Done when

1. Initialize runs one full `control_tick` (demand write + ∫ advance when gates allow; RLS per ADR 0006 on that tick).
2. Rising-edge into gated demand (Plant on ∧ Heating Demand) writes demand SWT without advancing ∫ and without stepping RLS; mid-demand zone/setpoint events neither write nor advance ∫.
3. Idle / plant-off / fail clears, weights-unusable fail (write `0` + clear), and plant equal-float / unavailable skip behave as on the existing demand path.
4. AGENTS, ADR 0005, and CONTEXT state the revised tick / event law; automated tests lock initialize first tick and gated-demand edge write; `knowledge/` only if a page contradicts.

## Boundaries

Owns AppDaemon `ha_smart_hvac` initialize scheduling and `control_event` gated-demand rising-edge write, plus docs language for that law. Does not change the PID law form, Exclusive Session, or Heating Demand definition. Does not roll back epic 1–3 deliveries. Does not own `knowledge/` unless entry 2 finds a contradiction.

- Touch point: `apps/ha_smart_hvac/` initialize + control_event gated-demand edge — owner: this epic
- Touch point: `AGENTS.md`, `docs/adr/0005-*.md`, `CONTEXT.md` — tick/event wording — owner: this epic
- Must not change: Exclusive Session; Heating Demand via `hvac_action`; RLS JSON persistence / unhealthy latch semantics beyond forbidding RLS step on demand-edge

## References

- parent — `_bmad-output/initiative-pid/initiative-pid.md`, Requirements R5–R6 (D25/D26); Constraints C1–C2
- sibling — `_bmad-output/initiative-pid/tickets/epic-fixed-pid-swt/epic-fixed-pid-swt.md` (prior tick-only R5/R6)
- adr — `docs/adr/0005-fixed-pid-swt.md`, tick/event schedule; `docs/adr/0006-rls-adaptive-pid.md`, tick-only RLS step
- decisions — `_bmad-output/initiative-pid/.memlog.md`, D25–D30

## Notes

- Waits on epic-fixed-pid-swt because: need shipped fixed PID tick/event machinery to extend.
- Waits on epic-pid-domain-docs because: entry 2 revises AGENTS/ADR/CONTEXT tick/event wording that epic 2 shipped.
- Waits on epic-rls-pid-retune because: initialize / control_event changes must coexist with the shipped RLS tick step.
- Decision: Tracer bullet is entry 1 (initialize first tick + rising-edge write without ∫); entry 2 is docs; no refactor sweep (two entries) (2026-11-09).
- Decision: Shared R5/R6 — epic 1 delivered the original tick-only law; this epic owns the D25/D26 revision (2026-11-09).
- Decision: Declined adding `.memlog.md` to initiative `sources:` — Spec forbids naming the memlog there; D25/D26 stay cited from Requirements/Notes like prior D-lines (2026-11-09).
- Decision: Declined trimming R5/R6 from epic 1 `covers` — shared ownership recorded; epic 1 stays historical for the original law (2026-11-09).
- Decision: Refine 2026-11-09 (user) — D28 gated-demand edge (Plant on ∧ Heating Demand, including plant-on while already demand); D29 no RLS step on edge; D30 no timer reset on edge; weights-unusable → write 0 + clear; knowledge/ out of Done when unless 4.2 finds a contradiction.
