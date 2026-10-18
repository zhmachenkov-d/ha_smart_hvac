---
type: Concept
title: Zone Error
description: Difference between a Zone’s thermostat setpoint and that Zone’s current temperature.
tags: [zone, control]
timestamp: 2026-07-08T15:34:24Z
---

# Zone Error

**Zone Error** is, per thermostat in a [Zone](/concepts/zone.md): setpoint minus zone sensor temperature. Zone-level error is the **maximum** across thermostats in that Zone whose `hvac_action` is `heating`; thermostats with idle, off, cooling, or unavailable action do not contribute. A Zone with no eligible thermostats cannot become the [Critical Zone](/concepts/critical-zone.md). The [Critical Zone](/concepts/critical-zone.md) is the Zone with the largest positive Zone Error in a control step.

Use **Heating Demand** when a Zone needs heat (zone error > 0). Avoid “delta” (ambiguous).

# Citations

- [`CONTEXT.md`](../../CONTEXT.md) — Zone Error
