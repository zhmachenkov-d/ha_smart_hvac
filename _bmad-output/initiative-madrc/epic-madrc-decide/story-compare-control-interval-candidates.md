# Compare control_interval candidates (R3)

## Never-disclaimer

This note is **unit/sim evidence** comparing `ladrc_config.dt` candidates under fixed example gains and production Euler/ωo/substep coupling (`_ESO_EULER_SUBSTEPS=2`). The sample period in sim is `ladrc_config.dt` only; the recommendation maps 1:1 to AppDaemon `control_interval` for **later** story 1.8 — this story does **not** write YAML, house-calibration, CONTEXT, or an ADR. Relative “material” bar \(X=30\%\) and latch floor \(Z=0.2\) are comparison language from the accepted metrics spike — not an ADR go/no-go, not an R1 re-classification, and not an R7 FF keep/drop.

Harness verifying-test pins (`K=0.45`, `T=300`, `n=3`, FF-on, `b0=5e-4`, `ωc=0.03`, `ωo=0.03`, `u_track_max=250`, \(N=40\)) are starter fixtures, not house-calibrated truth. Baseline = `dt=60` (`_example_aligned_config` / story-1). Only `dt` varies across candidates.

## Candidate table

Euler factor \(\rho = |1 - 2\cdot h\cdot\omega_o|\) with \(h = dt/2\) (production `_ESO_EULER_SUBSTEPS=2`); stable band \(\rho < 1\). Candidate is **stable** iff Euler-band stable **and** harness series stay finite. Metrics: M1 = max \|Δcommand\|; M2 = sample variance of `command`; M3 = mean(`latch`). \(\Delta_{\%}=100\cdot(M_{60}-M_c)/|M_{60}|\) (lower-is-better).

| dt (s) | Euler ρ | Euler-stable? | Finite? | Stable? | M1 | Δ% M1 | M2 | Δ% M2 | M3 |
|--------|---------|---------------|---------|---------|-----|-------|-----|-------|-----|
| 30 | 0.10 | yes | yes | yes | 7.121 | +38.23 | 54.210 | −1.00 | 0.000 |
| 60 | 0.80 | yes | yes | yes (baseline) | 11.530 | 0.00 | 53.671 | 0.00 | 0.000 |
| 120 | 2.60 | **no** | yes | **reject** | 15.000 | −30.10 | 39.605 | +26.22 | 0.300 |

### Euler-band notes

- Authority: `apps/ha_smart_hvac/ladrc.py` `_ESO_EULER_SUBSTEPS=2`; `docs/house-calibration.md` §4 — stability needs `|1 − 2·h·ωo| < 1` with `h = dt/2`; at `dt=60`, `ωo` below `1/30 ≈ 0.033`. Raising `control_interval` without lowering `ωo` (or deriving substeps from `ωo·dt`) is a documented footgun.
- **F-R8** (`epic-fix-ladrc-blow-up` retrospective): fixed `_ESO_EULER_SUBSTEPS=2` does not scale with `dt`/`ωo`; `dt=120`, `ωo=0.03` unstable. Disposition deferred there; this table confirms reject at example `ωo` — do **not** invent an `ωo` retune or substep code change in this story.
- At `dt=120`, series happened to stay finite (latch duty M3=0.300 ≥ Z) but Euler ρ=2.6 ≥ 1 → still **unstable / never recommend**.

## Recommendation

**Recommendation: recommend 30**

Rationale: among Euler-stable candidates with M3&lt;Z, `dt=30` shows material M1 improvement vs baseline 60 (Δ% M1 ≈ +38.23 ≥ X=30%); M2 is not material (Δ% ≈ −1.00). Rule: best by M1 then M2 among material winners → **30**. Keep-60 would apply only if no stable candidate cleared X on M1 or M2. Never recommend 120 without `ωo`↓ or substep code change (out of scope).

This recommendation is evidence for later story 1.8 (YAML / house-calibration apply) — **not** applied here.

## Citations

- Thresholds: `_bmad-output/initiative-madrc/epic-madrc-decide/spike-metrics-for-jump-madrc-and-ff-decisions.md` (accepted; X=30%; Z=0.2)
- Euler / calibration: `docs/house-calibration.md` §2–4; `apps/ha_smart_hvac/ladrc.py` (`_ESO_EULER_SUBSTEPS=2`)
- F-R8: `_bmad-output/initiative-fix-ladrc-blow-up/epic-fix-ladrc-blow-up/epic-fix-ladrc-blow-up-retrospective.md`
- Evidence module: `tests/test_r3_control_interval_candidates.py`
  - `test_candidates_euler_labels_and_finite_series` — Euler labels + finite for 30/60; reject 120
  - `test_recommendation_rule_matches_artifact` — recommendation rule → 30
  - `test_same_dts_replay_same_stability_and_recommendation` — same dts → same labels + recommendation
- Verifying baseline pins: `tests/test_plant_lag_harness.py` (`_example_aligned_config`, FF-on)
- Harness: `tests/harness/runner.py` (`run_closed_loop`), `tests/harness/plant.py` (`CascadeLagPlant`)
