# Walkthrough — PR #49: Plant-lag multi-tick sim harness

Target: [PR #49](https://github.com/zhmachenkov-d/ha_smart_hvac/pull/49) — branch `feat/madrc-1-1-plant-lag-harness`, feature commit `c3c319e` (branch also has BMAD ticket-tree chore + merge)
Focus: human review of plant-lag multi-tick sim harness (story 1.1 / decide epic setup)
Current block: closed — walkthrough complete; wrap-up done (staging deleted; commit `d34f305` pushed; PR #49 MERGED; plan Execution checked + status done)

## Blocks

- [x] **Intent** — done
- [x] **Broad strokes** — done
- [x] **Cascade plant** — done
- [x] **Closed-loop runner tick contract** — done
- [x] **Verifying tests** — done
- [x] **Periphery** — done

## Intent

Source: [story-plant-lag-multi-tick-sim-harness-plan.md](../epic-madrc-decide/story-plant-lag-multi-tick-sim-harness-plan.md) (frozen-after-approval Intent).

**Problem:** Later decide-epic work (R1 jump classification, R3 `control_interval`, R7 FF keep/drop) needs a shared closed-loop unit/sim of LADRC on a high-order lag plant; today tests only loop LADRC with fixed `y`/`u_ff` and never close the plant or log command/y/z series.

**Approach:** Add a reusable multi-tick harness: discrete \(K/(Ts+1)^n\) plant, outdoor as input, FF-on (via `weather_feedforward`) vs `u_ff=0`, production track → `guard_u_track` → residue advance, recording command / y / u_track / z each tick; ship one verifying unit test.

**Decisions:**
- Harness lives under `tests/harness/` (test-only package; production `ha_smart_hvac` stays clean). Later stories import from there.
- Blow-up latch across ticks uses production `sticky_blow_up_latch` (CAP-4), not bare `guard.latch_out`.
- On trip after a successful simulated write: `LadrcState.reset(y)` then `advance_with_tracking_residue` (same order as App).
- Plant pins stay absolute `K=0.45` starter (not house-calibrated); series field legend lives in Design Notes.

**Review notes (Intent):**
1. Frozen Intent matches shipped harness — test-only under [`tests/harness/`](../../../tests/harness/), sticky latch, reset-then-residue, `K=0.45` pins; no Intent renegotiation needed.
2. Feature commit `c3c319e` leaves production `apps/` untouched.

## Broad strokes

What the change is: test-only closed-loop LADRC↔plant runner under `tests/harness/`, plus verifying tests and pytest pythonpath for `import harness`.

Entry points (open in this order):

1. [`run_closed_loop`](../../../tests/harness/runner.py) — multi-tick App-path tick loop
2. [`CascadeLagPlant`](../../../tests/harness/plant.py) — Euler cascade \(K/(Ts+1)^n\)
3. [`tests/test_plant_lag_harness.py`](../../../tests/test_plant_lag_harness.py) — FF-on / zero-uff / trip / isolation AC
4. [`pyproject.toml` pythonpath](../../../pyproject.toml) — adds `tests` for `import harness`
5. [story plan Intent](../epic-madrc-decide/story-plant-lag-multi-tick-sim-harness-plan.md) — frozen Intent / AC

**Review notes (Broad strokes):**
1. Mechanism readable via runner → plant → tests → pythonpath → plan.
2. Production path (guard/sticky/residue) is inside [`run_closed_loop`](../../../tests/harness/runner.py), not a separate code entry — details deferred to runner slice.
3. Plan Verification commands passed (harness 5, ladrc+feedforward 13, ruff clean).

## Cascade plant

Discrete plant is a cascade of \(n\) first-order lags with gain \(K\) and time constant \(T\), stepped by forward Euler at the LADRC `dt`. State vector length is \(n\); output \(y\) is the last state. Same structure as knowledge MADRC \(G_p=K/(Ts+1)^n\), with absolute starter pins — not house-calibrated.

- [`CascadeLagPlant.__init__`](../../../tests/harness/plant.py) — validates \(n\)/\(T\)/`dt`; seeds `_x = [y0]*n`
- [`step`](../../../tests/harness/plant.py) — Euler: \(x_1\) from \(K\cdot u\), then cascade; returns \(y\)
- Design Notes plant equations in [plan](../epic-madrc-decide/story-plant-lag-multi-tick-sim-harness-plan.md)

**Review notes (Cascade plant):**
1. Equations match Design Notes / MADRC \(G_p\); simultaneous-update from old \(x\) is correct forward Euler.
2. No findings; walkthrough commit question still open.

## Closed-loop runner tick contract

Hass-free runner mirrors the App write path each tick: compute `u_ff` (`weather_feedforward` or 0), LADRC tracking, `guard_u_track` with sticky `latch_in`, update `sticky_blow_up_latch`, on trip `reset(y)`, `advance_with_tracking_residue`(`command − u_ff`), `plant.step(command)`, then append series. Fresh plant / LADRC / latch per call so modes do not share state.

- [`run_closed_loop` docstring tick contract](../../../tests/harness/runner.py) — documents App-path order
- [loop body guard / sticky / reset / residue / plant](../../../tests/harness/runner.py) — implements that contract
- [`ClosedLoopSeries` fields](../../../tests/harness/runner.py) — series legend
- Note: Design Notes tick order lists append before sticky; code appends after `plant.step` — triage-rejected as pedantry; series semantics still post-guard `command`/`y`/`u_track` and post-update `z`/latch ([plan](../epic-madrc-decide/story-plant-lag-multi-tick-sim-harness-plan.md))

**Review notes (Closed-loop runner tick contract):**
1. Order matches App successful-write path; assumes write always succeeds (Design Notes).
2. Sticky latch (not `latch_out`); residue via `advance_with_tracking_residue`; logged `y` is pre-step (track input).
3. No new findings requiring change.

## Verifying tests

One module pins starter defaults and covers the I/O matrix / AC — FF-on finite series, zero-uff residue capture, back-to-back isolation, forced trip clamp+latch, plus CAP-4 decay-band hold without re-trip (plan medium triage patch).

- [Pinned defaults / `_run` helper](../../../tests/test_plant_lag_harness.py) — shared starter pins
- [`test_ff_on_series_length_and_finite`](../../../tests/test_plant_lag_harness.py) — FF-on series length N, all finite
- [`test_zero_uff_residue_is_command`](../../../tests/test_plant_lag_harness.py) — patches `advance_with_tracking_residue`
- [`test_back_to_back_modes_do_not_mutate_each_others_series`](../../../tests/test_plant_lag_harness.py) — isolation
- [`test_forced_guard_trip_clamps_to_uff_and_sticky_latch`](../../../tests/test_plant_lag_harness.py) — forced trip clamp + latch
- [`test_sticky_latch_holds_in_decay_band_without_retrip`](../../../tests/test_plant_lag_harness.py) — CAP-4 decay-band hold

Note: Broad strokes Test already ran 5/5 green.

**Review notes (Verifying tests):**
1. All four AC covered; fifth test locks CAP-4 decay-band hold.
2. Soft: no explicit assert that `y` evolves; finite helper omits `tripped`/latch length (same append loop).
3. Accepted as-is for setup story.

## Periphery

- [`pyproject.toml` pytest pythonpath](../../../pyproject.toml) — adds `tests` so `import harness` works
- [story plan](../epic-madrc-decide/story-plant-lag-multi-tick-sim-harness-plan.md) — `status: built` + frozen Intent / AC / Design Notes
- BMAD ticket tree on branch (`f92b222`) — initiative-madrc epics/tickets if in PR #49 scope
- [walkthrough-pr-49](./walkthrough-pr-49.md) artifacts — this review; currently untracked
- [staging walkthrough-session/](../walkthrough-session/review-log.md) — can be deleted or ignored

**Review notes (Periphery):**
1. `pythonpath` OK; BMAD ticket tree in PR #49 scope OK.
2. Soft: plan Execution task checkboxes still unchecked while `status: built`.
3. Staging disposable; walkthrough-pr-49 still untracked — commit? delete staging?
