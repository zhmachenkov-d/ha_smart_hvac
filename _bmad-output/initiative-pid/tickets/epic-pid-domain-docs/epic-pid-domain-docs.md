---
type: epic
title: "PID domain language and ADR"
parent: initiative-pid
covers: ["R4"]
sources: []
companions: []
after: []
refined: false
risk: medium
---

# PID domain language and ADR

## Description

R4 docs only: write a new ADR that supersedes ADR 0004 and update CONTEXT and AGENTS so domain language matches the shipped fixed-PID SWT App (tick vs event, no weather/CAP-7, Critical Zone diagnostics-only).

## Outcome

Operators and agents read one coherent law — `clamp(base + u_pid)` — with ADR 0004 superseded and no leftover weather-curve commissioning story.

## Done when

1. A new ADR supersedes ADR 0004 for the live SWT law.
2. CONTEXT and AGENTS describe the PID path, tick/event split, and Critical Zone as diagnostics-only, with no weather/CAP-7 on the water path.
3. Language matches the App from epic 1 (no contradictory CAP-7 / Outdoor commissioning instructions).

## Boundaries

Owns `docs/adr/`, `CONTEXT.md`, and `AGENTS.md` language for this change. Does not change App runtime (epic 1) or deliver RLS (epic 3).

- Touch point: `docs/adr/`, `CONTEXT.md`, `AGENTS.md` — supersede 0004; owner: this epic
- Must not change: Exclusive Session (ADR 0001) semantics

## References

- parent — `_bmad-output/initiative-pid/initiative-pid.md`, Requirement R4 (docs)
- sibling — `_bmad-output/initiative-pid/tickets/epic-fixed-pid-swt/epic-fixed-pid-swt.md`

## Notes

- Waits on epic-fixed-pid-swt because: live SWT path must be clamp(base + fixed u_pid) with Outdoor/FF/CAP-7 and ff JSON removed before language locks.
- Decision: Operator HITL — do not commission live Exclusive Session on the new yaml until this epic closes (2026-11-07).
