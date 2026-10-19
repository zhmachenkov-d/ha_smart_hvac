---
title: 'Tracer: event-driven SWT gate re-evaluation'
type: 'feature'
ticket: '1'
created: '2026-10-19'
status: done
baseline_revision: 'aeac9876810d3ead360cf7ef7010bb979dfd1022'
route: 'full'
route_source: 'auto'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/initiative-weather-curve-zone-actuators/spec-weather-curve-swt-only/spec-weather-curve-swt-only.md'
  - '{project-root}/_bmad-output/initiative-weather-curve-zone-actuators/epic-immediate-swt-reactivity/epic-immediate-swt-reactivity.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Plant Management, thermostat `hvac_action` / setpoint, zone air, and Outdoor Temperature only affect Set Water Temperature on the next periodic `control_interval`, so CAP-1…CAP-3 gate writes can lag those inputs.

**Approach:** Register AppDaemon `listen_state` on the CAP-8 trigger set. Dual entrypoints share a gate prelude: `control_event` re-applies CAP-1…CAP-3 and on demand writes via `clamp_uff` only; `control_tick` keeps the full path including `process_demand` / CAP-7.

## Boundaries & Constraints

**Always:**
- Dual entrypoints: shared prelude for plant / outdoor / zones / demand; event demand = `clamp_uff` only; periodic demand = `process_demand` only.
- Event path preserves CAP-1…CAP-3 (plant-off: no write + clear ephemeral; plant-on idle / missing outdoor / no valid zones: write `0` + clear ephemeral; demand: write `clamp(u_ff)`).
- Event demand does not call `process_demand` and does not persist FF JSON.
- Periodic `control_tick` remains the only path that appends W15 / advances I1.
- Listeners cover: Plant Management, Outdoor Temperature, each configured zone air entity, and each configured thermostat’s `hvac_action` and `temperature` (setpoint) attributes (`attribute=` where needed).
- Event evaluation may run often (e.g. zone air churn); existing `_write_setpoint` equality skip is the write throttle — no debounce in this story.
- Hass-stub tests drive `control_event` / `control_tick` on mocks; they do not claim a live `run_every` timer race or “before next tick” ordering.

**Never:**
- Replace `run_every` / periodic scheduling with an event-only loop.
- An `advance_cap7` (or any) boolean that enables CAP-7 sampling on the event path.
- Advance CAP-7 rise-rate window or I1 on the event path.
- Restore air→SWT tracking / Critical Zone as an SWT driver.
- Change CAP-7 law inside `ff_auto_correct.py`, or ADR/docs (owned by story 2.2).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| CAP-8 demand | Plant on, demand present, outdoor/zones valid; `control_event` runs | `number/set_value` to `corrector.clamp_uff(outdoor)`; `process_demand` not called; CAP-7 `_window`/`_steady`/`_previous` unchanged | `_write_setpoint` False → stop; no further work |
| CAP-8 outdoor flip | Same demand plant; outdoor changes so `clamp_uff` differs; `control_event` runs | Write new `clamp_uff`; CAP-7 unchanged; no `process_demand` | Same as demand write-fail |
| CAP-8 plant off | Plant Management off; `control_event` runs | No setpoint write; ephemeral cleared | N/A |
| CAP-8 idle | Plant on, no Heating Demand; `control_event` runs | Write `0`; ephemeral cleared; JSON untouched | N/A |
| CAP-8 outdoor missing | Plant on; outdoor unreadable; `control_event` runs | Write `0`; ephemeral cleared; JSON untouched | N/A |
| CAP-8 no valid zones | Plant on; outdoor ok; no zone snapshots; `control_event` runs | Write `0`; ephemeral cleared; JSON untouched | N/A |
| CAP-8 no CAP-7 sample | Seeded corrector window, then CAP-8 demand event | Window/steady/I1 identical to pre-event; no FF persist from event | N/A |
| Periodic still CAP-7 | After listeners exist, `control_tick` on demand | Still runs `process_demand` (window can advance) | Unchanged |
| Event then periodic | Seeded window → CAP-8 demand (unchanged) → `control_tick` | Event left ephemeral intact; tick advances CAP-7 | N/A |
| Initialize listeners | `initialize` with multi-entity config | `listen_state` for each CAP-8 entity/attribute (incl. climate `attribute=`); `run_every` still scheduled | Config error: unchanged early return |
| Equal setpoint | `control_event` would command same float as plant entity | No `number/set_value` (equality skip); evaluation still ran | N/A |

</frozen-after-approval>

## Code Map

- `apps/ha_smart_hvac/hvac_app.py` `initialize` L37–42 — today only `run_every(control_tick)`; add CAP-8 `listen_state` → `control_event` (state + climate `attribute=`).
- `apps/ha_smart_hvac/hvac_app.py` `control_tick` L44–82 — periodic entry: shared prelude + `process_demand` L73; no boolean shared with the event entry.
- `apps/ha_smart_hvac/hvac_app.py` `control_event` — new event entry (AppDaemon `listen_state` callback shape `(entity, attribute, old, new, kwargs)`: ignore args, re-read state) + shared prelude; demand calls `corrector.clamp_uff` / `_write_setpoint` only.
- `apps/ha_smart_hvac/ff_auto_correct.py` `clamp_uff` L129–131, `clear_ephemeral` L115–119, `process_demand` L139+ — **reuse** clamp/clear; **do not change** process_demand / I1 / W15.
- `apps/ha_smart_hvac/coordinator.py` `has_heating_demand` — reuse for gate boolean.
- `apps/ha_smart_hvac/hvac_app.py` `_write_setpoint` L205–221 — equality skip stays the write throttle under frequent events.
- `tests/test_hvac_app.py` `_tick_app`, `_set_value_writes`, `_cap7_app`, `test_initialize_schedules_control_tick` — extend stubs for `listen_state` (assert `attribute=` where required); assert expected SWT via `corrector.clamp_uff(outdoor)` (yaml `_expected_ff_clamp` only when base/slope untouched); CAP-8 `control_event` + initialize + seed→event→tick locks.

## Tasks & Acceptance

**Execution:**
- [x] `apps/ha_smart_hvac/hvac_app.py` -- Shared prelude + `control_event` / `control_tick` dual entry (event=`clamp_uff`, tick=`process_demand`); wire CAP-8 `listen_state` in `initialize`; no advance flag -- W2 / CAP-8
- [x] `tests/test_hvac_app.py` -- Lock listener registration incl. `attribute=`; event demand / outdoor-flip / plant-off / idle / outdoor-missing / no-zones; CAP-7 unchanged on event; seed→event→tick; equality skip; stub-only (no timer race) -- verify matrix

**Acceptance Criteria:**
- Given plant on + demand + valid outdoor/zones, when `control_event` runs, then SWT is written to `corrector.clamp_uff(outdoor)` and `process_demand` is not invoked.
- Given plant on + demand, when outdoor changes so `clamp_uff` differs and `control_event` runs, then the new clamp is written, CAP-7 ephemeral is unchanged, and `process_demand` is not invoked.
- Given seeded CAP-7 ephemeral state, when a CAP-8 demand `control_event` runs, then `_window`, `_steady`, and `_previous` are unchanged and no FF JSON persist runs from that path.
- Given Plant Management off, when `control_event` runs, then there is no setpoint write and ephemeral is cleared.
- Given plant on and no Heating Demand, when `control_event` runs, then setpoint `0` is written, ephemeral is cleared, and FF JSON is untouched.
- Given plant on and outdoor unreadable (or no valid zones), when `control_event` runs, then setpoint `0` is written and ephemeral is cleared.
- Given seeded ephemeral, when CAP-8 demand `control_event` runs then `control_tick` on demand, then ephemeral is unchanged after the event and CAP-7 sampling advances on the tick.
- Given `control_event` would command the same float as the plant entity, when it runs, then no `number/set_value` occurs and evaluation still completed.
- Given `initialize` with configured entities, when it completes, then `listen_state` is registered for Plant Management, Outdoor Temperature, each zone air entity, and each thermostat `hvac_action` and `temperature` (with `attribute=`), and `run_every` still schedules `control_tick`.

## Implementation Notes

Party P1+S (2026-10-19): drop theatrical before-tick test claim; lock W2 dual entrypoints; equality skip = write throttle (no debounce).
Review R1 (2026-10-19): named `control_event`; matrix/AC for outdoor-missing/no-zones, outdoor flip, equality skip; split plant-off/idle; stub verification; assert `clamp_uff`.

## Plan Change Log

## Review Triage Log

- 2026-10-19 | quick | medium | patch | `tests/test_hvac_app.py` `test_cap8_outdoor_flip_writes_new_clamp` never mutates outdoor under the Hass stub before `control_event`; AC/matrix require outdoor to change so `clamp_uff` differs. Evidence: `_tick_app` closes over `outdoor`; test only compares `clamp_uff(0)` to `_expected_ff_clamp(..., 10)`.
- 2026-10-19 | quick | false | reject | `test_cap8_periodic_still_runs_process_demand` omits `initialize`/listeners. Evidence: `control_tick` does not depend on `listen_state`; matrix expected behavior (`process_demand` still runs) is asserted directly; listener registration is locked separately in `test_cap8_initialize_registers_listeners`.
- 2026-10-19 | quick | low | patch | `_bmad-output/party-mode/memories/installed/.memlog.md` party noise not required by CAP-8 AC/Code Map. Evidence: diff hunk is memlog-only; reverted to HEAD.

## Design Notes

**W2:** Dual entrypoints mandatory — `control_tick` and `control_event`. Shared prelude reads plant/outdoor/zones and branches plant-off, missing outdoor, no valid zones, and idle; demand forks by entry — never a boolean that turns on `process_demand` for events. `control_event` matches AppDaemon `listen_state` `(entity, attribute, old, new, kwargs)`, ignores those args, and re-reads current state. Climate setpoint and `hvac_action` use `attribute=` listeners; plant, outdoor, and zone air use entity state.

**S:** Frequent zone-air (and similar) events may re-evaluate often; do not add debounce here — rely on `_write_setpoint` equal-float skip to avoid bus spam.

**Stub Verify:** Tests call `control_event` / `control_tick` on Hass mocks. Do not sleep on timers, race `run_every`, or assert “before next tick” ordering.

## Verification

**Commands:**
- `uv run pytest tests/test_hvac_app.py -q` -- expected: all pass, including new CAP-8 locks (callback/entry driven; no timer-race claims)
- `uv run ruff check apps/ha_smart_hvac/hvac_app.py tests/test_hvac_app.py` -- expected: clean
