# Walkthrough — PR #39: omega-c gate refactor sweep

Target: [PR #39](https://github.com/zhmachenkov-d/ha-smart-hvac/pull/39) (`refactor/1-5-omega-c-sweep` → `main`, commit `15c23bb`)
Focus: human review of story 1.5 closing sweep (companion sync + naming/helper cleanups; no intentional behavior change)
Current block: closed — walkthrough complete; wrap-up: commit/push + merge PR #39 + mark story 1.5/epic/initiative done + delete feature branch

## Blocks

- [x] **Intent** — done
- [x] **Broad strokes** — done
- [x] **Companion R2/R4 sync** — done (intro R2 edited during review)
- [x] **should_apply_omega_c + track_and_guard** — done
- [x] **Post-write apply_proposed + tests** — done (inspect renamed during review)
- [x] **Periphery** — done

## Intent

Source: [story-refactor-sweep-plan.md](../epic-gate-omega-c-on-saturation/story-refactor-sweep-plan.md) (frozen Intent).

**Problem:** After R1–5 landed, deferred companion drift (R2 provisional apply-signal; R4 sticky-after-write) and soft review nits in `control_tick` (helper naming, redundant post-write commit re-check, duplicated track+guard branches) remain as maintenance debt with no intentional behavior change owed.

**Approach:** Closing sweep: sync deferred companions to stories 1–2 Intents; rename `should_commit_omega_c` → `should_apply_omega_c`; extract a tiny track+guard helper to collapse the three branches; simplify post-write commit to `apply_proposed` (no second helper call); leave `GuardUTrackResult.latch_out` as-is. Keep pytest green; no new capabilities.

**Review notes (Intent):**
1. Frozen Intent matches behavior-preserving close-out — companions + naming/helper nits only; no new capabilities in diff.
2. R2/R4 companions, flowchart, and [deferred-work.md](../deferred-work.md) align with stories 1–2 renegotiated wording; PR #31/#34 deferred entries cleared.
3. Shipped `control_tick`: `should_apply_omega_c`, `track_and_guard`, post-write `apply_proposed` commit, sticky-after-write; blocked path does not re-eval the helper on the final guard.
4. `GuardUTrackResult.latch_out` untouched; sticky path used — no Intent gaps vs code.

## Broad strokes

What the change is: behavior-preserving close-out of the omega-c gate epic — companions and flowchart catch up to renegotiated R2/R4 wording, and `control_tick` naming/structure matches that language without a second post-write apply gate.

Entry points (open in this order):

1. [`should_apply_omega_c`](../../../apps/hvac/hvac_app.py#L112) — renamed directional + guard apply gate
2. [`track_and_guard`](../../../apps/hvac/hvac_app.py#L239) — nested helper collapsing provisional / blocked-final / no-proposal track+guard
3. [post-write `if apply_proposed:`](../../../apps/hvac/hvac_app.py#L326) — normal commit after successful write (decay branch unchanged)
4. [R2 / R4 companions](../control-tick-behaviors.md) — provisional apply-signal; sticky-after-write
5. [flowchart](../architecture-diagrams.md) — provisional → write → sticky → `apply_proposed?`

**Review notes (Broad strokes):**
1. Five entry points cover rename gate, `track_and_guard` collapse, post-write `apply_proposed`, CAP companions, and flowchart — enough to grasp the mechanism without listing every touched file.
2. Sticky-after-write (`sticky_blow_up_latch` post-write) is intentionally not a sixth code entry; companions + flowchart carry it for Broad strokes (detail in later slices).
3. Inspect/tests and `deferred-work.md` correctly deferred out of Broad strokes.
4. Diff confirms behavior-preserving structure change only (rename + helper extract + drop second helper / `omega_to_commit`); no Broad strokes gaps vs Intent.

## Companion R2/R4 sync

Companions and mermaid now state the renegotiated Intent: provisional track+guard is an apply-signal only; blocked write-path uses committed ωc with no final re-eval; sticky latch is assigned after successful `_write_setpoint` and holds in `(0.8·u_track_max, u_track_max]`. Deferred PR #31 / #34 entries are cleared.

- [control-tick-behaviors.md R2](../control-tick-behaviors.md) — provisional apply-signal bullets
- [control-tick-behaviors.md R4](../control-tick-behaviors.md) — sticky-after-write + hold band
- [architecture-diagrams.md](../architecture-diagrams.md) — flowchart nodes through `apply_proposed?`
- [deferred-work.md](../deferred-work.md) — no open companion items

**Review notes (Companion R2/R4 sync):**
1. R2/R4 bullets and flowchart match plan Design Notes targets verbatim (provisional apply-signal; sticky-after-write; J=`apply_proposed?`).
2. [deferred-work.md](../deferred-work.md) cleared of PR #31/#34 entries — companion debt closed.
3. Soft residual closed: R2 intro rewritten to frame proposed-ωc apply (block *and* allow), not only “would block…”.
4. No companion/flowchart gaps vs renegotiated Intent or shipped tick order.

## should_apply_omega_c + track_and_guard

Symbol rename matches R2 “apply” language. Nested `track_and_guard` takes the ladrc config (and its `u_track_max`) plus latch; provisional path sets `apply_proposed`, blocked path re-tracks with committed ωc and must not re-call the apply helper on that final guard.

- [`should_apply_omega_c`](../../../apps/hvac/hvac_app.py#L112) — rename + docstring
- [`track_and_guard`](../../../apps/hvac/hvac_app.py#L239) — compute_tracking + `guard_u_track`
- [provisional / blocked / no-proposal](../../../apps/hvac/hvac_app.py#L258) — three call sites; blocked comment forbids final re-eval

**Review notes (should_apply_omega_c + track_and_guard):**
1. Rename is docstring-level; predicate body unchanged vs prior `should_commit_omega_c` (behavior-preserving).
2. Nested `track_and_guard` uses **that** ladrc’s `u_track_max` + passed latch; three call sites (provisional / blocked-final / no-proposal) match Design Notes.
3. Blocked path re-tracks committed only — no second `should_apply_omega_c` on the final guard (comment + code).
4. Soft (accepted): Design Notes said “pure function”; nested closure over `decision`/`u_ff`/bounds is what Tasks allowed (“module-level or nested”).
5. Test: `test_should_apply_omega_c_matrix` + ratchet + inspect skip-commit — 9 passed; broader apply/sticky/decay `-k` slice + ruff clean.

## Post-write apply_proposed + tests

After a successful write, normal ωc commit is gated only by `apply_proposed` (write-path already passed the gate). Inspect test locks rename + absence of a second helper in the post-write region; matrix test renamed.

- [post-write commit](../../../apps/hvac/hvac_app.py#L313) — decay branch, else `if apply_proposed:`
- [`test_control_tick_persists_omega_c_via_apply_proposed_after_write`](../../../tests/test_hvac_app.py#L349) — inspect locks
- [`test_should_apply_omega_c_matrix`](../../../tests/test_hvac_app.py#L398) — renamed matrix

**Review notes (Post-write apply_proposed + tests):**
1. Post-write normal commit is `if apply_proposed:` only — no second helper / no `omega_to_commit`; decay branch still precedes it (same order as before).
2. Inspect locks rename, post-write absence of helper/`omega_to_commit`, `commit_omega_c(new_omega_c)`, anti persistence-only, decay-before-gate order.
3. Hass-free ratchet already mirrors production: blocked → committed write_cfg; commit only when `apply_proposed` (optional plan mirror satisfied).
4. Soft residual closed: inspect renamed to `test_control_tick_persists_omega_c_via_apply_proposed_after_write`.

## Periphery

- [story-refactor-sweep-plan.md](../epic-gate-omega-c-on-saturation/story-refactor-sweep-plan.md) — plan artifact (`status: built`)
- `GuardUTrackResult.latch_out` left intact (not removed; `control_tick` still prefers sticky)
- Review edits (not in original PR commit): R2 intro in [control-tick-behaviors.md](../control-tick-behaviors.md); inspect rename in `tests/test_hvac_app.py`; this walkthrough folder

**Review notes (Periphery):**
1. Plan `status: built`; ADR/`docs/` have no leftover `should_commit_omega_c`.
2. `latch_out` still on `GuardUTrackResult`; `control_tick` does not read `guard.latch_out` (inspect already locks this).
3. Soft (accepted): older story plans / walkthroughs still name the pre-rename inspect — historical, not this PR’s deliverable.
4. Review deltas (R2 intro, inspect rename, walkthrough) need commit + push onto PR #39 before merge.
