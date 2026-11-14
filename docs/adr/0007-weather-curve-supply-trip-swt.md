---
status: accepted
---

# Weather-curve Set Water Temperature with supply rise-rate trip
The HVAC App commands Set Water Temperature from Weather Feedforward under Plant Management and Heating Demand gates, with a supply water rise-rate trip that can force and hold `0`. Demand command is `round-to-0.1(clamp(u_ff))` with `u_ff = base + slope × (comfort_ref − T_out)`. This supersedes ADR 0005 (fixed-PID SWT) and ADR 0006 (optional RLS adaptive Kp/Ki). CAP-7 rise-rate auto-correct, adapting `base`/`slope`, and `ff_auto_correct_state.json` are not on the water path, must not be commissioned, and are out of scope. Fixed PID / ∫ / RLS / `rls_state.json` are not live water law.

This ADR is **agent law** for the live App — MUST-floor only. Cite `hvac_app.py` / `feedforward.py` and `docs/decisions/adr-supply-event-no-outdoor-prelude.md`, `docs/decisions/adr-idle-trip-clear-after-write.md`; do not invent runtime.

## SWT gates
When Plant Management is on and Heating Demand is present, the HVAC App writes the demand command above (unless the supply trip is latched — then it keeps writing `0`). When Plant Management is on and a Plant-on non-demand exit applies (see Idle clear), it writes `0` and applies Decision C (disarm/wipe always; clear latch only after successful idle write `0`). When Plant Management is off, it does not write Set Water Temperature and clears trip state via `_clear_trip_state` — not “write 0”.

The HVAC App owns the OpenTherm Set Water Temperature write. The Multi-Zone Coordinator computes Zone Errors, Heating Demand, and Critical Zone selection for diagnostics and logging only — it does not drive Set Water Temperature or the supply rise-rate trip.

## Feedforward law
```
u_ff = base + slope × (comfort_ref − T_out)
command = round-to-0.1(clamp(u_ff, setpoint_min, setpoint_max))
```
`base`, `slope`, and `comfort_ref` commission from yaml (`weather_feedforward`). Outdoor Temperature is required on the demand path. Non-finite `u_ff` is a Plant-on non-demand exit (`_go_idle`).

## CAP-8 listeners (shared writer)
The same Outdoor-gated demand writer (`_run_demand`) runs on:

- **Initialize:** after a successful schedule, `initialize` runs one full `control_tick` so the first demand command does not wait a full `control_interval`.
- **Periodic `control_interval`** (`control_tick`): `_gate_prelude` then `_run_demand`.
- **Event path** (`listen_state` → `control_event`): re-evaluates on change of Plant Management, Outdoor Temperature, any configured zone air temperature, or any configured thermostat’s `hvac_action` or setpoint (`temperature` attribute). Same prelude + writer as the tick — every eligible event may rewrite demand SWT (not a one-shot rising-edge demand latch).

There is no debounce. The write throttle is the equal-float skip on Set Water Temperature plant readback. Unreadable or non-finite plant readback skips the write. Changing Heating Demand inputs must update those listeners in the same change. Periodic cadence remains; an event-only loop is a non-goal.

## Dual-gate
- **Outdoor / `control_tick` / `control_event`:** use `_gate_prelude` — Plant Management on, readable Outdoor Temperature, valid zone reads, and Heating Demand. Failures take plant-off (`_hands_off`) or `_go_idle` as appropriate. Empty zone reads leave `_zone_heating_prior` unchanged.
- **`supply_event`:** use `_plant_and_heating_demand` only (Plant on ∧ Heating Demand). Never call `_gate_prelude` or require Outdoor — see `docs/decisions/adr-supply-event-no-outdoor-prelude.md`.

## Trip latch
On `supply_event` under Plant∧Demand, the App samples supply water (`boiler_water`) and compares observed rise rate `r_obs` (°C/min) to yaml `r_max`. When `r_obs > r_max`, it attempts SWT write `0`. The trip **latches only after that write succeeds**; a failed write does not latch. While latched, demand `_run_demand` keeps writing `0`. Hold timer (`hold`) starts on successful latch; on hold expiry the App clears trip RAM and re-runs Outdoor prelude + demand only when `_gate_prelude` returns zones (prelude failure does not invent a demand write). A per-zone Heating Demand False→True rising edge under `_gate_prelude` also clears trip state. Plant-off clears via `_clear_trip_state` (no write).

## Idle clear (Decision C)
`_go_idle` covers every Plant-on non-demand exit: no Heating Demand, unavailable Outdoor, no valid zones, and non-finite `u_ff`. It always disarms the hold timer and wipes supply samples. It clears `_supply_trip_latched` only after a successful idle SWT write `0`; write-fail keeps the latch — see `docs/decisions/adr-idle-trip-clear-after-write.md`.

## Out of scope
CAP-7 / adapting `base`/`slope` / `ff_auto_correct_state.json`: not on the water path; do not commission; out of scope. Live PID / ∫ / RLS / `rls_state.json` and Critical Zone closed-loop air→water tracking are out of scope. ADR 0004–0006 are historical prior art with live-pointers to this ADR.
