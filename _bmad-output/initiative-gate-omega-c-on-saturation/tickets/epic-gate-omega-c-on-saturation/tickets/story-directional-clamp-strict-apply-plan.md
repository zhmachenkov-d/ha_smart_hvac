---
title: 'Directional clamp + strict apply'
type: 'feature'
ticket: '1'
created: '2026-10-16'
status: done
baseline_revision: '8ad563afd6d354c0e492995d631b10c71b6daff1'
route: 'full'
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

**Problem:** Healthy-but-saturated ticks still apply and commit upward ωc while Set Water Temperature sits at `setpoint_max`, ratcheting the tuner until a later ESO reset latches soft-kill.

**Approach:** Add directional `should_commit_omega_c` (skip on guard trip, max+ωc↑, min+ωc↓; allow relieving moves) and strict apply so a blocked proposal never enters **write-path** `with_omega_c` / `compute_tracking` / persistence. An **apply-signal** may run a provisional track+guard with proposed ωc only to evaluate the helper; if blocked, discard and track/write with committed ωc, and do not re-evaluate commit on the final guard. Wire both in `control_tick`; lock with a commit matrix and a Hass-free saturated upward-proposal ratchet regression.

## Boundaries & Constraints

**Always:**
- Directional clamp and strict apply together (persistence-only gating forbidden).
- Commit still skipped on guard trip; relieving ωc at a clamp may commit.
- Provisional evaluate of proposed ωc for the apply gate is allowed; a blocked proposal must not enter write-path tracking or persistence.
- Choose committed vs proposed ωc for **write-path** tracking before that tracking runs (architecture “Directional blocks apply?” node); the diagram omits the provisional apply-signal pass — Approach governs that detail.
- CAP-6 (a)(b) only in this story; write-on-change, latch decay, and docs stay later entries.

**Never:**
- Full freeze of ωc on any clamp.
- Changing `setpoint_min`/`setpoint_max`, `u_track_max`, or online `b0`/`ωo`/MADRC.
- Gate-only-on-persistence while still applying proposed ωc for the tick.
- Latch-decay / skip-adapt-while-latched (entry 2).
- ADR / house-calibration edits (entry 4).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| No proposal | `proposed is None` | Do not commit; track with committed ωc | No error |
| Guard tripped | `tripped=True`, any command / Δωc | Skip commit | No error |
| Max + ωc↑ | `command >= max`, proposed > current | Skip commit; write-path tracking must use current ωc | No error |
| Max + ωc↓ | `command >= max`, proposed < current | May commit; tracking may use proposed | No error |
| Min + ωc↓ | `command <= min`, proposed < current | Skip commit; write-path tracking must use current ωc | No error |
| Min + ωc↑ | `command <= min`, proposed > current | May commit; tracking may use proposed | No error |
| Interior | `min < command < max`, not tripped | May commit; tracking may use proposed | No error |
| Ratchet regression | Repeated saturated upward proposals at max | Applied and committed ωc do not rise across ticks | No error |

</frozen-after-approval>

## Code Map

- `apps/hvac/hvac_app.py` `control_tick` ~162–219 — today: `maybe_adapt(apply=False)` → always `with_omega_c(proposed|committed)` → track → guard → write → `if new_omega_c and not guard.tripped: commit`. Replace apply selection and commit gate with `should_commit_omega_c`.
- `apps/hvac/hvac_app.py` `guard_u_track` ~43–76 — reuse for provisional and real command/`tripped`; do not change trip criteria.
- `apps/hvac/ladrc.py` `LadrcState.compute_tracking` ~26–40 — pure u_track (no ESO advance); safe for a provisional pass before final track. Do not change math.
- `apps/hvac/ladrc_tuner.py` `maybe_adapt` / `commit_omega_c` — keep `apply=False` + explicit commit; do not change rate/deadband/bounds.
- `apps/hvac/models.py` `LadrcConfig.with_omega_c` — reuse; no API change.
- `tests/test_hvac_app.py` — add `should_commit_omega_c` matrix; update `test_control_tick_skips_commit_omega_c_when_guard_tripped` (~339) inspect lock to the helper; add Hass-free ratchet loop that mirrors strict-apply selection (which ωc enters write-path `compute_tracking` / `with_omega_c`) plus committed ωc (reuse `_run_guard` / `_config` patterns ~26–58).
- `tests/test_ladrc_tuner.py` `_tuner` / `_steady_adapt` / `test_maybe_adapt_deferred_apply` — reuse propose-then-commit pattern; prefer not to change tuner tests unless a shared fixture helps.
- Spec companions (context frontmatter) — behavior matrices and tick flowchart are the contract; Cursor plan `gate_omega_c_on_saturation_*.plan.md` is outdated (full freeze + persistence-only) — ignore.

## Tasks & Acceptance

**Execution:**
- [x] `apps/hvac/hvac_app.py` -- Add pure `should_commit_omega_c(proposed, current, *, guard_tripped, command, setpoint_min, setpoint_max) -> bool` per control-tick-behaviors matrix; wire strict apply (provisional track+guard with proposed → if helper false, final track+guard with committed and **skip commit**; if helper true, **reuse** provisional u_track/guard for write/advance and commit only via helper on that reused guard). Latch/WARN only from the guard chosen for write. -- Implements CAP-1/CAP-2 without persistence-only gating or resurrected upward commit.
- [x] `tests/test_hvac_app.py` -- Parametrized matrix for the helper (None / tripped / max+up / max+down / min+down / min+up / interior); Hass-free saturated upward-proposal loop asserting **write-path applied** and committed ωc do not rise; update inspect assertions to require `should_commit_omega_c` after successful write -- Locks CAP-6 (a)(b) and tick wiring.

**Acceptance Criteria:**
- Given command at `setpoint_max` and an upward proposed ωc, when the tick runs, then proposed ωc is neither applied to `compute_tracking` nor committed.
- Given command at `setpoint_max` and a downward proposed ωc (and not tripped), when commit is evaluated, then commit may proceed.
- Given a Hass-free saturated upward-proposal scenario, when many ticks propose higher ωc at max, then neither applied nor committed ωc increases.
- Given guard trip, when commit is evaluated, then ωc is not committed (existing AI-5 behavior preserved via the helper).

## Implementation Notes

## Plan Change Log

- 2026-10-17 walkthrough: polish Always — write-path choice cites arch node but Approach governs provisional; Min+ωc↓ matrix says write-path tracking (symmetric with Max+ωc↑).
- 2026-10-17 walkthrough: human renegotiated frozen Intent — Approach names apply-signal provisional vs write-path; Always allows provisional evaluate; Max+ωc↑ matrix says write-path tracking.
- 2026-10-17 review: block — skip commit when provisional helper false (no re-eval on final guard). should-fix — ratchet locks write-path applied ωc; latch/WARN only from write guard. nit — Intent says write-path tracking.

## Review Triage Log

| finding | verdict | evidence / route |
|---------|---------|------------------|
| Provisional `compute_tracking` vs literal AC/CAP-2 wording | false | Frozen Intent Approach allows a provisional pass for the apply gate and names **write-path** tracking; Design Notes lock provisional track+guard. Code matches Intent. Fixing AC/companion wording would edit the plan — rejected. |
| Hass-free ratchet reimplements selection, does not call `control_tick` | false | Plan Code Map / CAP-6(b) explicitly ask for a Hass-free loop that **mirrors** strict-apply selection; that shape is met. Production wiring is separately inspect-locked. |
| Inspect lock does not require helper return to gate `commit_omega_c` | low → patch | Claim verified: substring-only asserts allow a dead `should_commit_omega_c` call plus unconditional commit. Strengthen inspect to lock `omega_to_commit` / `if should_commit_omega_c` gating. |
| Unrelated `.memlog.md` in diff | low → patch | Party-mode memlog dirty tree, not part of Code Map. Reverted to HEAD (surgical hygiene). |

## Design Notes

**Apply-signal (locked):** provisional track+guard — not `_last_command`, not plant-entity read (entry 3).

**Strict-apply ordering.** Architecture flowchart decides “Directional blocks apply?” before the tracking used for write. `compute_tracking` does not advance the ESO, so a provisional pass with proposed ωc + `guard_u_track` (same latch/`u_ff`/bounds) yields `command`/`tripped` for `should_commit_omega_c`.
- If helper is **false**: discard proposed; run final `compute_tracking` + `guard_u_track` with **committed** ωc for write/advance; **do not commit** (do not re-evaluate the helper on the final guard — that can resurrect an upward commit when final command leaves the clamp).
- If helper is **true**: **reuse** provisional `u_track` and guard for write/advance; commit only if `should_commit_omega_c` is true on that **reused** guard (post-write).
- Latch / blow-up WARN: apply only from the guard chosen for write — never stick latch or emit WARN from a discarded provisional guard.
- Zone change: `compute_tracking` may `reset` on critical-zone switch. Provisional and final share the same `critical_zone` for the tick, so reset runs at most once (on the first pass that sees the new zone). Never run provisional and final with different zone ids.

**Relieving commit (locked):** I/O keeps CAP-1 **may** (not must). Matrix/tests: for max+ωc↓ / min+ωc↑ and not tripped, assert `should_commit_omega_c` returns True; do not require a full tick persistence proof beyond that in this story.

**Directional, not full freeze.** At max, only ωc↑ is blocked; ωc↓ may apply and commit. Symmetric at min.

**Inspect locks.** Existing source asserts on `not guard.tripped` must move to the helper so wiring cannot regress to persistence-only gating.

## Verification

**Commands:**
- `uv run pytest tests/test_hvac_app.py tests/test_ladrc_tuner.py -q` -- expected: all green, including new matrix and ratchet regression
- `uv run ruff check apps/hvac/hvac_app.py tests/test_hvac_app.py` -- expected: clean

## Code Review

### 2026-10-17

**Code review complete.** 0 `decision-needed`, 1 `patch`, 0 `defer`, 0 rejected.

- [x] [Review][Patch] Inspect lock matches `commit_omega_c` inside `should_commit_omega_c` [tests/test_hvac_app.py:352]

**Rejected:** (none)
