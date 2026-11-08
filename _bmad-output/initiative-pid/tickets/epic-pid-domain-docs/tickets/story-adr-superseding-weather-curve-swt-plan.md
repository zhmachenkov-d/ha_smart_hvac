---
title: 'ADR superseding weather-curve SWT'
type: 'chore'
ticket: '2'
created: '2026-11-08'
status: done
baseline_revision: '85a2e2257e78040323beb080dae9c4765a4f310c'
route: 'oneshot'
route_source: 'auto'
risk: 'high'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** ADR 0004 is still `status: accepted` and commissions weather-curve / CAP-7 SWT, so architecture docs contradict the shipped fixed-PID App and AGENTS’s “do not follow 0004” caveat.

**Approach:** Add `docs/adr/0005-fixed-pid-swt.md` as the accepted live SWT law (R1/R2 + epic Notes ADR inputs), mark 0004 superseded by ADR-0005, and point AGENTS at 0005 for live SWT (RLS stays planned, not commissioning).

</frozen-after-approval>

## Implementation Notes

Oneshot: three-file docs change — new ADR 0005 (~0004 length), 0004 status frontmatter only, AGENTS ADR pointer + Verified stamp. Body must match AGENTS conventions and epic Notes (tick-owned demand, event clear-only + ≤ control_interval clear latency, anti-windup I-clamp + same-sign saturation freeze, ∫ °C·h / I-term °C, R7 equal-float skip and no ∫ when plant unreadable). Do not edit CONTEXT, knowledge, or App code.
- Added `docs/adr/0005-fixed-pid-swt.md` (`status: accepted`); supersedes 0004; folds tick/event, clear latency, anti-windup, ∫ units, R7, Critical Zone diagnostics-only, RLS planned (C1).
- Set `0004` frontmatter to `superseded by ADR-0005` (bodies of 0002/0003 untouched).
- AGENTS: cite 0005 as live SWT; Verified stamp → `85a2e22`.
- Quick review patches: AGENTS R7 equal-float still advances ∫; ADR accepted-consequence split idle vs plant-off; event clear wording drops generic “fail” (weight-unusable tick-only).

## Plan Change Log

## Review Triage Log

### 2026-11-08 quick
**Code review complete.** 0 `decision-needed`, 3 `patch`, 0 `defer`, 2 rejected.

- [x] [Review][Patch] AGENTS omitted ∫ advance on equal-float skip while ADR 0005 stated R7 [AGENTS.md:tick bullet] — added “(∫ still advances)”
- [x] [Review][Patch] Accepted-consequence conflated plant-off with hold-at-0 [0005 §Tick vs event] — split idle/no-valid-zones write-0 vs plant-off no-write
- [x] [Review][Patch] Event “fail” overstated weight-unusable as event-clear [0005 §Tick vs event] — no-valid-zones + tick-only weight-unusable

Rejected:
- R4 Fourth file is the plan artifact — process metadata, not product scope breach.
- R5 Plan `status: in-progress` mid-oneshot — workflow updates status at Finalize; not a product defect.

## Verification

**Manual checks (if no CLI):**
- `docs/adr/0005-fixed-pid-swt.md` exists with `status: accepted`; body supersedes 0004; states round-to-0.1(clamp(base + u_pid)), tick vs event, no Outdoor/FF/CAP-7/`ff` JSON on the path, Critical Zone diagnostics-only, RLS planned not commissioned.
- `docs/adr/0004-weather-curve-swt.md` frontmatter is `status: superseded by ADR-0005` (bodies of 0002/0003 unchanged).
- `AGENTS.md` cites 0005 as live SWT / no longer defers supersede to story 2.2; conventions still match the ADR (including R7 equal-float ∫ advance); Verified stamp updated.

## Code Review

### 2026-11-08
**Code review complete.** 0 `decision-needed`, 3 `patch`, 0 `defer`, 9 rejected.

- [x] [Review][Patch] ADR 0005 PI formula underspecifies App command law (quantize / clamp bounds) [docs/adr/0005-fixed-pid-swt.md:PI law] — round-to-0.1(clamp(..., setpoint_min, setpoint_max)); same bounds in anti-windup commission line
- [x] [Review][Patch] Weight-unusable tick fail outcome missing from ADR [docs/adr/0005-fixed-pid-swt.md:20] — tick bullet: write 0 and clear ∫
- [x] [Review][Patch] Event bullet cites private `_run_demand` [docs/adr/0005-fixed-pid-swt.md:20] — prose: tick-only; events do not take that idle path

Rejected:
- R1 ADR 0004 body without in-body supersession notice — false: frontmatter-only matches 0002/0003 and plan.
- R3 PID title vs PI-only law — false: project domain term is PID; formula defines commissioned terms.
- R5 Plant-off resume latency not spelled out — low: already implied by tick-owned demand; not worth extra prose.
- R6 ADR never labels R1/R2 — false: R1/R2 content is present; ticket ids not required in ADR.
- R7 Free-text superseded status — false: matches established ADR frontmatter convention.
- R9 Plan Verification omits Notes checklist items — false: must-haves live in ADR body; not a product defect.
- R10 Empty Plan Change Log — false: Triage Log already records quick-review patches.
- R12 Event weight-unusable leaves stale SWT — false: intentional tick-only design already stated.
- R13 Epic R1/R2 CONTEXT vs untouched CONTEXT — false: deferred to story 2.3+ by plan/AGENTS.
