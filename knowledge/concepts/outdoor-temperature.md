---
type: Concept
title: Outdoor Temperature
description: Measured outdoor air temperature; not on the Set Water Temperature path or live commissioning.
tags: [sensing, plant]
timestamp: 2026-11-08T20:40:00Z
---

# Outdoor Temperature

**Outdoor Temperature** is the measured outdoor air temperature. It is not on the [Set Water Temperature](/concepts/set-water-temperature.md) path or live commissioning (not a control listener; not an input to the demand command).

Avoid “weather” or “forecast” unless forecast is explicitly in scope.

In Huang et al. (2018) the Simulink scenario fixes outdoor temperature at 0 °C; disturbance rejection is tested with an injected step, not weather models.

## Related

- [/concepts/set-water-temperature.md](/concepts/set-water-temperature.md)
- [/concepts/total-disturbance.md](/concepts/total-disturbance.md)

# Citations

- [`CONTEXT.md`](../../CONTEXT.md) — Outdoor Temperature
- [ADR 0005](../../docs/adr/0005-fixed-pid-swt.md) — Outdoor not on the water path
