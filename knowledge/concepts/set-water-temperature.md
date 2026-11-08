---
type: Concept
title: Set Water Temperature
description: OpenTherm boiler water setpoint the App commands on the Plant.
tags: [plant, opentherm]
timestamp: 2026-11-08T20:40:00Z
---

# Set Water Temperature

**Set Water Temperature** is the OpenTherm boiler water setpoint the App commands on the [Plant](/concepts/plant.md) (the boiler’s target water temperature via OpenTherm).

Not the same as a Zone thermostat air setpoint or a mixer setpoint.

The HVAC App owns this write. Under Plant Management and Heating Demand gates: demand → `round-to-0.1(clamp(base_water_temp + u_pid))` from weighted demand-zone air error; plant-on idle → write `0` and clear PID ephemeral state (∫); plant-off → no write and clear ∫. Only periodic `control_tick` advances PID and writes demand SWT; `control_event` may clear on idle / plant-off / no-valid-zones without a demand write or PID advance. The [Multi-Zone Coordinator](/concepts/multi-zone-coordinator.md) does not own this write. [Critical Zone](/concepts/critical-zone.md) is diagnostics-only and must not drive this setpoint.

Weather-curve / CAP-7 SWT (ADR 0004) and LADRC-on-water (ADR 0002) / ωc auto-tune (ADR 0003) are **removed** from the water path — **superseded by ADR 0005**. Outdoor Temperature, Weather Feedforward, CAP-7 rise-rate auto-correct, and `ff_auto_correct_state.json` are not on this path.

# Citations

- [`CONTEXT.md`](../../CONTEXT.md) — Set Water Temperature, PID
- [ADR 0005](../../docs/adr/0005-fixed-pid-swt.md) — fixed-gain PID SWT
