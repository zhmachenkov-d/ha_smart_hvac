---
type: initiative
title: "Weather-curve SWT with supply rise-rate trip"
parent: none
sources:
  - _bmad-output/initiative-weather-swt-supply-trip/source-user-weather-swt-supply-trip.md
  - docs/adr/0004-weather-curve-swt.md
  - docs/adr/0005-fixed-pid-swt.md
  - CONTEXT.md
companions:
  - _bmad-output/initiative-weather-swt-supply-trip/source-user-weather-swt-supply-trip.md
after: []
assignee: ""
risk: high
---

# Weather-curve SWT with supply rise-rate trip

## Description

Replace the live fixed-PID / optional RLS Set Water Temperature path (ADR 0005 / 0006) with weather-curve feedforward under the existing Plant Management and Heating Demand gates, and add a supply-water rise-rate trip that latches SWT to 0 when the circuit behaves as if thermostatic valves are closed. Supersedes the PID initiative's water law for live commissioning; CAP-7 curve auto-correct stays out.

## Outcome

Under Plant Management, demand Set Water Temperature follows `round-to-0.1(clamp(u_ff))` from Outdoor Temperature; a supply rise above `r_max` latches SWT to 0 until the hold timer expires or a zone newly enters Heating Demand — without PID/RLS on the water path.

## Requirements

1. **R1 (D1, D9):** Under Plant Management on and Heating Demand, and when the supply rise-rate latch is clear, the App commands Set Water Temperature = round-to-0.1(clamp(`u_ff`)), where `u_ff = base + slope × (comfort_ref − T_out)` from yaml-commissioned Weather Feedforward parameters and Outdoor Temperature.
2. **R2 (D9):** Plant Management on and no Heating Demand writes `0` and clears ephemeral / water-path state (not persisted trip-commission files beyond what Constraints allow).
3. **R3 (D9):** Plant Management off does not write Set Water Temperature and clears ephemeral / water-path state.
4. **R4 (D7):** Fixed PID (`base_water_temp + u_pid`, ∫), optional RLS adaptive gains, and `rls_state.json` are removed from the live SWT path and commissioning; domain docs and a new ADR supersede ADR 0005 / 0006 for this water law.
5. **R5 (D2, D3, D4, D6, D8):** Under Plant Management on and Heating Demand, on every supply temperature change the App computes `r_obs` from supply (°C/min); if `r_obs > r_max` (yaml, default 2 °C/min) it latches and writes SWT `0` until the latch clears — the weather curve is not applied while latched.
6. **R6 (D5):** The latch clears when the yaml hold timer elapses (default 900 s) or when Heating Demand appears on a zone that previously had none (zone rising-edge); after clear, demand SWT again follows R1 when gates allow.
7. **R7 (C5):** Supply temperature is read from a yaml-commissioned entity; Outdoor Temperature returns to the weather-curve SWT path and commissioning.
8. **R8 (C4, C6):** Critical Zone remains diagnostics/logging only and does not drive SWT or the trip; CAP-7 rise-rate auto-correct of `base`/`slope` and `ff_auto_correct_state.json` are not restored in this initiative.

## Constraints

1. **C1:** Implementation stays inside the AppDaemon `ha_smart_hvac` App writing the existing HA plant Set Water Temperature entity.
2. **C2:** Exclusive Session (ADR 0001) and Heating Demand via thermostat `hvac_action=heating` are unchanged.
3. **C3:** SWT uses round-to-0.1 and clamp into existing `setpoint_min` / `setpoint_max` only.
4. **C4:** Critical Zone must not drive Set Water Temperature or the supply rise-rate trip.
5. **C5:** Supply (and Outdoor) entity ids are yaml-commissioned; house entity ids are not hardcoded and house `apps.yaml` changes require owner confirmation.
6. **C6:** CAP-7 / adapting `base`/`slope` / `ff_auto_correct_state.json` are out of scope for this initiative.

## Done when

1. On Heating Demand with Plant Management on and latch clear, SWT equals round-to-0.1(clamp(`u_ff`)) from Outdoor and yaml `base`/`slope`/`comfort_ref` — no PID/RLS term.
2. Idle writes `0` + clear; plant-off does not write + clear.
3. Supply `r_obs > r_max` under demand latches SWT to `0`; clear after hold timer or zone rising-edge Heating Demand restores the weather-curve demand path.
4. PID/RLS commissioning and `rls_state.json` are gone from the live water path; a new ADR and CONTEXT/AGENTS/`knowledge/` match; CAP-7 JSON is still absent.
5. Automated tests lock gates, weather law, trip latch/clear, and absence of PID on the path; house yaml commission waits on confirmed supply entity id.

## Boundaries

Capability boundary: AppDaemon `ha_smart_hvac` Set Water Temperature path (weather curve + supply rise-rate trip), yaml commissioning, and domain ADR/docs. Not CAP-7 curve auto-correct, not zone TRV percent actuation, not MADRC/LADRC return, not changing Exclusive Session or Heating Demand definition. Tracer path: epic-weather-curve-swt-restore → epic-supply-rise-rate-trip → epic-supersede-pid-domain-docs.

- Touch point: `apps/ha_smart_hvac/` SWT path — weather `u_ff` (epic 1) + supply trip latch (epic 2); dead PID/RLS cleanup (epic 3)
- Touch point: `apps/apps.yaml` / `apps.yaml.example` — FF nest, Outdoor (epic 1); supply entity, `r_max`, hold (epic 2); remove remaining `pid` / RLS nests (epic 1 path, epic 3 cleanup)
- Touch point: `docs/adr/`, `CONTEXT.md`, `AGENTS.md`, `knowledge/` — supersede fixed-PID live law; owner: epic-supersede-pid-domain-docs
- Must not change: Exclusive Session (ADR 0001); Heating Demand via `hvac_action`
- Must not restore: CAP-7 / `ff_auto_correct_state.json` in this initiative

## References

- source — `_bmad-output/initiative-weather-swt-supply-trip/source-user-weather-swt-supply-trip.md`
- adr — `docs/adr/0004-weather-curve-swt.md` (curve law to restore; CAP-7 sections stay out)
- adr — `docs/adr/0005-fixed-pid-swt.md` (live law to supersede)
- domain — `CONTEXT.md`
- prior — `_bmad-output/initiative-pid/initiative-pid.md` (completed PID initiative being reversed on the water path)
- prior — `_bmad-output/initiative-weather-curve-zone-actuators/initiative-weather-curve-zone-actuators.md` (historical weather-curve delivery)

## Notes

- Decision: D1–D9 and C1–C6 approved with Sofia (2026-11-11).
- Decision: A1 approved — equal-float plant readback skip remains the write throttle (2026-11-11).
- Decision: A2 approved — Outdoor Temperature is again a control listener for weather-curve re-evaluation (2026-11-11).
- Decision: Q1 closed — new FF defaults from house 72h demand SWT + outdoor band: `base=37`, `slope=0.9`, `comfort_ref=20` (Tout=0 → 55; Tout=5 → 50.5; within setpoint 42…60) (2026-11-11).
- Decision: Q2 closed — supply rise-rate reads `boiler_water` = `sensor.opentherm_bridge_boiler_water_temperature_degc` (already in house `apps.yaml`) (2026-11-11).
- Decision: Slice approved — three epics in order: (1) weather-curve SWT restore (R4 path; R7 Outdoor+FF), (2) supply rise-rate trip (R7 supply), (3) supersede PID domain docs (R4 docs/cleanup); no separate platform-baseline; shared R4 and R7 split path vs docs and Outdoor/FF vs supply; declined one thick curve+trip epic (2026-11-11).
