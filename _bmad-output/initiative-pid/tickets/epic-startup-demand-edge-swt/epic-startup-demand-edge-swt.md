---
type: epic
title: "Startup tick and demand-edge SWT"
parent: initiative-pid
covers: ["R5", "R6"]
sources:
  - _bmad-output/initiative-pid/initiative-pid.md
companions: []
after: []
refined: false
risk: high
---

# Startup tick and demand-edge SWT

## Description

Close the comfort lag after App reload and after a thermostat enters Heating Demand: run one full control tick at initialize, and on rising-edge into Heating Demand write demand Set Water Temperature without advancing PID ∫. Mid-demand zone air and setpoint events stay no-op; idle / plant-off / fail clears stay as today. Align AGENTS, ADR 0005, and CONTEXT with the revised R5/R6.

## Outcome

After App start or thermostat activation under Plant Management on, the plant receives a demand SWT command without waiting up to a full `control_interval`, while ∫ still advances only on the periodic tick (and the initialize first tick).

## Done when

1. Initialize runs one full `control_tick` (demand write + ∫ advance when gates allow).
2. Rising-edge into Heating Demand writes demand SWT without advancing ∫; other demand-path events neither write nor advance ∫.
3. Idle / plant-off / fail clears and plant equal-float skip behave as before.
4. AGENTS, ADR 0005, and CONTEXT state the revised tick / event law; automated tests lock the new paths.

## Boundaries

Owns AppDaemon `ha_smart_hvac` initialize scheduling and `control_event` rising-edge demand write, plus docs language for that law. Does not change the PID law, RLS, Exclusive Session, or Heating Demand definition. Does not roll back epic 1–3 deliveries.

- Touch point: `apps/ha_smart_hvac/` initialize + control_event demand edge — owner: this epic
- Touch point: `AGENTS.md`, `docs/adr/0005-*.md`, `CONTEXT.md` — tick/event wording — owner: this epic
- Must not change: Exclusive Session; Heating Demand via `hvac_action`; RLS JSON / adaptive path semantics beyond when ∫ advances

## References

- parent — `_bmad-output/initiative-pid/initiative-pid.md`, Requirements R5–R6 (D25/D26); Constraints C1–C2
- sibling — `_bmad-output/initiative-pid/tickets/epic-fixed-pid-swt/epic-fixed-pid-swt.md` (prior tick-only R5/R6)
- decisions — `_bmad-output/initiative-pid/.memlog.md`, D25–D27

## Notes

- Waits on epic-fixed-pid-swt because: need shipped fixed PID tick/event machinery to extend.
- Waits on epic-pid-domain-docs because: entry 2 revises AGENTS/ADR/CONTEXT tick/event wording that epic 2 shipped.
- Waits on epic-rls-pid-retune because: initialize / control_event changes must coexist with the shipped RLS tick step.
- Decision: Tracer bullet is entry 1 (initialize first tick + rising-edge write without ∫); entry 2 is docs; no refactor sweep (two entries) (2026-11-09).
- Decision: Shared R5/R6 — epic 1 delivered the original tick-only law; this epic owns the D25/D26 revision (2026-11-09).
- Decision: Declined adding `.memlog.md` to initiative `sources:` — Spec forbids naming the memlog there; D25/D26 stay cited from Requirements/Notes like prior D-lines (2026-11-09).
- Decision: Declined trimming R5/R6 from epic 1 `covers` — shared ownership recorded; epic 1 stays historical for the original law (2026-11-09).
