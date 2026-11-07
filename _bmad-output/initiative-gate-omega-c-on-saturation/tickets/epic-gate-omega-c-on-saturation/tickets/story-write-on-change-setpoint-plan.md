---
title: 'Write-on-change setpoint'
type: 'feature'
ticket: '3'
created: '2026-10-17'
status: done
baseline_revision: '0082f93d8920c632c82341945093de9df590d7c0'
route: 'oneshot'
route_source: 'auto'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/initiative-gate-omega-c-on-saturation/spec-gate-omega-c-on-saturation/spec-gate-omega-c-on-saturation.md'
  - '{project-root}/_bmad-output/initiative-gate-omega-c-on-saturation/spec-gate-omega-c-on-saturation/control-tick-behaviors.md'
  - '{project-root}/_bmad-output/initiative-gate-omega-c-on-saturation/spec-gate-omega-c-on-saturation/architecture-diagrams.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Every demand and idle/0 plant write issues `number/set_value` even when Set Water Temperature already equals the desired float, adding redundant HA chatter while the tick still needs to continue after a successful write decision.

**Approach:** Inside `_write_setpoint` (all paths), read plant entity state; fail-closed abort when unreadable/unparseable; when desired equals the entity float (exact compare, no last-written cache), skip `set_value` but return success so the tick continues; otherwise call `set_value`. Lock CAP-6 (c)(d).

</frozen-after-approval>

## Implementation Notes

Oneshot: ~15 LOC in `_write_setpoint` (reuse `_read_float`) plus CAP-6 (c)(d) tests in `tests/test_hvac_app.py` — two files, mechanical equality/fail-closed change. Prefer a thin pure decision seam or lightweight Hass stub so tests do not need live AppDaemon; do not move sticky latch / ESO / decay relative to successful write.

- Reused `_read_float` inside `_write_setpoint`: unavailable/unknown/None/unparseable → False + WARN; `current == value` → True without `set_value`; else `number/set_value` + True.
- Tests via `_write_stub` (MagicMock get_state/call_service/log) — equal float/string/int skip; differ writes; unreadable matrix abort. No control_tick mirror needed: True return is the continue signal callers already use.
- Verification: `uv run pytest tests/test_hvac_app.py -q` → 65 passed; ruff clean.

## Plan Change Log

## Review Triage Log

### 2026-10-17 — Review pass
- verdicts: 0 findings — high 0, medium 0, low 0, false 0, maybe-false 0
- findings: (none)

## Verification

**Commands:**
- `uv run pytest tests/test_hvac_app.py -q` -- expected: all green, including identical-float skip without aborting tick side effects and unreadable entity abort
- `uv run ruff check apps/hvac/hvac_app.py tests/test_hvac_app.py` -- expected: clean
