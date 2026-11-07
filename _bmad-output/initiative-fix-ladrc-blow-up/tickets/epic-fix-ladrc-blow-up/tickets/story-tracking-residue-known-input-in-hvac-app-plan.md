---
title: 'Tracking-residue known input in hvac_app'
type: 'bugfix'
ticket: '2'
created: '2026-10-16'
status: done
baseline_revision: '42dfd834e5423caf083ec35f51c559ae7d4302df'
route: 'oneshot'
route_source: 'auto'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/initiative-fix-ladrc-blow-up/tickets/epic-fix-ladrc-blow-up/spec-fix-ladrc-blow-up/spec-fix-ladrc-blow-up.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** After clamp, `hvac_app.control_tick` advances the ESO with absolute post-clamp `command` (SWT °C). Spec CAP-1 / Constraints require known input `(command − u_ff)` — the tracking residue — not absolute command and not pre-clamp `u_track`. CAP-5 tests already use path C; live app does not.

**Approach:** Keep plant write `clamp(u_ff + u_track)`. After a successful write, advance with `(command − u_ff)`. Lock the wiring with a seam/unit test (no need to mock full AppDaemon `control_tick`).

</frozen-after-approval>

## Implementation Notes

Oneshot: ~1–3 LOC production change in `apps/hvac/hvac_app.py` L93 plus a small seam/unit test (~20–40 LOC). Continuity from story 1.1 (`ticket: 1`): continuous-form ESO done; do not retouch `LadrcState.advance`, example defaults, guard, or ADR.

- Production: `self._ladrc.advance(decision.measured, command - u_ff, effective_ladrc)` (or equivalent via a tiny extracted seam called from `control_tick`).
- Plant write path (`_write_setpoint(command)`) unchanged.
- Out of scope: `apps/apps.yaml.example` defaults (entry 3), blow-up guard (entry 4), ADR 0002 amend, `LadrcState` API.
- Prefer a seam the test can call without Hass (e.g. module helper that applies post-clamp known input to `LadrcState`) over a heavy `control_tick` mock.

- Extracted `advance_with_tracking_residue` in `apps/hvac/hvac_app.py`; `control_tick` calls it after `_write_setpoint(command)`.
- Tests in `tests/test_hvac_app.py` assert `_last_u_applied == command - u_ff` (and zero when command == u_ff).

## Plan Change Log

## Review Triage Log

- 2026-10-16 quick: high=0 medium=0 low=0 false=0 maybe-false=0 — no findings

## Verification

**Commands:**
- `uv run pytest tests/test_ladrc.py tests/test_hvac_app.py -q` -- known-input seam asserts ESO `u_applied == command - u_ff`; plant write remains absolute clamped SWT; existing LADRC suite still passes (create `tests/test_hvac_app.py` if the seam lives beside `hvac_app`)
- `uv run ruff check apps/hvac/hvac_app.py tests/` -- clean
