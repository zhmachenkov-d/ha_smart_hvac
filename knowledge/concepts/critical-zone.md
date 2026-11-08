---
type: Concept
title: Critical Zone
description: Zone with the largest Zone Error among Zones with Heating Demand; diagnostics and logging only — never drives Set Water Temperature.
tags: [zone, control]
timestamp: 2026-11-08T20:40:00Z
---

# Critical Zone

The **Critical Zone** is the [Zone](/concepts/zone.md) with the largest [Zone Error](/concepts/zone-error.md) among Zones with Heating Demand. It is retained for diagnostics and logging only — it must not drive [Set Water Temperature](/concepts/set-water-temperature.md).

Avoid “master zone” or “primary room”.

Chosen by the [Multi-Zone Coordinator](/concepts/multi-zone-coordinator.md).

The old roles of Critical Zone as SWT closed-loop / Plant water driver and as CAP-7 rise-rate signal are **removed** — **superseded by ADR 0005**.

# Citations

- [`CONTEXT.md`](../../CONTEXT.md) — Critical Zone
- [ADR 0005](../../docs/adr/0005-fixed-pid-swt.md) — Critical Zone diagnostics-only
