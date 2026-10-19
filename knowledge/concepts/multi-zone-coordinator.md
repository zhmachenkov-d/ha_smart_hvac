---
type: Concept
title: Multi-Zone Coordinator
description: App logic that computes Zone Error, Heating Demand, and Critical Zone selection for CAP-7 rise-rate auto-correct. Does not own the OpenTherm Set Water Temperature write.
tags: [zone, control]
timestamp: 2026-07-08T15:34:24Z
---

# Multi-Zone Coordinator

The **Multi-Zone Coordinator** computes [Zone Error](/concepts/zone-error.md) per [Zone](/concepts/zone.md), Heating Demand, and [Critical Zone](/concepts/critical-zone.md) selection for CAP-7 rise-rate auto-correct. It does not own the OpenTherm write to [Set Water Temperature](/concepts/set-water-temperature.md).

Not a thermostat or scheduler unless that is all it does.

The old Coordinator role as ADRC handoff and Plant water ownership is **removed** — **superseded by ADR 0004**.

Huang et al. (2018) study a **single** zone LADRC loop — no multi-zone coordination ([/references/huang-2018-ladrc-hvac.md](/references/huang-2018-ladrc-hvac.md)).

# Citations

- [`CONTEXT.md`](../../CONTEXT.md) — Multi-Zone Coordinator
- [ADR 0004](../../docs/adr/0004-weather-curve-swt.md) — weather-curve-only SWT
