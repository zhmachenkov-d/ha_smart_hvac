---
type: Concept
title: Critical Zone
description: Zone with the largest Zone Error among Zones with Heating Demand; diagnostics and logging only — never drives Set Water Temperature, TRV soft-close, or flame short-on trip.
tags: [zone, control]
timestamp: 2026-11-17T12:00:00Z
---

# Critical Zone

The **Critical Zone** is the [Zone](/concepts/zone.md) with the largest [Zone Error](/concepts/zone-error.md) among Zones with Heating Demand. It is retained for diagnostics and logging only — it must not drive [Set Water Temperature](/concepts/set-water-temperature.md), [TRV soft-close](/concepts/trv-soft-close.md), or the [flame short-on trip](/concepts/flame-short-on-trip.md).

Avoid “master zone” or “primary room”.

Chosen by the [Multi-Zone Coordinator](/concepts/multi-zone-coordinator.md).

The old roles of Critical Zone as SWT closed-loop / Plant water driver and as CAP-7 rise-rate signal are **removed** — **superseded by ADR 0008**.

# Citations

- [`CONTEXT.md`](../../CONTEXT.md) — Critical Zone
- [ADR 0008](../../docs/adr/0008-weather-curve-trv-flame-swt.md) — Critical Zone diagnostics-only; must not drive SWT / TRV / flame
