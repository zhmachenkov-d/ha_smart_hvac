# Walkthrough — PR #34: latch ωc decay + skip adapt

Target: [PR #34](https://github.com/zhmachenkov-d/ha-smart-hvac/pull/34) (`feat/1-2-latch-decay-skip-adapt` → `main`)
Focus: human review of R4 latch decay + skip-adapt while soft-kill held
Current block: closed — walkthrough complete; wrap-up: commit/push + merge PR #34 + mark story 1.2 done + delete feature branch

## Blocks

- [x] **Intent** — done (renegotiated sticky in Approach/Always)
- [x] **Broad strokes** — done (prose/anchors patched)
- [x] **Decay helpers + sticky latch predicate** — done (Thoughts + Test 18 passed)
- [x] **Skip-adapt + sticky latch in control_tick** — done (sticky-after-write patch)
- [x] **Decay commit vs should_commit** — done (mirror write_ok patch)
- [x] **Tests / R6(e) locks** — done (75 passed; R1–R3 accepted)
- [x] **Periphery** — done (R4 companion deferred)

## Intent

Source: [story-latch-decay-skip-adapt-plan.md](../epic-gate-omega-c-on-saturation/story-latch-decay-skip-adapt-plan.md) (intent-contract; Approach/Always renegotiated in this walkthrough).

**Problem:** Once the blow-up soft-kill latch sticks, healthy ticks still call `maybe_adapt` and cannot step ωc down on real `|u_track|`, so recovery stays ops-only.

**Approach:** When latch is already active at tick start, skip `maybe_adapt` entirely. After write-path `u_track` is known **and** the plant write succeeds, assign a **sticky** soft-kill latch (`tripped` or prior latch while residue holds)—so the latch stays active in `(0.8·u_track_max, u_track_max]` and clears only when finite `|u_track| ≤ 0.8·u_track_max` (not when `|u|≤u_track_max` alone). While that sticky latch is active and residue holds (`|u_track| > 0.8·u_track_max` or non-finite), step committed ωc down by tuner `max_rate_fraction` (≥ `omega_c_min`) and persist even when guard trip blocks normal `commit_omega_c`. On write failure, leave `_blow_up_latch` unchanged (WARN may still fire before write).

**Always:**
- Skip adapt uses latch state at **tick start** (before `maybe_adapt` / zone-change clear).
- Sticky R4 latch (not `latch_out` alone) only after successful `_write_setpoint`: hold in `(0.8·u_track_max, u_track_max]` so the 0.8 stop band is reachable; fail-write does not mutate latch.
- Decay uses **actual tick `|u_track|`** (write-path), not `|ωc·e/b0|`; threshold `0.8` is a code constant.
- Decay step/floor reuse existing `max_rate_fraction` / `omega_c_min`; persist via tuner even when `should_commit_omega_c` would skip.
- Trip-edge tick may still adapt before the guard; decay may run that same tick once latch is active and residue holds (architecture H→I).
- R6 (e) only; write-on-change and docs stay later entries.

**Never:**
- Propose-then-override while latched; hard reset to `config.omega_c`; one-shot safe-ωc jump.
- Changing `u_track_max`, plant limits, or online `b0`/`ωo`/MADRC.
- YAML knob for the 0.8 band; predicted `|ωc·e/b0|` as decay criterion.
- Directional/strict-apply rework (entry 1 done); ADR / house-calibration (entry 4).

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Latched at start | `_blow_up_latch` True entering demand path | `maybe_adapt` not called; track with committed ωc | No error |
| Latched + residue high | Latch active after write; `|u_track| > 0.8·u_track_max` | ωc steps down by `max_rate_fraction·ωc`, floored at `omega_c_min`, persisted; normal commit skipped | No error |
| Latched + residue OK | Latch active; finite `|u_track| ≤ 0.8·u_track_max` | No decay; adapt still skipped while latched at start | No error |
| Non-finite u_track | Latch active; `u_track` nan/inf | Same step-down persist as high residue | No error |
| Trip-edge | Latch False at start; guard trips this tick; residue high | Adapt may have run; commit skipped by trip; decay may persist | No error |
| Multi-tick decay | Latch held; `|u_track|` stays above band | Persisted ωc decreases each tick until band or floor | No error |

**Review notes (Intent):**
1. Thoughts: Approach underspecified sticky vs Design Notes/code.
2. Renegotiated: Approach + Always now name sticky hold in `(0.8·u_track_max, u_track_max]` (plan intent-contract updated to match).
3. Thoughts on renegotiated text: matches `sticky_blow_up_latch` + decay gate; no open findings.
4. Walkthrough patch: sticky only after successful write (AI-6 alignment); Intent Approach/Always updated again.

## Broad strokes

What the change is: while the blow-up latch is already active at tick start, skip online adapt; after **successful** plant write, assign a **sticky** R4 latch (not `guard.latch_out` alone) and, when residue holds, step committed ωc down via [`commit_omega_c`](../../../apps/hvac/ladrc_tuner.py) even if guard trip blocks the normal commit path.

Entry points (open in this order):

1. [`LATCH_DECAY_U_TRACK_FRACTION`](../../../apps/hvac/hvac_app.py#L134), [`latch_decay_residue_holds`](../../../apps/hvac/hvac_app.py#L137), [`next_decayed_omega_c`](../../../apps/hvac/hvac_app.py#L144), [`sticky_blow_up_latch`](../../../apps/hvac/hvac_app.py#L154) — pure R4 predicates and one decay step
2. [`control_tick`](../../../apps/hvac/hvac_app.py#L215) — `latch_at_start` gate before [`maybe_adapt`](../../../apps/hvac/ladrc_tuner.py)
3. [`control_tick`](../../../apps/hvac/hvac_app.py#L316) — sticky latch assignment **after** successful [`_write_setpoint`](../../../apps/hvac/hvac_app.py)
4. [`control_tick`](../../../apps/hvac/hvac_app.py#L334) — decay [`commit_omega_c`](../../../apps/hvac/ladrc_tuner.py) branch vs [`should_commit_omega_c`](../../../apps/hvac/hvac_app.py) else path
5. [R6(e) matrices](../../../tests/test_hvac_app.py#L540) (+ [skip-adapt inspect](../../../tests/test_hvac_app.py#L369), [`_mirror_decay_tick`](../../../tests/test_hvac_app.py#L577)) — persist locks and helper matrices

**Review notes (Broad strokes):** Thoughts soft nits patched; later walkthrough patch moved sticky after successful write (anchors refreshed).

## Decay helpers + sticky latch predicate

[`LATCH_DECAY_U_TRACK_FRACTION`](../../../apps/hvac/hvac_app.py#L134) (0.8, not YAML) drives [`latch_decay_residue_holds`](../../../apps/hvac/hvac_app.py#L137) (non-finite or `|u| > 0.8·u_track_max`). [`next_decayed_omega_c`](../../../apps/hvac/hvac_app.py#L144) applies one `max_rate_fraction` step down floored at `omega_c_min`. [`sticky_blow_up_latch`](../../../apps/hvac/hvac_app.py#L154) combines trip with “latch_in and residue holds” so the stop band at ≤0.8·max is reachable without copying [`guard_u_track`](../../../apps/hvac/hvac_app.py) `latch_out` alone.

**Review notes (Decay helpers + sticky latch predicate):** Thoughts — matches Intent; `|u|==max` holds via residue without trip (tested); `latch_out=tripped` alone would miss gray band. Test — 18 passed (residue/sticky matrices, fraction, next_decayed step/floor).

## Skip-adapt + sticky latch in control_tick

In [`control_tick`](../../../apps/hvac/hvac_app.py#L215), capture `latch_at_start = self._blow_up_latch` before zone-change clear and adapt; when true, set `new_omega_c = None` so write-path tracking uses committed ωc only. After [`latch_after_zone_change`](../../../apps/hvac/hvac_app.py#L231), `latch_in` feeds the write-path guard; WARN may fire before write; after **successful** `_write_setpoint`, [`sticky_blow_up_latch`](../../../apps/hvac/hvac_app.py#L316) updates `_blow_up_latch` from trip + residue (entry-1 strict apply / provisional path unchanged when adapt runs).

- [`control_tick` skip-adapt](../../../apps/hvac/hvac_app.py#L215)
- [`control_tick` sticky assignment](../../../apps/hvac/hvac_app.py#L316)

**Review notes (Skip-adapt + sticky latch in control_tick):** Soft fixed (sticky after write). Post-patch Thoughts: order WARN→write→sticky→ESO→advance→decay matches Intent; no open defects. Residual: fail-write latch-unchanged locked by inspect only (no behavioral Hass mock).

## Decay commit vs should_commit

After write + [`advance_with_tracking_residue`](../../../apps/hvac/ladrc.py), if sticky latch is active and [`latch_decay_residue_holds`](../../../apps/hvac/hvac_app.py#L334) on write-path `u_track`, [`commit_omega_c`](../../../apps/hvac/ladrc_tuner.py) with [`next_decayed_omega_c`](../../../apps/hvac/hvac_app.py#L338) — no [`should_commit_omega_c`](../../../apps/hvac/hvac_app.py) on that tick. Otherwise the existing directional commit else path runs (blocked apply still passes `omega_to_commit = None`).

- [`control_tick` decay branch](../../../apps/hvac/hvac_app.py#L333)
- [`control_tick` normal commit else](../../../apps/hvac/hvac_app.py#L344)

**Review notes (Decay commit vs should_commit):** Soft mirror gap fixed. Post-patch Thoughts: write_ok fail path + success decay XOR should_commit align with Intent; no open findings.

## Tests / R6(e) locks

- [test_latch_decay_residue_holds_matrix](../../../tests/test_hvac_app.py#L540) / [test_next_decayed_omega_c_step_and_floor](../../../tests/test_hvac_app.py#L550) / [test_sticky_blow_up_latch_matrix](../../../tests/test_hvac_app.py#L570) — helper matrices
- [test_control_tick_skips_maybe_adapt_when_latched_at_start](../../../tests/test_hvac_app.py#L369) — inspect skip-adapt wiring
- [test_control_tick_wires_should_warn_and_sticky_latch](../../../tests/test_hvac_app.py#L336) — inspect sticky latch + decay-before-commit ordering
- [`_mirror_decay_tick`](../../../tests/test_hvac_app.py#L576) (`write_ok`) + [multi-tick](../../../tests/test_hvac_app.py#L615), [band-stop](../../../tests/test_hvac_app.py#L640), [non-finite](../../../tests/test_hvac_app.py#L659), [trip-edge](../../../tests/test_hvac_app.py#L678), [fail-write](../../../tests/test_hvac_app.py#L740) — real tuner persist / latch unchanged on fail

**Review notes (Tests / R6(e) locks):** Intent matrix covered. Soft residuals R1–R3 accepted as-is. Test — `uv run pytest tests/test_hvac_app.py tests/test_ladrc_tuner.py -q` → 75 passed; ruff clean.

## Periphery

- [story-latch-decay-skip-adapt-plan.md](../epic-gate-omega-c-on-saturation/story-latch-decay-skip-adapt-plan.md) — status `built`; Intent renegotiated in this walkthrough (sticky + sticky-after-write)
- [walkthrough-pr-34.md](./walkthrough-pr-34.md) / [walkthrough-pr-34-log.md](./walkthrough-pr-34-log.md) — this review
- [PR #34](https://github.com/zhmachenkov-d/ha-smart-hvac/pull/34) — review target (head still `e332fef` until walkthrough patches push)

**Review notes (Periphery):** Thoughts — PR #34 CI green on `e332fef` but local patches unpushed (must commit/push before merge). R4 companion lag **deferred** to R5 — see [deferred-work.md](../deferred-work.md) (PR #34 section).
