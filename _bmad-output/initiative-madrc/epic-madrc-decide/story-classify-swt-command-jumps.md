# Classify SWT command jumps (R1)

## Never-disclaimer

This note is a **unit/sim classification** of commanded Set Water Temperature jumps under the accepted Screen-2 protocol (`spike-metrics-for-jump-madrc-and-ff-decisions.md`). It is **not** an ADR go/no-go, **not** a Weather Feedforward keep/drop recommendation, and **not** a `control_interval` recommendation.

Sample period in these ablations is varied via `ladrc_config.dt` only (plant stepped with the same `dt`). AppDaemon `control_interval` is unchanged by this story. Relative “material” bar \(X=30\%\) is comparison language only — **not** an R1 pick gate. Ranking uses \(\varepsilon=10\) pp and latch floor \(Z=0.2\).

Harness verifying-test pins (`K=0.45`, etc.) are starter fixtures, not house-calibrated truth. Baseline = FF-on verifying pins from `tests/test_plant_lag_harness.py` / `_example_aligned_config` shape.

## R1 verdict

**Class (c)** — plant-lag family wins Screen 2 (M2 pick; no M1/M5 pick; no M3≥Z; no cross-metric conflict).

## Ablation table

One knob at a time vs the verifying baseline (FF-on). Metrics: M1 = max \|Δcommand\|; M2 = sample variance of `command`; M3 = mean(`latch`); M5 = Pearson corr(`z1`, `y`). \(\Delta_{\%}=100\cdot(M_b-M_c)/|M_b|\) (M5 inverted as higher-is-better).

| Run | Family | Knob | M1 | Δ% M1 | M2 | Δ% M2 | M3 | M5 | Δ% M5 |
|-----|--------|------|-----|-------|-----|-------|-----|-----|-------|
| baseline | — | verifying pins (`dt=60`, `n=3`, `T=300`, `b0=5e-4`, `ωc=0.03`, `ωo=0.03`) | 11.530 | — | 53.671 | — | 0.000 | 0.99936 | — |
| tuning_omega_c_0.08 | tuning | `omega_c=0.08` | 15.000 | −30.10 | 56.069 | −4.47 | 0.000 | 0.99935 | −0.00 |
| tuning_b0_1e-3 | tuning | `b0=1e-3` | 10.930 | +5.20 | 52.475 | +2.23 | 0.000 | 0.99937 | +0.00 |
| dt_30 | dt | `ladrc_config.dt=30` | 7.121 | +38.23 | 54.210 | −1.00 | 0.000 | 0.99852 | −0.08 |
| plant_n_8 | plant | plant `n=8` | 10.205 | +11.48 | 38.785 | +27.74 | 0.000 | 0.99997 | +0.06 |
| plant_T_600 | plant | plant `T=600` | 9.653 | +16.28 | 55.418 | −3.25 | 0.000 | 0.99986 | +0.05 |

## \|Δ%\| summary (family max per metric)

| Metric | tuning | dt | plant | Pick (lead ≥ ε=10 pp) |
|--------|--------|-----|-------|------------------------|
| M1 | 30.10 | 38.23 | 16.28 | none (dt−tuning lead ≈ 8.13 < ε) |
| M2 | 4.47 | 1.00 | 27.74 | **plant** (lead ≈ 23.27 ≥ ε) |
| M5 | 0.00 | 0.08 | 0.06 | none |

Screen 2: M3 gate clear → M1 no pick → M2 picks **plant** → M5 no conflicting pick → class **(c)**.

## Citations

- Protocol / thresholds: `_bmad-output/initiative-madrc/epic-madrc-decide/spike-metrics-for-jump-madrc-and-ff-decisions.md` (accepted; ε=10; Z=0.2; X not a pick gate).
- Evidence module: `tests/test_r1_jump_classification.py`
  - `test_recorded_ablations_finite_and_screen2_class_c` — finite series + Screen-2 outcome **(c)** on the knobs above
  - `test_same_recorded_knobs_replay_same_screen2_outcome` — same knobs → same Screen-2 outcome
- Verifying baseline pins: `tests/test_plant_lag_harness.py` (`_example_aligned_config`, FF-on)
- Harness: `tests/harness/runner.py` (`run_closed_loop`), `tests/harness/plant.py` (`CascadeLagPlant`)
