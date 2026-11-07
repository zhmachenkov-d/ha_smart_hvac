---
type: epic
title: "RLS retune of PID gains"
parent: initiative-pid
covers: ["R9"]
sources: []
companions: []
after: []
refined: false
risk: high
---

# RLS retune of PID gains

## Description

Later delivery: adapt PID gains (Kp/Ki and agreed RLS state) online from plant/zone signals without restoring Weather Feedforward or CAP-7. Fixed-gain yaml remains the fallback commission.

## Outcome

Gains can retune in production without bringing back the weather curve; the house still falls back to commissioned fixed PID.

## Done when

1. RLS (or agreed adaptive retune) updates Kp/Ki from live signals under the same plant gates.
2. Weather Feedforward and CAP-7 stay absent from the SWT path.
3. Fixed-gain yaml remains a working fallback commission.
4. Adaptive scope and persistence are refined before stories are planned.

## Boundaries

Owns adaptive gain retune on top of the fixed PID from epic 1. Does not restore outdoor/FF. Does not own the fixed-PID ADR language (epic 2) unless refine adds RLS-specific doc lines later.

- Must not change: Exclusive Session; Heating Demand definition; derivative gain stays 0 unless a later Decision revises C4

## References

- parent — `_bmad-output/initiative-pid/initiative-pid.md`, Requirement R9
- sibling — `_bmad-output/initiative-pid/tickets/epic-fixed-pid-swt/epic-fixed-pid-swt.md`
- source — `_bmad-output/initiative-pid/source-user-pid-rls-example.md`

## Notes

- Waits on epic-fixed-pid-swt because: fixed PID module, yaml gains/weights, and tick-owned advance must exist to retune.
- Decision: RLS docs stay in this epic when refined; no `after` on epic-pid-domain-docs (2026-11-07).
