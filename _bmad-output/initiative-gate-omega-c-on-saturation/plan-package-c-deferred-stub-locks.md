---
title: 'Package C deferred stub locks'
type: 'bugfix'
created: '2026-10-17'
status: 'built'
baseline_revision: '16a14bff2f0e895eb445bcfe27513a00cffb7b32'
route: 'full'
route_source: 'auto'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/initiative-gate-omega-c-on-saturation/deferred-work.md'
  - '{project-root}/_bmad-output/initiative-gate-omega-c-on-saturation/plan-package-c-latch-hygiene.md'
  - '{project-root}/_bmad-output/initiative-gate-omega-c-on-saturation/control-tick-behaviors.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Package C Q5 deferred two Hass-stubbed `control_tick` locks: multi-tick latched decay persist (mirrors cover helpers only) and equal-value write-on-change side effects (`_write_setpoint` unit tests cover equality skip only). R6 still has those seams unguarded through the real tick path.

**Approach:** Add two named `_tick_app` tests only — no production behavior change. (1) Multi-tick latched residue through real `control_tick` decreases and persists ωc. (2) Plant float equal to desired SWT skips `number/set_value` while post-write sticky/decay still run.

**Decisions (plan review 2026-10-17):**
- R1: Under trip/residue, desired SWT is `clamp(weather_feedforward(outdoor), setpoint_min, setpoint_max)` — not `setpoint_max`. With outdoor `0` and Package C weather config that is `49.0`.
- R2: Unavailable / fail-closed plant is already locked (Package C fail-write + R6(d)); no new Hass test for it.
- R3: Multi-tick AC requires ≥3 strict ωc decreases + JSON/reload match; floor-to-`omega_c_min` stays with mirrors.

## Boundaries & Constraints

**Always:**
- Reuse Package C `_tick_app` / `_tick_args` recipe; mock only Hass I/O.
- Sticky latch + decay + ESO reset remain after successful write only.
- Equality baseline is entity float state; exact `==`; fail-closed unreadability unchanged.
- Multi-tick Hass lock proves wiring (≥3 strict decreases + state-file persist); mirror floor-to-`omega_c_min` coverage stays as-is.
- Pin trip/residue stub numbers: `omega_c=0.10`, `u_track_max=50.0`, `zone_temp=15.0`, `setpoint=22.0`, `outdoor=0.0`, `blow_up_latch=True` (same family as fail-then-success ~957).

**Never:**
- Change production decay, sticky, write-on-change, clamp, or WARN episode logic.
- Rewrite mirror decay tests into Hass stubs, or expand to all R6 mirrors.
- ADR / retrospective / deferred-work framing notes (separate deferred bullets).
- Idle/`_go_idle` fail-closed symmetry (retro AI-4).
- New Hass lock for unavailable plant (already covered).
- Heuristic “desired SWT = setpoint_max” under trip.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Multi-tick decay persist | Latch True; `u_track_max=50`, `zone_temp=15`, `outdoor=0`, plant readable ≠ desired ok; ≥3 demand ticks | Latch stays True; ωc strictly decreases each tick; final ωc matches state JSON / `LadrcTuner` reload | N/A |
| Equal SWT skip + side effects | Same trip/residue numbers; `plant_setpoint = clamp(weather_feedforward(0), min, max)` (= `49.0`) | No `number`/`set_value` call; latch sticky True; ωc == one `next_decayed_omega_c` step | N/A |

</frozen-after-approval>

## Code Map

- `tests/test_hvac_app.py` — `_tick_app` (~806–851), Package C control_tick tests (~865–1050). Add two tests beside them.
- `tests/test_hvac_app.py` — mirrors `test_multi_tick_decay_persists_until_omega_c_min` (~606), `test_decay_stops_when_residue_at_or_below_band` (~631): reuse `next_decayed_omega_c`; do not duplicate floor-to-min loop in Hass stub.
- `tests/test_hvac_app.py` — `_write_stub` R6(c)/(d) (~1109–1160) and `test_control_tick_fail_write_warns_once_no_sticky`: leave as unit/fail-closed locks.
- `apps/hvac/hvac_app.py` — read-only: skip-adapt / clear_steady (~217–221); fail-write return (~297–298); sticky (~299–305); decay commit (~319–329); `_write_setpoint` equality (~440–441); trip command = clamp(u_ff) (~66). **Do not edit** unless a test reveals a real bug (then stop and renegotiate).
- `apps/hvac/feedforward.py` — `weather_feedforward` for computing equal-value plant float.
- `apps/hvac/ladrc_tuner.py` — `next_decayed_omega_c`, `commit_omega_c`, persist — reuse in assertions; no API change.
- Spec / ADR companions — out of scope for this plan.

### Stub recipe (carry Package C Q4 + R1)

Same as Package C: `parse_config(_tick_args(...))`, thermal b0/ωo, parse-valid `omega_c=0.10`, `tune_state_path` under `tmp_path`. Trip/residue: `u_track_max=50.0`, `zone_temp=15.0`, `setpoint=22.0`, `outdoor=0.0`, start with `blow_up_latch=True` for multi-tick (or let sticky set it on first success for equal-value).

Equal-value: compute `desired = max(setpoint_min, min(setpoint_max, weather_feedforward(0.0, config.weather_feedforward)))` (expect `49.0`); pass that as `plant_setpoint`. Assert no `call_service` with domain/service `number`/`set_value` (other services may still fire). Alternate allowed: capture first-tick write value into a mutable plant holder, then assert skip on a later tick — only if feedforward calc is awkward; prefer the pinned formula.

## Tasks & Acceptance

**Execution:**
- [x] `tests/test_hvac_app.py` -- Add `test_control_tick_multi_tick_latched_decay_persists` (≥3 strict decreases + JSON reload; pinned stub numbers) -- deferred Q5 multi-tick lock
- [x] `tests/test_hvac_app.py` -- Add `test_control_tick_equal_setpoint_skips_set_value_still_sticky_decays` (plant=`49.0` via R1; no number/set_value; sticky + one decay step) -- deferred Q5 write-on-change side effects
- [x] `tests/test_hvac_app.py` -- Keep existing mirrors, `_write_stub` equality, and fail-write Hass locks; do not delete or weaken them

**Acceptance Criteria:**
- Given latch active and residue held (`u_track_max=50`, `zone_temp=15`, `outdoor=0`) across ≥3 successful demand ticks, when each `control_tick` runs, then persisted ωc strictly decreases each tick and a fresh `LadrcTuner` reload from the state path matches the final ωc.
- Given plant entity float equals `clamp(weather_feedforward(0), min, max)` under the same trip/residue setup, when `control_tick` runs, then no `number`/`set_value` call occurs, `_blow_up_latch` is True, and ωc equals `next_decayed_omega_c` of the prior value.
- Given the suite, when `uv run pytest tests/test_hvac_app.py` runs, then all new and existing tests pass.

## Implementation Notes

- 2026-10-17: Added two Hass-stubbed `_tick_app` locks only (no production change). Multi-tick: latch True + pinned trip/residue numbers → ≥3 strict ωc decreases + JSON/`LadrcTuner` reload match. Equal-value: `plant_setpoint = clamp(weather_feedforward(0), min, max)` (= `49.0`) → no `number/set_value`, sticky True, one `next_decayed_omega_c` step. Verified: `uv run pytest tests/test_hvac_app.py -q` → 75 passed; `uv run ruff check tests/test_hvac_app.py` → clean.

## Plan Change Log

- 2026-10-17 plan review: R1 desired SWT = clamp(u_ff) not setpoint_max; R2 drop unavailable I/O row; R3 strict ≥3 decreases (no floor clause); pin stub numbers; assert number/set_value only.

## Review Triage Log

### 2026-10-17 quick (iteration 0)

- lenses_ran: quick
- findings: none
- verdict counts: high=0 medium=0 low=0 false=0 maybe-false=0
- matrix audit: both I/O rows covered by named control_tick tests; both passed; full `test_hvac_app.py` 75 passed at implement

## Design Notes

Multi-tick Hass lock is intentional thinner than `_mirror_decay_tick`×200: mirrors own floor/stop/non-finite math; stub owns `control_tick` order (skip-adapt → write success → sticky → decay persist).

Equal-value lock pairs with trip/residue so asserted side effects are sticky+decay. On trip, `guard_u_track` sets `command = clamp(u_ff)` — so plant must match feedforward, not `setpoint_max`.

## Verification

**Commands:**
- `uv run pytest tests/test_hvac_app.py -q` -- expected: all passed
- `uv run ruff check tests/test_hvac_app.py` -- expected: clean
