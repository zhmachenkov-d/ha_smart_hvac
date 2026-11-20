---
okf_version: "0.1"
title: Concepts
description: Index of concepts in the knowledge bundle.
---

# Concepts

| Title | Description |
|-------|-------------|
| [ADRC](/concepts/adrc.md) | Active Disturbance Rejection Control — estimate and cancel total disturbance each sample, then apply a simple outer controller. |
| [Critical Zone](/concepts/critical-zone.md) | Zone with the largest Zone Error among Zones with Heating Demand; diagnostics and logging only — never drives Set Water Temperature, TRV soft-close, or flame short-on trip. |
| [Extended State Observer](/concepts/extended-state-observer.md) | Observer that estimates plant output (or state) and an extra state for total disturbance — the sensing core of ADRC/LADRC. |
| [Flame short-on trip](/concepts/flame-short-on-trip.md) | Anti-cycle latch — short flame_on True duration under _flame_observe_gate forces SWT 0 after successful write∧hold; RAM-only (ADR 0008). |
| [LADRC](/concepts/ladrc.md) | Linear Active Disturbance Rejection Control — linear ESO plus linear state feedback; practical ADRC form with fewer tuning knobs. |
| [MADRC](/concepts/madrc.md) | Modified ADRC — delay the ESO’s command input with an inertia compensator so it stays synchronized with a high-order lag plant’s delayed output. |
| [Multi-Zone Coordinator](/concepts/multi-zone-coordinator.md) | App logic that computes Zone Error, Heating Demand, and Critical Zone selection; Critical Zone selection is diagnostics-only. Does not own the OpenTherm Set Water Temperature write, TRV soft-close, or flame trip. |
| [Outdoor Temperature](/concepts/outdoor-temperature.md) | Measured outdoor air T_out; required on the SWT demand path and a control_event listener (ADR 0008); not an input to flame observe. |
| [Plant](/concepts/plant.md) | Boiler and primary water circuit supplying heat to Zones, commanded via OpenTherm. |
| [RLS adaptive PID](/concepts/rls-adaptive-pid.md) | Historical RLS retune of Kp/Ki — not on the live water path; superseded by ADR 0008. |
| [Set Water Temperature](/concepts/set-water-temperature.md) | OpenTherm SWT from Weather Feedforward `round-to-0.1(clamp(u_ff))` with TRV soft-close and flame short-on (ADR 0008). |
| [Total disturbance](/concepts/total-disturbance.md) | ADRC’s lumped unknown — internal model error plus external loads — estimated by the ESO and cancelled in the control law. |
| [TRV soft-close](/concepts/trv-soft-close.md) | Commissioned Sonoff TRVs write valve_closure_degree before the Outdoor water prelude; house-idle floor + hold then 100 (ADR 0008). |
| [Zone](/concepts/zone.md) | Controllable heating area with a temperature reading and one or more HA climate thermostats, sharing boiler demand. |
| [Zone Error](/concepts/zone-error.md) | Difference between a Zone’s thermostat setpoint and that Zone’s current temperature. |
