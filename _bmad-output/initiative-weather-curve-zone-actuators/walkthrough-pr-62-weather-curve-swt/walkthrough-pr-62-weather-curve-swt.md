# Walkthrough — PR #62: weather-curve SWT law

Target: [PR #62](https://github.com/zhmachenkov-d/ha_smart_hvac/pull/62) (`feat/1-1-weather-curve-swt-law` → `main`, commit `a10c00d`)
Focus: human review of Tracer entry — Set Water Temperature as `clamp(weather_feedforward)` only
Current block: **complete**

## Blocks

- [x] **Intent** — done
- [x] **Broad strokes** — done
- [x] **Demand-path clamp law** — done
- [x] **Heating-demand gate** — done
- [x] **CAP-5 tests / kill-list** — done
- [x] **Dormancy of LADRC** — done
- [x] **Periphery** — done

## Intent

Source: [story-tracer-weather-curve-swt-law-plan.md](../epic-weather-curve-swt-only/story-tracer-weather-curve-swt-law-plan.md) (`<frozen-after-approval>` ## Intent, pasted verbatim).

**Problem:** With Critical Zone air near setpoint, LADRC tracking on the water path still grows `u_track` until Set Water Temperature pegs at `setpoint_max`. Feedforward alone is not the culprit — air→SWT closed loop keeps raising water when the room barely moves.

**Approach:** Rewire the control tick so Plant Management / Heating Demand gates command Set Water Temperature as `clamp(weather_feedforward)` only (Heating Demand = any-zone boolean). Leave LADRC/tuner modules on disk but unwired from the demand write path (entry 2 deletes them). Lock the law with CAP-5 automated tests.

## Broad strokes

What the change is: on a demand tick, Set Water Temperature is `clamp(u_ff)` from the weather curve only — no air tracking, no Critical Zone driver, no ωc adapt/publish on that path. Heating Demand is an any-zone boolean; LADRC/tuner stay constructed but dormant for SWT until entry 2.

Entry points (open in this order):

1. [`control_tick` demand branch](../../../apps/ha_smart_hvac/hvac_app.py#L184) — PM / outdoor / zones gates, then `clamp(u_ff)` write + outdoor/`u_ff`/command INFO
2. [`has_heating_demand`](../../../apps/ha_smart_hvac/coordinator.py#L8) — heating-eligible Zone Error > 0; replaces Critical Zone selection on the SWT tick
3. [`weather_feedforward`](../../../apps/ha_smart_hvac/feedforward.py#L8) — reused unchanged as the sole SWT baseline
4. [CAP-5 suite](../../../tests/test_hvac_app.py#L792) — locks (a–e); kill-list removed former LADRC demand-path asserts
5. [`initialize` LADRC/tuner construct](../../../apps/ha_smart_hvac/hvac_app.py#L165) — still built/`_load()` ωc; clear on idle/off; unwired from demand write

## Demand-path clamp law

Under Plant Management on and Heating Demand, [`control_tick`](../../../apps/ha_smart_hvac/hvac_app.py#L211) computes `u_ff = weather_feedforward(...)`, clamps with `setpoint_min`/`setpoint_max`, and writes via [`_write_setpoint`](../../../apps/ha_smart_hvac/hvac_app.py#L296). The demand INFO line reports outdoor / `u_ff` / command only — no Critical Zone, no `u_track`. Tracking, guard, adapt, commit, advance, and `publish_sensor` are absent from this branch.

- Demand write: [`hvac_app.py:211–215`](../../../apps/ha_smart_hvac/hvac_app.py#L211)
- Fail-write abort (no `command=` INFO): [`test_demand_fail_write_aborts_without_success_info`](../../../tests/test_hvac_app.py#L846)
- Idle clear + write 0: [`hvac_app.py:202–209`](../../../apps/ha_smart_hvac/hvac_app.py#L202)
- Plant-off hands-off (no write): [`_hands_off`](../../../apps/ha_smart_hvac/hvac_app.py#L217)
- Sensor-missing idle: [`_go_idle`](../../../apps/ha_smart_hvac/hvac_app.py#L224)

## Heating-demand gate

[`has_heating_demand`](../../../apps/ha_smart_hvac/coordinator.py#L8) is true when any zone has positive Zone Error among heating-eligible thermostats — the same eligibility as `ZoneSnapshot.zone_error` (idle/non-heating do not demand). [`control_tick`](../../../apps/ha_smart_hvac/hvac_app.py#L202) uses that boolean only; it does not call `select_critical_zone` on the SWT path in this entry.

- Gate: [`coordinator.py:8–15`](../../../apps/ha_smart_hvac/coordinator.py#L8)
- Wire: [`hvac_app.py:202`](../../../apps/ha_smart_hvac/hvac_app.py#L202)
- Tests: [`test_has_heating_demand_*`](../../../tests/test_coordinator.py#L25), including all-idle / non-heating → false

## CAP-5 tests / kill-list

CAP-5 in [`test_hvac_app.py`](../../../tests/test_hvac_app.py#L792) locks the weather-curve-only law: (a) demand → `clamp(u_ff)` with no tracking/publish/adapt; (b) plant-on idle → write 0 + clear; (c) plant-off → no write + clear; (d) flat near-setpoint air multi-tick stays at FF clamp; (e) max-error zone air not additive on SWT. Former tick-level asserts of `clamp(u_ff + u_track)` / LADRC demand wiring are on the plan kill-list and removed in this PR; Hass-free helper/mirror units stay until entry 2.

- CAP-5(a–e): [`test_cap5_*`](../../../tests/test_hvac_app.py#L808)
- Kill-list / leave-list: [plan Code Map](../epic-weather-curve-swt-only/story-tracer-weather-curve-swt-law-plan.md) (`tests/test_hvac_app.py` bullets)

## Dormancy of LADRC

[`ladrc.py`](../../../apps/ha_smart_hvac/ladrc.py) / [`ladrc_tuner.py`](../../../apps/ha_smart_hvac/ladrc_tuner.py) remain on disk. [`initialize`](../../../apps/ha_smart_hvac/hvac_app.py#L172) still constructs `LadrcState` and `LadrcTuner` (constructor [`_load()`](../../../apps/ha_smart_hvac/ladrc_tuner.py#L29) may hydrate persisted ωc). Idle/off paths still clear LADRC/tuner/latch flags so leftover state cannot affect a later demand tick. The demand write path must not call tracking, guard, adapt, commit, or `publish_sensor` — temporary dormancy until entry 2 (CAP-4); this entry does not claim the spec’s “remove now” end-state.

- Construct: [`hvac_app.py:172–176`](../../../apps/ha_smart_hvac/hvac_app.py#L172)
- Clear on no-demand / hands-off / go-idle: [`hvac_app.py:203–206`](../../../apps/ha_smart_hvac/hvac_app.py#L203), [`217–221`](../../../apps/ha_smart_hvac/hvac_app.py#L217), [`224–228`](../../../apps/ha_smart_hvac/hvac_app.py#L224)
- Module helpers still present (unused on demand path until entry 2): [`guard_u_track`](../../../apps/ha_smart_hvac/hvac_app.py#L43), [`advance_with_tracking_residue`](../../../apps/ha_smart_hvac/hvac_app.py#L24)

## Periphery

- [story-tracer-weather-curve-swt-law-plan.md](../epic-weather-curve-swt-only/story-tracer-weather-curve-swt-law-plan.md) — status `built`; frozen Intent / AC / CAP-5 recipe
- [spec-weather-curve-swt-only.md](../spec-weather-curve-swt-only/spec-weather-curve-swt-only.md) — CAP-1/2/3/5 contract (docs only this entry; no CONTEXT/ADR update)
- [brownfield.md](../spec-weather-curve-swt-only/brownfield.md) — gate table context
