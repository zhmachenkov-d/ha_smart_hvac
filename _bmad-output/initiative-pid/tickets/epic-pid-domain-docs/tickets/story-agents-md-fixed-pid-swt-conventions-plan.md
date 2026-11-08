---
title: 'AGENTS.md fixed-PID SWT conventions'
type: 'chore'
ticket: '1'
created: '2026-11-08'
status: 'built'
baseline_revision: '0a3bf9b83b89e27cf5c682a024d9410f8a782056'
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

**Problem:** `AGENTS.md` bmad:context still commissions weather-curve / CAP-7 / CAP-8 Outdoor listeners and `ff_auto_correct_state.json`, so a new agent session loads a law that contradicts the shipped fixed-PID App from epic 1.

**Approach:** Rewrite the conventions (and the ADR pointer that still names live 0004 weather-curve) so agents load `clamp(base_water_temp + u_pid)`, tick-owned demand / event clear-only, and Critical Zone diagnostics-only — without Outdoor/FF/CAP-7 commissioning. Leave ADR id citation as `docs/adr/` until story 2.2; do not edit CONTEXT, knowledge, or App code.

</frozen-after-approval>

## Implementation Notes

Oneshot: single-file AGENTS rewrite matching shipped `hvac_app.py` gates; conventions stay short bullets (ADR detail deferred to 2.2).
- Rewrote `AGENTS.md` bmad:context conventions + ADR pointer; bumped Verified stamp to 2026-11-08 / 0a3bf9b.
- Dropped weather/CAP-7/CAP-8 Outdoor/`ff` JSON commissioning; stated round-to-0.1(clamp(base + u_pid)), tick-owned demand / event clear-only, Critical Zone diagnostics-only.
- ADR cite left as `docs/adr/` with 0004 supersede pending (story 2.2).

## Plan Change Log

## Review Triage Log

- 2026-11-08 quick: no findings.

## Verification

**Manual checks (if no CLI):**
- Open `AGENTS.md`: no live weather-curve / CAP-7 / `ff_auto_correct_state.json` / Outdoor-as-control commissioning; demand law is round-to-0.1(clamp(base + u_pid)); plant-off = no write + clear ∫; idle = write 0 + clear; demand SWT + ∫ only on `control_tick`; `control_event` clears only; Critical Zone diagnostics/log only; ADR pointer does not present 0004 as live SWT law.
