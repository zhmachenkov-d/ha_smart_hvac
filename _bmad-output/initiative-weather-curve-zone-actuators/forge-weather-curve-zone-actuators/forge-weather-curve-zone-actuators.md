---
title: Weather-curve SWT only (drop LADRC on water)
status: hardened
created: 2026-10-18
updated: 2026-10-18
---

# Weather-curve SWT only

## Locked

- **Do it:** narrow A — worth doing against live windup logs.
- **SWT law:** Plant Management on + Heating Demand → `clamp(weather_feedforward)`; else write `0`. No LADRC tracking on water.
- **Zones:** leave on/off in Home Assistant; App does not command TRV position or floor actuators.
- **CH gate:** existing `plant_management` / CH enabled — no extra circuit signal.
- **Remove now:** LADRC and ωc auto-tune from the SWT path (code + docs/ADR), not dormant on water.
- **Pain proof:** air near setpoint (`error≈0.2`, `y` flat), moderate `u_ff`, `u_track` climbs → `command→setpoint_max`.
- **setpoint_min:** keep **40** (soft `u_ff` below min still clamps up).
- **Critical Zone:** drop from the SWT control path; Heating Demand is any-zone boolean. Do not keep Critical Zone for logging-only or “future valves” in this wave.
- **FF params:** house-commission (base/slope); **auto-correct in this wave** from room temperature rise rate of the **zone with largest Zone Error** among zones with Heating Demand — informs FF params only, never an air tracking term on SWT.
- **ADRs:** supersede 0002 and 0003 with a **new ADR** (weather-curve-only SWT + FF commission/auto-correct).
- **Plant Management / Heating Demand:** semantics stay as in `CONTEXT.md` (off = no write + clear; idle-0 only when Plant on).

## Rejected

- **B** this wave: LADRC/MADRC on continuous Sonoff TRVZB opening (possible via opening/closing-degree hack; costly, no reliable position feedback).
- **C:** keep LADRC on SWT + deadband/anti-windup.
- App owning zone on/off or valve percent in this initiative wave.
- Lowering `setpoint_min` below 40 to chase softer curve water.
- Keeping Critical Zone selection for logging or deferred valve work in this wave.
- Reintroducing Critical Zone / max-error air as a closed-loop driver of Set Water Temperature under another name.

## Why (load-bearing)

- Closed-loop air→SWT keeps raising water when the room barely moves; feedforward alone was not the culprit.
- Weather curve + existing zone climates fixes the failure mode without waiting on TRV proportional control.
- Dropping LADRC/ωc on water matches the chosen law; parking them for a later valve wave was declined.
- FF auto-correct from max-error zone rise rate adapts the curve without restoring air→SWT tracking.

## Open (implementation, not idea)

- _(none — walkthrough closed; see `../spec-weather-curve-swt-only/`)_
