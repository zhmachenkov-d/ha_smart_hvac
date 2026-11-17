---
type: Concept
title: Flame short-on trip
description: Anti-cycle latch — short flame_on True duration under _flame_observe_gate forces SWT 0 after successful write∧hold; RAM-only; clears on hold/zone/plant-off/Decision C (ADR 0008).
tags: [flame, plant, anti-cycle]
timestamp: 2026-11-17T12:00:00Z
---

# Flame short-on trip

**Flame short-on trip** is live anti-cycle protection under [ADR 0008](../../docs/adr/0008-weather-curve-trv-flame-swt.md). Short-on = `flame_on` True duration `< flame_on_min_s` on a True→False fall while `_flame_observe_gate` holds.

## Observe gate

`_flame_observe_gate` = Plant Management on ∧ Heating Demand ∧ `ch_active` on ∧ ¬`_flame_trip_latched` — **never Outdoor** ([`adr-flame-observe-gate-no-outdoor`](../../docs/decisions/adr-flame-observe-gate-no-outdoor.md)). Flame observe does not call `_gate_prelude`.

## Latch

Latch `_flame_trip_latched` only after a successful trip [Set Water Temperature](/concepts/set-water-temperature.md) write `0` **and** hold `run_in` scheduled ([`adr-write-gated-flame-latch`](../../docs/decisions/adr-write-gated-flame-latch.md)). Latch / since / hold live in process **RAM-only**; while latched, flame / `ch_active` observers wipe `since` only and do **not** re-assert SWT ([`adr-flame-latch-ram-only-no-reassert`](../../docs/decisions/adr-flame-latch-ram-only-no-reassert.md)). Latched demand keeps writing `0` (no curve / no Critical Zone select-log).

[Critical Zone](/concepts/critical-zone.md) never drives the flame trip.

## Clear paths

- **Hold expiry:** clear latch, `_apply_trv_law`, then Outdoor `_gate_prelude` + demand when prelude returns zones ([`adr-flame-hold-expiry-trv-then-prelude`](../../docs/decisions/adr-flame-hold-expiry-trv-then-prelude.md)).
- **Zone Heating Demand rising-edge** under `_gate_prelude`: `_clear_flame_trip_state`.
- **Plant-off:** `_clear_flame_trip_state` (no SWT write).
- **Decision C idle:** `_go_idle` always disarms hold; clears `_flame_trip_latched` only after successful idle write `0` — write-fail keeps the latch ([`adr-idle-flame-clear-after-write`](../../docs/decisions/adr-idle-flame-clear-after-write.md)).

## Related

- [/concepts/set-water-temperature.md](/concepts/set-water-temperature.md)
- [/concepts/trv-soft-close.md](/concepts/trv-soft-close.md)

# Citations

- [`CONTEXT.md`](../../CONTEXT.md) — Flame short-on trip
- [ADR 0008](../../docs/adr/0008-weather-curve-trv-flame-swt.md) — live water law (flame short-on)
- [`docs/decisions/adr-flame-observe-gate-no-outdoor.md`](../../docs/decisions/adr-flame-observe-gate-no-outdoor.md)
- [`docs/decisions/adr-write-gated-flame-latch.md`](../../docs/decisions/adr-write-gated-flame-latch.md)
- [`docs/decisions/adr-flame-latch-ram-only-no-reassert.md`](../../docs/decisions/adr-flame-latch-ram-only-no-reassert.md)
- [`docs/decisions/adr-flame-hold-expiry-trv-then-prelude.md`](../../docs/decisions/adr-flame-hold-expiry-trv-then-prelude.md)
- [`docs/decisions/adr-idle-flame-clear-after-write.md`](../../docs/decisions/adr-idle-flame-clear-after-write.md)
