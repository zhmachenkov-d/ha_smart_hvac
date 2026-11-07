---
title: 'Refactor sweep'
type: 'refactor'
ticket: '5'
created: '2026-10-17'
status: done
baseline_revision: 'd4487ca98d487ec2fa5d7d961a0b2fe3fbe4f5a1'
route: 'full'
route_source: 'auto'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/initiative-gate-omega-c-on-saturation/deferred-work.md'
  - '{project-root}/_bmad-output/initiative-gate-omega-c-on-saturation/spec-gate-omega-c-on-saturation/control-tick-behaviors.md'
  - '{project-root}/_bmad-output/initiative-gate-omega-c-on-saturation/spec-gate-omega-c-on-saturation/architecture-diagrams.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** After CAP-1–5 landed, deferred companion drift (CAP-2 provisional apply-signal; CAP-4 sticky-after-write) and soft review nits in `control_tick` (helper naming, redundant post-write commit re-check, duplicated track+guard branches) remain as maintenance debt with no intentional behavior change owed.

**Approach:** Closing sweep: sync deferred companions to stories 1–2 Intents; rename `should_commit_omega_c` → `should_apply_omega_c`; extract a tiny track+guard helper to collapse the three branches; simplify post-write commit to `apply_proposed` (no second helper call); leave `GuardUTrackResult.latch_out` as-is. Keep pytest green; no new capabilities.

## Boundaries & Constraints

**Always:**
- Behavior-preserving relative to stories 1–4 (CAP-1–4 tick semantics and CAP-5 ADR/house-calibration stay as shipped).
- Companion wording matches frozen story Intent (provisional apply-signal + write-path; sticky latch after successful write; hold in `(0.8·u_track_max, u_track_max]`).
- Rename symbol to `should_apply_omega_c`; extract one small track+guard helper used by provisional / blocked-final / no-proposal; post-write commit when `apply_proposed` (decay branch unchanged).
- Keep `GuardUTrackResult.latch_out` and its `guard_u_track` unit tests; `control_tick` continues to ignore it in favor of sticky.
- Existing CAP-6 matrices/regressions in `tests/test_hvac_app.py` stay green without relaxing assertions.

**Never:**
- New capabilities, algorithm changes, or YAML knobs.
- Reworking `u_track_max` / plant limits / online b0/ωo/MADRC.
- Broad test rewrite or deleting CAP-6 coverage to “simplify.”
- Removing or deprecating `latch_out`.
- Touching ADR 0003 / house-calibration §5 unless a factual contradiction appears (story 1.4 already shipped criterion A).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Saturated upward proposal | command at max, proposed ωc↑ | Still neither write-path-applied nor committed | No error |
| Latched decay | latch at start, residue above band | Still skip adapt; sticky after write; decay persist | No error |
| Write-on-change | desired == entity float | Still skip `set_value`, tick continues | No error |
| Companion CAP-2 | Reader of control-tick-behaviors | Provisional apply-signal allowed; write-path uses committed when blocked | No error |
| Companion CAP-4 | Reader of control-tick-behaviors / flowchart | Sticky hold + sticky-after-write stated | No error |

</frozen-after-approval>

## Code Map

- `_bmad-output/initiative-gate-omega-c-on-saturation/deferred-work.md` — open items: CAP-2 companion + arch flowchart (PR #31); CAP-4 sticky companion (PR #34). Clear both after sync.
- `_bmad-output/.../control-tick-behaviors.md` CAP-2 (~20–28) — replace with target bullets in Design Notes (provisional apply-signal allowed; write-path blocked → committed ωc only).
- Same file CAP-4 (~41–54) — replace/extend with sticky target bullets in Design Notes.
- `_bmad-output/.../architecture-diagrams.md` — mermaid target in Design Notes (provisional → B → write → sticky → J=`apply_proposed?`).
- `apps/hvac/hvac_app.py` `should_commit_omega_c` ~112–130 — rename to `should_apply_omega_c`; update docstring.
- `apps/hvac/hvac_app.py` `control_tick` ~239–301 — extract module-level or nested helper `(u_track, guard) = track_and_guard(ladrc, latch_in)` using that ladrc’s `u_track_max`; call from provisional / blocked-final / no-proposal; blocked path must not re-call `should_apply_omega_c` on the final guard.
- `apps/hvac/hvac_app.py` `control_tick` ~344–357 — replace `omega_to_commit` + second helper with `if apply_proposed: commit_omega_c(new_omega_c)` in the else of the decay branch.
- `apps/hvac/hvac_app.py` `GuardUTrackResult.latch_out` ~35–76 — leave field + guard unit tests; `control_tick` keeps using `sticky_blow_up_latch`.
- `tests/test_hvac_app.py` `test_control_tick_skips_commit_omega_c_when_guard_tripped` ~349–367 — rewrite inspect locks for rename + post-write `apply_proposed` commit (drop `omega_to_commit` / second helper asserts); keep “no persistence-only” and decay-before-normal-commit order.
- `tests/test_hvac_app.py` matrix / imports / ratchet — rename helper; optionally align Hass-free ratchet post-write to `apply_proposed`-only so it does not silently drift from production.
- Do not change: `ladrc.py`, `ladrc_tuner.py`, `docs/adr/0003-*`, `docs/house-calibration.md`.

## Tasks & Acceptance

**Execution:**
- [x] `_bmad-output/.../control-tick-behaviors.md` + `architecture-diagrams.md` + `deferred-work.md` -- Apply Design Notes target CAP-2/CAP-4 bullets and mermaid nodes; remove PR #31/#34 deferred entries -- Closes deferred doc debt without guessing.
- [x] `apps/hvac/hvac_app.py` -- Rename to `should_apply_omega_c`; extract `track_and_guard` (correct `u_track_max`/latch_in); no helper re-eval on blocked final guard; post-write `if apply_proposed: commit`; leave `latch_out` -- Closes code nits without behavior change.
- [x] `tests/test_hvac_app.py` -- Rewrite trip/commit inspect for `apply_proposed` post-write; rename matrix/imports; keep CAP-6 regressions; optionally mirror ratchet commit to `apply_proposed` -- Prevents inspect failure and production/mirror drift.

**Acceptance Criteria:**
- Given the companion texts, when a reader checks CAP-2/CAP-4 and the flowchart, then provisional apply-signal, write-path committed-on-block, sticky-after-write, and 0.8 band hold are explicit (per Design Notes targets).
- Given existing CAP-6 tests, when `uv run pytest tests/test_hvac_app.py` runs after the sweep, then all still pass (including rewritten inspect).
- Given a blocked saturated upward proposal, when the tick runs, then proposed ωc still neither enters write-path tracking nor commits (no resurrect via final-guard re-eval).
- Given `deferred-work.md` after the sweep, when companions are synced, then the PR #31 and PR #34 entries are gone without new deferred CAP scope.
- Given production `control_tick` source, when inspected, then pre-write gate is `should_apply_omega_c`, post-write normal commit is gated by `apply_proposed` (no second helper / no `omega_to_commit`), and `guard.latch_out` is not read.

## Implementation Notes

## Plan Change Log

- 2026-10-17 plan review: high — rewrite inspect for post-write `apply_proposed` (was rename-only vs `omega_to_commit` lock). medium — paste companion/flowchart targets; helper contract (u_track_max, no final re-eval). low — optional ratchet mirror. KEEP: frozen 1A/2A/3A/4A; docs→code→tests order.

## Review Triage Log

### 2026-10-17 — Pre-approval plan review
- verdicts: needs-revision — high 1, medium 2, low 1, false 0, maybe-false 0
- findings:
  - `[high]` `[patched]` post-write simplify vs inspect lock — Tasks/Code Map/AC now rewrite inspect for `apply_proposed`
  - `[medium]` `[patched]` companion sync under-specified — Design Notes target CAP-2/CAP-4 bullets + mermaid
  - `[medium]` `[patched]` helper/post-write behavior risk — Tasks require no final re-eval + correct u_track_max
  - `[low]` `[patched]` ratchet double-gate drift — optional mirror note in Tasks

### 2026-10-17 — Review pass (quick)
- verdicts: high 0, medium 0, low 1, false 0, maybe-false 0
- findings:
  - `[low]` `[patch]` `tests/test_hvac_app.py` saturated ratchet blocked branch left orphaned `compute_tracking`/`_run_guard` after dropping `write_guard` — verified unused; deleted; write_cfg + asserts kept
- followup_review_recommended: false

## Design Notes

**Target CAP-2 (`control-tick-behaviors.md`):** Replace the current “do not call `with_omega_c(proposed)` for that tick’s `compute_tracking`” block with:
1. May run a **provisional** track+guard with `with_omega_c(proposed)` solely as the apply-signal (to evaluate `should_apply_omega_c`).
2. If blocked: discard provisional; **write-path** track/guard/write/advance use **committed** ωc; do **not** re-evaluate apply/commit on the final guard.
3. If allowed: reuse provisional `u_track`/guard for write-path (no second track); persist only when `apply_proposed` after a successful write (outside decay).
4. Gate-only-on-persistence (apply proposed, skip commit) remains rejected.

**Target CAP-4:** Keep skip-adapt / decay / non-finite / trip-edge / 0.8 constant. Add:
- Soft-kill latch assigned only **after successful `_write_setpoint`** via sticky: `tripped ∨ (latch_in ∧ residue_holds)` where residue is `|u| > 0.8·u_track_max` or non-finite.
- Latch **holds** while residue is in `(0.8·u_track_max, u_track_max]` (even if not currently tripped); clears when finite `|u| ≤ 0.8·u_track_max`.
- On write failure, leave `_blow_up_latch` unchanged.

**Target flowchart:** Provisional track+guard → `{Directional blocks apply?}` → write-path track (committed if yes / reuse provisional if no) → `_write_setpoint` → sticky latch assign → `{residue decay?}` → else `{apply_proposed?}` → commit / skip. Do not label post-write J as a second `should_apply_omega_c` call.

**Post-write gate.** When `apply_proposed` is True, the write-path guard already passed `should_apply_omega_c`; a second helper call is identity. Commit when `apply_proposed` (outside decay) preserves “no resurrect.”

**Track+guard helper.** Pure function returning `(u_track, guard)` for a given ladrc config + `latch_in`, using **that** config’s `u_track_max`. Provisional path decides `apply_proposed` once; blocked path calls helper again only for committed ωc and must not re-call `should_apply_omega_c`.

**Companions vs ADR.** Story 1.4 shipped criterion A in ADR/house-calibration; deferred companions must match renegotiated Intent.

## Verification

**Commands:**
- `uv run pytest tests/test_hvac_app.py -q` -- expected: all green (no intentional behavior change)
- `uv run ruff check apps/hvac/hvac_app.py tests/test_hvac_app.py` -- expected: clean
