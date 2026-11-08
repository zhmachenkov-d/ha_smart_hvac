---
type: Concept
title: ADRC
description: Active Disturbance Rejection Control — estimate and cancel total disturbance each sample, then apply a simple outer controller.
tags: [control, adrc, plant]
timestamp: 2026-11-08T22:19:00Z
---

# ADRC

**Active Disturbance Rejection Control** (Han, 1998) treats unknown dynamics and external effects as a single [total disturbance](/concepts/total-disturbance.md), estimates it with an [extended state observer (ESO)](/concepts/extended-state-observer.md), and cancels it so a modest outer loop can track the reference.

Original ADRC uses nonlinear ESO and nonlinear feedback; parameter tuning is awkward. [LADRC](/concepts/ladrc.md) (Gao) keeps the same structure with linear observer and controller. [MADRC](/concepts/madrc.md) keeps that linear core but delays the ESO command path to cope with high-order inertia.

## In this project

ADRC / LADRC on the water path is **removed** — **superseded by ADR 0005**. Live [Set Water Temperature](/concepts/set-water-temperature.md) is fixed-gain PID (`round-to-0.1(clamp(base_water_temp + u_pid))`) under Plant Management / Heating Demand; the [Multi-Zone Coordinator](/concepts/multi-zone-coordinator.md) selects [Critical Zone](/concepts/critical-zone.md) for diagnostics and logging only. This page stays as literature depth, not the live App stack.

Literature:

- HVAC air loop (LADRC vs PID): [/references/huang-2018-ladrc-hvac.md](/references/huang-2018-ladrc-hvac.md)
- High-order lag / wide operating range (adaptive MADRC, field): [/references/wang-2026-madrc-sst.md](/references/wang-2026-madrc-sst.md)

## Related

- [/concepts/ladrc.md](/concepts/ladrc.md)
- [/concepts/madrc.md](/concepts/madrc.md)
- [/concepts/extended-state-observer.md](/concepts/extended-state-observer.md)
- [/concepts/plant.md](/concepts/plant.md)

# Citations

- [/references/huang-2018-ladrc-hvac.md](/references/huang-2018-ladrc-hvac.md) §1, §3.1
- [/references/wang-2026-madrc-sst.md](/references/wang-2026-madrc-sst.md) §3
- [ADR 0005](../../docs/adr/0005-fixed-pid-swt.md) — live SWT is fixed-gain PID, not ADRC
