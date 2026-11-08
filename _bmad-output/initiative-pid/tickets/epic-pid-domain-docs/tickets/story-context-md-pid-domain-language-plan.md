---
title: 'CONTEXT.md PID domain language'
type: 'chore'
ticket: '3'
created: '2026-11-08'
status: done
baseline_revision: 'e69cc2a7fb4ceba87e8ac73a1966008d50858087'
route: 'oneshot'
route_source: 'auto'
risk: 'medium'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `CONTEXT.md` glossary and expert Q&A still commission weather-curve SWT (`clamp(u_ff)`, CAP-7/8, Outdoor-as-control, FF JSON), so domain language contradicts ADR 0005 and the shipped fixed-PID App.

**Approach:** Rewrite glossary + example dialogue against ADR 0005 (R1/R2): demand `round-to-0.1(clamp(base_water_temp + u_pid))`, tick-owned demand / event clear-only, Critical Zone / Multi-Zone Coordinator diagnostics-only; drop live Outdoor/FF/CAP-7 commissioning. Do not edit AGENTS, knowledge, ADR, or App code.

</frozen-after-approval>

## Implementation Notes

Oneshot: single-file `CONTEXT.md` rewrite (~Plant Management through Multi-Zone Coordinator + last three dialogue turns). Match ADR 0005 / AGENTS law; keep Exclusive Session and Zone/Plant/SWT/Heating Demand terms that still hold. Reframe Outdoor as not on the SWT path; remove Weather Feedforward as live SWT commissioning (or mark not commissioned). Add PID / `u_pid` / `base_water_temp` language needed for glossary + dialogue. Leave AGENTS “pending 2.3+” caveat and `knowledge/` to later stories.
- Rewrote Plant Management / Zone Error / Critical Zone / Outdoor / Multi-Zone Coordinator; replaced Weather Feedforward glossary entry with PID; updated dialogue turns for demand law, plant-off, and tick vs event.
- Left AGENTS.md, ADR, knowledge/, and App untouched.
- Quick review patches: Multi-Zone Coordinator diagnostics-only scoped to Critical Zone only; event dialogue says shared gate prelude (not “same gates”).
- Full review patches: event idle/no-valid-zones write 0 vs plant-off no write; base_water_temp / weighted `e` / ∫ gloss; weight-unusable tick-only; PID Avoid residues; Verification MZC wording.

## Plan Change Log

## Review Triage Log

### 2026-11-08 quick
**Code review complete.** 0 `decision-needed`, 2 `patch`, 0 `defer`, 0 rejected.

- [x] [Review][Patch] Multi-Zone Coordinator over-scoped diagnostics-only onto Heating Demand [CONTEXT.md:Multi-Zone Coordinator] — Critical Zone selection only is diagnostics-only; coordinator still computes ZE/HD without owning SWT write
- [x] [Review][Patch] Event dialogue claimed “the same gates” vs tick [CONTEXT.md:final Expert] — “shared gate prelude”; weight-unusable stays tick-only

## Verification

**Manual checks (if no CLI):**
- `CONTEXT.md` has no live weather-curve / CAP-7 / CAP-8 / `clamp(u_ff)` / FF auto-correct JSON / Outdoor-as-control commissioning story.
- Demand law is `round-to-0.1(clamp(base_water_temp + u_pid))`; plant-off = no write + clear ∫; idle = write 0 + clear ∫.
- Critical Zone selection is diagnostics/logging only and must not drive Set Water Temperature; Multi-Zone Coordinator still computes Zone Error and Heating Demand without owning the SWT write.
- Tick vs event: demand SWT + ∫ only on `control_tick` (weight-unusable tick-only write 0 + clear ∫); `control_event` listeners exclude Outdoor; event idle/no-valid-zones write 0 + clear ∫; plant-off clear ∫ with no write.
- Language matches ADR 0005 and the shipped App; Exclusive Session / Zone / Plant / Heating Demand glossary that still holds is preserved.

## Code Review

### 2026-11-08
**Code review complete.** 0 `decision-needed`, 5 `patch`, 0 `defer`, 3 rejected (incl. F4→B).

- [x] [Review][Decision] Plant readback throttle/∫ rule absent from CONTEXT — resolved: **B** — leave readback throttle in AGENTS/ADR only; no CONTEXT change.
- [x] [Review][Patch] Event clear path omits idle/no-valid-zones write 0 [CONTEXT.md:59-60]
- [x] [Review][Patch] base_water_temp / weighted averages / ∫ underdefined [CONTEXT.md:59-60]
- [x] [Review][Patch] Weight-unusable tick-only fail path undocumented [CONTEXT.md:59-60]
- [x] [Review][Patch] Plan Verification still over-scopes Multi-Zone Coordinator [story-context-md-pid-domain-language-plan.md:Verification]
- [x] [Review][Patch] PID Avoid list incomplete for weather-curve residues [CONTEXT.md:61]

#### Rejected
- F4/R3 Plant readback throttle absent from CONTEXT — rejected after decision **B**: leave in AGENTS/ADR only.
- R5 Weather Feedforward deleted instead of not-commissioned entry — false: plan Approach allows remove or mark not-commissioned; Avoid lists Weather Feedforward / CAP-7.
- R7 Plan Change Log empty — low: rarely visible process hygiene; not worth filling for this run.
