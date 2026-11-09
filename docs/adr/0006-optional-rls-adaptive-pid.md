---
status: accepted
---

# Optional RLS adaptive PID gains

On top of ADR 0005’s fixed-PID Set Water Temperature law, the HVAC App may optionally retune only **Kp** and **Ki** online via Recursive Least Squares when `pid.adaptive` is enabled. The SWT command stays `round-to-0.1(clamp(base_water_temp + u_pid))`; Outdoor Temperature, Weather Feedforward, CAP-7 rise-rate auto-correct, and `ff_auto_correct_state.json` remain off the water path.

## Commission

`pid.adaptive` is optional and defaults **off** (YAML bool). When adaptive is on, top-level `boiler_water` must be a strip-nonempty entity id (ConfigError at parse otherwise); when adaptive is off, `boiler_water` may be omitted. Derivative stays 0. Off or unhealthy RLS uses yaml-commissioned fixed `kp` / `ki`.

## Tick-only step

At most one RLS step per periodic `control_interval` (`control_tick`), and only under Plant Management on, Heating Demand present, adaptive enabled, plant setpoint available, and finite prior demand `u` / `y_prev` with finite current `y`. No RLS step on `control_event` paths.

## Persistence

Learned RLS state lives in `rls_state.json` under the AppDaemon app directory — separate from PID ephemeral clears (∫ / `y_prev`). Idle, plant-off, no-valid-zones, and weights-unusable clear PID ephemeral / water-path state and must not delete or rewrite this file. Reset learned state by deleting the JSON; do not disable `adaptive` to reset. After reload, JSON may restore θ/P and adapted gains with the unhealthy/rails latch false — that latch is process memory only and starts false after reload.

## Out of scope

Weather Feedforward / CAP-7 / Outdoor on the water path; ARX / λ / rails equation tables (see the epic planning companion); changing ADR 0005’s fixed-PID gate, tick vs event, anti-windup, or Critical Zone diagnostics-only law.
