# Walkthrough — PR #36: write-on-change setpoint

Target: [PR #36](https://github.com/zhmachenkov-d/ha-smart-hvac/pull/36) (`feat/1-3-write-on-change-setpoint` → `main`, commit `7177934`)
Focus: human review of R3 write-on-change + R6 (c)(d) (story 1.3)
Current block: closed — walkthrough complete; wrap-up: commit/push + merge PR #36 + mark story 1.3 done + delete feature branch

## Blocks

- [x] **Intent** — done
- [x] **Broad strokes** — done
- [x] **Write-on-change in _write_setpoint** — done
- [x] **R6 (c)(d) tests** — done
- [x] **Periphery** — done

## Intent

Source: [story-write-on-change-setpoint-plan.md](../epic-gate-omega-c-on-saturation/story-write-on-change-setpoint-plan.md) (frozen Intent).

**Problem:** Every demand and idle/0 plant write issues `number/set_value` even when Set Water Temperature already equals the desired float, adding redundant HA chatter while the tick still needs to continue after a successful write decision.

**Approach:** Inside `_write_setpoint` (all paths), read plant entity state; fail-closed abort when unreadable/unparseable; when desired equals the entity float (exact compare, no last-written cache), skip `set_value` but return success so the tick continues; otherwise call `set_value`. Lock R6 (c)(d).

**Review notes (Intent):**
1. Thoughts: frozen Intent matches R3 / control-tick-behaviors (entity float equality; fail-closed unreadability; success-on-skip continues tick; all paths inside `_write_setpoint`; no last-written cache).
2. Approach correctly scopes R6 (c)(d) only — no R4/docs creep.
3. Soft residual (not Intent defect): idle/0 call sites ignore `_write_setpoint` return; fail-closed abort is demand-path only — Intent already says abort via false return, which demand uses; no renegotiation needed.
4. No unmet Intent gaps vs shipped `_read_float` + equality skip.

## Broad strokes

What the change is: [`_write_setpoint`](../../../apps/hvac/hvac_app.py#L452) reuses [`_read_float`](../../../apps/hvac/hvac_app.py#L428) so an identical plant entity float skips `number/set_value` but still returns success; unreadable/unparseable stays fail-closed (`False`).

Entry points (open in this order):

1. [`_write_setpoint`](../../../apps/hvac/hvac_app.py#L452) — write-on-change skip vs `set_value` vs fail-closed
2. [`_read_float`](../../../apps/hvac/hvac_app.py#L428) — entity float parse; equality baseline (not a last-written cache)
3. Call sites: [idle/0 in `control_tick`](../../../apps/hvac/hvac_app.py#L207), [demand write](../../../apps/hvac/hvac_app.py#L313), [`_go_idle`](../../../apps/hvac/hvac_app.py#L385) — all paths share the method; demand aborts on `False`
4. [R6 (c)(d) tests](../../../tests/test_hvac_app.py#L763) — stubbed equal-skip / differ-write / unreadable-abort

**Review notes (Broad strokes):**
1. Thoughts: four entry points map the mechanism; `_write_setpoint` + `_read_float` are the right first opens; call sites correctly note shared method + demand-only abort.
2. Soft: Broad strokes lists three call sites but not that `_go_idle` / idle ignore return — already noted under Intent; no narrative rewrite required.
3. Test section entry is the right last stop for R6 (c)(d); no missing top-level entry.
4. No Broad strokes defects vs Intent/code.
5. Test — `uv run pytest … -k write_setpoint` → 9 passed; full `tests/test_hvac_app.py` → 65 passed; ruff clean. Unverified: live HA / AppDaemon tick.

## Write-on-change in _write_setpoint

[`_write_setpoint`](../../../apps/hvac/hvac_app.py#L452) reads current via [`_read_float`](../../../apps/hvac/hvac_app.py#L428). If that is `None` (unavailable / unknown / unparseable), WARN and return `False` (demand tick aborts; no advance). If `current == value` (exact float compare), return `True` without `number/set_value` so sticky latch / ESO / decay can still run. Otherwise call `set_value` and return `True`.

- [`_write_setpoint`](../../../apps/hvac/hvac_app.py#L452)
- Demand abort on fail: [`control_tick`](../../../apps/hvac/hvac_app.py#L313)

**Review notes (Write-on-change in _write_setpoint):**
1. Thoughts: `_read_float` then None→False / ==→skip True / else set_value matches R3 and Intent; exact `==` is intentional.
2. WARN message still says "unavailable" for all None cases including unparseable — cosmetic, pre-existing phrasing; not worth a code change in this PR unless user wants.
3. Demand abort before sticky/ESO confirmed at L313–326; equality-skip returns True so latch/decay path stays reachable.
4. No functional defects in the write-on-change body.

## R6 (c)(d) tests

Hass-free stub [`_write_stub`](../../../tests/test_hvac_app.py#L768) binds `get_state` / `call_service` / `log`. Equal float / `"42.0"` / `42` skips `set_value` and returns success; a different float issues `set_value`; unreadable matrix (`None` / unavailable / unknown / unparseable) returns `False` with no service call.

- [test_write_setpoint_skips_set_value_when_entity_float_equals](../../../tests/test_hvac_app.py#L782)
- [test_write_setpoint_calls_set_value_when_entity_float_differs](../../../tests/test_hvac_app.py#L792)
- [test_write_setpoint_fail_closed_when_entity_unreadable](../../../tests/test_hvac_app.py#L809)

**Review notes (R6 (c)(d) tests):**
1. Thoughts: equal-skip / differ-write / unreadable matrices lock R6 (c)(d) at the `_write_setpoint` seam; stub is appropriate Hass-free pattern.
2. Soft residual: R6(c) "without aborting tick side effects" is locked via return True (callers already gate sticky/ESO on that), not a full control_tick mirror — acceptable oneshot residual, same class as entry-1/2 Hass-free mirrors.
3. Unreadable matrix covers None/unavailable/unknown/unparseable/object — matches fail-closed expansion beyond pre-change unavailable-only.
4. No missing R6 (c)(d) cases vs Intent.
5. Test — `uv run pytest … -k write_setpoint` → 9 passed; full `tests/test_hvac_app.py` → 65 passed; ruff clean. (Re-run on this block.)

## Periphery

- [story-write-on-change-setpoint-plan.md](../epic-gate-omega-c-on-saturation/story-write-on-change-setpoint-plan.md) — status `built`; oneshot R3 plan
- [walkthrough-pr-36.md](./walkthrough-pr-36.md) / [walkthrough-pr-36-log.md](./walkthrough-pr-36-log.md) — this review
- [PR #36](https://github.com/zhmachenkov-d/ha-smart-hvac/pull/36) — head `7177934`

**Review notes (Periphery):**
1. Thoughts: plan `built` + PR #36 CI green / MERGEABLE on `7177934`; walkthrough folder still untracked — commit/push before merge if it should land with the PR.
2. Soft residuals from earlier blocks (WARN wording; True-return vs control_tick mirror) accepted as-is — no new deferred R3 items.
3. Ticket 1.3 is `built` / state `review`; mark-done is wrap-up, not a Periphery defect.
4. No Periphery gaps blocking the code change.
