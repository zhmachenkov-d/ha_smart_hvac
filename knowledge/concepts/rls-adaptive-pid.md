---
type: Concept
title: RLS adaptive PID
description: Historical optional online retune of PID Kp/Ki via RLS — not on the live water path; superseded by ADR 0007 weather-curve SWT.
tags: [pid, plant, adaptive, historical]
timestamp: 2026-11-14T14:53:00Z
---

# RLS adaptive PID

## Project note

RLS adaptive PID is **not on the live water path** — **superseded by ADR 0007**. Live [Set Water Temperature](/concepts/set-water-temperature.md) is Weather Feedforward `round-to-0.1(clamp(u_ff))` with supply rise-rate trip under Plant Management and Heating Demand. ADR 0005 (fixed-PID SWT) and ADR 0006 (optional RLS) are historical prior art only. The mechanics below describe what the App *used* to support; do not commission `pid.adaptive` or `rls_state.json` on the current path.

---

**RLS adaptive PID** was the optional online retune of only **Kp** and **Ki** (derivative stays 0) on top of [ADR 0005](../../docs/adr/0005-fixed-pid-swt.md)’s fixed-PID Set Water Temperature law. `pid.adaptive` defaulted **off**. When adaptive was on, `boiler_water` was required; off or unhealthy RLS used yaml-commissioned fixed `kp` / `ki`. At most one RLS step per periodic `control_tick` — never on `control_event`.

Learned state lived in `rls_state.json` under the AppDaemon app directory, separate from PID ephemeral clears (∫ / `y_prev`). Idle / plant-off / no-valid-zones / weights-unusable did not wipe that file; reset learned state by deleting the JSON. The unhealthy/rails latch was process memory only (starts false after reload); JSON could restore adapted gains with latch false. CAP-7 / `ff_auto_correct_state.json` were never on the live water path after ADR 0007.

## Related

- [/concepts/set-water-temperature.md](/concepts/set-water-temperature.md)
- [/concepts/plant.md](/concepts/plant.md)

# Citations

- [`CONTEXT.md`](../../CONTEXT.md) — Weather Feedforward (live); PID terms historical
- [ADR 0007](../../docs/adr/0007-weather-curve-supply-trip-swt.md) — live SWT law
- [ADR 0006](../../docs/adr/0006-optional-rls-adaptive-pid.md) — historical optional RLS adaptive Kp/Ki
- [ADR 0005](../../docs/adr/0005-fixed-pid-swt.md) — historical fixed-PID SWT law
