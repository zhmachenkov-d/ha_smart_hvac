---
type: epic
title: "Immediate SWT gate reactivity"
parent: initiative-weather-curve-zone-actuators
covers: [R8]
after: []
assignee: ""
risk: medium
status: done
---

# Immediate SWT gate reactivity

## Description

Add event-driven re-evaluation of the existing Plant Management / Heating Demand / weather-curve SWT gate law on the R8 trigger set while keeping R7 rise-rate sampling on periodic `control_interval` only.

## Outcome

Plant Management, thermostat inputs, zone air, and Outdoor Temperature changes apply R1…R3 writes without waiting solely for the next periodic `control_interval`, without advancing R7 samples; periodic ticks still run the full path including R7 — matching the parent spec’s R8 success.

## Requirements

Referenced numbered source: `_bmad-output/initiative-weather-curve-zone-actuators/initiative-weather-curve-zone-actuators.md` — Capability R8 (parent covers). Constraints (event path preserves R1…R3; event evaluations must not advance R7 sampling) and Non-goals (not event-only scheduling) bind this epic via References.

## Done when

1. Changing any R8 trigger (Plant Management, thermostat `hvac_action` or setpoint, zone air temperature, Outdoor Temperature) applies the matching R1 / R2 / R3 write behavior without waiting solely for the next periodic `control_interval`.
2. The event path does not advance R7 rise-rate window or I1 sampling.
3. Periodic `control_interval` still runs the full demand path including R7.
4. Automated tests lock event write + R7 untouched on the event path and (3); ADR/docs (and spec companions if updated) state the reactivity contract. Hass stubs lock callback behavior, not a live timer race.

## Boundaries

The `apps/ha_smart_hvac` control-loop reactivity, its tests, ADR 0004 / CONTEXT / AGENTS language for R8, and alignment of spec companions `brownfield.md` / `architecture-diagrams.md`. Not replacing periodic scheduling with an event-only loop; not zone actuators or TRV percent — see parent spec Non-goals.

Touch points owned by this epic: `apps/ha_smart_hvac/hvac_app.py` (and helpers it needs), `tests/test_hvac_app.py`, `docs/adr/0004-weather-curve-swt.md`, `CONTEXT.md` / `AGENTS.md` as needed, and the R8 sections of the spec companions above.

## References

- parent — `_bmad-output/initiative-weather-curve-zone-actuators/initiative-weather-curve-zone-actuators.md`
- spec — `_bmad-output/initiative-weather-curve-zone-actuators/initiative-weather-curve-zone-actuators.md`, R8 and Constraints
- companion — `_bmad-output/initiative-weather-curve-zone-actuators/brownfield.md`
- companion — `_bmad-output/initiative-weather-curve-zone-actuators/architecture-diagrams.md`
- adr — `docs/adr/0004-weather-curve-swt.md`
- domain — `CONTEXT.md`

## Notes

- Decision: tracer is entry 1; docs after code; no refactor sweep (only two entries) (2026-10-19).
- Decision: one epic owns R8; R7 sampling cadence stays periodic-only per spec walkthrough Q1=A (2026-10-19).
- Waits on epic-weather-curve-swt-only because: weather-curve SWT law and R7 periodic sampling must already be shipped (initiative epic 1 done).
- Assumption: AppDaemon `listen_state` (entity state and climate attributes) is sufficient to detect the R8 trigger set.
- Decision: plan P1+S — honest stub Verify (no theatrical before-tick race); W2 dual entrypoints (forbid advance_cap7 flag); `_write_setpoint` equality skip is the write throttle, no debounce in tracer (2026-10-19).
- Closed: Done when verified against implementation (code, R8 tests, ADR 0004, companions); user approved (2026-10-20).
