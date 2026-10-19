---
type: Concept
title: Set Water Temperature
description: OpenTherm boiler water setpoint the App commands on the Plant.
tags: [plant, opentherm]
timestamp: 2026-07-08T15:34:24Z
---

# Set Water Temperature

**Set Water Temperature** is the OpenTherm boiler water setpoint the App commands on the [Plant](/concepts/plant.md) (the boiler’s target water temperature via OpenTherm).

Not the same as a Zone thermostat air setpoint or a mixer setpoint.

The HVAC App owns this write. Under Plant Management and Heating Demand gates: demand → `clamp(u_ff)` from Weather Feedforward; plant-on idle → write `0` and clear ephemeral / water-path state; plant-off → no write and clear ephemeral / water-path state (persisted `ff_auto_correct_state.json` untouched). The [Multi-Zone Coordinator](/concepts/multi-zone-coordinator.md) does not own this write.

LADRC-on-water (ADR 0002) and ωc auto-tune (ADR 0003) are **removed** from the water path — **superseded by ADR 0004**. Live law is weather-curve-only SWT under the gates above; no air→water closed-loop term on this path.

# Citations

- [`CONTEXT.md`](../../CONTEXT.md) — Set Water Temperature
- [ADR 0004](../../docs/adr/0004-weather-curve-swt.md) — weather-curve-only SWT
