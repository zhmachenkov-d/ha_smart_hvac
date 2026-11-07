---
title: 'ADR 0003 + house-calibration'
type: 'chore'
ticket: '4'
created: '2026-10-17'
status: done
baseline_revision: 'fdfc03b4a42138ca0190b0aab06561f012780867'
route: 'oneshot'
route_source: 'auto'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/initiative-gate-omega-c-on-saturation/spec-gate-omega-c-on-saturation/spec-gate-omega-c-on-saturation.md'
  - '{project-root}/_bmad-output/initiative-gate-omega-c-on-saturation/spec-gate-omega-c-on-saturation/control-tick-behaviors.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** ADR 0003 Guards and house-calibration §5 still describe only classic adapt guards (demand, steady, deadband, rate/bounds, freeze on Critical Zone switch). Maintainers do not see criterion A: directional clamp, strict apply, write-on-change with fail-closed unreadability, or latched `|u_track|` decay with adapt skipped — and could still read the story as headroom-only freeze or ops-reset-only recovery.

**Approach:** Amend only ADR 0003 Guards and house-calibration §5 so they state the locked CAP-1–4 behaviors under criterion A; keep zone-switch freeze; do not invent headroom-only full-freeze or ops-only recovery as the rationale.

</frozen-after-approval>

## Implementation Notes

Oneshot: docs-only CAP-5 — two prose sections (~ADR Guards + house-calibration §5), no code/tests. Frame criterion A explicitly; name directional skip (max+up / min+down blocked, relieving moves allowed), strict apply (blocked proposed ωc not used for tracking), write-on-change equality skip with fail-closed unreadability, latched `|u_track|` decay with adapt skipped while latched. Leave Persistence / Out of scope / §1–4 / §6 untouched. Code map for wording fidelity: `should_commit_omega_c`, strict re-track in `control_tick`, `_write_setpoint` / `_read_float`, `latch_at_start` + decay helpers in `apps/hvac/hvac_app.py`.

- Amended `docs/adr/0003-online-ladrc-omega-c-auto-tune.md` Guards with two paragraphs: directional clamp + strict apply under criterion A; latch decay / skip-adapt and write-on-change fail-closed. Kept classic demand/steady/deadband/rate/CZ-switch freeze opener.
- Amended `docs/house-calibration.md` §5 with one criterion-A paragraph covering the same locked behaviors; left §1–4 / §6 / closing list untouched.
- Quick review: patched latch-at-start vs post-write decay scoping, `max_rate_fraction × ωc` floor wording, command-based saturation (not entity read), and expanded `SWT` → Set Water Temperature.

## Plan Change Log

## Review Triage Log

### 2026-10-17 — Review pass
- verdicts: high 0, medium 5, low 1, false 0, maybe-false 0
- findings:
  - medium/patch — house-calibration §5 adapt-skip “already held” vs latch_at_start: real (trip-edge); clarified “already active at tick start”
  - medium/patch — house-calibration §5 decay wrongly scoped with adapt-skip: real; split adapt-skip vs post-write latch-held decay
  - medium/patch — ADR decay ambiguous (latch-at-start-only vs residue-alone): real; “Separately… after successful plant write (including trip-edge)”
  - medium/patch — ADR “steps down by max_rate_fraction (≥ omega_c_min)”: real; now `max_rate_fraction × ωc`, floored at `omega_c_min`
  - medium/patch — ADR “already at” invites entity headroom read: real; now “tick’s Set Water Temperature command”
  - low/patch — undefined `SWT` in ADR: real; expanded to Set Water Temperature

## Verification

**Manual checks:**
- `git diff docs/adr/0003-online-ladrc-omega-c-auto-tune.md docs/house-calibration.md` — Guards and §5 state directional clamp, strict apply, write-on-change fail-closed, latched `|u_track|` decay with adapt skipped; no headroom-only full-freeze rationale; Critical Zone switch freeze still present.
- Spec CAP-5 success line matches the amended wording (criterion A, not ops-reset-only recovery).
