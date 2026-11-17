---
type: Concept
title: Outdoor Temperature
description: Measured outdoor air T_out; required on the Set Water Temperature demand path and a control_event listener under ADR 0008 — not an input to flame observe.
tags: [sensing, plant]
timestamp: 2026-11-17T12:00:00Z
---

# Outdoor Temperature

**Outdoor Temperature** is the measured outdoor air temperature (`T_out`). It is required on the [Set Water Temperature](/concepts/set-water-temperature.md) demand path: Weather Feedforward uses it in `u_ff = base + slope × (comfort_ref − T_out)`, and it is a `control_event` listener that re-evaluates the Outdoor-gated demand writer (with Plant Management, zone air, thermostat `hvac_action` / setpoint, and commissioned accuracy). Unavailable Outdoor under plant-on conditions is a Plant-on non-demand exit (idle).

Outdoor is **not** an input to `_flame_observe_gate` and is never required for flame observe — that gate is Plant∧Demand∧`ch_active` on∧¬latch only (see [flame short-on trip](/concepts/flame-short-on-trip.md)).

Avoid “weather” as a synonym for Outdoor Temperature when you mean Weather Feedforward. Avoid “forecast” unless forecast is explicitly in scope.

In Huang et al. (2018) the Simulink scenario fixes outdoor temperature at 0 °C; disturbance rejection is tested with an injected step, not weather models.

## Related

- [/concepts/set-water-temperature.md](/concepts/set-water-temperature.md)
- [/concepts/flame-short-on-trip.md](/concepts/flame-short-on-trip.md)
- [/concepts/total-disturbance.md](/concepts/total-disturbance.md)

# Citations

- [`CONTEXT.md`](../../CONTEXT.md) — Outdoor Temperature, Weather Feedforward
- [ADR 0008](../../docs/adr/0008-weather-curve-trv-flame-swt.md) — Outdoor required on the demand path; dual-gate (never Outdoor for flame observe)
