---
type: Concept
title: TRV soft-close
description: Commissioned Sonoff TRVs write valve_closure_degree before the Outdoor water prelude; plant-off max-close keeps overshoot latch (ADR 0008).
tags: [trv, plant, zone]
timestamp: 2026-11-17T12:00:00Z
---

# TRV soft-close

**TRV soft-close** is the App’s commissioned Sonoff TRV law under [ADR 0008](../../docs/adr/0008-weather-curve-trv-flame-swt.md): write only `valve_closure_degree` (never `valve_opening_degree`), and run `_apply_trv_law` **before** `_gate_prelude` / the Outdoor water prelude on `control_tick`, `control_event`, and flame hold expiry ([`adr-trv-before-water-prelude`](../../docs/decisions/adr-trv-before-water-prelude.md)).

Flame observe / latch handlers do **not** run `_apply_trv_law`. [Critical Zone](/concepts/critical-zone.md) never drives TRV.

## Plant-off vs plant-on

- **Plant Management off:** every commissioned TRV gets closure `100` **without** clearing `_trv_overshoot_latched` ([`adr-trv-plant-off-no-latch-clear`](../../docs/decisions/adr-trv-plant-off-no-latch-clear.md)). No [Set Water Temperature](/concepts/set-water-temperature.md) write on plant-off.
- **Plant Management on:** floor / overshoot-to-100 hysteresis is **write-gated** ([`adr-trv-write-gated-overshoot-latch`](../../docs/decisions/adr-trv-write-gated-overshoot-latch.md)) — overshoot latches only after a successful closure-100 write; clear to floor discards the latch only after a successful floor write.

## Accuracy listen

When a thermostat `accuracy` entity is commissioned, it listens on the same shared `control_event` path as other CAP-8 inputs ([`adr-trv-accuracy-shared-control-event`](../../docs/decisions/adr-trv-accuracy-shared-control-event.md)) — re-evaluate TRV then Outdoor-gated water, not a separate TRV-only loop.

## Related

- [/concepts/set-water-temperature.md](/concepts/set-water-temperature.md)
- [/concepts/flame-short-on-trip.md](/concepts/flame-short-on-trip.md)

# Citations

- [`CONTEXT.md`](../../CONTEXT.md) — TRV soft-close
- [ADR 0008](../../docs/adr/0008-weather-curve-trv-flame-swt.md) — live water law (TRV before prelude)
- [`docs/decisions/adr-trv-before-water-prelude.md`](../../docs/decisions/adr-trv-before-water-prelude.md)
- [`docs/decisions/adr-trv-write-gated-overshoot-latch.md`](../../docs/decisions/adr-trv-write-gated-overshoot-latch.md)
- [`docs/decisions/adr-trv-plant-off-no-latch-clear.md`](../../docs/decisions/adr-trv-plant-off-no-latch-clear.md)
- [`docs/decisions/adr-trv-accuracy-shared-control-event.md`](../../docs/decisions/adr-trv-accuracy-shared-control-event.md)
