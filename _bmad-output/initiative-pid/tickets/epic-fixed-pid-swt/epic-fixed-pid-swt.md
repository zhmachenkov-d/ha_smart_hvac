---
type: epic
title: "Fixed-gain PID Set Water Temperature"
parent: initiative-pid
covers: ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R10"]
sources: []
companions: []
after: []
refined: false
risk: high
---

# Fixed-gain PID Set Water Temperature

## Description

Replace the weather-curve SWT path with fixed-gain multi-zone PID under the same Plant Management / Heating Demand gates: demand writes round-to-0.1(clamp(`base_water_temp` + `u_pid`)); idle writes 0 and clears ephemeral state; plant-off does not write and clears. Remove Outdoor Temperature, Weather Feedforward, CAP-7, and `ff_auto_correct_state.json` from the water path and commissioning yaml. ADR/CONTEXT/AGENTS language is epic 2 (R4 docs only).

## Outcome

The house holds zone comfort on a 300s control tick via `clamp(base + fixed u_pid)` with no outdoor/FF term on the SWT path.

## Done when

1. On Heating Demand with Plant Management on, SWT equals round-to-0.1(clamp(`base` + fixed `u_pid`)) with weighted demand-zone averages; no outdoor/FF term.
2. Idle writes `0` + clear; plant-off does not write + clear.
3. Outdoor/FF/CAP-7 and `ff_auto_correct_state.json` are gone from the App water path and example commissioning.
4. Demand SWT writes and PID advances occur only on `control_interval` (default 300s); events may clear without demand SWT writes or PID advance.
5. Equal rounded SWT skips the plant call; automated tests lock gates, rounding/skip, weighted averages, and absence of weather on the path.
6. Critical Zone remains selectable for diagnostics/logging only and does not drive SWT.

## Boundaries

Owns the AppDaemon `ha_smart_hvac` SWT runtime path and yaml commission for base, PID gains, zone weights, and `control_interval`. Does not own ADR/CONTEXT/AGENTS supersede of 0004 (epic 2). Does not deliver RLS (epic 3). Must not change Exclusive Session (ADR 0001) or Heating Demand via thermostat `hvac_action`.

- Touch point: `apps/ha_smart_hvac/` SWT path — replace FF with PID; owner: this epic
- Touch point: `apps/apps.yaml` / `apps.yaml.example` — base, gains, weights, interval 300; remove weather_feedforward; owner: this epic
- Must not change: Exclusive Session; Heating Demand definition

## References

- parent — `_bmad-output/initiative-pid/initiative-pid.md`, Requirements R1–R8, R10 (R4 path/commissioning)

## Notes

- Waits on nothing: opening epic / platform baseline for this initiative.
- Decision: No separate platform-baseline epic; this epic is the opening tracer (2026-11-07).
