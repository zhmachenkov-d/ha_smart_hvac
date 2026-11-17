---
type: initiative
title: "Weather-curve SWT only"
parent: none
after: []
assignee: ""
risk: medium
status: done
sources: [forge-weather-curve-zone-actuators/forge-weather-curve-zone-actuators.md]
companions: [_bmad-output/initiative-weather-curve-zone-actuators/brownfield.md, _bmad-output/initiative-weather-curve-zone-actuators/architecture-diagrams.md, ../../../../CONTEXT.md]
---

# Weather-curve SWT only

## Description

Stop Set Water Temperature windup from closed-loop air→SWT tracking by commanding weather-curve-only water under existing Plant Management / Heating Demand gates, with commissionable and rise-rate auto-corrected Weather Feedforward parameters, then make that gate law react immediately to Plant Management, thermostat, zone-air, and Outdoor Temperature changes without advancing R7 sampling off the periodic cadence. The numbered spec owns capabilities, constraints, and non-goals; this initiative delivers that wave. Folder name retains the broader historical label; zone actuators are out of scope here.

## Outcome

The house no longer climbs Set Water Temperature to `setpoint_max` via a tracking term when Critical Zone air is near setpoint and flat; the spec's success signal holds with R5 tests, commissionable FF (R6), max-error-zone rise-rate auto-correct (R7), immediate R8 gate reactivity, and a new ADR that supersedes ADR 0002 and ADR 0003.

## Requirements

- R1 (CAP-1): When Plant Management is on and Heating Demand is present, the system can command Set Water Temperature from Weather Feedforward alone (clamped), with no air-temperature tracking contribution. Success: On a demand evaluation, the written command equals `clamp(weather_feedforward)` for that outdoor/comfort inputs and current FF parameters; no `u_track` (or equivalent tracking term) is added.
- R2 (CAP-2): When Plant Management is on and no Zone has Heating Demand, the system can idle the plant water setpoint at zero and clear water-path controller state. Success: Idle path writes `0` to Set Water Temperature and does not leave LADRC/tuner water-path state active for the next demand evaluation.
- R3 (CAP-3): When Plant Management is off, the system can stay hands-off on the plant water setpoint. Success: No Set Water Temperature write occurs; controller state is cleared. Writing `0` is not used as the off representation.
- R4 (CAP-4): Maintainers and agents can treat LADRC-on-Critical-Zone water control, online ωc auto-tune on water, and Critical Zone as an SWT driver as removed, not dormant. Success: Code on the SWT path no longer runs LADRC tracking or ωc adaptation; SWT is not driven by Critical Zone air; a **new ADR** supersedes ADR 0002 and ADR 0003; CONTEXT/AGENTS no longer describe Critical Zone air as driving Set Water Temperature (max-error zone may remain only as the R7 rise-rate source).
- R5 (CAP-5): Automated tests can lock the weather-curve-only SWT law so tracking windup cannot return silently. Success: Tests cover (a) demand → `clamp(u_ff)` only, (b) Plant-on idle → write `0` + clear, (c) Plant-off → no write + clear, (d) a near-setpoint flat-air scenario that formerly grew `u_track` to max no longer drives command above the feedforward clamp toward `setpoint_max` via tracking, (e) max-error zone air does not appear as an additive tracking term on SWT.
- R6 (CAP-6): Operators can commission Weather Feedforward parameters for the house so the demand-path water command matches the intended outdoor curve. Success: Base/slope (or equivalent) are configurable and used by R1; changing them changes `clamp(u_ff)` under the same outdoor/comfort inputs without reintroducing air→SWT tracking.
- R7 (CAP-7): The system can auto-correct Weather Feedforward parameters from the temperature rise rate of the zone with the largest Zone Error among zones with Heating Demand. Success: Under sustained Heating Demand, FF parameters move in response to that max-error zone’s measured air temperature rise rate; SWT command remains `clamp(weather_feedforward)` with updated params — not `u_ff + u_track`. Identifying the max-error zone for rise-rate must not restore Critical Zone / air-error as an SWT tracking driver. Rise-rate window and I1 sampling advance only on periodic `control_interval` evaluations — not on R8 event re-evaluations.
- R8 (CAP-8): The system can re-apply the Plant Management / Heating Demand / Set Water Temperature gate law as soon as Plant Management, any configured thermostat `hvac_action` or setpoint, any configured zone air temperature, or Outdoor Temperature changes, without waiting solely for the next periodic `control_interval`. Success: A change of any of those inputs that flips Plant Management, Heating Demand presence, or `clamp(u_ff)` produces the corresponding R1 / R2 / R3 write behavior before the next scheduled periodic evaluation would have run; R7 sampling is unchanged by that event path.

## Constraints

- Plant Management off means **no write** and cleared state — not “write 0”.
- Heating Demand idle write-`0` runs only when Plant Management is on.
- CH / circuit gate is the existing `plant_management` entity; no additional boiler-circuit signal.
- App does not command zone on/off actuators or TRV valve percent in this wave.
- Remove LADRC and ωc auto-tune from the SWT path now; do not leave them dormant for water.
- Do **not** use Critical Zone / max-error zone air to form an SWT tracking term; Heating Demand for the SWT gate is an any-zone boolean.
- R7 may identify the zone with largest Zone Error solely as the rise-rate signal for FF auto-correct.
- `setpoint_min` stays **40**; soft weather-curve `u_ff` below min still clamps up to min — do not lower min in this wave to chase softer water.
- Document the new SWT law in a **new ADR** that supersedes 0002 and 0003.
- Domain language for Plant Management, Heating Demand, Weather Feedforward, and Set Water Temperature follows `CONTEXT.md`; retire Critical Zone as an SWT driver when docs update with the new ADR.
- R7 auto-correct adjusts FF parameters only; it must not add an air-error tracking term to the SWT command.
- Immediate re-evaluation on Plant Management, thermostat `hvac_action` / setpoint, zone air temperature, or Outdoor Temperature change must preserve R1…R3 gate law and must not introduce air→SWT tracking.
- Event-driven evaluations must not advance R7 rise-rate window or I1 sampling; R7 samples stay on the periodic `control_interval` cadence only.

## Done when

1. On Heating Demand with Plant Management on, Set Water Temperature equals `clamp(weather_feedforward)` with `setpoint_min` still 40 — no air-temperature tracking term.
2. Plant Management on and no Heating Demand writes `0` and clears water-path controller state; Plant Management off does not write and clears state.
3. LADRC tracking, ωc auto-tune, and Critical Zone as an SWT driver are gone from the water path; a new ADR supersedes 0002 and 0003; CONTEXT/AGENTS no longer describe Critical Zone air as driving Set Water Temperature.
4. Automated tests lock demand → `clamp(u_ff)`, plant-on idle → write 0 + clear, plant-off → no write + clear, near-setpoint flat-air no climb to max via tracking, and max-error zone air not added as an SWT tracking term.
5. Weather Feedforward base/slope are configurable and used on the demand path; under sustained Heating Demand, FF parameters auto-correct from the max-error zone's air temperature rise rate without restoring air→SWT tracking.
6. R8 triggers re-apply R1…R3 before the next periodic tick alone would, without advancing R7 samples; periodic ticks still run R7; tests and ADR/docs lock that contract.

## Boundaries

Capability boundary: the AppDaemon `ha_smart_hvac` Set Water Temperature path and its docs/ADR language. Not zone on/off or TRV valve percent, not MADRC, not lowering `setpoint_min` below 40, not event-only scheduling — see the spec's Non-goals. Tracer path: epic 1 owns R1…R7; epic 2 owns R8.

- Touch point: `apps/apps.yaml` and `apps.yaml.example` — FF config and removal of water-path LADRC/tune yaml; owner: epic-weather-curve-swt-only
- Touch point: `docs/adr/`, `CONTEXT.md`, `AGENTS.md`, `docs/house-calibration.md` — ADR supersession and domain language; owner: epic-weather-curve-swt-only (R8 reactivity doc updates: epic-immediate-swt-reactivity)
- Touch point: Home Assistant entities (outdoor temperature, plant setpoint, zone climates) — consumed; no new entities required for R1…R5; owner: epic-weather-curve-swt-only; R8 listens on existing entities — owner: epic-immediate-swt-reactivity
- Touch point: persistence paths — remove water-path ωc tune state; R6/7 may add or reuse FF-param persistence; owner: epic-weather-curve-swt-only
- Non-goal: LADRC/MADRC control of continuous Sonoff TRVZB valve opening (option B valve wave).
- Non-goal: Keeping LADRC on SWT with deadband / anti-windup (option C).
- Non-goal: App ownership of zone on/off or floor actuators.
- Non-goal: Adopting MADRC for this plant.
- Non-goal: Lowering `setpoint_min` below 40 to deliver sub-min curve water.
- Non-goal: Keeping Critical Zone selection for logging-only or “future valves” in this wave.
- Non-goal: Reintroducing Critical Zone / max-error air as a closed-loop driver of Set Water Temperature under another name.
- Non-goal: Replacing periodic `control_interval` scheduling with an event-only loop (periodic cadence remains unless decided otherwise).

## References

- spec — `_bmad-output/initiative-weather-curve-zone-actuators/initiative-weather-curve-zone-actuators.md`, Capabilities R1…R8
- constraint — same spec, section Constraints
- companion — `_bmad-output/initiative-weather-curve-zone-actuators/brownfield.md`
- companion — `_bmad-output/initiative-weather-curve-zone-actuators/architecture-diagrams.md`
- forge — `_bmad-output/initiative-weather-curve-zone-actuators/forge-weather-curve-zone-actuators/forge-weather-curve-zone-actuators.md` (hardened input; history only)
- domain — `CONTEXT.md`
- companion — brownfield.md
- companion — architecture-diagrams.md
- companion — ../../../../CONTEXT.md

## Notes

- Decision: initiative title is "Weather-curve SWT only"; folder stays `initiative-weather-curve-zone-actuators` (2026-10-18).
- Decision: one epic owns R1…R7; R7 not split for an early windup-only ship (2026-10-18).
- Decision: no platform-baseline epic — brownfield AppDaemon app; Exclusive Session and CI already exist (ADR 0001) (2026-10-18).
- Parked: zone on/off / TRV proportional control — forge rejected for this wave; not covered by any epic.
- Closed 2026-10-19: epic `epic-weather-curve-swt-only` done; retrospective accepted; zone actuators remain out of scope.
- Decision: reopen initiative for R8 follow-on as epic `epic-immediate-swt-reactivity` (2026-10-19).
- Closed: both epics done; Done when 1–6 verified (epic retros + closure check); user approved (2026-10-20). Zone actuators remain parked / out of scope.
