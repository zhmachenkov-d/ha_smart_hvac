---
title: 'Package C latch hygiene'
type: 'bugfix'
created: '2026-10-17'
status: built
baseline_revision: '3435c63d01cf0cd4c1d9a28b695e89fe680677af'
route: 'full'
route_source: 'auto'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/initiative-gate-omega-c-on-saturation/tickets/epic-gate-omega-c-on-saturation/epic-gate-omega-c-on-saturation-retrospective.md'
  - '{project-root}/_bmad-output/initiative-gate-omega-c-on-saturation/spec-gate-omega-c-on-saturation/control-tick-behaviors.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** After CAP-4 skip-adapt, `LadrcTuner._steady_ticks` stays hot so the first unlatched tick can immediately propose upward ωc and undo decay. Separately, trip + fail-write never sticks the latch, so `should_warn` fires every 60 s. CAP-6 locks are mostly mirrors/inspect and miss both seams.

**Approach:** Package C (retro / product-team): (1) `clear_steady()` when `latch_at_start`; (2) app-level `_blow_up_warned` so fail-write does not spam WARNING while sticky/decay stay after successful write only; (3) Hass-stubbed `control_tick` tests locking AI-1+AI-2 only; (4) companion CAP-4 + WARN episode wording.

**Decisions (plan review 2026-10-17):**
- Q1: Clear `_blow_up_warned` on every successful demand tick that ends with `_blow_up_latch is False`, plus `_hands_off` / `_go_idle` / no-demand clears. Never clear on fail-write early-return.
- Q2: No special zone-change clear for warned; only Q1 / idle paths.
- Q3: Episode WARN gate only in app (`guard.should_warn and not self._blow_up_warned`); `guard_u_track` unchanged.
- Q4: Integration tests seed `tuner._steady_ticks` / `_blow_up_latch` (and `LadrcState` if needed); force trip via low `u_track_max` and/or high zone error; mock only Hass I/O.
- Q5: Stub locks AI-1+AI-2 only; multi-tick decay-persist and write-on-change legs deferred (see initiative `deferred-work.md`).
- Q6: Required companion updates for `clear_steady` and `_blow_up_warned`.

## Boundaries & Constraints

**Always:**
- Sticky latch + decay + ESO reset remain after successful plant write only (CAP-4 sticky-after-write / AI-6).
- Fail-write on demand still early-returns before sticky/decay/reset.
- Directional clamp / strict apply / write-on-change behavior unchanged.
- Idle / `_go_idle` fail-closed symmetry stays out of scope (retro AI-4 deferred).

**Never:**
- Full freeze on clamp, changing `u_track_max` / plant limits, online b0/ωo/MADRC.
- Rewriting all CAP-6 mirrors into Hass stubs.
- Setting `_blow_up_latch` on fail-write to suppress WARN; use separate `_blow_up_warned`.
- Expanding this package’s integration stub to multi-tick decay-persist or equal-value write-on-change (deferred explicitly).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Post-latch rebound | Seed warm `_steady_ticks` (≥ min_steady), `_blow_up_latch=True` for N ticks, then clear latch + demand | First unlatched tick: `maybe_adapt` returns None; persisted ωc does not rise | N/A |
| Fail-write WARN | Trip-edge (low `u_track_max` / high error), plant unreadable two ticks | WARNING logged once; latch stays False; ωc unchanged; no decay; `_blow_up_warned=True` | Early return both ticks |
| Fail then success | Same trip, then plant readable + write OK | Success tick: no WARNING; sticky True; decay commits ωc down while residue holds | N/A |
| Episode clear (Q1) | After warned, successful demand tick ends latch False | `_blow_up_warned` clears | N/A |
| Re-arm WARN | After Q1 clear, new trip-edge with write OK or fail | WARNING emits again | N/A |

</frozen-after-approval>

## Code Map

- `apps/hvac/hvac_app.py` — `control_tick` skip-adapt (~214–225); warn/write/sticky (~283–323); `_hands_off` / `_go_idle` / no-demand / `initialize`. Add `clear_steady()` under `latch_at_start`; add `_blow_up_warned` init/set/clear per Q1–Q3.
- `apps/hvac/ladrc_tuner.py` — reuse `clear_steady()`; do not change tuner API.
- `tests/test_hvac_app.py` — `_write_stub` pattern; add `_tick_app` Hass stub; named tests for rebound, fail-write WARN, fail-then-success, re-arm; update `test_control_tick_wires_should_warn_and_sticky_latch` / skip-adapt inspect for `clear_steady` and compound warn gate.
- `spec-gate-omega-c-on-saturation/control-tick-behaviors.md` — CAP-4 bullet for `clear_steady` on `latch_at_start`; WARN episode note (app flag, sticky-after-write unchanged).

### Stub recipe (Q4)

Build `HvacConfig` via `parse_config` using the same ladrc numbers as `tests/test_hvac_app.py` `_config()` / `_THERMAL_*` (not `apps.yaml.example` package A — different `omega_c`). Override `u_track_max` / zone error only when forcing trip. Keep `min_steady_ticks` from that config, `tune_state_path` under `tmp_path`, one zone + heating thermostat, `setpoint_min/max` 40/55.

`object.__new__(HvacApp)` then set:
- `_config`, `_ladrc=LadrcState()`, `_tuner=LadrcTuner(...)`, `_blow_up_latch`, `_blow_up_warned`
- `get_state` side_effect by entity: plant_management → `"on"`; outdoor → float; zone temp → float; climate `temperature` attr → setpoint; `hvac_action` → `"heating"`; plant setpoint → float or `"unavailable"` per tick
- `call_service`, `log`, `set_state` = MagicMock
- Seed: `tuner._steady_ticks`, `tuner._last_critical_zone`, latch flags; for trip use small `u_track_max` (e.g. 50) and/or large zone error so `|u_track|` trips
- Drive: `app.control_tick({})` for each phase; assert on `log` WARNING count, `tuner.omega_c`, `_blow_up_latch`, `_blow_up_warned`

## Tasks & Acceptance

**Execution:**
- [x] `apps/hvac/hvac_app.py` -- `clear_steady()` on `latch_at_start`; `_blow_up_warned` per Q1–Q3 (log only when `should_warn and not warned`; set on emit; clear on successful demand with latch False + idle/hands_off/no-demand) -- AI-1/AI-2
- [x] `tests/test_hvac_app.py` -- `_tick_app` + tests: rebound (ωc not up), fail-write single WARN, fail-then-success sticky+decay + no second WARN, episode clear asserts `_blow_up_warned is False`, re-arm after Q1 clear, idle/hands_off/no-demand clear warned -- AI-3 (narrowed)
- [x] `tests/test_hvac_app.py` -- Update inspect locks: `clear_steady` under latch_at_start; warn gate includes `_blow_up_warned`; fail-write still before sticky
- [x] `control-tick-behaviors.md` -- Required CAP-4 `clear_steady` + WARN episode sentences (Q6)

**Acceptance Criteria:**
- Given warm steady then latched ticks, when latch clears on a demand tick, then the first unlatched `control_tick` leaves persisted ωc unchanged upward (no upward proposal from residual steady).
- Given trip-edge with unreadable plant for two ticks, when both ticks run, then WARNING is logged exactly once, latch stays False, and ωc is unchanged.
- Given trip fail-write then a later successful trip write with residue above the decay band, when the success tick completes, then sticky latch is True, decay commits ωc down, and that success tick logs no WARNING.
- Given `_blow_up_warned` is True and a successful demand tick ends with `_blow_up_latch` False (healthy), when that tick completes, then `_blow_up_warned` is False (assert the flag — do not only re-arm).
- Given `_blow_up_warned` cleared after a successful healthy demand tick, when a new trip-edge occurs, then WARNING emits again.
- Given `_blow_up_warned` is True, when `_go_idle` / `_hands_off` / no-demand clear runs, then `_blow_up_warned` becomes False (same paths that clear `_blow_up_latch`).
- Given the suite, when `uv run pytest tests/test_hvac_app.py` runs, then all new and existing tests pass.

## Implementation Notes

- 2026-10-17: Implemented Package C. `clear_steady()` on `latch_at_start`; app `_blow_up_warned` gates episode WARN (Q1–Q3). Hass-stubbed `_tick_app` locks AI-1+AI-2 only (multi-tick decay-persist / write-on-change deferred). Companion CAP-4 updated. Verified: `uv run pytest tests/test_hvac_app.py -q` → 71 passed; `uv run ruff check apps/hvac/hvac_app.py tests/test_hvac_app.py` → clean. Stub uses thermal b0/ωo/tune with parse-valid `omega_c=0.10` ( `_config()`’s 0.01 is below `omega_c_min` and cannot pass `parse_config`).

## Plan Change Log

- 2026-10-17 plan review: incorporated Q1–Q6; stub recipe; hardened ACs (no “may”); explicit AI-3 narrow + defer; required companion for clear_steady + WARN episode.
- 2026-10-17 plan review pass 2: N1 episode-clear AC on `_blow_up_warned`; N2 idle/hands_off/no-demand warned-clear AC; N3 stub baseline = `test_hvac_app._config` / `_THERMAL_*` (not package A).

## Review Triage Log

### 2026-10-17 quick (iteration 0)

- lenses_ran: quick
- findings: none
- verdict counts: high=0 medium=0 low=0 false=0 maybe-false=0
- matrix audit: all five I/O rows covered by named control_tick tests; 7 focused tests passed (plus full `test_hvac_app.py` 71 passed at implement)

## Design Notes

`_blow_up_warned` is independent of `_blow_up_latch`. Fail-write never assigns sticky latch or runs decay/ESO reset. App gates WARN; guard seam stays detect-only.

## Verification

**Commands:**
- `uv run pytest tests/test_hvac_app.py -q` -- expected: all passed
- `uv run ruff check apps/hvac/hvac_app.py tests/test_hvac_app.py` -- expected: clean

## Code Review

### 2026-10-17

**Code review complete.** 0 `decision-needed`, 3 `patch`, 2 `defer`, 8 rejected.

- [x] [Review][Patch] Lock `clear_steady` to latched-only path — add Hass-stubbed unlatched tick that seeds mid-range `_steady_ticks` and asserts it increments (not reset) [`tests/test_hvac_app.py`]
- [x] [Review][Patch] Pin `_blow_up_warned` (and latch) via `initialize` harness — stubs currently set the flag via `__new__` only [`apps/hvac/hvac_app.py:174`]
- [x] [Review][Patch] Assert `_blow_up_warned` stays True after fail-then-success sticky tick [`tests/test_hvac_app.py:919`]
- [x] [Review][Defer] ADR 0003 Guards omit Package C `clear_steady` / episode WARN [`docs/adr/0003-online-ladrc-omega-c-auto-tune.md:21`] — deferred: companion CAP-4 was Q6 scope; ADR sync is agent/spec follow-up
- [x] [Review][Defer] Retro / deferred-work still frame AI-3 / WARN open items without Package C close-out note [`epic-gate-omega-c-on-saturation-retrospective.md`] — deferred: process-doc hygiene after build

Rejected:
- `false` min_steady_ticks=1 first unlatched propose — clear_steady clears residual; first-tick propose with min_steady=1 is fresh accumulation (normal tuner), not leftover warm counter
- `low` AI-1 test forces latch rather than sticky→clear episode — AC still locked; end-to-end sticky drive is more complexity than everyday value
- `low` warn_rearms mid-test config swap — brittle style; no product harm
- `low` duplicated get_state side_effects — refactor without named invariant break
- `low` companion buries clear_steady in skip bullet — cosmetic wording
- `low` no multi-success sticky “warned stays True” lock — beyond Q5; fail-then-success already covers one success tick
- `false` intent R2 (full retro AI-3) vs shipped stubs — Q5 explicitly narrowed; not a defect
- `low` deferred-work omits “AI-1/AI-2 closed” note — process; subsumed by defer bullet above
