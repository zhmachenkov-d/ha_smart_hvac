# Walkthrough — PR #31: directional clamp + strict apply

Target: [PR #31](https://github.com/zhmachenkov-d/ha-smart-hvac/pull/31) (`feat/directional-clamp-strict-apply` → `main`, commit `2868763`)
Focus: human review of directional ωc clamp + strict apply
Current block: closed — walkthrough complete; wrap-up: deferred-work + follow-up commit/push + merge PR #31 + delete feature branch

## Blocks

- [x] **Intent** — done (renegotiated/polished)
- [x] **Broad strokes** — done
- [x] **Directional helper** — done (inspect patch)
- [x] **Strict apply in control_tick** — done
- [x] **Tests / R6 locks** — done
- [x] **Periphery** — done

## Intent

Source: [story-directional-clamp-strict-apply-plan.md](../epic-gate-omega-c-on-saturation/story-directional-clamp-strict-apply-plan.md) (frozen Intent, pasted verbatim).

**Problem:** Healthy-but-saturated ticks still apply and commit upward ωc while Set Water Temperature sits at `setpoint_max`, ratcheting the tuner until a later ESO reset latches soft-kill.

**Approach:** Add directional `should_commit_omega_c` (skip on guard trip, max+ωc↑, min+ωc↓; allow relieving moves) and strict apply so a blocked proposal never enters **write-path** `with_omega_c` / `compute_tracking` / persistence. An **apply-signal** may run a provisional track+guard with proposed ωc only to evaluate the helper; if blocked, discard and track/write with committed ωc, and do not re-evaluate commit on the final guard. Wire both in `control_tick`; lock with a commit matrix and a Hass-free saturated upward-proposal ratchet regression.

**Always:**
- Directional clamp and strict apply together (persistence-only gating forbidden).
- Commit still skipped on guard trip; relieving ωc at a clamp may commit.
- Provisional evaluate of proposed ωc for the apply gate is allowed; a blocked proposal must not enter write-path tracking or persistence.
- Choose committed vs proposed ωc for **write-path** tracking before that tracking runs (architecture “Directional blocks apply?” node); the diagram omits the provisional apply-signal pass — Approach governs that detail.
- R6 (a)(b) only in this story; write-on-change, latch decay, and docs stay later entries.

**Never:**
- Full freeze of ωc on any clamp.
- Changing `setpoint_min`/`setpoint_max`, `u_track_max`, or online `b0`/`ωo`/MADRC.
- Gate-only-on-persistence while still applying proposed ωc for the tick.
- Latch-decay / skip-adapt-while-latched (entry 2).
- ADR / house-calibration edits (entry 4).

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

**Review notes (Intent):**
1. Renegotiated during walkthrough: Approach/Always now distinguish apply-signal provisional vs write-path (closes R2 companion wording tension for this story).
2. Companion `control-tick-behaviors.md` R2 literal still older — deferred to later doc sync (option 3 not chosen).
3. Always bullet now notes arch diagram omits provisional; Approach wins. Min+ωc↓ matrix aligned with Max+ωc↑ write-path wording.

## Broad strokes

What the change is: directional [`should_commit_omega_c`](../../../apps/hvac/hvac_app.py) gates both apply and commit so saturated upward (or min+down) proposals never enter write-path tracking or persistence (a provisional apply-signal may still evaluate proposed ωc); relieving moves and interior ticks may still apply and commit.

Entry points (open in this order):

1. [`should_commit_omega_c`](../../../apps/hvac/hvac_app.py) — pure directional + guard-trip gate
2. [`control_tick`](../../../apps/hvac/hvac_app.py) — provisional apply / write-path / commit via helper
3. [`guard_u_track`](../../../apps/hvac/hvac_app.py) — reused; trip criteria unchanged
4. [tests/test_hvac_app.py](../../../tests/test_hvac_app.py) — matrix, ratchet, inspect
5. [story-directional-clamp-strict-apply-plan.md](../epic-gate-omega-c-on-saturation/story-directional-clamp-strict-apply-plan.md) — built plan / AC

**Review notes (Broad strokes):**
1. Local Verification green (50 tests, ruff). CI on PR #31 all pass.
2. Uncommitted plan Intent polish + walkthrough not yet on the PR branch tip.

## Directional helper

[`should_commit_omega_c`](../../../apps/hvac/hvac_app.py) is a pure predicate: reject `None`, guard trip, max+ωc↑, and min+ωc↓; otherwise allow (so relieving moves at a clamp and interior commands may commit). The same helper is used for the provisional apply gate and the post-write commit gate — persistence-only gating is not enough.

**Review notes (Directional helper):**
1. Formal review (quick): inspect lock used `index("commit_omega_c")`, which matched inside `should_commit_omega_c` — patched to `_tuner.commit_omega_c`.

## Strict apply in control_tick

In [`control_tick`](../../../apps/hvac/hvac_app.py), when there is a proposal: provisional [`compute_tracking`](../../../apps/hvac/ladrc.py) + [`guard_u_track`](../../../apps/hvac/hvac_app.py) with proposed ωc → [`should_commit_omega_c`](../../../apps/hvac/hvac_app.py). If the helper is false: final track+guard with committed ωc and skip commit (`omega_to_commit = None` — no re-eval that could resurrect). If true: reuse provisional `u_track`/guard for write/advance. Latch/WARN only from the write-path guard; post-write commit calls the helper again on `omega_to_commit`.

- [`control_tick` apply_proposed / provisional](../../../apps/hvac/hvac_app.py)
- [`control_tick` omega_to_commit / commit gate](../../../apps/hvac/hvac_app.py)

**Review notes (Strict apply):**
1. Thoughts: wiring matches Design Notes (no-resurrect, latch from write guard, zone reset once).
2. Test: local `test_hvac_app` 31 passed + ruff; CI on PR tip still green (inspect patch unpushed).

## Tests / R6 locks

- [test_should_commit_omega_c_matrix](../../../tests/test_hvac_app.py) — R6(a) parametrized matrix
- [test_saturated_upward_proposal_does_not_ratchet_applied_or_committed](../../../tests/test_hvac_app.py) — R6(b) Hass-free ratchet
- [test_control_tick_skips_commit_omega_c_when_guard_tripped](../../../tests/test_hvac_app.py) — inspect lock on helper wiring / `omega_to_commit`

**Review notes (Tests):**
1. Thoughts: R6(a)(b) as planned; known gaps (no live tick / no min ratchet) accepted.
2. Test: R6 trio 9 passed; Verification 50 passed + ruff clean (includes inspect patch).

## Periphery

- [story-directional-clamp-strict-apply-plan.md](../epic-gate-omega-c-on-saturation/story-directional-clamp-strict-apply-plan.md) — status `built`; planning artifact and AC source

**Review notes (Periphery):**
1. Companion R2 / arch diagram still stale vs renegotiated Intent — defer doc sync; record in deferred-work on wrap-up if desired.
2. Dirty tree: plan Intent polish, inspect patch, walkthrough-pr-31/ — follow-up commit + push to PR #31.
