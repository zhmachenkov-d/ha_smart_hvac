---
type: Concept
title: Multi-Zone Coordinator
description: App logic that computes Zone Error, Heating Demand, and Critical Zone selection; Critical Zone is diagnostics-only (must not drive SWT, TRV soft-close, or flame trip). Does not own Set Water Temperature write.
tags: [zone, control]
timestamp: 2026-11-17T12:00:00Z
---

# Multi-Zone Coordinator

The **Multi-Zone Coordinator** computes [Zone Error](/concepts/zone-error.md) per [Zone](/concepts/zone.md), Heating Demand, and [Critical Zone](/concepts/critical-zone.md) selection. Critical Zone selection is for diagnostics and logging only and must not drive [Set Water Temperature](/concepts/set-water-temperature.md), [TRV soft-close](/concepts/trv-soft-close.md), or the [flame short-on trip](/concepts/flame-short-on-trip.md). The Coordinator does not own the OpenTherm write to Set Water Temperature, TRV soft-close, or the flame trip.

Not a thermostat or scheduler unless that is all it does.

The old Coordinator roles as ADRC handoff, Plant water ownership, and CAP-7 Critical Zone commissioning are **removed** — **superseded by ADR 0008**.

Huang et al. (2018) study a **single** zone LADRC loop — no multi-zone coordination ([/references/huang-2018-ladrc-hvac.md](/references/huang-2018-ladrc-hvac.md)).

# Citations

- [`CONTEXT.md`](../../CONTEXT.md) — Multi-Zone Coordinator
- [ADR 0008](../../docs/adr/0008-weather-curve-trv-flame-swt.md) — Coordinator does not own SWT / TRV / flame; Critical Zone diagnostics-only
