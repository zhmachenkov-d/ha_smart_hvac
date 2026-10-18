---
type: Concept
title: Zone
description: Controllable heating area with a temperature reading and one or more HA climate thermostats, sharing boiler demand.
tags: [zone, home-assistant]
timestamp: 2026-07-08T15:34:24Z
---

# Zone

A **Zone** is a controllable heating area of the house that participates in shared boiler demand. It has a temperature reading and one or more Home Assistant thermostats (climate entities).

Avoid calling a Zone a “room” unless it is exactly one room, or an “entity” (entities are HA objects).

Huang et al. (2018) model a single AHU-served zone for LADRC; this project coordinates **multiple** Zones via the [Multi-Zone Coordinator](/concepts/multi-zone-coordinator.md).

## Related

- [/concepts/zone-error.md](/concepts/zone-error.md)
- [/concepts/critical-zone.md](/concepts/critical-zone.md)
- [/concepts/plant.md](/concepts/plant.md)

# Citations

- [`CONTEXT.md`](../../CONTEXT.md) — Zone
- [/references/huang-2018-ladrc-hvac.md](/references/huang-2018-ladrc-hvac.md) §2.1 (literature zone model)
