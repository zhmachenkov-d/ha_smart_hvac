---
title: 'Compare control_interval candidates'
type: 'feature'
ticket: '4'
created: '2026-10-18'
status: done
baseline_revision: '67fa9dc9171d9b56334a2f72ca316c4353f8b29f'
route: 'full'
route_source: 'auto'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
followup_review_recommended: false
context:
  - '{project-root}/_bmad-output/initiative-madrc/epic-madrc-decide/spike-metrics-for-jump-madrc-and-ff-decisions.md'
  - '{project-root}/docs/house-calibration.md'
  - '{project-root}/_bmad-output/initiative-madrc/initiative-madrc.md'
warnings: []
deferred: []
---

<intent-contract>

## Intent

**Problem:** R3 needs unit/sim evidence comparing `control_interval` candidates under the fixed Euler/ωo/substep coupling before any config or ADR apply.

**Approach:** Run the shared harness at candidate `ladrc_config.dt` values with example-aligned gains, record Euler-band status plus M1/M2/M3, and write a recommendation artifact only (keep 60 or a stable alternative) — do not change production config.

**Decisions:**
- Candidates (fixed set): **30, 60, 120** seconds. Baseline = verifying pins at `dt=60` (`_example_aligned_config` / story-1). Same FF-on plant pins as R1.
- Sample period in sim = `ladrc_config.dt` only; recommendation maps 1:1 to AppDaemon `control_interval` for later story 1.8 — this story does **not** write YAML/calibration.
- Euler gate (production `_ESO_EULER_SUBSTEPS=2`, example `ωo=0.03`): candidate is **stable** iff `|1 − 2·h·ωo| < 1` with `h = dt/2`, **and** harness series stay finite over N=40. Unstable → document reject; never recommend.
- Metrics: reuse R1 formulas M1/M2/M3 (M5 optional appendix). Material bar **X=30%** improvement Δ% vs baseline 60 for M1/M2; latch floor **Z=0.2** — if M3≥Z at a candidate, do not recommend it.
- Recommendation rule: among **stable** candidates with M3&lt;Z, if any shows material M1 **or** M2 improvement vs 60 → recommend the best by M1 then M2; else **keep 60**. Never recommend 120 without ωo↓ or substep code change (out of scope).
- Artifact + epic Notes pointer; own test module (do not break harness/R1/CAP-5).

## Boundaries & Constraints

**Always:**
- Fixed example `ωo=0.03`, `b0=5e-4`, `ωc=0.03`, `u_track_max=250`, plant `(K=0.45,T=300,n=3)`, N=40, FF-on — only `dt` varies across candidates.
- Artifact: Never-disclaimer → candidate table (dt, Euler factor, stable?, M1/M2/M3, Δ% vs 60) → one recommendation line with rationale → test citations; epic Notes points at it.
- Cite house-calibration Euler band prose and `ladrc.py` `_ESO_EULER_SUBSTEPS=2` as the stability authority; F-R8 (`dt=120` unstable) must appear as a band note.

**Never:**
- No edits to `apps.yaml` / `apps.yaml.example` / `house-calibration.md` / CONTEXT / ADR (story 1.8 / 1.6).
- No change to `_ESO_EULER_SUBSTEPS`, production ESO math, or example `ωo`.
- No R1 re-classification, no R7 FF keep/drop, no MADRC \(G_{cp}\), no Exclusive Session.
- No shared `tests/harness/metrics.py` (duplicate M1/M2/M3 in the R3 module or import from R1 only if already public — prefer local copies to avoid coupling).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Candidate dt=30 | Example gains, verifying plant | Euler stable; finite series; M1/M2/M3 + Δ% vs 60 recorded | Assert finite |
| Candidate dt=60 | Baseline pins | Euler stable; metrics are baseline (Δ%=0) | Assert finite |
| Candidate dt=120 | Same ωo=0.03, n_sub=2 | Euler **unstable** and/or non-finite → reject; never recommend | Record reject; do not invent ωo retune |
| Recommendation | Stable table + X/Z rules | One line: keep 60 **or** a stable material winner | N/A |
| Re-run recorded dts | Same candidate set in test module | Same stability labels + same recommendation outcome | N/A |

</intent-contract>

## Code Map

- `tests/harness/runner.py` — `run_closed_loop` / `ClosedLoopSeries`; vary only `ladrc_config.dt`.
- `tests/harness/plant.py` — `CascadeLagPlant`; shares `dt` from config.
- `tests/test_plant_lag_harness.py` — verifying baseline pins / `_example_aligned_config` shape; do not break; duplicate pins in R3 module.
- `tests/test_r1_jump_classification.py` — M1/M2/M3 formulas + `delta_pct` pattern to copy (not Screen-2 ranker); already has `dt=30` datapoint for continuity.
- `apps/ha_smart_hvac/ladrc.py` — `_ESO_EULER_SUBSTEPS=2`; `h = dt/2`; stability `|1−2·h·ωo|<1` (read-only authority).
- `apps/ha_smart_hvac/config.py` — `control_interval` → `LadrcConfig.dt` (read-only; do not change).
- `docs/house-calibration.md` §2–4 — `control_interval: 60`; ωo band at dt=60; raise-interval footgun (cite, do not edit).
- `_bmad-output/initiative-madrc/epic-madrc-decide/spike-metrics-for-jump-madrc-and-ff-decisions.md` — X=30%, Z=0.2; Never-disclaimer language.
- `_bmad-output/initiative-fix-ladrc-blow-up/epic-fix-ladrc-blow-up/epic-fix-ladrc-blow-up-retrospective.md` — F-R8 `dt=120`/ωo=0.03 unstable (cite in band notes).
- `tests/test_r3_control_interval_candidates.py` — **new**: Euler gate helper, candidate runs, assert stability labels + recommendation rule + replay.
- `_bmad-output/initiative-madrc/epic-madrc-decide/story-compare-control-interval-candidates.md` — **new** R3 evidence/recommendation artifact.
- `_bmad-output/initiative-madrc/epic-madrc-decide/epic-madrc-decide.md` — Notes pointer.

**Reuse:** harness + verifying pins; spike X/Z; Euler formula from `ladrc.py` comments/calibration.

**Do not change:** production App/LADRC/FF; example YAML; house-calibration; `_ESO_EULER_SUBSTEPS`; R1 module behavior.

## Tasks & Acceptance

**Execution:**
- [x] `tests/test_r3_control_interval_candidates.py` — Euler stability helper; run candidates 30/60/120 at example gains; assert finite⇔stable for 30/60, reject 120; compute M1/M2/M3 + Δ% vs 60; assert recommendation rule outcome; same-dts replay — unit/sim evidence
- [x] `_bmad-output/initiative-madrc/epic-madrc-decide/story-compare-control-interval-candidates.md` — Never-disclaimer + candidate/stability/metrics table + recommendation line + citations — ticket verify
- [x] `_bmad-output/initiative-madrc/epic-madrc-decide/epic-madrc-decide.md` — Notes bullet → interval artifact — discoverability

**Acceptance Criteria:**
- Given candidates {30, 60, 120} at example `ωo=0.03` and `_ESO_EULER_SUBSTEPS=2`, when the test module runs, then 30 and 60 are labeled Euler-stable with finite series, and 120 is labeled unstable/rejected (non-finite and/or Euler factor ≥ 1).
- Given the recommendation rule (stable + M3&lt;Z; material X on M1 or M2 vs 60 → best by M1 then M2; else keep 60; never recommend 120), when metrics are computed, then the test asserts the same recommendation the artifact records.
- Given the interval artifact, when opened, then it leads with Never-disclaimer (sim `dt` = recommendation target for later `control_interval`; no YAML/ADR apply here), then the candidate table with Euler-band notes (incl. F-R8 / house-calibration footgun), then one recommendation line with rationale, then `tests/test_r3_control_interval_candidates.py` citations.
- Given epic Notes after this story, when read, then a bullet points at `story-compare-control-interval-candidates.md`.
- Given existing harness/R1/CAP-5/FF tests, when the new module is added, then those suites still pass.

## Implementation Notes

- **Decision (recommendation):** Among Euler-stable candidates with M3&lt;Z, `dt=30` clears material X on M1 (Δ% ≈ +38.23); M2 not material. Rule → **recommend 30**. `dt=120` Euler ρ=2.6 ≥ 1 → reject (never recommend); series stayed finite but latch duty M3=0.300 ≥ Z.
- **Decision (metrics locality):** Duplicated M1/M2/M3 + lower-is-better `delta_pct` in the R3 module (no import from R1; no shared `tests/harness/metrics.py`).
- **Files touched:**
  - `tests/test_r3_control_interval_candidates.py` (new)
  - `_bmad-output/initiative-madrc/epic-madrc-decide/story-compare-control-interval-candidates.md` (new)
  - `_bmad-output/initiative-madrc/epic-madrc-decide/epic-madrc-decide.md` (Notes pointer)
  - this plan’s Implementation Notes only
- **Surprises:** At example `ωo=0.03` / n_sub=2, `dt=120` produced **finite** series (not NaN/Inf) despite Euler-unstable ρ=2.6 — reject still via Euler gate; latch duty elevated. No production/YAML/calibration edits.
- **Verification:** `uv run pytest tests/test_r3_control_interval_candidates.py tests/test_plant_lag_harness.py tests/test_r1_jump_classification.py -q` → 13 passed; `uv run ruff check tests/test_r3_control_interval_candidates.py` → clean.

## Plan Change Log

## Review Triage Log

### 2026-10-18 — Review pass
- verdicts: 0 findings — high 0, medium 0, low 0, false 0, maybe-false 0
- findings:
  - (none)

## Auto Run Result

- **Summary:** R3 evidence comparing `control_interval` candidates {30, 60, 120} under fixed Euler/ωo/substeps; artifact recommends **30** (material M1 vs baseline 60); 120 rejected (Euler ρ≥1). No YAML/calibration/production apply.
- **Files changed:**
  - `tests/test_r3_control_interval_candidates.py` — Euler gate, candidate runs, recommendation rule, artifact citations
  - `story-compare-control-interval-candidates.md` — Never-disclaimer, table, recommend 30, citations
  - `epic-madrc-decide.md` — Notes pointer to R3 artifact
  - `story-compare-control-interval-candidates-plan.md` — plan / auto-run record
- **Review:** quick lens — 0 findings; patches applied 0; deferred 0; rejected 0. Patched counts: high 0, medium 0 → `followup_review_recommended: false`.
- **Verification:** `uv run pytest tests/test_r3_control_interval_candidates.py tests/test_plant_lag_harness.py tests/test_r1_jump_classification.py -q` → 13 passed; `uv run ruff check tests/test_r3_control_interval_candidates.py` → clean. Manual: no YAML/calibration in diff; artifact recommendation matches test assert (30).
- **Residual risks:** Recommendation is evidence for story 1.8 only; live `control_interval` still 60 until apply. `dt=120` can stay finite while Euler-unstable — reject relies on Euler gate, not finiteness alone.

## Design Notes

**Euler factor:** \(\rho = |1 - 2\cdot(dt/2)\cdot\omega_o| = |1 - dt\cdot\omega_o|\). Stable iff \(\rho < 1\) (equiv. \(\omega_o < 2/dt\) at n_sub=2). At ωo=0.03: dt=30 → 0.1; dt=60 → 0.8; dt=120 → 2.6.

**Δ%:** same as spike — \(100\cdot(M_{60}-M_c)/|M_{60}|\) for lower-is-better M1/M2.

**Artifact skeleton:** Never-disclaimer → table → **Recommendation:** keep 60 | recommend N — rationale → citations.

## Verification

**Commands:**
- `uv run pytest tests/test_r3_control_interval_candidates.py tests/test_plant_lag_harness.py tests/test_r1_jump_classification.py -q` — expected: all pass
- `uv run ruff check tests/test_r3_control_interval_candidates.py` — expected: clean

**Manual checks:**
- Artifact recommendation matches test assertion; no YAML/calibration edits in the diff.
