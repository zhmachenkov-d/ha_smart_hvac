---
type: epic
title: "Weather-curve SWT only"
parent: initiative-weather-curve-zone-actuators
covers: [CAP-1, CAP-2, CAP-3, CAP-4, CAP-5, CAP-6, CAP-7]
after: []
assignee: ""
risk: medium
---

# Weather-curve SWT only

## Description

Replace LADRC-on-Critical-Zone water control with weather-curve-only Set Water Temperature under existing Plant Management / Heating Demand gates, remove ωc auto-tune from the water path, commission and auto-correct Weather Feedforward parameters from the max-error zone's rise rate, lock the law with tests, and supersede ADR 0002 and ADR 0003. The numbered parent spec is the requirement source.

## Outcome

On the live plant (via the normal Exclusive Session / AppDaemon path), Set Water Temperature follows `clamp(weather_feedforward)` without air→SWT tracking windup; FF is commissionable and rise-rate auto-corrected; maintainers treat LADRC/ωc/Critical Zone as removed from water — matching the parent initiative's success signal.

## Requirements

Referenced numbered source: `_bmad-output/initiative-weather-curve-zone-actuators/spec-weather-curve-swt-only/spec-weather-curve-swt-only.md` — Capabilities CAP-1…CAP-7 (parent covers). Constraints and Non-goals bind this epic via References.

## Done when

1. Demand path writes `clamp(weather_feedforward)` only (`setpoint_min` 40); no `u_track` or equivalent on SWT.
2. Plant-on idle writes `0` and clears water-path state; plant-off does not write and clears state.
3. LADRC, ωc auto-tune, and Critical Zone as SWT driver are removed from the water path (not dormant); new ADR supersedes 0002 and 0003; CONTEXT/AGENTS updated.
4. CAP-5 automated suite passes, including near-setpoint flat-air no climb to `setpoint_max` via tracking and max-error zone air not additive on SWT.
5. CAP-6 commissioning and CAP-7 rise-rate auto-correct of FF params are live under Heating Demand without restoring air→SWT tracking.
6. Delivered on the house AppDaemon path (Exclusive Session / Production add-on) for verification against the windup shape in the spec's success signal.

## Boundaries

The `apps/ha_smart_hvac` SWT control path, its tests, AppDaemon yaml/example, persistence for removed ωc / FF auto-correct, and ADR/CONTEXT/AGENTS/house-calibration language. Not zone actuators or TRV percent, not MADRC, not lowering `setpoint_min` — see parent spec Non-goals.

## References

- parent — `_bmad-output/initiative-weather-curve-zone-actuators/initiative-weather-curve-zone-actuators.md`
- spec — `_bmad-output/initiative-weather-curve-zone-actuators/spec-weather-curve-swt-only/spec-weather-curve-swt-only.md`, Capabilities and Constraints
- companion — `_bmad-output/initiative-weather-curve-zone-actuators/spec-weather-curve-swt-only/brownfield.md`
- companion — `_bmad-output/initiative-weather-curve-zone-actuators/spec-weather-curve-swt-only/architecture-diagrams.md`
- domain — `CONTEXT.md`
- adr — `docs/adr/0002-ladrc-critical-zone-control.md` (to supersede)
- adr — `docs/adr/0003-online-ladrc-omega-c-auto-tune.md` (to supersede)

## Notes

- Decision: CAP-7 stays in this epic with CAP-1…CAP-6 (2026-10-18).
- Decision: CAP-6 stays yaml-only — no new HA entities for FF params (2026-10-18).
- Decision: entry 3 (ADR/docs) waits on spike 4 so CAP-7 formula/persistence land in the ADR (2026-10-18).
- Decision: tracer bullet is entry 1; entries 2∥4 after 1; 3 and 5 after 2+4; refactor sweep 6; live Exclusive Session check 7 last (2026-10-18).
- Decision (draft, 2026-10-19, Denys): CAP-7 rise-rate auto-correct — Signal W15/1A+1B, Law I1/CS-base/N2+G25, Guards N-both+2B/2C/3A, Persistence B1 (`ff_auto_correct_state.json`); full contract in `spike-ff-rise-rate-auto-correct-rule-decision.md`. Pending Denys accept before 1.5; supersedes prior Unknown rise-rate line.
