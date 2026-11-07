---
type: epic
title: "Fixed-gain PID Set Water Temperature"
parent: initiative-pid
covers: ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R10"]
sources:
  - _bmad-output/initiative-pid/initiative-pid.md
companions: []
after: []
refined: true
risk: high
---

# Fixed-gain PID Set Water Temperature

## Description

Replace the weather-curve SWT path with fixed-gain multi-zone PID under the same Plant Management / Heating Demand gates: demand writes round-to-0.1(clamp(`base_water_temp` + `u_pid`)); idle writes 0 and clears ephemeral state; plant-off does not write and clears. Remove Outdoor Temperature, Weather Feedforward, CAP-7, and `ff_auto_correct_state.json` from the water path and commissioning yaml. ADR/CONTEXT/AGENTS language is epic 2 (R4 docs only).

## Outcome

The house holds zone comfort on a 300s control tick via `clamp(base + fixed u_pid)` with no outdoor/FF term on the SWT path.

## Requirements

1. **R1 (parent R1):** Under Plant Management on and Heating Demand, the App commands Set Water Temperature = round-to-0.1(clamp(`base_water_temp` + `u_pid`)), where `u_pid` is fixed-gain PID on weight-normalized demand-zone air temperature versus weight-normalized demand-zone setpoints — `e = Tset_w − Tair_w`, `u_pid = Kp·e + Ki·∫e`, `dt = control_interval`, Kd = 0.
2. **R2 (parent R2):** Plant Management on and no Heating Demand writes `0` and clears PID ephemeral / water-path state (integral and last commanded SWT); no persisted PID/FF JSON in this epic.
3. **R3 (parent R3):** Plant Management off does not write Set Water Temperature and clears ephemeral / water-path state (same inventory as R2).
4. **R4 (parent R4, path/commissioning):** Outdoor Temperature, Weather Feedforward, CAP-7 rise-rate auto-correct, and `ff_auto_correct_state.json` are removed from the SWT path and commissioning yaml; Outdoor is not listened for control. CONTEXT/AGENTS and the new ADR that supersede ADR 0004 are epic 2.
5. **R5 (parent R5):** Periodic `control_interval` (default 300s in example yaml and when the key is omitted in the parser) is the only schedule that advances PID state and issues a demand-path SWT write.
6. **R6 (parent R6):** Event listeners may clear immediately on idle / plant-off / fail paths; they must not write a new demand SWT or advance PID state. Listeners stay on Plant Management, zone air, and thermostat `hvac_action` / setpoint — not Outdoor Temperature.
7. **R7 (parent R7):** After 0.1 °C rounding, if the value equals the last commanded SWT, the App skips the plant service call.
8. **R8 (parent R8):** Heating Demand stays as today; PID averages use only Zones with Heating Demand and per-zone yaml weights (omit → 1.0, then normalize); max Zone Error is not an SWT driver.
9. **R9 (parent R10):** Critical Zone selection is retained for diagnostics/logging only and must not drive Set Water Temperature.

## Constraints

1. **C1 (parent C1):** SWT clamp uses existing `setpoint_min` / `setpoint_max` only.
2. **C2 (parent C2):** Implementation stays inside the AppDaemon `ha_smart_hvac` App writing the existing HA plant entity — no direct OpenTherm daemon or numpy process from the example.
3. **C3 (parent C3):** Fixed PID ships before RLS; they are not one mixed delivery (RLS is epic 3).
4. **C4 (parent C4):** Derivative gain stays 0 for this thermal plant; zone weights are yaml-commissioned, not invented at runtime outside config. Default commission gains: `kp=1.0`, `ki=0.1`, `integral_min=-50`, `integral_max=50`; anti-windup is those integral clamps only unless a later Decision adds SWT-saturation freeze.

## Done when

1. On Heating Demand with Plant Management on, SWT equals round-to-0.1(clamp(`base` + fixed `u_pid`)) with weighted demand-zone averages and `e = Tset_w − Tair_w`; no outdoor/FF term.
2. Idle writes `0` + clear (integral + last commanded SWT); plant-off does not write + clear.
3. Outdoor/FF/CAP-7 and `ff_auto_correct_state.json` are gone from the App water path and example commissioning; Outdoor is not a control listener.
4. Demand SWT writes and PID advances occur only on `control_interval` (default 300s); events may clear without demand SWT writes or PID advance.
5. Equal rounded SWT skips the plant call; automated tests lock gates, rounding/skip, weighted averages, and absence of weather on the path.
6. Critical Zone remains selectable for diagnostics/logging only and does not drive SWT.

## Boundaries

Owns the AppDaemon `ha_smart_hvac` SWT runtime path and yaml commission for base, PID gains, zone weights, and `control_interval`. Does not own ADR/CONTEXT/AGENTS supersede of 0004 (epic 2). Does not deliver RLS (epic 3). Must not change Exclusive Session (ADR 0001) or Heating Demand via thermostat `hvac_action`.

- Touch point: `apps/ha_smart_hvac/` SWT path — replace FF with PID; owner: this epic
- Touch point: `apps/apps.yaml` / `apps.yaml.example` — base, gains, weights, interval 300; remove weather_feedforward; owner: this epic
- Must not change: Exclusive Session; Heating Demand definition

## References

- parent — `_bmad-output/initiative-pid/initiative-pid.md`, Requirements R1–R8, R10; Constraints C1–C4 (R4 path/commissioning)

## Notes

- Waits on nothing: opening epic / platform baseline for this initiative.
- Decision: No separate platform-baseline epic; this epic is the opening tracer (2026-11-07).
- Decision: PID form — `e = Tset_w − Tair_w`, `u_pid = Kp·e + Ki·∫e`, `dt = control_interval`, Kd = 0 (2026-11-07).
- Decision: Clear inventory — ephemeral integral + last commanded SWT; no persisted PID/FF JSON in this epic (2026-11-07).
- Decision: Drop Outdoor Temperature from control listeners; keep Plant Management, zone air, thermostat `hvac_action` / setpoint (2026-11-07).
- Decision: Parser default `control_interval` when omitted is 300s, matching example yaml (2026-11-07).
- Decision: Anti-windup beyond yaml integral clamps, and module layout (e.g. new `pid.py`), left to stories (2026-11-07).
- Decision: Tracer bullet is entry 1 (fixed-gain PID SWT law); least-certain next is entry 2 (tick-owned advance / event clear-only); then remove Outdoor/FF/CAP-7 (3); refactor sweep (4). No live Exclusive Session HITL, no opening refactor, Critical Zone folded into tracer; verify via automated tests (2026-11-07).
