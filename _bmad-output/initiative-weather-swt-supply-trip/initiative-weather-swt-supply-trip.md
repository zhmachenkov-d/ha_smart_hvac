---
type: initiative
title: "Weather-curve SWT with TRV soft-close and flame short-on trip"
parent: none
sources:
  - _bmad-output/initiative-weather-swt-supply-trip/source-user-weather-swt-supply-trip.md
  - _bmad-output/initiative-weather-swt-supply-trip/forge-trv-valve-closure-anti-cycle/forge-trv-valve-closure-anti-cycle.md
  - docs/adr/0004-weather-curve-swt.md
  - docs/adr/0005-fixed-pid-swt.md
  - CONTEXT.md
companions:
  - _bmad-output/initiative-weather-swt-supply-trip/source-user-weather-swt-supply-trip.md
  - _bmad-output/initiative-weather-swt-supply-trip/forge-trv-valve-closure-anti-cycle/forge-trv-valve-closure-anti-cycle.md
after: []
assignee: ""
risk: high
---

# Weather-curve SWT with TRV soft-close and flame short-on trip

## Description
Replace the live fixed-PID / optional RLS Set Water Temperature path (ADR 0005 / 0006) with weather-curve feedforward under the existing Plant Management and Heating Demand gates; remove the supply rise-rate trip; add Sonoff TRV idle max-close soft-close as primary anti-cycle and a flame short-on SWT trip as fallback. Supersedes the PID initiative's water law for live commissioning; CAP-7 curve auto-correct stays out.

## Outcome
Under Plant Management, demand Set Water Temperature follows `round-to-0.1(clamp(u_ff))` from Outdoor Temperature; commissioned Sonoff TRVs hold an idle max-close floor (with overshoot to full close); a flame short-on under the observe gate latches SWT to 0 until clear — yielding less boiler short-cycling and more stable zone temperature, without PID/RLS on the water path.

## Requirements
1. **R1 (D1, D9, forge):** Under Plant Management on and Heating Demand, and when the flame short-on latch is clear, the App commands Set Water Temperature = round-to-0.1(clamp(`u_ff`)), where `u_ff = base + slope × (comfort_ref − T_out)` from yaml-commissioned Weather Feedforward parameters and Outdoor Temperature.
2. **R2 (D9):** Plant Management on and no Heating Demand writes `0` and clears ephemeral / water-path state (not persisted trip-commission files beyond what Constraints allow).
3. **R3 (D9):** Plant Management off does not write Set Water Temperature and clears ephemeral / water-path state.
4. **R4 (D7):** Fixed PID (`base_water_temp + u_pid`, ∫), optional RLS adaptive gains, and `rls_state.json` are removed from the live SWT path and commissioning; domain docs and a new ADR supersede ADR 0005 / 0006 for this water law.
5. **R7 (C5, forge):** Outdoor Temperature is yaml-commissioned on the weather-curve SWT path and commissioning; anti-cycle no longer requires a supply rise-rate entity.
6. **R8 (C4, C6, forge):** Critical Zone remains diagnostics/logging only and does not drive Set Water Temperature, TRV soft-close, or the flame trip; CAP-7 rise-rate auto-correct of `base`/`slope` and `ff_auto_correct_state.json` are not restored in this initiative.
7. **R9 (forge):** Under Plant Management on, for every commissioned Sonoff TRV the App writes only `valve_closure_degree` as idle max-close: yaml `valve_closure_floor` (default **80**) by default; **100** when that TRV's zone `T_zone > setpoint + accuracy`; restore floor when `T_zone ≤ setpoint` — with or without Heating Demand.
8. **R10 (forge):** Under Plant Management off, the App writes `valve_closure_degree` = **100** on all commissioned Sonoff TRVs.
9. **R11 (forge):** Under Plant on ∧ Heating Demand ∧ bridge `ch_active` ∧ latch clear, if `flame_on` True duration (True→False) is &lt; yaml `flame_on_min_s` (default **300**), the App attempts SWT `0` and latches only after that write succeeds — the weather curve is not applied while latched.
10. **R12 (forge, Decision C):** The flame latch clears when yaml `flame_trip_hold_s` (default **900**) elapses, when Heating Demand appears on a zone that previously had none (zone rising-edge), on Plant Management off (clear without SWT write), or after a successful idle SWT write `0` (Decision C — write-fail keeps the latch); after clear, demand SWT again follows R1 when gates allow. While flame-latched, the TRV soft-close law (R9/R10) keeps running.

## Constraints
1. **C1:** Implementation stays inside the AppDaemon `ha_smart_hvac` App writing the existing HA plant Set Water Temperature entity and commissioned Sonoff TRV `valve_closure_degree` numbers.
2. **C2:** Exclusive Session (ADR 0001) and Heating Demand via thermostat `hvac_action=heating` are unchanged.
3. **C3:** SWT uses round-to-0.1 and clamp into existing `setpoint_min` / `setpoint_max` only.
4. **C4:** Critical Zone must not drive Set Water Temperature, TRV soft-close, or the flame trip.
5. **C5:** Outdoor, `flame_on`, `ch_active`, and per-TRV closure/accuracy entity ids are yaml-commissioned; house entity ids are not hardcoded and house `apps.yaml` changes require owner confirmation.
6. **C6:** CAP-7 / adapting `base`/`slope` / `ff_auto_correct_state.json` are out of scope for this initiative.
7. **C7 (forge):** The App never writes `valve_opening_degree`; heating max-open stays with the TRV. TRV wiring is explicit yaml per Sonoff TRV (closure number + accuracy source) — no name guessing; generic thermostats have no TRV-law keys.

## Done when
1. On Heating Demand with Plant Management on and flame latch clear, SWT equals round-to-0.1(clamp(`u_ff`)) from Outdoor and yaml `base`/`slope`/`comfort_ref` — no PID/RLS term.
2. Idle writes `0` + clear; plant-off does not write SWT + clear.
3. Supply rise-rate trip (`r_obs` / `r_max` / `boiler_water` trip path) is gone from code, yaml, tests, and live domain docs.
4. Commissioned Sonoff TRVs follow idle max-close floor / overshoot / plant-off 100; App never writes `valve_opening_degree`.
5. Flame short-on under the observe gate latches SWT `0` after successful write; clear after hold, zone rising-edge, plant-off, or successful idle write-0 restores weather-curve demand; TRV law keeps running while latched.
6. PID/RLS are gone from the live water path; ADR/CONTEXT/AGENTS/`knowledge/` match the shipped law; CAP-7 JSON is still absent; house yaml commissions the confirmed `flame_on` / `ch_active` / per-TRV closure+accuracy entities.

## Boundaries
Capability boundary: AppDaemon `ha_smart_hvac` Set Water Temperature path (weather curve + flame short-on trip), Sonoff TRV idle max-close soft-close, yaml commissioning, and domain ADR/docs. Not CAP-7 curve auto-correct, not App control of `valve_opening_degree`, not MADRC/LADRC return, not changing Exclusive Session or Heating Demand definition. Not supply rise-rate trip (removed). Tracer path (historical epics 1–3 kept as delivered; new work after): TRV soft-close → replace supply trip with flame short-on → ADR/docs for the new law.

- Touch point: `apps/ha_smart_hvac/` SWT path — weather `u_ff` (epic 1, done); remove supply trip; flame latch; TRV soft-close writes
- Touch point: `apps/apps.yaml` / `apps.yaml.example` — FF nest, Outdoor (epic 1); remove `r_max`/hold/supply-trip commission; add TRV closure/accuracy, `flame_on`, `ch_active`, floor / on-min / hold
- Touch point: `docs/adr/`, `CONTEXT.md`, `AGENTS.md`, `knowledge/` — supersede fixed-PID live law and amend/supersede supply-trip portions of ADR 0007 for flame + TRV
- Must not change: Exclusive Session (ADR 0001); Heating Demand via `hvac_action`
- Must not restore: CAP-7 / `ff_auto_correct_state.json`; supply rise-rate trip; App writes to `valve_opening_degree`

## References
- source — `_bmad-output/initiative-weather-swt-supply-trip/source-user-weather-swt-supply-trip.md` (weather-curve + original supply-trip intent; anti-cycle mechanism superseded by forge)
- source — `_bmad-output/initiative-weather-swt-supply-trip/forge-trv-valve-closure-anti-cycle/forge-trv-valve-closure-anti-cycle.md` (TRV soft-close + flame short-on; supply trip removed)
- adr — `docs/adr/0004-weather-curve-swt.md` (curve law to restore; CAP-7 sections stay out)
- adr — `docs/adr/0005-fixed-pid-swt.md` (live law to supersede)
- adr — `docs/adr/0007-weather-curve-supply-trip-swt.md` (shipped curve+supply-trip; trip portion to amend/supersede)
- domain — `CONTEXT.md`
- prior — `_bmad-output/initiative-pid/initiative-pid.md` (completed PID initiative being reversed on the water path)
- prior — `_bmad-output/initiative-weather-curve-zone-actuators/initiative-weather-curve-zone-actuators.md` (historical weather-curve delivery)

## Notes
- Decision: D1–D9 and C1–C6 approved with Sofia (2026-11-11).
- Decision: A1 approved — equal-float plant readback skip remains the write throttle (2026-11-11).
- Decision: A2 approved — Outdoor Temperature is again a control listener for weather-curve re-evaluation (2026-11-11).
- Decision: Q1 closed — new FF defaults from house 72h demand SWT + outdoor band: `base=37`, `slope=0.9`, `comfort_ref=20` (Tout=0 → 55; Tout=5 → 50.5; within setpoint 42…60) (2026-11-11).
- Decision: Q2 closed — supply rise-rate reads `boiler_water` = `sensor.opentherm_bridge_boiler_water_temperature_degc` (already in house `apps.yaml`) (2026-11-11). Superseded for anti-cycle by forge (2026-11-15): supply rise-rate trip removed; entity may remain unrelated to trip.
- Decision: Slice approved — three epics in order: (1) weather-curve SWT restore (R4 path; R7 Outdoor+FF), (2) supply rise-rate trip (R7 supply), (3) supersede PID domain docs (R4 docs/cleanup); no separate platform-baseline; shared R4 and R7 split path vs docs and Outdoor/FF vs supply; declined one thick curve+trip epic (2026-11-11).
- Decision: Replan approved (2026-11-15) — adopt forge-trv-valve-closure-anti-cycle; defer story 3.4 until re-slice; weather-curve kept; retire R5/R6 (supply rise-rate trip); add R9–R12 (TRV soft-close + flame short-on); re-slice new epics after historical 1–3.
- Source conflict: source-user D2–D6/D8 (supply rise-rate anti-cycle) vs forge Locked — resolved by replan Decision 2026-11-15 (forge wins).
- Dropped: **R5**, **R6** — supply rise-rate trip and its latch-clear requirements; replaced by R9–R12 (2026-11-15).
- Assumption: Writing `valve_closure_degree` alone as idle max-close leaves TRV idle/heating mode logic intact without the App touching `valve_opening_degree`.
- Decision: Flame latch clear = hold OR zone rising-edge OR plant-off OR successful idle SWT write-0 (Decision C); write-fail on idle keeps latch (2026-11-15).
- Decision: House entities closed (2026-11-15) — `flame_on`=`binary_sensor.opentherm_bridge_flame_on`; `ch_active`=`binary_sensor.opentherm_bridge_ch_active`; livingroom TRV×2: `number.livingroom_sonoff_trvzb_valve_closure_degree` + `number.livingroom_sonoff_trvzb_temperature_control_accuracy` and `…_closure_degree_2` + `…_accuracy_2`; bedroom: `number.bedroom_sonoff_trvzb_valve_closure_degree` + `number.bedroom_sonoff_trvzb_temperature_control_accuracy`; childroom: `number.childroom_sonoff_trvzb_valve_closure_degree` + `number.childroom_sonoff_trvzb_temperature_control_accuracy`.
- Decision: Re-slice approved (2026-11-15) — drop 3.4; epics 4 TRV idle max-close → 5 replace supply trip with flame (one epic) → 6 docs TRV+flame; order TRV before remove+flame; historical epics 1–3 kept.
