---
type: Concept
title: RLS adaptive PID
description: Optional online retune of PID Kp/Ki via Recursive Least Squares; defaults off; yaml fixed gains when off or unhealthy.
tags: [pid, plant, adaptive]
timestamp: 2026-11-09T15:30:00Z
---

# RLS adaptive PID

**RLS adaptive PID** is the optional online retune of only **Kp** and **Ki** (derivative stays 0) on top of [ADR 0005](../../docs/adr/0005-fixed-pid-swt.md)’s fixed-PID Set Water Temperature law. `pid.adaptive` defaults **off**. When adaptive is on, `boiler_water` is required; off or unhealthy RLS uses yaml-commissioned fixed `kp` / `ki`. At most one RLS step per periodic `control_tick` — never on `control_event`.

Learned state lives in `rls_state.json` under the AppDaemon app directory, separate from PID ephemeral clears (∫ / `y_prev`). Idle / plant-off / no-valid-zones / weights-unusable do not wipe that file; reset learned state by deleting the JSON. The unhealthy/rails latch is process memory only (starts false after reload); JSON may restore adapted gains with latch false. Outdoor Temperature, Weather Feedforward, CAP-7, and `ff_auto_correct_state.json` stay off the water path.

## Related

- [/concepts/set-water-temperature.md](/concepts/set-water-temperature.md)
- [/concepts/plant.md](/concepts/plant.md)

# Citations

- [`CONTEXT.md`](../../CONTEXT.md) — PID
- [ADR 0006](../../docs/adr/0006-optional-rls-adaptive-pid.md) — optional RLS adaptive Kp/Ki
- [ADR 0005](../../docs/adr/0005-fixed-pid-swt.md) — fixed-PID SWT law
