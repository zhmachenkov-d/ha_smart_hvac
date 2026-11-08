---
type: epic
title: "RLS retune of PID gains"
parent: initiative-pid
covers: ["R9"]
sources:
  - _bmad-output/initiative-pid/initiative-pid.md
  - _bmad-output/initiative-pid/source-user-pid-rls-example.md
companions:
  - _bmad-output/initiative-pid/tickets/epic-rls-pid-retune/rls-adaptive-algorithm.md
after: []
refined: true
risk: high
---

# RLS retune of PID gains

## Description

Adapt PID gains (Kp/Ki) online via RLS from plant/zone signals on top of the shipped fixed-gain SWT path, without restoring Weather Feedforward or CAP-7. Fixed-gain yaml remains the default-off fallback commission. Algorithm shape lives in the HOW companion.

## Outcome

Operators can enable RLS retune so Kp/Ki adapt under the same plant gates; with adaptive off or unhealthy, the house keeps commissioned fixed PID and never sees outdoor/FF on the water path.

## Requirements

1. **R1 (parent R9):** Under Plant Management on and Heating Demand, when adaptive retune is enabled and healthy, the App commands Set Water Temperature with the same `clamp(base_water_temp + u_pid)` law as fixed PID, using RLS-adapted **Kp** and **Ki** only; Weather Feedforward and CAP-7 remain absent from the SWT path and commissioning.
2. **R2 (parent R9):** Adaptive retune updates only Kp/Ki; RLS model/covariance state persists in a separate App JSON file; clearing PID ephemeral / water-path state does not clear that file.
3. **R3 (parent R9):** An RLS step runs only on `control_interval` ticks under the same demand gates as PID advance; no step while the plant entity is unavailable; event clear paths never step RLS.
4. **R4 (parent R9):** When adaptive is disabled or RLS is unhealthy, the App uses yaml-commissioned fixed `kp` / `ki` (fallback commission).
5. **R5 (parent R9):** Commission yaml exposes an adaptive on/off switch that defaults **off**.

## Constraints

1. **C1 (parent C2):** Implementation stays inside the AppDaemon `ha_smart_hvac` App writing the existing HA plant entity — no direct OpenTherm daemon or numpy process from the example.
2. **C2 (parent C4):** Derivative gain stays 0; zone weights remain yaml-commissioned.
3. **C3 (refine 2026-11-08):** RLS is ARX + forgetting RLS in pure Python per `rls-adaptive-algorithm.md`; `u` is last commanded SWT; `y` is commissioned boiler/plant water entity when present, else weight-normalized demand-zone air.

## Done when

1. With adaptive on and healthy, demand SWT uses RLS-adapted Kp/Ki under Plant Management / Heating Demand; Weather Feedforward and CAP-7 stay absent.
2. Adaptive off or unhealthy RLS falls back to yaml fixed `kp` / `ki`.
3. RLS state persists across clears of PID ephemeral state; idle / plant-off clear paths do not wipe the RLS file.
4. RLS steps only on `control_interval` when the plant is available; automated tests lock gates, fallback, persistence, and absence of weather on the path.
5. Domain docs for RLS (ADR/CONTEXT/AGENTS/`knowledge/` as needed) match the shipped adaptive path.

## Boundaries

Owns adaptive gain retune and its persistence/commission flag on top of fixed PID from epic 1. Does not restore outdoor/FF. Does not own the fixed-PID ADR language from epic 2 except RLS-specific doc lines this epic adds. Gain min/max rails and legacy-scale `ki` WARN/migrate are story-owned.

- Touch point: `apps/ha_smart_hvac/` — RLS step + gain apply on the existing PID SWT path; owner: this epic
- Touch point: `apps/apps.yaml` / `apps.yaml.example` — adaptive flag (default off); optional boiler-water entity for `y`; owner: this epic
- Touch point: App JSON RLS state file; owner: this epic
- Touch point: `docs/adr/`, `CONTEXT.md`, `AGENTS.md`, `knowledge/` — RLS-specific lines only; owner: this epic
- Must not change: Exclusive Session; Heating Demand definition; derivative gain stays 0 unless a later Decision revises parent C4

## References

- parent — `_bmad-output/initiative-pid/initiative-pid.md`, Requirement R9; Constraints C2, C4
- sibling — `_bmad-output/initiative-pid/tickets/epic-fixed-pid-swt/epic-fixed-pid-swt.md`
- source — `_bmad-output/initiative-pid/source-user-pid-rls-example.md`
- algorithm — `_bmad-output/initiative-pid/tickets/epic-rls-pid-retune/rls-adaptive-algorithm.md`

## Notes

- Waits on epic-fixed-pid-swt because: fixed PID module, yaml gains/weights, and tick-owned advance must exist to retune.
- Decision: RLS docs stay in this epic when refined; no `after` on epic-pid-domain-docs (2026-11-07).
- Decision: Refine accepted without spike/architecture/deep recon — product picks locked for Requirements (2026-11-08): RLS ARX pure Python; adapt Kp/Ki only; `u`=last SWT, `y`=boiler water entity if commissioned else weighted demand-zone air; separate JSON persistence; `pid.adaptive` default off with fixed-gain fallback; RLS step only on control tick when plant available; gain rails and legacy `ki` WARN left to stories.
- Decision: Tracer is entry 1 (config + RLS module + tick wiring, in-memory only); then 2 rails/unhealthy (least-certain; legacy-scale `ki` = WARN not ConfigError), 3 JSON persist, 4 RLS docs, 5 Refactor sweep; entry 1 waits on epic-fixed-pid-swt; declined opening refactor and closing e2e suite (pytest per story) (2026-11-08).
