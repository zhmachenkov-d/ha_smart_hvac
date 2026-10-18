---
title: 'Tracer: weather-curve SWT law'
type: 'feature'
ticket: '1'
created: '2026-10-18'
status: done
baseline_revision: '406b6a00d8cbdaf8681b1e69275bedf2de20448b'
route: 'full'
route_source: 'auto'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - '{project-root}/CONTEXT.md'
  - '{project-root}/_bmad-output/initiative-weather-curve-zone-actuators/spec-weather-curve-swt-only/spec-weather-curve-swt-only.md'
  - '{project-root}/_bmad-output/initiative-weather-curve-zone-actuators/spec-weather-curve-swt-only/brownfield.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** With Critical Zone air near setpoint, LADRC tracking on the water path still grows `u_track` until Set Water Temperature pegs at `setpoint_max`. Feedforward alone is not the culprit — air→SWT closed loop keeps raising water when the room barely moves.

**Approach:** Rewire the control tick so Plant Management / Heating Demand gates command Set Water Temperature as `clamp(weather_feedforward)` only (Heating Demand = any-zone boolean). Leave LADRC/tuner modules on disk but unwired from the demand write path (entry 2 deletes them). Lock the law with CAP-5 automated tests.

## Boundaries & Constraints

**Always:**
- Plant Management off → no Set Water Temperature write + clear water-path state (not write 0).
- Plant Management on + no Heating Demand → write `0` + clear water-path state.
- Plant Management on + Heating Demand → write `clamp(u_ff)` with `setpoint_min`/`setpoint_max` (min stays 40).
- Heating Demand for the SWT gate is any-zone boolean (any Zone with positive Zone Error among heating-eligible thermostats).
- Clear on idle/off still resets existing LADRC/tuner/latch flags so leftover state cannot affect a later demand tick.
- Demand-path INFO log reports outdoor / `u_ff` / command only — no Critical Zone as driver, no `u_track`.
- Demand path does not call `LadrcTuner.publish_sensor` (or `maybe_adapt` / `commit_omega_c`).
- Heating Demand ≡ any Zone with positive Zone Error among **heating-eligible** thermostats (`hvac_action == "heating"`); idle/non-heating do not count — same rule as today’s `ZoneSnapshot.zone_error`.
- LADRC/tuner stay on disk and may still construct/`_load()` persisted ωc into memory: **temporary dormancy until entry 2 (CAP-4)**; this entry unwires them from the SWT demand write only — it does not claim the spec’s “remove now / not dormant” end-state.
- CAP-5 tests must pass; suite must stay green (`uv run pytest`, ruff).
- This entry does not update CONTEXT/ADRs; PR must not claim ADR 0002 still governs the live SWT law.

**Never:**
- Claim CAP-4 (do not delete `ladrc.py` / `ladrc_tuner.py` / yaml ladrc keys / ADR supersession / strip `initialize` `_load()` — entry 2/3).
- Add any air-temperature tracking term (or Critical Zone measured/reference) into the SWT command.
- Lower `setpoint_min` below 40; command zone actuators/TRV; implement CAP-6/CAP-7.
- Leave tick-level tests asserting `clamp(u_ff + u_track)` / LADRC wiring as the live SWT law.
- Publish or adapt ωc from the weather-curve demand write path.
- Invent a demand boolean that ignores heating-eligibility (raw any `zone_error > 0` without `-inf` idle zones).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Demand | PM on, ≥1 zone Zone Error > 0, outdoor OK | Write `clamp(u_ff)` only | No error expected |
| Plant-on idle | PM on, no Heating Demand | Write `0`; clear LADRC/tuner/latch | No error expected |
| Plant-off | PM off | No `number/set_value`; clear state | No error expected |
| Flat-air windup shape | PM on, demand, near-setpoint flat air, multi-tick | Command stays at FF clamp; never climbs toward `setpoint_max` via tracking | No error expected |
| Max-error air | PM on, demand, distinct max-error zone air | Max-error zone air not additive on SWT (command = clamp(u_ff)) | No error expected |
| Outdoor/zones missing (existing, out of CAP-5) | PM on, outdoor None or no valid zones | Keep today’s `_go_idle`: write `0` + clear | Log warning |

</frozen-after-approval>

## Code Map

- `apps/ha_smart_hvac/hvac_app.py` — `control_tick` (~184–350): today PM off → `_hands_off`; no demand → clear + write 0; demand → LADRC `compute_tracking` + `guard_u_track` → `clamp(u_ff+u_track)` then `publish_sensor`. **Change:** demand branch = `u_ff = weather_feedforward(...)` then `_write_setpoint(clamp(u_ff))`; stop tracking/guard/tuner adapt/commit/advance/`publish_sensor` on that path. Demand INFO: outdoor + `u_ff` + command (no CZ driver, no `u_track`). Reuse `_write_setpoint`, `_hands_off`, `_go_idle`, clear helpers. Clamp inline as `max(setpoint_min, min(setpoint_max, u_ff))`. Module-level `guard_u_track` / residue helpers may remain unused until entry 2.
- `apps/ha_smart_hvac/coordinator.py` — **Lock:** add `has_heating_demand(zones) -> bool` using the same eligibility as `ZoneSnapshot.zone_error` (heating-only; `-inf` idle zones never demand). Wire `control_tick` to that boolean only — do **not** call `select_critical_zone` on the SWT path in this entry (CZ selection deferred to entry 2 deletion / CAP-7 later). Mirror existing coordinator idle tests (`test_all_idle_zone_has_no_demand`, etc.).
- `apps/ha_smart_hvac/feedforward.py` — `weather_feedforward` — **reuse unchanged**.
- `apps/ha_smart_hvac/ladrc.py`, `ladrc_tuner.py` — **do not delete**; keep constructed/cleared on idle/off; `initialize` may still `_load()` persisted ωc into memory (unused for SWT). Unwire from demand write only (temporary dormancy → entry 2 CAP-4). Stale HA `sensor.hvac_ladrc_omega_c` from prior runs is entry-2 cleanup.
- `apps/ha_smart_hvac/config.py` / `models.py` — **no CAP-4 yaml/config strip** in this entry.
- `tests/test_hvac_app.py` — CAP-5 home; reuse `_tick_app` / `_tick_args` / entity consts. **Kill in this entry** (remove or rewrite off LADRC demand path): `test_control_tick_uses_tracking_residue_seam`, `test_control_tick_calls_guard_after_compute_tracking`, `test_control_tick_warns_before_write_on_demand_path`, `test_control_tick_latch_helper_before_compute_tracking`, `test_control_tick_trip_info_uses_guarded_marker`, `test_control_tick_wires_should_warn_and_sticky_latch`, `test_control_tick_persists_omega_c_via_apply_proposed_after_write`, `test_control_tick_skips_maybe_adapt_when_latched_at_start`, `test_control_tick_resets_eso_after_successful_write_on_trip`, `test_control_tick_post_latch_clear_steady_no_upward_rebound`, `test_control_tick_unlatched_does_not_clear_steady`, `test_control_tick_fail_write_warns_once_no_sticky`, `test_control_tick_fail_then_success_sticky_decay_no_second_warn`, `test_control_tick_episode_clear_resets_blow_up_warned`, `test_control_tick_warn_rearms_after_episode_clear`, `test_control_tick_multi_tick_latched_decay_persists`, `test_control_tick_equal_setpoint_skips_set_value_still_sticky_decays`. **Keep until entry 2 (Hass-free helper / mirror units — do not kill):** residue (`test_residue_*`, `test_advance_with_tracking_residue_*`), `test_guard_*`, `test_format_blow_up_warning_floor_fields`, `test_latch_after_zone_change_matrix`, `test_should_apply_omega_c_matrix`, `test_latch_decay_*`, `test_next_decayed_omega_c_*`, `test_sticky_blow_up_latch_matrix`, `test_multi_tick_decay_persists_until_omega_c_min`, `test_decay_stops_when_residue_at_or_below_band`, `test_non_finite_u_track_decay_persists`, `test_trip_edge_decay_persists_despite_guard_trip`, `test_single_decay_step_matches_max_rate_fraction`, `test_fail_write_leaves_latch_and_omega_c_unchanged`, `test_saturated_upward_proposal_does_not_ratchet_applied_or_committed`. **Keep/adapt:** idle clear (`test_idle_paths_clear_blow_up_*`), `test_initialize_sets_blow_up_flags_false`, `test_write_setpoint_*`, plus new CAP-5 (a–e).
- `tests/test_feedforward.py`, `test_plant_management.py`, `test_coordinator.py` — keep; add/adjust tests for `has_heating_demand`.
- Spec contract: `_bmad-output/.../spec-weather-curve-swt-only.md` CAP-1/2/3/5; brownfield gate table.

## Tasks & Acceptance

**Execution:**
- [x] `apps/ha_smart_hvac/coordinator.py` -- Add `has_heating_demand(zones)` (heating-eligible Zone Error > 0 only); stop using `select_critical_zone` on the SWT tick -- ticket Heating Demand boolean
- [x] `apps/ha_smart_hvac/hvac_app.py` -- Demand path: `clamp(u_ff)` write; no tracking/guard/adapt/commit/advance/`publish_sensor`; demand INFO = outdoor/`u_ff`/command; keep PM/idle/sensor gates + clear-on-idle/off; leave tuner `_load` alone -- CAP-1/2/3 + log/ωc hygiene
- [x] `tests/test_coordinator.py` -- Cover `has_heating_demand` incl. all-idle / non-heating → false -- eligibility lock
- [x] `tests/test_hvac_app.py` -- Add CAP-5 (a–e); kill Code Map kill-list only; leave helper/mirror leave-list until entry 2 -- CAP-5 + suite green

**Acceptance Criteria:**
- Given Plant Management on and Heating Demand, when a control tick runs with known outdoor/FF params, then the written Set Water Temperature equals `clamp(u_ff)` and no tracking term is added.
- Given Plant Management on and no Heating Demand, when a control tick runs, then Set Water Temperature is written `0` and water-path controller state/latch flags are cleared.
- Given Plant Management off, when a control tick runs, then no Set Water Temperature write occurs and controller state is cleared.
- Given near-setpoint flat air over multiple demand ticks with fixed outdoor/FF (former windup shape), when the new law runs, then each tick’s command equals `clamp(u_ff)` and never climbs toward `setpoint_max` via tracking.
- Given a max-error zone with distinct air temperature, when demand ticks run, then that zone’s air does not appear as an additive term on SWT (command remains `clamp(u_ff)`).
- Given a successful demand write, when inspecting call/logs, then no `publish_sensor` / ωc adapt runs and INFO does not present Critical Zone as the SWT driver.
- Given the package test suite, when `uv run pytest` and project ruff checks run, then they pass.

Sensor-idle / missing outdoor → `_go_idle` stays existing behavior (I/O matrix); not a new CAP-5 AC.

## Implementation Notes

## Plan Change Log

## Review Triage Log

| Finding | Verdict | Evidence | Route |
|---------|---------|----------|-------|
| `hvac_app.py` demand branch ignores `_write_setpoint` False and still INFO-logs `command=` as applied | medium | Verified: lines 211–214 call write then always log; baseline aborted on False before success path; CAP-6(d) still documents False = tick abort | patch |
| `has_heating_demand` docstring says idle/non-heating yield zone_error `-inf` | low | Verified: `models.py` returns `-inf` only when no heating-eligible thermostats; heating with ≤0 error is finite | patch |

## Design Notes

Demand path golden shape (after change):

```python
u_ff = weather_feedforward(outdoor, config.weather_feedforward)
command = max(config.setpoint_min, min(config.setpoint_max, u_ff))
self._write_setpoint(command)
# log outdoor, u_ff, command — not Critical zone / u_track
# do not call self._tuner.publish_sensor / maybe_adapt / commit_omega_c
```

Heating Demand: `has_heating_demand(zones)` only — no `select_critical_zone` on this tick. If false → clear + write `0`. LADRC/tuner may still construct, `_load()` ωc, and clear on idle/off; they must not run, adapt, commit, or publish on the demand write path (temporary dormancy until entry 2).

**CAP-5 assert recipe:** spy `_write_setpoint` / `number.set_value` values; for (a)/(d)/(e) assert each written command == `max(setpoint_min, min(setpoint_max, weather_feedforward(outdoor, ff_cfg)))` with outdoor/FF fixed. (d) N ticks, air flat near setpoint (shape that formerly grew `u_track`). (e) two zones, distinct max-error air — command still equals that same clamp (air not additive). Optional: assert demand path never calls `compute_tracking`.

## Verification

**Commands:**
- `uv run pytest` -- expected: all tests pass, including new CAP-5 cases
- `uv run ruff check apps/ha_smart_hvac tests` -- expected: clean
- `uv run ruff format --check apps/ha_smart_hvac tests` -- expected: clean
