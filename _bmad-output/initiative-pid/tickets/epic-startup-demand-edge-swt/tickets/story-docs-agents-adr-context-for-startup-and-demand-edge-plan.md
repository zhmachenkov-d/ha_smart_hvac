---
title: 'Docs: AGENTS ADR CONTEXT for startup and demand-edge'
type: 'chore'
ticket: '2'
created: '2026-11-10'
status: 'built'
baseline_revision: '05958533b73ac8150da10990e85947a984682d2d'
route: 'oneshot'
route_source: 'auto'
risk: 'medium'
review: 'quick'
review_source: 'auto'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - /workspaces/ha-smart-hvac/AGENTS.md
  - /workspaces/ha-smart-hvac/CONTEXT.md
  - /workspaces/ha-smart-hvac/docs/adr/0005-fixed-pid-swt.md
  - /workspaces/ha-smart-hvac/knowledge/concepts/set-water-temperature.md
  - /workspaces/ha-smart-hvac/_bmad-output/initiative-pid/tickets/epic-startup-demand-edge-swt/epic-startup-demand-edge-swt.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** AGENTS, ADR 0005, CONTEXT, and `knowledge/concepts/set-water-temperature.md` still describe tick-only demand SWT / events never write demand, so agents and readers contradict the shipped initialize-first-tick and gated-demand edge write (D25–D30 / story 4.1).

**Approach:** Rewrite those tick/event passages for initialize first full `control_tick`, gated-demand rising-edge demand SWT write without ∫/RLS step or timer reset, mid-demand no-op, and weights-unusable on edge same as tick; leave ADR 0006 / RLS knowledge pages unchanged.

</frozen-after-approval>

## Implementation Notes

Oneshot: docs-only prose aligned to shipped 4.1 law; risk medium from ticket; ~4 files / well under 100 lines; no App or test code.

- Rewrote tick/event law in `AGENTS.md` (Verified stamp → baseline), `docs/adr/0005-fixed-pid-swt.md` § Tick vs event, `CONTEXT.md` PID + FAQ, and `knowledge/concepts/set-water-temperature.md` (contradiction fix; timestamp bumped).
- Left ADR 0006 and `knowledge/concepts/rls-adaptive-pid.md` unchanged (already forbid RLS on `control_event`).
- Manual verify: stale “only control_tick writes demand” / tick-only weight-unusable denying edge fail grepped clean in the four targets.
- Quick review patches: dropped AGENTS “own the full demand write path”; clarified mid-demand as after successful demand-path write; ADR frames initialize as explicit first `control_tick` on the tick path (not a third schedule).

## Plan Change Log

## Review Triage Log

- medium → patch — AGENTS “own the full demand write path” contradicted edge demand write — removed ownership phrase; ticks own ∫/RLS only.
- low → reject — ADR “two schedules” vs Initialize bullet — initialize is an explicit first `control_tick` of the tick path; patched opening to say tick path + event path instead of counting three schedules.
- medium → patch — unconditional “mid-demand no-op” overstated sticky-open R7 retry — all four targets now say after successful demand-path write / until clear; ADR notes skipped write leaves edge open.
- false — ADR 0005 init RLS vs unchanged ADR 0006 — 0006 gates by `control_tick` vs `control_event`; init invokes `control_tick`, so no 0006 edit.
- low → reject — CONTEXT FAQ omits initialize — ticket verify is satisfied by PID glossary; FAQ answers listener-driven changes.

## Verification

**Manual checks (if no CLI):**
- Grep AGENTS / ADR 0005 / CONTEXT / `knowledge/concepts/set-water-temperature.md` for leftover “only … control_tick … writes demand” / “events never write demand” / “weight-unusable … tick-only” that denies the edge fail path.
- Confirm each names: initialize first full tick; gated-demand edge write without ∫/RLS; mid-demand no-op; timer not reset by edge.
- Confirm ADR 0006 and `rls-adaptive-pid.md` untouched and still forbid RLS on `control_event`.
