---
type: Concept
title: Set Water Temperature
description: OpenTherm boiler water setpoint from Weather Feedforward demand round-to-0.1(clamp(u_ff)) with TRV soft-close and flame short-on under ADR 0008.
tags: [plant, opentherm]
timestamp: 2026-11-17T12:00:00Z
---

# Set Water Temperature

**Set Water Temperature** is the OpenTherm boiler water setpoint the App commands on the [Plant](/concepts/plant.md) (the boiler’s target water temperature via OpenTherm).

Not the same as a Zone thermostat air setpoint or a mixer setpoint.

The HVAC App owns this write. Under Plant Management and Heating Demand (and when the flame trip is not latched), demand is `round-to-0.1(clamp(u_ff))` with `u_ff = base + slope × (comfort_ref − T_out)` from yaml Weather Feedforward (`base`, `slope`, `comfort_ref`). [Outdoor Temperature](/concepts/outdoor-temperature.md) is required on the demand path and is a `control_event` listener that re-evaluates the same Outdoor-gated demand writer as periodic `control_tick`. `initialize` runs one full `control_tick` after scheduling; tick and every eligible `control_event` run [TRV soft-close](/concepts/trv-soft-close.md) then the Outdoor prelude and may rewrite demand SWT (not a one-shot rising-edge demand latch). Event-path writes must not reset or reschedule `control_interval`. Plant-off → no Set Water Temperature write and clear flame trip state (`_clear_flame_trip_state`), not “write 0” (TRV soft-close still applies). Plant-on non-demand exits (including non-finite `u_ff`) → idle write `0` with Decision C flame handling. The write throttle is equal-float skip on plant readback; unreadable or non-finite plant readback skips the write.

**Dual-gate:** Outdoor / `control_tick` / `control_event` use `_gate_prelude` (Plant on, readable Outdoor, valid zones, Heating Demand). Flame observe uses `_flame_observe_gate` only (Plant∧Demand∧`ch_active` on∧¬latch) — never Outdoor.

Live anti-cycle depth lives on the companions: [TRV soft-close](/concepts/trv-soft-close.md) and [flame short-on trip](/concepts/flame-short-on-trip.md). While `_flame_trip_latched`, demand keeps writing `0` (no curve / no Critical Zone select-log).

The [Multi-Zone Coordinator](/concepts/multi-zone-coordinator.md) does not own this write. [Critical Zone](/concepts/critical-zone.md) is diagnostics-only and must not drive this setpoint, TRV soft-close, or the flame short-on trip.

CAP-7 rise-rate auto-correct, adapting `base`/`slope`, and `ff_auto_correct_state.json` are **not** on the water path, must not be commissioned, and are out of scope. Fixed-gain PID on zone air error, ∫, optional [RLS adaptive PID](/concepts/rls-adaptive-pid.md), and LADRC-on-water are **removed** from the live path — **superseded by ADR 0008** (ADR 0004–0006 are historical prior art). ADR 0007’s supply rise-rate trip era is historical; live anti-cycle is flame short-on + TRV soft-close.

# Citations

- [`CONTEXT.md`](../../CONTEXT.md) — Set Water Temperature, Weather Feedforward
- [ADR 0008](../../docs/adr/0008-weather-curve-trv-flame-swt.md) — live weather-curve SWT + TRV soft-close + flame short-on
- [ADR 0007](../../docs/adr/0007-weather-curve-supply-trip-swt.md) — historical weather-curve + supply rise-rate trip (superseded)
- [ADR 0005](../../docs/adr/0005-fixed-pid-swt.md) — historical fixed-PID SWT (superseded)
- [ADR 0006](../../docs/adr/0006-optional-rls-adaptive-pid.md) — historical optional RLS (superseded)
