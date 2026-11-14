---
type: Concept
title: Multi-Zone Coordinator
description: App logic that computes Zone Error, Heating Demand, and Critical Zone selection; Critical Zone is diagnostics-only (must not drive SWT or supply trip). Does not own Set Water Temperature write or supply trip.
tags: [zone, control]
timestamp: 2026-11-14T14:58:00Z
---

# Multi-Zone Coordinator

The **Multi-Zone Coordinator** computes [Zone Error](/concepts/zone-error.md) per [Zone](/concepts/zone.md), Heating Demand, and [Critical Zone](/concepts/critical-zone.md) selection. Critical Zone selection is for diagnostics and logging only and must not drive [Set Water Temperature](/concepts/set-water-temperature.md) or the supply rise-rate trip. The Coordinator does not own the OpenTherm write to Set Water Temperature or the supply trip.

Not a thermostat or scheduler unless that is all it does.

The old Coordinator roles as ADRC handoff, Plant water ownership, and CAP-7 Critical Zone commissioning are **removed** — **superseded by ADR 0007**.

Huang et al. (2018) study a **single** zone LADRC loop — no multi-zone coordination ([/references/huang-2018-ladrc-hvac.md](/references/huang-2018-ladrc-hvac.md)).

# Citations

- [`CONTEXT.md`](../../CONTEXT.md) — Multi-Zone Coordinator
- [ADR 0007](../../docs/adr/0007-weather-curve-supply-trip-swt.md) — Coordinator does not own SWT or trip; Critical Zone diagnostics-only
