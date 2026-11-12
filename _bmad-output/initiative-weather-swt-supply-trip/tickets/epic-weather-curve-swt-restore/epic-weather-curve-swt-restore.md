---
type: epic
title: "Weather-curve SWT restore"
parent: initiative-weather-swt-supply-trip
covers: ["R1", "R2", "R3", "R4", "R7", "R8"]
sources:
  - _bmad-output/initiative-weather-swt-supply-trip/initiative-weather-swt-supply-trip.md
companions: []
after: []
refined: true
risk: high
status: done
---

# Weather-curve SWT restore

## Description

Restore weather-curve Set Water Temperature under the existing Plant Management and Heating Demand gates: on demand write round-to-0.1(clamp(`u_ff`)) with `u_ff = base + slope × (comfort_ref − T_out)` from yaml Weather Feedforward and Outdoor Temperature; idle writes `0`; plant-off does not write (leave SWT untouched). After PID detach, water-path ephemeral clear is vacuous until epic 2 trip state. Remove fixed PID / optional RLS from the live SWT path and commissioning yaml (R4 path only). Outdoor Temperature is again a control listener. CAP-7 and Critical Zone as SWT drivers stay out. ADR/CONTEXT/AGENTS/`knowledge/` and dead module cleanup are epic 3.

## Outcome

On Heating Demand with Plant Management on, the house follows Outdoor-driven weather-curve SWT with no PID/RLS term on the water path.

## Requirements

1. **R1 (parent R1):** Under Plant Management on and Heating Demand, and when the supply rise-rate latch is clear, the App commands Set Water Temperature = round-to-0.1(clamp(`u_ff`)), where `u_ff = base + slope × (comfort_ref − T_out)` from yaml-commissioned Weather Feedforward parameters and Outdoor Temperature.
2. **R2 (parent R2):** Plant Management on and no Heating Demand writes `0`. Water-path ephemeral clear is vacuous until epic 2 trip state (not persisted trip-commission files beyond what Constraints allow).
3. **R3 (parent R3):** Plant Management off does not write Set Water Temperature (leave SWT untouched). Same vacuous clear until epic 2 trip state.
4. **R4 (parent R4):** Fixed PID (`base_water_temp + u_pid`, ∫), optional RLS adaptive gains, and `rls_state.json` are removed from the live SWT path and commissioning; domain docs and a new ADR supersede ADR 0005 / 0006 for this water law.
5. **R7 (parent R7):** Supply temperature is read from a yaml-commissioned entity; Outdoor Temperature returns to the weather-curve SWT path and commissioning.
6. **R8 (parent R8):** Critical Zone remains diagnostics/logging only and does not drive SWT or the trip; CAP-7 rise-rate auto-correct of `base`/`slope` and `ff_auto_correct_state.json` are not restored in this initiative.

## Constraints

1. **C1 (parent C1):** Implementation stays inside the AppDaemon `ha_smart_hvac` App writing the existing HA plant Set Water Temperature entity.
2. **C2 (parent C2):** Exclusive Session (ADR 0001) and Heating Demand via thermostat `hvac_action=heating` are unchanged.
3. **C3 (parent C3):** SWT uses round-to-0.1 and clamp into existing `setpoint_min` / `setpoint_max` only.
4. **C4 (parent C4):** Critical Zone must not drive Set Water Temperature or the supply rise-rate trip.
5. **C5 (parent C5):** Supply (and Outdoor) entity ids are yaml-commissioned; house entity ids are not hardcoded and house `apps.yaml` changes require owner confirmation.
6. **C6 (parent C6):** CAP-7 / adapting `base`/`slope` / `ff_auto_correct_state.json` are out of scope for this initiative.

## Done when

1. On Heating Demand with Plant Management on, SWT equals round-to-0.1(clamp(`u_ff`)) from Outdoor and yaml `base`/`slope`/`comfort_ref` (defaults base=37, slope=0.9, comfort_ref=20) — no PID/RLS term.
2. Idle writes `0`; plant-off does not write (leave SWT untouched). Ephemeral clear is vacuous until epic 2 trip state.
3. Outdoor Temperature is a control listener for weather-curve re-evaluation; FF nest is commissioned in example yaml (house yaml HITL).
4. Fixed PID / optional RLS / `rls_state.json` no longer drive live SWT or commissioning for the water path (docs/ADR cleanup remains epic 3).
5. Critical Zone remains diagnostics/logging only; CAP-7 / `ff_auto_correct_state.json` are not restored.
6. Automated tests lock gates, weather law, Outdoor listener, and absence of PID on the demand path.

## Boundaries

Owns the AppDaemon `ha_smart_hvac` demand SWT runtime restore to weather curve, Outdoor listener, and FF yaml commission. Does not deliver the supply rise-rate trip (epic 2). Does not own ADR/CONTEXT/AGENTS/`knowledge/` supersede of 0005/0006 or final dead PID/RLS module deletion beyond what the path swap requires (epic 3). Must not change Exclusive Session (ADR 0001) or Heating Demand via thermostat `hvac_action`.

- Touch point: `apps/ha_smart_hvac/` SWT path — replace PID with `u_ff`; Outdoor listener; owner: this epic
- Touch point: `apps/apps.yaml` / `apps.yaml.example` — FF nest, Outdoor; remove live `pid` / RLS commission from the water path; owner: this epic
- Must not change: Exclusive Session; Heating Demand definition
- Must not restore: CAP-7 / `ff_auto_correct_state.json`

## References

- parent — `_bmad-output/initiative-weather-swt-supply-trip/initiative-weather-swt-supply-trip.md`, Requirements R1–R4, R7–R8 (R4 path/commissioning; R7 Outdoor+FF); Constraints C1–C6
- adr — `docs/adr/0004-weather-curve-swt.md` (curve law to restore; CAP-7 sections stay out)
- adr — `docs/adr/0005-fixed-pid-swt.md` (live law to leave on the path)

## Notes

- Waits on nothing: opening tracer epic / platform baseline for this initiative.
- Decision: Slice approved — three epics; this epic is the tracer (weather-curve restore before trip); R4 path here, R4 docs in epic 3; R7 Outdoor+FF here, R7 supply in epic 2 (2026-11-11).
- Shared covers: R4 with epic 3 (path vs docs/cleanup); R7 with epic 2 (Outdoor/FF vs supply entity); R8 runtime diagnostics-only here (docs language in epic 3 as needed).
- Decision: Refine from parent covers only — no extra companions before stories (2026-11-11).
- Decision: R1 latch clause — this epic delivers weather-curve as if latch always clear; latch gate is epic 2 (2026-11-11).
- Decision: Missing / invalid Outdoor — `_go_idle` write `0` + WARN (not plant-unreadable skip); no curve write (2026-11-11; clarified 2026-11-12).
- Decision: R4 scope here — remove PID/RLS from live SWT path and commissioning yaml; dead modules and domain ADR/docs remain epic 3 (2026-11-11).
- Decision: R7 scope here — Outdoor + Weather Feedforward commission and listener; supply entity commission is epic 2 (2026-11-11).
- Decision: Tracer bullet — entry 1 restores weather-curve SWT law, gates, Outdoor listener, and apps.yaml.example FF commission; entry 2 detaches PID/RLS (least-certain); entry 3 house yaml HITL; entry 4 refactor sweep; declined separate live Exclusive Session / closing e2e suite (2026-11-11).
- Decision: R2/R3 vacuous clear — reconcile epic prose to as-built after story 1.2 F1-A; epic 2 owns trip-state clear (2026-11-12 retrospective).
