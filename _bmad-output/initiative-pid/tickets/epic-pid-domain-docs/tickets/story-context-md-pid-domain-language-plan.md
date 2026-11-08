---
title: 'CONTEXT.md PID domain language'
type: 'chore'
ticket: '3'
created: '2026-11-08'
status: 'built'
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
- Critical Zone and Multi-Zone Coordinator are diagnostics/logging only and do not drive Set Water Temperature.
- Tick vs event: demand SWT + ∫ only on `control_tick`; `control_event` listeners exclude Outdoor; events clear-only on idle / plant-off / no-valid-zones.
- Language matches ADR 0005 and the shipped App; Exclusive Session / Zone / Plant / Heating Demand glossary that still holds is preserved.
