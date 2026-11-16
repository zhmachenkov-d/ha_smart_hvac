---
type: epic
title: "Replace supply trip with flame short-on"
parent: initiative-weather-swt-supply-trip
covers: ["R11", "R12", "R1"]
sources:
  - _bmad-output/initiative-weather-swt-supply-trip/initiative-weather-swt-supply-trip.md
  - _bmad-output/initiative-weather-swt-supply-trip/forge-trv-valve-closure-anti-cycle/forge-trv-valve-closure-anti-cycle.md
companions: []
after: []
refined: true
risk: high
---

# Replace supply trip with flame short-on

## Description
Remove the supply rise-rate trip (`r_obs` / `r_max` / `boiler_water` trip path) from code, yaml, and tests, and replace it with a flame short-on SWT trip: under Plant on ∧ Heating Demand ∧ `ch_active` ∧ latch clear, if `flame_on` True duration &lt; `flame_on_min_s`, attempt SWT `0` and latch only after successful write. Clear on hold, zone rising-edge, plant-off, or successful idle write-0 (Decision C). While latched, weather curve is not applied; TRV soft-close from epic 4 keeps running.

## Outcome
Plant anti-cycle is flame short-on latching SWT to 0 (not supply rise-rate); after clear, demand SWT follows the weather curve again when gates allow.

## Requirements
1. **R1 (parent R11):** Under Plant on ∧ Heating Demand ∧ bridge `ch_active` ∧ latch clear, if `flame_on` True duration (True→False) is &lt; yaml `flame_on_min_s` (default **300**), the App attempts SWT `0` and latches only after that write succeeds — the weather curve is not applied while latched.
2. **R2 (parent R12):** The flame latch clears when yaml `flame_trip_hold_s` (default **900**) elapses, when Heating Demand appears on a zone that previously had none (zone rising-edge), on Plant Management off (clear without SWT write), or after a successful idle SWT write `0` (Decision C — write-fail keeps the latch); after clear, demand SWT again follows parent R1 when gates allow. While flame-latched, the TRV soft-close law (parent R9/R10) keeps running.
3. **R3 (parent R1):** Under Plant Management on and Heating Demand, and when the flame short-on latch is clear, the App commands Set Water Temperature = round-to-0.1(clamp(`u_ff`)), where `u_ff = base + slope × (comfort_ref − T_out)` from yaml-commissioned Weather Feedforward parameters and Outdoor Temperature.

## Constraints
1. **C1 (parent C1):** Implementation stays inside the AppDaemon `ha_smart_hvac` App writing the existing HA plant Set Water Temperature entity and commissioned Sonoff TRV `valve_closure_degree` numbers.
2. **C2 (parent C2):** Exclusive Session (ADR 0001) and Heating Demand via thermostat `hvac_action=heating` are unchanged.
3. **C3 (parent C3):** SWT uses round-to-0.1 and clamp into existing `setpoint_min` / `setpoint_max` only.
4. **C4 (parent C4):** Critical Zone must not drive Set Water Temperature, TRV soft-close, or the flame trip.
5. **C5 (parent C5):** Outdoor, `flame_on`, `ch_active`, and per-TRV closure/accuracy entity ids are yaml-commissioned; house entity ids are not hardcoded and house `apps.yaml` changes require owner confirmation.
6. **C6 (parent C6):** CAP-7 / adapting `base`/`slope` / `ff_auto_correct_state.json` are out of scope for this initiative.

## Done when
1. Supply rise-rate trip path is gone from App, config models (`boiler_water`, `r_max`, supply-trip hold), example yaml, and tests.
2. Flame observe gate + short-on duration trip latches SWT `0` only after successful write; while latched, demand keeps `0`.
3. Latch clears on hold, zone rising-edge, plant-off, or successful idle write-0; then weather-curve demand (R3) when gates allow; hold-expiry clear also re-applies TRV law (ADV8).
4. TRV soft-close continues while flame-latched; house yaml commissions confirmed `flame_on` / `ch_active`.
5. Automated tests lock remove + flame latch/clear and interaction with weather-curve demand.

## Boundaries
Owns supply-trip removal and flame short-on observe/latch/clear on the SWT path, plus `flame_on` / `ch_active` / `flame_on_min_s` / `flame_trip_hold_s` yaml. Does not own TRV soft-close (epic 4) or ADR/docs (epic 6). Must not restore supply rise-rate trip.

- Touch point: `apps/ha_smart_hvac/` — remove supply trip; flame latch; gate CAP-8 FF writer; owner: this epic
- Touch point: `apps/apps.yaml` / `apps.yaml.example` — remove trip keys (`boiler_water`, `r_max`, supply hold); add flame entities/defaults; owner: this epic
- Must not change: Exclusive Session; Heating Demand definition; TRV soft-close behavior from epic 4

## References
- parent — `_bmad-output/initiative-weather-swt-supply-trip/initiative-weather-swt-supply-trip.md`, Requirements R11–R12 and R1 latch; Constraints C1–C6
- source — `_bmad-output/initiative-weather-swt-supply-trip/forge-trv-valve-closure-anti-cycle/forge-trv-valve-closure-anti-cycle.md`
- sibling — `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-trv-idle-max-close/epic-trv-idle-max-close.md`

## Notes
- Waits on epic-trv-idle-max-close because: TRV soft-close primary anti-cycle must be live before supply trip is removed.
- Shared covers: R1 with epic 1 (weather formula there; flame latch gate here).
- Decision: Envelope approved thin (`refined: false`) — remove+flame one epic (2026-11-15); refine before stories.
- Decision: Refine from parent covers only — no extra companions before stories (2026-11-16).
- Decision: ADV8 — after flame latch clear via hold expiry, call `_apply_trv_law` then Outdoor prelude + demand (same order as tick/`control_event`) (2026-11-16).
- Decision: Remove `boiler_water`, `r_max`, and supply-trip hold from App config with the trip path; HA sensor may remain unused (2026-11-16).
