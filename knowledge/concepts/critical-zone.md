---
type: Concept
title: Critical Zone
description: Zone with the largest Zone Error among Zones with Heating Demand; CAP-7 rise-rate signal only — never drives Set Water Temperature as closed-loop air→water tracking.
tags: [zone, control]
timestamp: 2026-07-08T15:34:24Z
---

# Critical Zone

The **Critical Zone** is the [Zone](/concepts/zone.md) with the largest [Zone Error](/concepts/zone-error.md) among Zones with Heating Demand. Its air temperature rise rate is the signal for Weather Feedforward rise-rate auto-correct (CAP-7) only — it never drives [Set Water Temperature](/concepts/set-water-temperature.md) as a closed-loop air→water tracking term.

Avoid “master zone” or “primary room”.

Chosen by the [Multi-Zone Coordinator](/concepts/multi-zone-coordinator.md).

The old role of Critical Zone as SWT closed-loop / Plant water driver is **removed** — **superseded by ADR 0004**.

# Citations

- [`CONTEXT.md`](../../CONTEXT.md) — Critical Zone
- [ADR 0004](../../docs/adr/0004-weather-curve-swt.md) — weather-curve-only SWT
