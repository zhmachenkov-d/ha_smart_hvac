---
type: Concept
title: Multi-Zone Coordinator
description: App logic that computes Zone Error, Heating Demand, and Critical Zone selection; Critical Zone selection is diagnostics-only. Does not own the OpenTherm Set Water Temperature write.
tags: [zone, control]
timestamp: 2026-11-08T20:40:00Z
---

# Multi-Zone Coordinator

The **Multi-Zone Coordinator** computes [Zone Error](/concepts/zone-error.md) per [Zone](/concepts/zone.md), Heating Demand, and [Critical Zone](/concepts/critical-zone.md) selection. Critical Zone selection is for diagnostics and logging only and must not drive [Set Water Temperature](/concepts/set-water-temperature.md). The Coordinator does not own the OpenTherm write to Set Water Temperature.

Not a thermostat or scheduler unless that is all it does.

The old Coordinator roles as ADRC handoff, Plant water ownership, and CAP-7 Critical Zone commissioning are **removed** — **superseded by ADR 0005**.

Huang et al. (2018) study a **single** zone LADRC loop — no multi-zone coordination ([/references/huang-2018-ladrc-hvac.md](/references/huang-2018-ladrc-hvac.md)).

# Citations

- [`CONTEXT.md`](../../CONTEXT.md) — Multi-Zone Coordinator
- [ADR 0005](../../docs/adr/0005-fixed-pid-swt.md) — Coordinator does not own SWT; Critical Zone diagnostics-only
