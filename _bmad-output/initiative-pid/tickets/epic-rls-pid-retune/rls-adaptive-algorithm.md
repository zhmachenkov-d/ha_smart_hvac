# RLS adaptive algorithm (HOW companion)

Spec-authored companion for `epic-rls-pid-retune`. Requirements name outcomes; this file holds the agreed implementation shape from the 2026-11-08 refine.

## Model

- Recursor: ARX `y(k) = a₁·y(k−1) + b₀·u(k−1)`.
- Identifier: Recursive Least Squares with forgetting factor ≈ 0.98; θ=`[a₁,b₀]`, φ=`[y_prev,u_prev]` (equations in the tracer plan Design Notes).
- Language: pure Python inside AppDaemon `ha_smart_hvac` — no numpy process (parent C2).
- Source sketch: `_bmad-output/initiative-pid/source-user-pid-rls-example.md` (historical intent; deviations already listed there).

## Signals

- `u(k)`: last commanded Set Water Temperature on the **demand** path (idle/plant-off/no-valid-zones write of 0 must not become `u`; equal-float demand skip still updates `u`).
- `y(k)`: boiler / plant water temperature from top-level yaml `boiler_water` (required when `pid.adaptive` is on — ConfigError at parse if missing/whitespace). Not demand-zone air (party 2026-11-08).

## What adapts

- Only PID gains **Kp** and **Ki**. Derivative stays 0 (parent C4).
- Persisted RLS state: ARX coefficients and covariance (and any agreed bookkeeping the stories name). Not yaml gains.

## Persistence

- Separate JSON under the App data dir (same class of artifact as the removed `ff_auto_correct_state.json`).
- Clearing PID ephemeral / water-path state (idle / plant-off / no-valid-zones / weights-unusable) must not delete or rewrite this file; in-memory θ/P and last-good gains likewise survive clears, but `y_prev` is cleared so the next tick is seed-only (no idle-spanning RLS sample).

## Tick and gates

- One RLS step at most per `control_interval` tick, and only when Plant Management is on, Heating Demand is present, adaptive is enabled, the plant setpoint entity is available, and prior demand `u` + prior `y_prev` exist with finite current `y`.
- No RLS step on `control_event` paths (clear or demand-still-true).

## Commission

- Yaml flag (working name `pid.adaptive`) defaults **off** (YAML bool only).
- When adaptive is on, `boiler_water` must be a strip-nonempty entity id (ConfigError otherwise); when adaptive is off, `boiler_water` may be omitted.
- Off or unhealthy RLS → use yaml-commissioned fixed `kp` / `ki` (unhealthy/rails story-owned).
- Gain rails / WARN for legacy-scale `ki` are story-owned, not locked here.
