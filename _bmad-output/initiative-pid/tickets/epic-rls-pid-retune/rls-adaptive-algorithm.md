# RLS adaptive algorithm (HOW companion)

Spec-authored companion for `epic-rls-pid-retune`. Requirements name outcomes; this file holds the agreed implementation shape from the 2026-11-08 refine.

## Model

- Recursor: ARX `y(k) = a₁·y(k−1) + b₀·u(k−1)`.
- Identifier: Recursive Least Squares with forgetting factor ≈ 0.98.
- Language: pure Python inside AppDaemon `ha_smart_hvac` — no numpy process (parent C2).
- Source sketch: `_bmad-output/initiative-pid/source-user-pid-rls-example.md` (historical intent; deviations already listed there).

## Signals

- `u(k)`: last commanded Set Water Temperature (rounded demand path).
- `y(k)`: boiler / plant water temperature from an existing Home Assistant entity when commissioned in yaml; otherwise the weight-normalized demand-zone air temperature already used by fixed PID.

## What adapts

- Only PID gains **Kp** and **Ki**. Derivative stays 0 (parent C4).
- Persisted RLS state: ARX coefficients and covariance (and any agreed bookkeeping the stories name). Not yaml gains.

## Persistence

- Separate JSON under the App data dir (same class of artifact as the removed `ff_auto_correct_state.json`).
- Clearing PID ephemeral / water-path state (idle / plant-off) must not delete or rewrite this file.

## Tick and gates

- One RLS step at most per `control_interval` tick, and only when Plant Management is on, Heating Demand is present, adaptive is enabled, and the plant entity is available.
- No RLS step on event clear paths.

## Commission

- Yaml flag (working name `pid.adaptive`) defaults **off**.
- Off or unhealthy RLS → use yaml-commissioned fixed `kp` / `ki`.
- Gain rails / WARN for legacy-scale `ki` are story-owned, not locked here.
