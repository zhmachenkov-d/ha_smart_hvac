---
type: Concept
title: Set Water Temperature
description: OpenTherm boiler water setpoint from Weather Feedforward demand round-to-0.1(clamp(u_ff)) with supply rise-rate trip under ADR 0007.
tags: [plant, opentherm]
timestamp: 2026-11-14T14:53:00Z
---

# Set Water Temperature

**Set Water Temperature** is the OpenTherm boiler water setpoint the App commands on the [Plant](/concepts/plant.md) (the boiler’s target water temperature via OpenTherm).

Not the same as a Zone thermostat air setpoint or a mixer setpoint.

The HVAC App owns this write. Under Plant Management and Heating Demand gates, demand is `round-to-0.1(clamp(u_ff))` with `u_ff = base + slope × (comfort_ref − T_out)` from yaml Weather Feedforward (`base`, `slope`, `comfort_ref`). [Outdoor Temperature](/concepts/outdoor-temperature.md) is required on the demand path and is a `control_event` listener that re-evaluates the same Outdoor-gated demand writer as periodic `control_tick`. `initialize` runs one full `control_tick` after scheduling; tick and every eligible `control_event` may rewrite demand SWT (not a one-shot rising-edge demand latch). Event-path writes must not reset or reschedule `control_interval`. Plant-off → no Set Water Temperature write and clear supply-trip state (`_clear_trip_state`), not “write 0”. Plant-on non-demand exits (including non-finite `u_ff`) → idle write `0` with Decision C trip handling. The write throttle is equal-float skip on plant readback; unreadable or non-finite plant readback skips the write.

**Dual-gate:** Outdoor / `control_tick` / `control_event` use `_gate_prelude` (Plant on, readable Outdoor, valid zones, Heating Demand). `supply_event` uses Plant∧Heating Demand only — never Outdoor prelude.

**Supply rise-rate trip:** On `supply_event`, observed supply rise rate `r_obs` (°C/min) vs yaml `r_max`. When `r_obs > r_max`, the App attempts SWT write `0`; the trip **latches only after that write succeeds**. While latched, demand keeps writing `0`. Latch clears on hold expiry (then Outdoor prelude + demand when prelude returns zones), per-zone Heating Demand rising edge under `_gate_prelude`, and on successful idle write `0` after a Plant-on non-demand exit (Decision C — failed idle write keeps latch).

The [Multi-Zone Coordinator](/concepts/multi-zone-coordinator.md) does not own this write. [Critical Zone](/concepts/critical-zone.md) is diagnostics-only and must not drive this setpoint or the supply trip.

CAP-7 rise-rate auto-correct, adapting `base`/`slope`, and `ff_auto_correct_state.json` are **not** on the water path, must not be commissioned, and are out of scope. Fixed-gain PID on zone air error, ∫, optional [RLS adaptive PID](/concepts/rls-adaptive-pid.md), and LADRC-on-water are **removed** from the live path — **superseded by ADR 0007** (ADR 0004–0006 are historical prior art).

# Citations

- [`CONTEXT.md`](../../CONTEXT.md) — Set Water Temperature, Weather Feedforward
- [ADR 0007](../../docs/adr/0007-weather-curve-supply-trip-swt.md) — live weather-curve SWT + supply rise-rate trip
- [ADR 0005](../../docs/adr/0005-fixed-pid-swt.md) — historical fixed-PID SWT (superseded)
- [ADR 0006](../../docs/adr/0006-optional-rls-adaptive-pid.md) — historical optional RLS (superseded)
