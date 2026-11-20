---
title: 'Codebase research: TRV soft-close and hold timers'
type: codebase
ask: |-
  Factual questions on how plant-on TRV valve_closure soft-close works, how accuracy is commissioned and listened, how flame hold timers run, how those paths are tested, why accuracy is required, and what touches _apply_trv_law / overshoot state — for epic-trv-house-idle-soft-close refine.
ticket: '_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-trv-house-idle-soft-close/epic-trv-house-idle-soft-close.md'
repository: '/workspaces/ha-smart-hvac'
commit: '2ec1908088a50a2a88fb157b9652532cbb46e704'
branch: 'main'
status: complete
validation: 'normal'
claims: {verified: 10, unverified: 0, overturned: 0}
created: '2026-11-20'
updated: '2026-11-20'
---

# Codebase research: TRV soft-close and hold timers
## Questions
1. **how** — How does the App, under Plant Management on, decide and write `valve_closure_degree` for each commissioned Sonoff TRV (including floor, overshoot latch behavior, and Plant Management off)?
2. **where / how** — How does thermostat yaml commission define a Sonoff TRV (`valve_closure`, `accuracy`), and when are `accuracy` entities registered as state listeners?
3. **how** — How does the flame short-on path schedule, cancel, and run its hold timer callback?
4. **how tested** — How are TRV soft-close behavior and hold/timer behavior covered in automated tests?
5. **why** — Why does commissioned TRV soft-close require `accuracy` (commit / PR history of the requirement)?
6. **what touches** — What call sites invoke `_apply_trv_law` or read/write TRV overshoot latch state?

## 1. How does plant-on TRV soft-close write `valve_closure_degree`?
`_apply_trv_law` loops every zone thermostat and skips unless both `valve_closure` and `accuracy` entity ids are set (`apps/ha_smart_hvac/hvac_app.py:404-407 (_apply_trv_law) @ 2ec1908`). It runs before `_gate_prelude` on `control_tick` (`apps/ha_smart_hvac/hvac_app.py:239 (control_tick) @ 2ec1908`), `control_event` (`apps/ha_smart_hvac/hvac_app.py:256 (control_event) @ 2ec1908`), and `_flame_trip_hold_expired` (`apps/ha_smart_hvac/hvac_app.py:165 (_flame_trip_hold_expired) @ 2ec1908`). Flame observe/latch handlers do not call it.

Plant on is `get_state(plant_management) == "on"` (`apps/ha_smart_hvac/hvac_app.py:401 (_apply_trv_law) @ 2ec1908`; `apps/ha_smart_hvac/models.py:73-74 (plant_management_enabled) @ 2ec1908`).

Writes go through `_write_number`: unreadable current → WARNING and `False`; equal float → `True` with no service call; else `number/set_value` (`apps/ha_smart_hvac/hvac_app.py:379-396 (_write_number) @ 2ec1908`). No `valve_opening_degree` writes under `apps/` at this commit.

**Plant on, per commissioned TRV:** reads zone air and climate setpoint; skips write if either unreadable (`apps/ha_smart_hvac/hvac_app.py:416-419 (_apply_trv_law) @ 2ec1908`). Overshoot latch is a RAM `set[str]` keyed by closure entity id (`apps/ha_smart_hvac/hvac_app.py:45 (initialize) @ 2ec1908`):

- Latched and `t_zone > setpoint` → write `100.0` (“overshoot hold”) (`apps/ha_smart_hvac/hvac_app.py:433-441 (_apply_trv_law) @ 2ec1908`).
- Latched and `t_zone <= setpoint` → write `valve_closure_floor`; discard latch only if write returns `True` (`apps/ha_smart_hvac/hvac_app.py:423-432 (_apply_trv_law) @ 2ec1908`).
- Not latched and `t_zone >= setpoint + abs(accuracy)` → write `100.0` and add latch only if write succeeds (`apps/ha_smart_hvac/hvac_app.py:444-457 (_apply_trv_law) @ 2ec1908`).
- Else → write `valve_closure_floor` (`apps/ha_smart_hvac/hvac_app.py:458-466 (_apply_trv_law) @ 2ec1908`).

Floor defaults to `80.0` (`apps/ha_smart_hvac/models.py:91 (valve_closure_floor) @ 2ec1908`; `apps/ha_smart_hvac/config.py:31 (_DEFAULT_VALVE_CLOSURE_FLOOR) @ 2ec1908`; `apps/ha_smart_hvac/config.py:261-262 (valve_closure_floor) @ 2ec1908`).

**Plant off:** write closure `100.0` with reason “plant management off” (`apps/ha_smart_hvac/hvac_app.py:408-414 (_apply_trv_law) @ 2ec1908`). Code does not clear `_trv_overshoot_latched` on that branch.

**Looked for, not found:** clearing overshoot latch on plant-off / idle / flame clear; TRV gated on Heating Demand, Outdoor, or Critical Zone.

## 2. How is Sonoff TRV yaml commission defined, and when is `accuracy` listened?
Zone `thermostats` accept a climate string (no TRV ids) or a mapping (`apps/ha_smart_hvac/config.py:128-145 (_parse_thermostat) @ 2ec1908`). A mapping missing either key name `valve_closure` or `accuracy` raises `ConfigError` (“requires valve_closure and accuracy”) (`apps/ha_smart_hvac/config.py:135-137 (_parse_thermostat) @ 2ec1908`). `ThermostatConfig.commissioned` is true only when both ids are non-`None` (`apps/ha_smart_hvac/models.py:17-18 (commissioned) @ 2ec1908`).

`apps.yaml.example` shows a TRV mapping with both number entities beside a climate-only string thermostat (`apps.yaml.example:35-40 (thermostats) @ 2ec1908`).

After successful `parse_config`, `initialize` calls `_register_control_listeners` (`apps/ha_smart_hvac/hvac_app.py:47 (initialize) @ 2ec1908`). For each thermostat with `accuracy is not None`, it registers `listen_state(self.control_event, thermo.accuracy)` (`apps/ha_smart_hvac/hvac_app.py:74-75 (_register_control_listeners) @ 2ec1908`). Climate `hvac_action` and `temperature` are also listened; `valve_closure` is not registered as a listener.

`control_event` re-runs `_apply_trv_law` then the water prelude (`apps/ha_smart_hvac/hvac_app.py:256 (control_event) @ 2ec1908`).

**Looked for, not found:** `listen_state` on `valve_closure`; use of the `.commissioned` property in `hvac_app.py` (runtime uses None checks on ids).

## 3. How does the flame short-on hold timer schedule, cancel, and fire?
Hold is scheduled only in `flame_event` after a successful SWT `0` trip write on a short `on→off` fall under `_flame_observe_gate` (`apps/ha_smart_hvac/hvac_app.py:190-207 (flame_event) @ 2ec1908`): bump `_flame_trip_hold_token`, `run_in(_flame_trip_hold_expired, flame_trip_hold_s, token=…)`, store handle, set `_flame_trip_latched`. Failed trip write schedules nothing and does not latch (`apps/ha_smart_hvac/hvac_app.py:214-220 (flame_event) @ 2ec1908`).

`flame_trip_hold_s` defaults to 900 and must parse to int ≥ 1 (`apps/ha_smart_hvac/config.py:234-239 (flame_trip_hold_s) @ 2ec1908`).

`_disarm_flame_trip_hold` clears `_flame_on_since`, increments the token, and `cancel_timer` when a handle exists (`apps/ha_smart_hvac/hvac_app.py:152-158 (_disarm_flame_trip_hold) @ 2ec1908`). `_clear_flame_trip_state` clears the latch then disarms (`apps/ha_smart_hvac/hvac_app.py:147-150 (_clear_flame_trip_state) @ 2ec1908`). Clear/disarm call sites include plant-off `_hands_off` (`apps/ha_smart_hvac/hvac_app.py:81-82 (_gate_prelude) @ 2ec1908`; `apps/ha_smart_hvac/hvac_app.py:301-303 (_hands_off) @ 2ec1908`), zone rising-edge under latch in `_gate_prelude` (`apps/ha_smart_hvac/hvac_app.py:104-105 (_gate_prelude) @ 2ec1908`), hold-callback start, and `_go_idle` (disarm only; latch cleared after successful idle write `0`) (`apps/ha_smart_hvac/hvac_app.py:305-308 (_go_idle) @ 2ec1908`).

`_flame_trip_hold_expired`: return if `token` mismatches; else clear state, `_apply_trv_law`, `_gate_prelude`, optional `_run_demand` (`apps/ha_smart_hvac/hvac_app.py:160-170 (_flame_trip_hold_expired) @ 2ec1908`).

**Looked for, not found:** a second production schedule path for this hold besides `flame_event` → `run_in`.

## 4. How are TRV soft-close and hold/timer covered in tests?
Runtime coverage is mocked `HvacApp` unit tests in `tests/test_hvac_app.py`, plus YAML parse tests in `tests/test_config.py`. No TRV tests in other `tests/` files; no live AppDaemon timer integration tests.

**TRV (`test_trv_*`, ~2083–2613):** floor at/below setpoint (`tests/test_hvac_app.py:2106 (test_trv_at_or_below_setpoint_writes_floor) @ 2ec1908`); overshoot 100 + latch (`tests/test_hvac_app.py:2117 (test_trv_overshoot_writes_100_and_latches) @ 2ec1908`); dead-band hold (`tests/test_hvac_app.py:2124 (test_trv_dead_band_keeps_100_while_latched) @ 2ec1908`); clear (`tests/test_hvac_app.py:2132 (test_trv_clear_writes_floor_and_unlatches) @ 2ec1908`); plant-off 100 (`tests/test_hvac_app.py:2147 (test_trv_plant_off_writes_100_no_plant_setpoint) @ 2ec1908`); TRV still runs while flame latched (`tests/test_hvac_app.py:2083 (test_trv_runs_while_flame_latched) @ 2ec1908`; `tests/test_hvac_app.py:2095 (test_trv_runs_while_flame_latched_via_control_event) @ 2ec1908`); accuracy init listen and accuracy-only reapply (`tests/test_hvac_app.py:2294 (test_initialize_trv_mapping_listens_on_climate_attrs) @ 2ec1908`; `tests/test_hvac_app.py:2425 (test_trv_accuracy_state_change_reapplies_law) @ 2ec1908`); plain-string thermostats skip closure writes (`tests/test_hvac_app.py:2160 (test_trv_plain_string_thermostats_no_closure_write) @ 2ec1908`).

**Flame hold:** short-on schedules `run_in` to `_flame_trip_hold_expired` with `flame_trip_hold_s` and token (`tests/test_hvac_app.py:1080 (test_flame_short_on_latches_and_writes_zero) @ 2ec1908`); expiry order TRV then prelude (`tests/test_hvac_app.py:1433 (test_flame_hold_expiry_gated_runs_trv_then_curve) @ 2ec1908`; `tests/test_hvac_app.py:1462 (test_flame_hold_expiry_applies_trv_valve_then_curve) @ 2ec1908`); plant-off cancel (`tests/test_hvac_app.py:1516 (test_plant_off_clears_flame_trip_state) @ 2ec1908`); orphan tokens (`tests/test_hvac_app.py:1581 (test_orphan_hold_callback_after_clear_no_demand_write) @ 2ec1908`; `tests/test_hvac_app.py:1595 (test_orphan_hold_callback_after_retrip_does_not_clear_new_latch) @ 2ec1908`); idle write-fail disarms hold (`tests/test_hvac_app.py:1617 (test_idle_write_fail_keeps_latch_disarms_hold) @ 2ec1908`).

**Config:** commissioned mapping (`tests/test_config.py:536 (test_parse_thermostat_mapping_commissioned) @ 2ec1908`); reject partial (`tests/test_config.py:600 (test_parse_rejects_partial_or_invalid_trv_fields) @ 2ec1908`); `valve_closure_floor` override (`tests/test_config.py:511 (test_parse_valve_closure_floor_override) @ 2ec1908`); `flame_trip_hold_s` reject/truncate (`tests/test_config.py:323 (test_parse_rejects_flame_trip_hold_in_open_unit_interval) @ 2ec1908`; `tests/test_config.py:331 (test_parse_flame_trip_hold_truncates_fractional_seconds) @ 2ec1908`) — parse only, not runtime hold.

## 5. Why does commissioned TRV soft-close require `accuracy`?
At `2ec1908`, blame on the pair-mandatory parse and `commissioned` property traces to `784fc71` “feat(trv): add idle max-close soft-close for Sonoff valves” merged as **#146** (`5f41e86`). That commit introduced mapping that requires both `valve_closure` and `accuracy`, `ThermostatConfig.commissioned` as both non-`None`, and overshoot hysteresis using the accuracy number entity (`784fc71 "feat(trv): add idle max-close soft-close for Sonoff valves" #146`).

Follow-on history (still ≤10 commits followed):

- `b4d7603 "fix(trv): keep latched soft-close without accuracy" #146` — latched path no longer skips on unread accuracy; unlatched overshoot still needs a readable accuracy.
- `e1a3c81 "chore(trv): close epic-4 soft-close deferred leftovers" #148` — `listen_state` on accuracy → shared `control_event`.
- `eb79e95 "fix(trv): use abs(accuracy) for overshoot band" #161` — signed Sonoff accuracy false-trips.
- `ef4d7a0 "fix(trv): trip overshoot at T_zone >= setpoint+|accuracy|" #162` — inclusive band edge.

`2ec1908` is merge **#163** (replan); it does not introduce the accuracy requirement. `git log -S "valve_closure and accuracy"` finds only `784fc71`.

## 6. What touches `_apply_trv_law` / `_trv_overshoot_latched`?
Production references under `apps/` are only in `apps/ha_smart_hvac/hvac_app.py`:

**`_apply_trv_law`**

- Definition: `apps/ha_smart_hvac/hvac_app.py:398 (_apply_trv_law) @ 2ec1908`
- `apps/ha_smart_hvac/hvac_app.py:165 (_flame_trip_hold_expired) @ 2ec1908` — call after flame clear, before prelude
- `apps/ha_smart_hvac/hvac_app.py:239 (control_tick) @ 2ec1908` — first step of tick
- `apps/ha_smart_hvac/hvac_app.py:256 (control_event) @ 2ec1908` — first step of event path

`initialize` reaches it only via `control_tick` (`apps/ha_smart_hvac/hvac_app.py:57 (initialize) @ 2ec1908`).

**`_trv_overshoot_latched`**

- Init empty set: `apps/ha_smart_hvac/hvac_app.py:45 (initialize) @ 2ec1908`
- Read membership: `apps/ha_smart_hvac/hvac_app.py:421 (_apply_trv_law) @ 2ec1908`
- Discard after successful floor clear: `apps/ha_smart_hvac/hvac_app.py:432 (_apply_trv_law) @ 2ec1908`
- Add after successful overshoot 100: `apps/ha_smart_hvac/hvac_app.py:457 (_apply_trv_law) @ 2ec1908`

No other production read/add/discard under `apps/`.

## Where the answers meet
**`_apply_trv_law` → `_write_number`:** Questions 1 and 6 share the write path. Unreadable current rejects the service call with WARNING and `False`; equal float skips the service call and returns `True` (`apps/ha_smart_hvac/hvac_app.py:379-396 (_write_number) @ 2ec1908`). Latch add/discard in Q1 is gated on that return value (`apps/ha_smart_hvac/hvac_app.py:423-457 (_apply_trv_law) @ 2ec1908`).

**Hold callback → TRV then water prelude:** Questions 1, 3, and 6 meet at `_flame_trip_hold_expired`: orphan token reject returns early; else clear flame state, `_apply_trv_law`, then `_gate_prelude` (None aborts demand) (`apps/ha_smart_hvac/hvac_app.py:160-170 (_flame_trip_hold_expired) @ 2ec1908`).

**Commission pair:** Questions 2 and 5 meet at pair-mandatory yaml: mapping without both keys raises `ConfigError` (`apps/ha_smart_hvac/config.py:135-137 (_parse_thermostat) @ 2ec1908`), introduced with the overshoot law in `784fc71 #146`.

## Prior documents
- ADR 0008 — weather-curve TRV flame SWT (title listed at plan gate; not opened as primary evidence)
- `adr-trv-accuracy-shared-control-event` (title)
- `adr-trv-write-gated-overshoot-latch` (title)
- `adr-trv-plant-off-no-latch-clear` (title)
- `adr-trv-before-water-prelude` (title)
- `adr-flame-hold-expiry-trv-then-prelude` (title)