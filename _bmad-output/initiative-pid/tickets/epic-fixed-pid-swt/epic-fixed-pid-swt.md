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

1. **R1 (parent R1):** Under Plant Management on and Heating Demand, the App commands Set Water Temperature = round-to-0.1(clamp(`base_water_temp` + `u_pid`)), where `u_pid` is fixed-gain PID on weight-normalized demand-zone air temperature versus weight-normalized demand-zone setpoints — `e = Tset_w − Tair_w`, `u_pid = Kp·e + Ki·∫e`, `dt = control_interval / 3600` (hours, per C4), Kd = 0.
2. **R2 (parent R2):** Plant Management on and no Heating Demand writes `0` and clears PID ephemeral / water-path state (integral and last commanded SWT); no persisted PID/FF JSON in this epic.
3. **R3 (parent R3):** Plant Management off does not write Set Water Temperature and clears ephemeral / water-path state (same inventory as R2).
4. **R4 (parent R4, path/commissioning):** Outdoor Temperature, Weather Feedforward, CAP-7 rise-rate auto-correct, and `ff_auto_correct_state.json` are removed from the SWT path and commissioning yaml; Outdoor is not listened for control. CONTEXT/AGENTS and the new ADR that supersede ADR 0004 are epic 2.
5. **R5 (parent R5):** Periodic `control_interval` (default 300s in example yaml and when the key is omitted in the parser) is the only schedule that advances PID state and issues a demand-path SWT write.
6. **R6 (parent R6):** Event listeners may clear immediately on idle / plant-off / fail paths; they must not write a new demand SWT or advance PID state. Listeners stay on Plant Management, zone air, and thermostat `hvac_action` / setpoint — not Outdoor Temperature.
7. **R7 (parent R7):** After 0.1 °C rounding, the App skips the plant service call when the plant entity already reads that value; PID state does not advance while the plant entity is unavailable.
8. **R8 (parent R8):** Heating Demand stays as today; PID averages use only Zones with Heating Demand and per-zone yaml weights (omit → 1.0, then normalize); max Zone Error is not an SWT driver.
9. **R9 (parent R10):** Critical Zone selection is retained for diagnostics/logging only and must not drive Set Water Temperature.

## Constraints

1. **C1 (parent C1):** SWT clamp uses existing `setpoint_min` / `setpoint_max` only.
2. **C2 (parent C2):** Implementation stays inside the AppDaemon `ha_smart_hvac` App writing the existing HA plant entity — no direct OpenTherm daemon or numpy process from the example.
3. **C3 (parent C3):** Fixed PID ships before RLS; they are not one mixed delivery (RLS is epic 3).
4. **C4 (parent C4):** Derivative gain stays 0 for this thermal plant; zone weights are yaml-commissioned, not invented at runtime outside config. The integral is in °C·h (`dt = control_interval / 3600`, `ki` in 1/h), and yaml bounds the I-term contribution `ki·∫` in °C of water (`i_term_min` / `i_term_max`). Default commission: `kp=1.0`, `ki=1.0` (1/h), `i_term_min=-10`, `i_term_max=15` (starting defaults, not house-proven; D15 supersedes `ki=0.1`, `integral_min/max=±50`). Anti-windup: those I-term clamps **plus** SWT-saturation freeze on tick when `raw = base + u_pid` is outside `[setpoint_min, setpoint_max]` and `e` has the same sign (Decision 2026-11-07).
5. **C5 (D20):** Commission parsing rejects non-numeric or non-finite `setpoint_min`, `setpoint_max`, `pid.*`, `base_water_temp` and `control_interval`, negative `kp` / `ki`, an I-term range that excludes 0, and `base_water_temp` outside `[setpoint_min, setpoint_max]` with a config error the App logs; legacy or unknown top-level and `pid` keys (AppDaemon's reserved app keys excepted) are reported and logged as one WARNING.

## Done when

1. On Heating Demand with Plant Management on, SWT equals round-to-0.1(clamp(`base` + fixed `u_pid`)) with weighted demand-zone averages and `e = Tset_w − Tair_w`; no outdoor/FF term.
2. Idle writes `0` + clear (integral + last commanded SWT); plant-off does not write + clear.
3. Outdoor/FF/CAP-7 and `ff_auto_correct_state.json` are gone from the App water path, the example commissioning, and the house `apps/apps.yaml` (non-entity keys only); Outdoor is not a control listener.
4. Demand SWT writes and PID advances occur only on `control_interval` (default 300s); events may clear without demand SWT writes or PID advance.
5. Equal rounded SWT skips the plant call only when the plant already reads it; automated tests lock gates, rounding/skip, weighted averages, gains and I-term carry across ticks, and absence of weather on the path.
6. Critical Zone remains selectable for diagnostics/logging only and does not drive SWT.

## Boundaries

Owns the AppDaemon `ha_smart_hvac` SWT runtime path and yaml commission for base, PID gains, zone weights, and `control_interval`. Does not own ADR/CONTEXT/AGENTS supersede of 0004 (epic 2). Does not deliver RLS (epic 3). Must not change Exclusive Session (ADR 0001) or Heating Demand via thermostat `hvac_action`.

- Touch point: `apps/ha_smart_hvac/` SWT path — replace FF with PID; owner: this epic
- Touch point: `apps/apps.yaml` / `apps.yaml.example` — base, gains, weights, interval 300; remove weather_feedforward; owner: this epic
- Must not change: Exclusive Session; Heating Demand definition

## References

- parent — `_bmad-output/initiative-pid/initiative-pid.md`, Requirements R1–R8, R10; Constraints C1–C4 (R4 path/commissioning)
- retrospective — `_bmad-output/initiative-pid/tickets/epic-fixed-pid-swt/epic-fixed-pid-swt-retrospective.md`, Action items A1–A5
- decisions — `_bmad-output/initiative-pid/.memlog.md`, D15–D22

## Notes

- Waits on nothing: opening epic / platform baseline for this initiative.
- Decision: No separate platform-baseline epic; this epic is the opening tracer (2026-11-07).
- Decision: PID form — `e = Tset_w − Tair_w`, `u_pid = Kp·e + Ki·∫e`, `dt = control_interval`, Kd = 0 (2026-11-07) (dt units superseded by C4 / D15).
- Decision: Clear inventory — ephemeral integral + last commanded SWT; no persisted PID/FF JSON in this epic (2026-11-07).
- Decision: Drop Outdoor Temperature from control listeners; keep Plant Management, zone air, thermostat `hvac_action` / setpoint (2026-11-07).
- Decision: Parser default `control_interval` when omitted is 300s, matching example yaml (2026-11-07).
- Decision: Module layout (e.g. new `pid.py`) left to stories; anti-windup = integral clamps + SWT saturation freeze (same-sign e) locked in entry 1 (2026-11-07).
- Decision: Tracer bullet is entry 1 (fixed-gain PID SWT law; Outdoor listener dropped here; interim demand event writes with tick-only integral; sat. freeze; A1 partial-zone skip; D1 demand INFO Floor); least-certain next is entry 2 (tick-owned demand write / event clear-only); then remove Outdoor/FF/CAP-7 (3); refactor sweep (4). No live Exclusive Session HITL as epic-1 AC (operator note before epic 2); no opening refactor, Critical Zone folded into tracer; verify via automated tests (2026-11-07).
- Decision: Replan from `epic-fixed-pid-swt-retrospective.md` (accepted-with-open-items): R7 and C4 re-rendered from initiative D16→D22 / D15; entries added after the closed refactor sweep 4 — 5 (integral units and R7 skip, retro A1/A2/A4), 7 (parse hardening and legacy-key warning, retro A3/A5 code, C5 from D20), 6 (commission house `apps/apps.yaml`, hitl, retro A5), then closing refactor sweep 8 (DU1, EC1, deferrals of 5–7); nothing built is rolled back (2026-11-07).
- Decision: Entry 5 split into 5 and 7 for one-session sizing; closing sweep 8 added so a sweep still closes the epic (user, 2026-11-07).
- Decision: SR3 accepted — event clears may hold the plant at 0 until the next tick and reset ∫; R6 unchanged, documented via epic 2's ADR (2026-11-07).
