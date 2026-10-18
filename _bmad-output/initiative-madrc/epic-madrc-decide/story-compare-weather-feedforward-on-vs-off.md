# Compare Weather Feedforward on vs off (R7)

## Never-disclaimer

This note is **unit/sim evidence** comparing Weather Feedforward on (`zero_uff=False`) vs `u_ff=0` (`zero_uff=True`) on Screen-3 metrics (M1/M2/M4/M6). It is **comparison language for later entry 6** (ADR outdoor-vs-scheduling and FF policy) — **not** an ADR verdict, **not** a policy lean, and **not** an R1 re-classification or `control_interval` recommendation. Relative “material” bar \(X=30\%\) is from the accepted metrics spike — relative Δ only.

Harness verifying-test pins (`K=0.45`, `T=300`, `n=3`, `b0=5e-4`, `ωc=0.03`, `ωo=0.03`, `dt=60`, `u_track_max=250`, \(N=40\), `reference=21`, FF config `base=25`, `slope=1.2`, `comfort_ref=20`) are starter fixtures, not house-calibrated truth. Within each outdoor row only `zero_uff` flips. Outdoor scenarios: **cold** `outdoor=0` (`u_ff=49` when FF-on); **hot** `outdoor=10` (`u_ff=37` when FF-on). Baseline = FF-on; candidate = `zero_uff=True`.

## Compare table

Metrics: M1 = max \|Δcommand\|; M2 = sample variance of `command`; M4 = \(\sum_t \lvert\texttt{reference}-y[t]\rvert\cdot\texttt{dt}\); M6 = sample variance of `command − u_ff`. \(\Delta_{\%}=100\cdot(M_{\text{FF-on}}-M_{\text{zero}})/|M_{\text{FF-on}}|\) (lower-is-better). Material iff \(\Delta_{\%} \ge X=30\%\).

| outdoor | mode | u_ff | M1 | Δ% M1 | mat? | M2 | Δ% M2 | mat? | M4 | Δ% M4 | mat? | M6 |
|---------|------|------|-----|-------|------|-----|-------|------|------|-------|------|-----|
| 0 | FF-on | 49 | 11.530 | — | — | 53.671 | — | — | 1914.237 | — | — | 53.671 |
| 0 | zero_uff | 0 | 11.530 | 0.00 | not | 53.671 | 0.00 | not | 1914.237 | 0.00 | not | 53.671 |
| 10 | FF-on | 37 | 11.530 | — | — | 53.671 | — | — | 1914.237 | — | — | 53.671 |
| 10 | zero_uff | 0 | 11.530 | 0.00 | not | 53.671 | 0.00 | not | 1914.237 | 0.00 | not | 53.671 |

On these verifying pins the setpoint clamp band dominates commanded SWT motion: FF-on and `zero_uff` series agree on M1/M2/M4 to reporting precision (Δ% ≈ 0 on both outdoors), so no material relative improvement vs \(X\). M6 equals M2 whenever `u_ff` is constant over the run (`var(command − c) = var(command)`).

## Residue-at-zero

On every `zero_uff=True` path, `u_ff` is all 0 and known-input residue observed as `command − 0` equals `command` (residue-at-zero = `command`). Documented for both cold and hot zero rows above; locked by harness `test_zero_uff_residue_is_command` and this module’s residue asserts.

## Citations

- Thresholds / Screen 3: `_bmad-output/initiative-madrc/epic-madrc-decide/spike-metrics-for-jump-madrc-and-ff-decisions.md` (accepted; X=30%; residue-at-zero; relative Δ only)
- Evidence module: `tests/test_r7_weather_feedforward_compare.py`
  - `test_cold_and_hot_finite_uff_and_residue_at_zero` — finite; cold/hot `u_ff` pins; residue-at-zero on zero paths
  - `test_screen3_metrics_match_artifact_absolutes_and_material_labels` — M1/M2/M4/M6 absolutes, Δ%, material-vs-X labels
  - `test_same_outdoors_replay_same_metrics_and_labels` — same outdoors × modes → same metrics + labels
- Verifying pins / residue continuity: `tests/test_plant_lag_harness.py` (`_example_aligned_config`, `test_zero_uff_residue_is_command`)
- Harness: `tests/harness/runner.py` (`run_closed_loop(..., zero_uff=)`), `tests/harness/plant.py` (`CascadeLagPlant`)
- FF formula (read-only): `apps/ha_smart_hvac/feedforward.py` (`weather_feedforward`)
