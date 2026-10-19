---
type: initiative
title: "Weather-curve SWT only"
parent: none
covers: [CAP-1, CAP-2, CAP-3, CAP-4, CAP-5, CAP-6, CAP-7, CAP-8]
after: []
assignee: ""
risk: medium
status: in-progress
---

# Weather-curve SWT only

## Description

Stop Set Water Temperature windup from closed-loop air→SWT tracking by commanding weather-curve-only water under existing Plant Management / Heating Demand gates, with commissionable and rise-rate auto-corrected Weather Feedforward parameters, then make that gate law react immediately to Plant Management, thermostat, zone-air, and Outdoor Temperature changes without advancing CAP-7 sampling off the periodic cadence. The numbered spec owns capabilities, constraints, and non-goals; this initiative delivers that wave. Folder name retains the broader historical label; zone actuators are out of scope here.

## Outcome

The house no longer climbs Set Water Temperature to `setpoint_max` via a tracking term when Critical Zone air is near setpoint and flat; the spec's success signal holds with CAP-5 tests, commissionable FF (CAP-6), max-error-zone rise-rate auto-correct (CAP-7), immediate CAP-8 gate reactivity, and a new ADR that supersedes ADR 0002 and ADR 0003.

## Done when

1. On Heating Demand with Plant Management on, Set Water Temperature equals `clamp(weather_feedforward)` with `setpoint_min` still 40 — no air-temperature tracking term.
2. Plant Management on and no Heating Demand writes `0` and clears water-path controller state; Plant Management off does not write and clears state.
3. LADRC tracking, ωc auto-tune, and Critical Zone as an SWT driver are gone from the water path; a new ADR supersedes 0002 and 0003; CONTEXT/AGENTS no longer describe Critical Zone air as driving Set Water Temperature.
4. Automated tests lock demand → `clamp(u_ff)`, plant-on idle → write 0 + clear, plant-off → no write + clear, near-setpoint flat-air no climb to max via tracking, and max-error zone air not added as an SWT tracking term.
5. Weather Feedforward base/slope are configurable and used on the demand path; under sustained Heating Demand, FF parameters auto-correct from the max-error zone's air temperature rise rate without restoring air→SWT tracking.
6. CAP-8 triggers re-apply CAP-1…CAP-3 before the next periodic tick alone would, without advancing CAP-7 samples; periodic ticks still run CAP-7; tests and ADR/docs lock that contract.

## Boundaries

Capability boundary: the AppDaemon `ha_smart_hvac` Set Water Temperature path and its docs/ADR language. Not zone on/off or TRV valve percent, not MADRC, not lowering `setpoint_min` below 40, not event-only scheduling — see the spec's Non-goals. Tracer path: epic 1 owns CAP-1…CAP-7; epic 2 owns CAP-8.

- Touch point: `apps/apps.yaml` and `apps.yaml.example` — FF config and removal of water-path LADRC/tune yaml; owner: epic-weather-curve-swt-only
- Touch point: `docs/adr/`, `CONTEXT.md`, `AGENTS.md`, `docs/house-calibration.md` — ADR supersession and domain language; owner: epic-weather-curve-swt-only (CAP-8 reactivity doc updates: epic-immediate-swt-reactivity)
- Touch point: Home Assistant entities (outdoor temperature, plant setpoint, zone climates) — consumed; no new entities required for CAP-1…CAP-5; owner: epic-weather-curve-swt-only; CAP-8 listens on existing entities — owner: epic-immediate-swt-reactivity
- Touch point: persistence paths — remove water-path ωc tune state; CAP-6/7 may add or reuse FF-param persistence; owner: epic-weather-curve-swt-only

## References

- spec — `_bmad-output/initiative-weather-curve-zone-actuators/spec-weather-curve-swt-only/spec-weather-curve-swt-only.md`, Capabilities CAP-1…CAP-8
- constraint — same spec, section Constraints
- companion — `_bmad-output/initiative-weather-curve-zone-actuators/spec-weather-curve-swt-only/brownfield.md`
- companion — `_bmad-output/initiative-weather-curve-zone-actuators/spec-weather-curve-swt-only/architecture-diagrams.md`
- forge — `_bmad-output/initiative-weather-curve-zone-actuators/forge-weather-curve-zone-actuators/forge-weather-curve-zone-actuators.md` (hardened input; history only)
- domain — `CONTEXT.md`

## Notes

- Decision: initiative title is "Weather-curve SWT only"; folder stays `initiative-weather-curve-zone-actuators` (2026-10-18).
- Decision: one epic owns CAP-1…CAP-7; CAP-7 not split for an early windup-only ship (2026-10-18).
- Decision: no platform-baseline epic — brownfield AppDaemon app; Exclusive Session and CI already exist (ADR 0001) (2026-10-18).
- Parked: zone on/off / TRV proportional control — forge rejected for this wave; not covered by any epic.
- Closed 2026-10-19: epic `epic-weather-curve-swt-only` done; retrospective accepted; zone actuators remain out of scope.
- Decision: reopen initiative for CAP-8 follow-on as epic `epic-immediate-swt-reactivity` (2026-10-19).
