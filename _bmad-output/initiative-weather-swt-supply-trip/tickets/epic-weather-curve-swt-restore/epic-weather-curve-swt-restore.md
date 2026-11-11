---
type: epic
title: "Weather-curve SWT restore"
parent: initiative-weather-swt-supply-trip
covers: ["R1", "R2", "R3", "R4", "R7", "R8"]
sources:
  - _bmad-output/initiative-weather-swt-supply-trip/initiative-weather-swt-supply-trip.md
companions: []
after: []
refined: false
risk: high
---

# Weather-curve SWT restore

## Description

Restore weather-curve Set Water Temperature under the existing Plant Management and Heating Demand gates: on demand write round-to-0.1(clamp(`u_ff`)) with `u_ff = base + slope × (comfort_ref − T_out)` from yaml Weather Feedforward and Outdoor Temperature; idle writes `0` and clears ephemeral water-path state; plant-off does not write and clears. Remove fixed PID / optional RLS from the live SWT path and commissioning yaml (R4 path only). Outdoor Temperature is again a control listener. CAP-7 and Critical Zone as SWT drivers stay out. ADR/CONTEXT/AGENTS/`knowledge/` and dead module cleanup are epic 3.

## Outcome

On Heating Demand with Plant Management on, the house follows Outdoor-driven weather-curve SWT with no PID/RLS term on the water path.

## Done when

1. On Heating Demand with Plant Management on, SWT equals round-to-0.1(clamp(`u_ff`)) from Outdoor and yaml `base`/`slope`/`comfort_ref` (defaults base=37, slope=0.9, comfort_ref=20) — no PID/RLS term.
2. Idle writes `0` + clear; plant-off does not write + clear.
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
