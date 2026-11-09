---
okf_version: "0.1"
title: Concepts
description: Index of concepts in the knowledge bundle.
---

# Concepts

| Title | Description |
|-------|-------------|
| [ADRC](/concepts/adrc.md) | Active Disturbance Rejection Control — estimate and cancel total disturbance each sample, then apply a simple outer controller. |
| [Critical Zone](/concepts/critical-zone.md) | Zone with the largest Zone Error among Zones with Heating Demand; diagnostics and logging only — never drives Set Water Temperature. |
| [Extended State Observer](/concepts/extended-state-observer.md) | Observer that estimates plant output (or state) and an extra state for total disturbance — the sensing core of ADRC/LADRC. |
| [LADRC](/concepts/ladrc.md) | Linear Active Disturbance Rejection Control — linear ESO plus linear state feedback; practical ADRC form with fewer tuning knobs. |
| [MADRC](/concepts/madrc.md) | Modified ADRC — delay the ESO’s command input with an inertia compensator so it stays synchronized with a high-order lag plant’s delayed output. |
| [Multi-Zone Coordinator](/concepts/multi-zone-coordinator.md) | App logic that computes Zone Error, Heating Demand, and Critical Zone selection; Critical Zone selection is diagnostics-only. Does not own the OpenTherm Set Water Temperature write. |
| [Outdoor Temperature](/concepts/outdoor-temperature.md) | Measured outdoor air temperature; not on the Set Water Temperature path or live commissioning. |
| [Plant](/concepts/plant.md) | Boiler and primary water circuit supplying heat to Zones, commanded via OpenTherm. |
| [RLS adaptive PID](/concepts/rls-adaptive-pid.md) | Optional online retune of PID Kp/Ki via Recursive Least Squares; defaults off; yaml fixed gains when off or unhealthy. |
| [Set Water Temperature](/concepts/set-water-temperature.md) | OpenTherm boiler water setpoint from PID demand `round-to-0.1(clamp(base_water_temp + u_pid))`; gains may be yaml-fixed or optionally RLS-adapted (ADR 0006). |
| [Total disturbance](/concepts/total-disturbance.md) | ADRC’s lumped unknown — internal model error plus external loads — estimated by the ESO and cancelled in the control law. |
| [Zone](/concepts/zone.md) | Controllable heating area with a temperature reading and one or more HA climate thermostats, sharing boiler demand. |
| [Zone Error](/concepts/zone-error.md) | Difference between a Zone’s thermostat setpoint and that Zone’s current temperature. |
