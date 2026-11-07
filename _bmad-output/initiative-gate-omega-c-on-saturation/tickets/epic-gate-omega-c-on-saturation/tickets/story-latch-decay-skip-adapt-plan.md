---
title: 'Latch decay + skip adapt'
type: 'feature'
ticket: '2'
created: '2026-10-17'
status: done
baseline_revision: 'a05577942e6bea82afd0cc81f0b4f3c0930cb7eb'
route: 'full'
route_source: 'auto'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 1
followup_review_recommended: false
context:
  - '{project-root}/_bmad-output/initiative-gate-omega-c-on-saturation/spec-gate-omega-c-on-saturation/spec-gate-omega-c-on-saturation.md'
  - '{project-root}/_bmad-output/initiative-gate-omega-c-on-saturation/spec-gate-omega-c-on-saturation/control-tick-behaviors.md'
  - '{project-root}/_bmad-output/initiative-gate-omega-c-on-saturation/spec-gate-omega-c-on-saturation/architecture-diagrams.md'
warnings: []
deferred: []
---

<intent-contract>

## Intent

**Problem:** Once the blow-up soft-kill latch sticks, healthy ticks still call `maybe_adapt` and cannot step ωc down on real `|u_track|`, so recovery stays ops-only.

**Approach:** When latch is already active at tick start, skip `maybe_adapt` entirely. After write-path `u_track` is known **and** the plant write succeeds, assign a **sticky** soft-kill latch (`tripped` or prior latch while residue holds)—so the latch stays active in `(0.8·u_track_max, u_track_max]` and clears only when finite `|u_track| ≤ 0.8·u_track_max` (not when `|u|≤u_track_max` alone). While that sticky latch is active and residue holds (`|u_track| > 0.8·u_track_max` or non-finite), step committed ωc down by tuner `max_rate_fraction` (≥ `omega_c_min`) and persist even when guard trip blocks normal `commit_omega_c`. On write failure, leave `_blow_up_latch` unchanged (WARN may still fire before write).

## Boundaries & Constraints

**Always:**
- Skip adapt uses latch state at **tick start** (before `maybe_adapt` / zone-change clear).
- Sticky CAP-4 latch (not `latch_out` alone) only after successful `_write_setpoint`: hold in `(0.8·u_track_max, u_track_max]` so the 0.8 stop band is reachable; fail-write does not mutate latch.
- Decay uses **actual tick `|u_track|`** (write-path), not `|ωc·e/b0|`; threshold `0.8` is a code constant.
- Decay step/floor reuse existing `max_rate_fraction` / `omega_c_min`; persist via tuner even when `should_commit_omega_c` would skip.
- Trip-edge tick may still adapt before the guard; decay may run that same tick once latch is active and residue holds (architecture H→I).
- CAP-6 (e) only; write-on-change and docs stay later entries.

**Never:**
- Propose-then-override while latched; hard reset to `config.omega_c`; one-shot safe-ωc jump.
- Changing `u_track_max`, plant limits, or online `b0`/`ωo`/MADRC.
- YAML knob for the 0.8 band; predicted `|ωc·e/b0|` as decay criterion.
- Directional/strict-apply rework (entry 1 done); ADR / house-calibration (entry 4).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Latched at start | `_blow_up_latch` True entering demand path | `maybe_adapt` not called; track with committed ωc | No error |
| Latched + residue high | Latch active after write; `|u_track| > 0.8·u_track_max` | ωc steps down by `max_rate_fraction·ωc`, floored at `omega_c_min`, persisted; normal commit skipped | No error |
| Latched + residue OK | Latch active; finite `|u_track| ≤ 0.8·u_track_max` | No decay; adapt still skipped while latched at start | No error |
| Non-finite u_track | Latch active; `u_track` nan/inf | Same step-down persist as high residue | No error |
| Trip-edge | Latch False at start; guard trips this tick; residue high | Adapt may have run; commit skipped by trip; decay may persist | No error |
| Multi-tick decay | Latch held; `|u_track|` stays above band | Persisted ωc decreases each tick until band or floor | No error |

</intent-contract>

## Code Map

- `apps/hvac/hvac_app.py` `control_tick` ~183–302 — today always calls `maybe_adapt` then strict-apply / `should_commit_omega_c`. Capture latch-at-start; if True skip `maybe_adapt` (`new_omega_c=None`). After write-path guard, assign sticky CAP-4 latch (Design Notes) — do not copy `guard.latch_out` alone. After successful write + ESO advance, decay branch before normal commit (architecture I vs J).
- `apps/hvac/hvac_app.py` — add pure helpers: latch-decay residue predicate (`|u| > 0.8·u_track_max` or non-finite) and next ωc (step down by `max_rate_fraction·ωc`, floor `omega_c_min`). Constant `0.8` beside helpers. Optional pure sticky-latch helper if it keeps `control_tick` thin.
- `apps/hvac/ladrc_tuner.py` `commit_omega_c` / `max_rate_fraction` / `omega_c_min` — reuse persist; do not change adapt rate math or bounds API.
- `apps/hvac/hvac_app.py` `guard_u_track` — reuse trip/command/`should_warn` as-is; do not change trip magnitude. Sticky soft-kill for CAP-4 is assigned in `control_tick` after the guard returns (not by rewriting `latch_out=tripped` inside `guard_u_track` unless that is the smallest equivalent).
- `tests/test_hvac_app.py` — residue/step matrix; sticky-latch matrix (trip sets; holds in `(0.8·max, max]`; clears at ≤ band); latched-at-start skips adapt (inspect); multi-tick + non-finite + trip-edge lock **persisted** ωc via real `LadrcTuner.commit_omega_c` / state file (not helper-only mirrors). Reuse `_config` / tuner tmp_path patterns from `tests/test_ladrc_tuner.py`.
- Spec companions (context frontmatter) — CAP-4 matrix + architecture H→I are the contract; ignore outdated Cursor freeze plans.

## Tasks & Acceptance

**Execution:**
- [x] `apps/hvac/hvac_app.py` -- Add decay helpers + `0.8` constant; skip-`maybe_adapt` when latch active at tick start; after write-path guard assign sticky CAP-4 latch; after write+advance if latch active and residue holds, step ωc down and `commit_omega_c`, else `should_commit_omega_c` path -- Implements CAP-4 including reachable 0.8 stop band.
- [x] `tests/test_hvac_app.py` -- Lock residue/step + sticky latch; latched-at-start skips adapt; multi-tick / non-finite / trip-edge decay with real tuner persist until ≤ `0.8·u_track_max` or floor -- Locks CAP-6 (e).

**Acceptance Criteria:**
- Given latch already active at tick start, when the demand tick runs, then `maybe_adapt` is not called.
- Given latch active and `|u_track| > 0.8·u_track_max`, when the tick completes a successful write, then persisted ωc decreases by one `max_rate_fraction` step (≥ `omega_c_min`).
- Given repeated latched ticks with `|u_track|` above the band, when enough ticks run, then persisted ωc decays until finite `|u_track|` would be ≤ `0.8·u_track_max` or ωc hits `omega_c_min`.
- Given latch active and non-finite `u_track`, when decay is evaluated, then ωc steps down and persists.

## Implementation Notes

- Re-derive after bad_plan: sticky_blow_up_latch + skip-adapt + decay commit; CAP-6(e) tests use real LadrcTuner persist (74 pytest green).

## Plan Change Log

- 2026-10-17 review bad_plan: assigning `_blow_up_latch = guard.latch_out` alone made finite stop at `0.8·u_track_max` unreachable (`latch_out` clears once `|u|≤u_track_max`). Amended Code Map / Design Notes / Tasks for sticky CAP-4 latch after guard + tuner-persist tests. Known-bad avoided: decay-only-while-tripping with helper-only multi-tick mirror. KEEP: `LATCH_DECAY_U_TRACK_FRACTION` / `latch_decay_residue_holds` / `next_decayed_omega_c`; latched-at-start skip-adapt; decay `commit_omega_c` branch before `should_commit` else; entry-1 strict-apply untouched.

## Review Triage Log

### 2026-10-17 — Review pass
- verdicts: 5 findings — high 0, medium 3, low 2, false 0, maybe-false 0
- findings:
  - `[medium]` `[bad_plan]` CAP-4 stop at ≤0.8·u_track_max unreachable under latch_out=tripped — verified: decay requires latch and residue; latch_out equals tripped so finite decay only while `|u|>u_track_max`. Amendment: sticky CAP-4 latch after guard (see Plan Change Log).
  - `[medium]` `[bad_plan]` non-finite test does not lock persist — same root: helper-only CAP-6(e); amendment requires `LadrcTuner.commit_omega_c` / state file in tests.
  - `[medium]` `[bad_plan]` multi-tick mirror never persists via tuner — same root / amendment.
  - `[low]` `[bad_plan]` multi-tick forces sticky latch production does not have — same root as finding 1; sticky assignment is the plan fix.
  - `[low]` `[bad_plan]` trip-edge inspect-only, no persist proof — same root / amendment (behavioral trip-edge + tuner persist).

### 2026-10-17 — Review pass
- verdicts: 3 findings — high 0, medium 0, low 2, false 1, maybe-false 0
- findings:
  - `[low]` `[patch]` trip-edge test bypassed decay branch with direct commit_omega_c — verified; rewritten to use `_mirror_decay_tick(latch=False, u_track=150)`.
  - `[low]` `[patch]` unused `_decay_tuner` orphan — verified unused; deleted.
  - `[false]` `[reject]` multi-tick only hits floor not band-exit — AC allows floor or ≤0.8 band; band clear locked by `test_decay_stops_when_residue_at_or_below_band`.

## Auto Run Result

- **Summary:** CAP-4 latch decay + skip-adapt: while latched at tick start, skip `maybe_adapt`; sticky soft-kill latch holds while residue > 0.8·u_track_max; stepped ωc persist via `commit_omega_c` even when guard trip blocks normal commit.
- **Files changed:**
  - `apps/hvac/hvac_app.py` — decay helpers, sticky latch, skip-adapt, decay commit branch
  - `tests/test_hvac_app.py` — CAP-6(e) matrices and tuner-persist mirrors
  - plan file — story 1.2 build plan
- **Review:** first pass bad_plan (sticky latch) → re-derive; second pass 2 low patches applied, 1 false rejected; deferred none. Patched counts this pass: high 0, medium 0, low 2 → followup_review_recommended false.
- **Verification:** `uv run pytest tests/test_hvac_app.py tests/test_ladrc_tuner.py -q` → 74 passed; `uv run ruff check apps/hvac/hvac_app.py tests/test_hvac_app.py` → clean.
- **Residual risks:** Decay/skip-adapt persist locked via Hass-free `_mirror_decay_tick`, not a live AppDaemon `control_tick` (same pattern as entry 1 ratchet). CAP-3/CAP-5 remain later epic entries.

## Design Notes

**Latch-at-start vs post-guard latch.** Skip adapt reads `_blow_up_latch` before `maybe_adapt` (and before `latch_after_zone_change`). After write-path `guard_u_track`, do **not** set `_blow_up_latch = guard.latch_out` alone: that clears as soon as `|u|≤u_track_max` and makes the CAP-4 stop band unreachable.

**Sticky CAP-4 latch (locked).** Let `latch_in` be `_blow_up_latch` after zone-change clear (the value passed into `guard_u_track`). After **successful** `_write_setpoint` (not merely after the write-path guard returns), set:
`_blow_up_latch = guard.tripped or (latch_in and latch_decay_residue_holds(u_track, u_track_max))`.
Fail-write leaves `_blow_up_latch` unchanged. WARN may still fire before write. Trip-edge (`latch_in` False, `tripped` True) latches and may decay the same tick after a successful write. While residue holds above the 0.8 band, latch stays True even if not currently tripped. When finite `|u|≤0.8·u_track_max`, latch clears. Keep using `guard.should_warn` / `guard.tripped` for WARN and ESO reset — do not change soft-kill command selection.

**Decay vs normal commit.** Architecture: decay branch ends the tick without `should_commit_omega_c`. Do not also commit a proposed ωc on a decay tick. Decay reads `_blow_up_latch` after the sticky assignment above.

**Step size.** Match adapt’s magnitude: `step = max_rate_fraction * current_omega_c`; `new = max(omega_c_min, current - step)`. Persist via existing `commit_omega_c`.

**Strict apply when not latched-at-start.** Leave entry-1 provisional/write-path wiring unchanged when adapt runs.

**Tests (locked).** Multi-tick / non-finite / trip-edge must call real `LadrcTuner.commit_omega_c` (tmp_path state) so “persists” is locked; sticky-latch matrix must cover hold in `(0.8·max, max]` and clear at ≤ band.

## Verification

**Commands:**
- `uv run pytest tests/test_hvac_app.py tests/test_ladrc_tuner.py -q` -- expected: all green, including new latch-decay / skip-adapt coverage
- `uv run ruff check apps/hvac/hvac_app.py tests/test_hvac_app.py` -- expected: clean
