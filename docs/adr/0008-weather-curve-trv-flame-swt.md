---
status: accepted
---

# Weather-curve Set Water Temperature with TRV soft-close and flame short-on
The HVAC App commands Set Water Temperature from Weather Feedforward under Plant Management and Heating Demand gates, with TRV soft-close before the water prelude and a flame short-on trip that can force and hold `0`. Demand command is `round-to-0.1(clamp(u_ff))` with `u_ff = base + slope × (comfort_ref − T_out)`. This supersedes ADR 0007 for live water law. CAP-7 rise-rate auto-correct, adapting `base`/`slope`, and `ff_auto_correct_state.json` are not on the water path, must not be commissioned, and are out of scope. Fixed PID / ∫ / RLS / `rls_state.json` are not live water law.

This ADR is **agent law** for the live App — MUST-floor only. Cite `hvac_app.py` / `feedforward.py` / `coordinator.py` and live flame/TRV decisions (`docs/decisions/adr-flame-observe-gate-no-outdoor.md`, `docs/decisions/adr-write-gated-flame-latch.md`, `docs/decisions/adr-flame-latch-ram-only-no-reassert.md`, `docs/decisions/adr-flame-hold-expiry-trv-then-prelude.md`, `docs/decisions/adr-idle-flame-clear-after-write.md`, `docs/decisions/adr-trv-before-water-prelude.md`, `docs/decisions/adr-trv-write-gated-overshoot-latch.md`, `docs/decisions/adr-trv-plant-off-no-latch-clear.md`, `docs/decisions/adr-trv-accuracy-shared-control-event.md`); do not invent runtime.

## SWT gates
When Plant Management is on and Heating Demand is present and `_flame_trip_latched` is false, the HVAC App writes the demand command above. When Plant Management is on, Heating Demand is present, and `_flame_trip_latched` is true, demand `_run_demand` keeps writing SWT `0` (no curve evaluation, no Critical Zone select-log). When Plant Management is on and a Plant-on non-demand exit applies (see Idle clear), it writes `0` and applies Decision C. When Plant Management is off, it does not write Set Water Temperature and clears flame trip state via `_clear_flame_trip_state` — not “write 0” (TRV soft-close still runs).

The HVAC App owns the OpenTherm Set Water Temperature write. The Multi-Zone Coordinator computes Zone Errors, Heating Demand, and Critical Zone selection for diagnostics and logging only — Critical Zone must not drive Set Water Temperature, TRV soft-close, or the flame short-on trip.

## Feedforward law
```
u_ff = base + slope × (comfort_ref − T_out)
command = round-to-0.1(clamp(u_ff, setpoint_min, setpoint_max))
```
`base`, `slope`, and `comfort_ref` commission from yaml (`weather_feedforward`). Outdoor Temperature is required on the demand path. Non-finite `u_ff` is a Plant-on non-demand exit (`_go_idle`).

## CAP-8 listeners (shared writer)
The same Outdoor-gated demand writer (`_run_demand`) runs on:

- **Initialize:** after a successful schedule, `initialize` runs one full `control_tick` so the first demand command does not wait a full `control_interval`.
- **Periodic `control_interval`** (`control_tick`): `_apply_trv_law` then `_gate_prelude` then `_run_demand`.
- **Event path** (`listen_state` → `control_event`): re-evaluates on change of Plant Management, Outdoor Temperature, any configured zone air temperature, any configured thermostat’s `hvac_action` or setpoint (`temperature` attribute), or a commissioned thermostat `accuracy` entity. Same TRV-then-prelude + writer as the tick — every eligible event may rewrite demand SWT (not a one-shot rising-edge demand latch). Accuracy listen is shared `control_event` only — see `docs/decisions/adr-trv-accuracy-shared-control-event.md`.

There is no debounce. The write throttle is the equal-float skip on Set Water Temperature plant readback. Unreadable or non-finite plant readback skips the write. Changing Heating Demand inputs must update those listeners in the same change. Periodic cadence remains; an event-only loop is a non-goal. Event writes must not reset or reschedule `control_interval`.

## TRV soft-close
`_apply_trv_law` runs before `_gate_prelude` on `control_tick`, `control_event`, and flame hold expiry — see `docs/decisions/adr-trv-before-water-prelude.md`. Flame observe / latch handlers do not call `_apply_trv_law`. Writes target only `valve_closure_degree`; never `valve_opening_degree`. Critical Zone never drives TRV.

Under Plant Management off, every commissioned Sonoff TRV gets closure `100` **without** clearing `_trv_overshoot_latched` — see `docs/decisions/adr-trv-plant-off-no-latch-clear.md`. Under Plant Management on: floor / overshoot-to-100 hysteresis is write-gated (`docs/decisions/adr-trv-write-gated-overshoot-latch.md`); overshoot latches only after a successful closure-100 write; clear to floor discards the latch only after a successful floor write.

## Flame trip latch
Short-on = `flame_on` True duration `< flame_on_min_s` on a True→False fall under the observe gate. `_flame_observe_gate` = Plant Management on ∧ Heating Demand ∧ `ch_active` on ∧ ¬`_flame_trip_latched` — **never Outdoor** — see `docs/decisions/adr-flame-observe-gate-no-outdoor.md`.

Latch only after a successful trip SWT write `0` **and** hold `run_in` scheduled — see `docs/decisions/adr-write-gated-flame-latch.md`. Latch / since / hold live in process RAM only; while latched, `flame_event` / `ch_active_event` wipe `since` only and do not re-assert SWT — see `docs/decisions/adr-flame-latch-ram-only-no-reassert.md`. Hold callbacks carry `_flame_trip_hold_token`; a mismatched token on `_flame_trip_hold_expired` is a no-op (orphan guard).

Clear paths:

- Hold expiry: clear latch, `_apply_trv_law`, then Outdoor `_gate_prelude` + `_run_demand` when prelude returns zones — see `docs/decisions/adr-flame-hold-expiry-trv-then-prelude.md`.
- Zone Heating Demand rising-edge under `_gate_prelude`: `_clear_flame_trip_state` — see `docs/decisions/adr-zone-rising-edge-decision-a.md`.
- Plant-off: `_clear_flame_trip_state` (no SWT write).
- Idle Decision C (below).

## Idle clear (Decision C)
`_go_idle` covers every Plant-on non-demand exit: no Heating Demand, unavailable Outdoor, no valid zones, and non-finite `u_ff`. It always disarms the hold via `_disarm_flame_trip_hold` (no supply-sample wipe). It clears `_flame_trip_latched` only after a successful idle SWT write `0`; write-fail keeps the latch — see `docs/decisions/adr-idle-flame-clear-after-write.md`.

## Dual-gate
- **Outdoor / `control_tick` / `control_event`:** use `_gate_prelude` — Plant Management on, readable Outdoor Temperature, valid zone reads, and Heating Demand. Failures take plant-off (`_hands_off`) or `_go_idle` as appropriate. Empty zone reads leave `_zone_heating_prior` unchanged.
- **Flame observe:** use `_flame_observe_gate` only (Plant∧Demand∧`ch_active` on∧¬latch). Never call `_gate_prelude` or require Outdoor.

## Out of scope
CAP-7 / adapting `base`/`slope` / `ff_auto_correct_state.json`: not on the water path; do not commission; out of scope. Live PID / ∫ / RLS / `rls_state.json` and Critical Zone closed-loop air→water tracking are out of scope. ADR 0007’s prior anti-cycle era is historical; live anti-cycle is flame short-on + TRV soft-close. ADR 0004–0006 are historical prior art with live-pointers to this ADR.