---
type: Concept
title: TRV soft-close
description: Commissioned Sonoff TRVs write valve_closure_degree before the Outdoor water prelude; house-idle floor + hold then 100 (ADR 0008).
tags: [trv, plant, zone]
timestamp: 2026-11-20T12:00:00Z
---

# TRV soft-close

**TRV soft-close** is the App’s commissioned Sonoff TRV law under [ADR 0008](../../docs/adr/0008-weather-curve-trv-flame-swt.md): write only `valve_closure_degree` (never `valve_opening_degree`), and run `_apply_trv_law` **before** `_gate_prelude` / the Outdoor water prelude on `control_tick`, `control_event`, and flame hold expiry ([`adr-trv-before-water-prelude`](../../docs/decisions/adr-trv-before-water-prelude.md)). Soft-close hold expiry writes closure `100` while still all-idle and does **not** run the Outdoor prelude.

**Limit semantics** (not stem position): `valve_closure_degree` is the max close allowed while the TRV is in **idle**; `valve_opening_degree` is the max open allowed while in **heating**. Raising closure does not choke an active heating open — heating max-open stays with the TRV.

Sonoff TRV mappings are **closure-only**; a leftover yaml `accuracy` key is a `ConfigError`. The App does not register accuracy listeners for soft-close. Flame observe / latch handlers do **not** run `_apply_trv_law`. [Critical Zone](/concepts/critical-zone.md) never drives TRV.

## Plant-off vs plant-on

- **Plant Management off:** every commissioned TRV gets closure `100` and any soft-close hold is cancelled. No [Set Water Temperature](/concepts/set-water-temperature.md) write on plant-off.
- **Plant Management on:** first observe of house all-idle writes yaml `valve_closure_floor` (default **80**) and arms one soft-close hold of yaml `trv_soft_close_hold_s` (default **300**); while still all-idle with that hold active, later ticks/events do not re-arm. Hold expiry while idle writes closure `100` and stays at `100` without re-flooring; orphan/token-mismatch expiry is a no-op. Any Heating Demand (cold start, rising-edge, or sustained) writes closure `100` and cancels or never arms the hold. Return to all-idle writes floor again and arms a new hold.

## Related

- [/concepts/set-water-temperature.md](/concepts/set-water-temperature.md)
- [/concepts/flame-short-on-trip.md](/concepts/flame-short-on-trip.md)

# Citations

- [`CONTEXT.md`](../../CONTEXT.md) — TRV soft-close
- [ADR 0008](../../docs/adr/0008-weather-curve-trv-flame-swt.md) — live water law (house-idle soft-close)
- [`docs/decisions/adr-trv-before-water-prelude.md`](../../docs/decisions/adr-trv-before-water-prelude.md)
