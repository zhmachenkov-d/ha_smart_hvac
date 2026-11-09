---
type: initiative
title: "Multi-zone PID Set Water Temperature"
parent: none
sources:
  - _bmad-output/initiative-pid/source-user-pid-rls-example.md
  - CONTEXT.md
  - docs/adr/0004-weather-curve-swt.md
companions:
  - _bmad-output/initiative-pid/source-user-pid-rls-example.md
after: []
assignee: ""
risk: high
status: done
---

# Multi-zone PID Set Water Temperature

## Description

Replace weather-curve-only Set Water Temperature (ADR 0004) with a multi-zone air→water fixed-gain PID that commands the Plant through the existing Home Assistant OpenTherm entity under the same Plant Management / Heating Demand gates, then add RLS gain retune in a later epic. Folder remains `initiative-pid`.

## Outcome

The house holds zone comfort via `clamp(base_water_temp + u_pid)` on a 300s control tick without Outdoor Temperature on the SWT path; Weather Feedforward and CAP-7 are gone; a later epic can adapt Kp/Ki via RLS without restoring the weather curve.

## Requirements

1. **R1 (D5, D6, D9, D10):** Under Plant Management on and Heating Demand, the App commands Set Water Temperature = round-to-0.1(clamp(`base_water_temp` + `u_pid`)), where `u_pid` is fixed-gain PID on weight-normalized demand-zone air temperature versus weight-normalized demand-zone setpoints.
2. **R2 (D5):** Plant Management on and no Heating Demand writes `0` and clears PID ephemeral / water-path state.
3. **R3 (D5):** Plant Management off does not write Set Water Temperature and clears ephemeral / water-path state.
4. **R4 (D1):** Outdoor Temperature, Weather Feedforward, CAP-7 rise-rate auto-correct, and `ff_auto_correct_state.json` are removed from the SWT path and commissioning; CONTEXT/AGENTS and a new ADR supersede ADR 0004.
5. **R5 (D8):** Periodic `control_interval` (default 300s) is the only schedule that advances PID state and issues a demand-path SWT write.
6. **R6 (D8):** Event listeners may clear immediately on idle / plant-off / fail paths; they must not write a new demand SWT or advance PID state.
7. **R7 (D9, D22):** After 0.1 °C rounding, the App skips the plant service call when the plant entity already reads that value; PID state does not advance while the plant entity is unavailable.
8. **R8 (D2, D7):** Heating Demand stays as today; PID averages use only Zones with Heating Demand and per-zone yaml weights (omit → 1.0, then normalize); max Zone Error is not an SWT driver.
9. **R9 (D4):** A later epic delivers RLS-based retune of PID gains without restoring Weather Feedforward.
10. **R10 (D14):** Critical Zone selection is retained for diagnostics/logging only and must not drive Set Water Temperature; CONTEXT/AGENTS state diagnostics-only after CAP-7 removal.

## Constraints

1. **C1 (D10):** SWT clamp uses existing `setpoint_min` / `setpoint_max` only.
2. **C2 (D3, D11):** Implementation stays inside the AppDaemon `ha_smart_hvac` App writing the existing HA plant entity — no direct OpenTherm daemon or numpy process from the example.
3. **C3 (D4):** Fixed PID ships before RLS; they are not one mixed delivery.
4. **C4 (D11):** Derivative gain stays 0 for this thermal plant; zone weights are yaml-commissioned, not invented at runtime outside config.

## Done when

1. On Heating Demand with Plant Management on, SWT equals round-to-0.1(clamp(`base` + fixed `u_pid`)) with no outdoor/FF term.
2. Idle writes `0` + clear; plant-off does not write + clear — same gate law as today.
3. Weather Feedforward, CAP-7, and `ff_auto_correct_state.json` are gone from the water path; a new ADR supersedes 0004; CONTEXT/AGENTS match.
4. Demand SWT writes and PID advances occur only on `control_interval` (default 300s); events clear without demand SWT writes.
5. Equal rounded SWT skips the plant call only when the plant already reads it; automated tests lock gates, rounding/skip, weighted demand averages, and absence of weather on the path.
6. RLS remains a planned later epic, not required to close the fixed-PID delivery.
7. Critical Zone remains selectable for diagnostics only; docs state it does not drive SWT.

## Boundaries

Capability boundary: AppDaemon `ha_smart_hvac` Set Water Temperature path, zone weighting for PID averages, docs/ADR language. Not zone TRV percent, not MADRC/LADRC return, not direct OT hardware stacks, not RLS in the first closed-loop ship. Tracer path: epic-fixed-pid-swt → epic-pid-domain-docs → epic-rls-pid-retune (sequential).

- Touch point: `apps/ha_smart_hvac/` SWT path — replace FF with PID; owner: epic-fixed-pid-swt
- Touch point: `apps/apps.yaml` / `apps.yaml.example` — `base_water_temp`, PID gains, zone weights, `control_interval` default 300; remove weather_feedforward nest; owner: epic-fixed-pid-swt
- Touch point: `docs/adr/`, `CONTEXT.md`, `AGENTS.md`, `knowledge/` concept pages — supersede ADR 0004; owner: epic-pid-domain-docs
- Operator note: do not commission live Exclusive Session on the new PID yaml until epic-pid-domain-docs closes (CONTEXT/ADR match the App).
- Must not change: Exclusive Session (ADR 0001); Heating Demand definition via thermostat `hvac_action`

## References

- source — `_bmad-output/initiative-pid/source-user-pid-rls-example.md`
- domain — `CONTEXT.md`
- adr — `docs/adr/0004-weather-curve-swt.md` (to supersede)
- prior — `_bmad-output/initiative-weather-curve-zone-actuators/initiative-weather-curve-zone-actuators.md` (current FF wave, historical)

## Notes

- Decision: A1–A3 approved — base 40 °C; omitted zone weight 1.0; example yaml `control_interval` default 300 (2026-11-07).
- Decision: Q1 closed — default fixed PID `kp=1.0`, `ki=0.1`, `integral_min=-50`, `integral_max=50` in yaml; Kd=0 (2026-11-07).
- Decision: Q2 closed — Critical Zone kept for diagnostics/logging only; not an SWT driver (2026-11-07).
- Decision: D1–D14 recorded in `.memlog.md` (session with Sofia).
- Decision: Slice approved — three epics in order: (1) fixed-PID SWT runtime / FF-kill, (2) ADR/CONTEXT/AGENTS, (3) RLS retune; no separate platform-baseline; epic 1 Done when excludes docs; R4 path owned by epic 1, R4 docs by epic 2 (2026-11-07).
- Decision: Operator HITL/note between epic 1 and 2 — do not live-commission Exclusive Session until epic 2 closes; not an epic-1 acceptance check (2026-11-07).
- Decision: Declined fold of docs into epic 1; sequential ship kept (party 2026-11-07).
- Decision: Replan from the epic-fixed-pid-swt retrospective (`tickets/epic-fixed-pid-swt/epic-fixed-pid-swt-retrospective.md`): D15 supersedes Q1/D12 defaults (∫ in °C·h, ki 1/h, I-term limits in °C, defaults kp 1.0 / ki 1.0 / I-term [−10, +15] °C); D16/D22 revise R7 (skip when the plant already reads the command; no ∫ advance while the plant is unavailable); D17 accepts event-clear latency up to `control_interval` as an ADR input; D18 puts `knowledge/` in epic 2 with AGENTS.md first; D19–D21 add epic-1 stories 5–8 (integral units and R7 skip; parse hardening per D20; hitl house yaml; closing sweep). Production stays on v1.5.1 until then (2026-11-07).
- Decision: Closed 2026-11-09 after Closure check PASS on Done when 1–7, R1–R10, C1–C4 against App/ADR 0005–0006/tests; optional leftovers (two-tick plant-drift R7 test, RLS/AGENTS hygiene, R9/Done when 6 past-tense sync) accepted as non-blocking; live Exclusive Session not required to close.
