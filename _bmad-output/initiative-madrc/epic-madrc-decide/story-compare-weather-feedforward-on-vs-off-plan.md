---
title: 'Compare Weather Feedforward on vs off'
type: 'feature'
ticket: '5'
created: '2026-10-18'
status: built
baseline_revision: '2668fd3c58253b673b20d04b6454078468b7f830'
route: 'full'
route_source: 'auto'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/initiative-madrc/epic-madrc-decide/spike-metrics-for-jump-madrc-and-ff-decisions.md'
  - '{project-root}/_bmad-output/initiative-madrc/initiative-madrc.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** R7 needs unit/sim evidence comparing Weather Feedforward on vs `u_ff=0` on tracking and SWT command-motion metrics, plus residue semantics at zero — before any ADR keep/drop prose (entry 6).

**Approach:** On verifying pins, run FF-on vs `zero_uff=True` at two outdoor points (cold and hot), compute Screen-3 metrics (M1/M2/M4/M6) with relative Δ% vs X, and write a comparison artifact only — no keep/drop lean, no production FF changes.

**Decisions:**
- Pins (shared): `_example_aligned_config`, plant `K=0.45,T=300,n=3`, N=40, FF config `base=25,slope=1.2,comfort_ref=20`, reference=21. Within a scenario only `zero_uff` flips.
- Outdoor scenarios (HITL): **cold** `outdoor=0` (verifying-pin continuity; `u_ff=49` when FF-on); **hot** `outdoor=10` (milder; `u_ff=37` when FF-on). Both keep `u_ff` non-zero and below comfort clamp concerns.
- Baseline = FF-on (`zero_uff=False`); candidate = `zero_uff=True`. Per outdoor: report M1/M2/M4 absolutes + improvement Δ% vs that outdoor’s FF-on baseline; material iff Δ% ≥ **X=30%**.
- M6: always document sample variance of `command − u_ff`; on every zero path state residue-at-zero = `command` (observed as `command − 0`).
- Artifact + epic Notes pointer; own test module. Relative Δ only — **no keep/drop-lean** wording (ADR outdoor-vs-scheduling stays in entry 6).
- Duplicate M1/M2/M4/M6 + `delta_pct` locally (no `tests/harness/metrics.py`; do not import R1/R3).
- Token risk accepted (Keep full ~1773).

## Boundaries & Constraints

**Always:**
- Toggle only via harness `run_closed_loop(..., zero_uff=)`; outdoor is the only other knob between cold/hot rows.
- Artifact: Never-disclaimer → compare table (cold and hot × FF-on vs zero_uff: M1/M2/M4 + Δ%; M6 both modes) → residue-at-zero rule → test citations; epic Notes points at it.
- Thresholds from accepted metrics spike (X=30%); cite spike note.

**Never:**
- No ADR keep/drop or outdoor-vs-scheduling prose (entry 6).
- No production App/LADRC/FF enable-flag / config / YAML / house-calibration / CONTEXT changes.
- No harness tick-contract changes; do not break `test_plant_lag_harness` / R1 / R3 / CAP-5.
- No shared metrics module; no R1 re-classification; no `control_interval` / MADRC \(G_{cp}\) work.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| cold FF-on | pins, outdoor=0, `zero_uff=False` | Finite; `u_ff=49` constant; M1/M2/M4/M6 baseline | Assert finite |
| cold zero_uff | outdoor=0, `zero_uff=True` | Finite; `u_ff=0`; residue=`command`; Δ% vs cold FF-on | Assert finite; residue |
| hot FF-on | pins, outdoor=10, `zero_uff=False` | Finite; `u_ff=37` constant; baseline for hot row | Assert finite |
| hot zero_uff | outdoor=10, `zero_uff=True` | Finite; residue=`command`; Δ% vs hot FF-on | Assert finite; residue |
| Material report | Δ% on M1/M2/M4 vs X per outdoor | Table marks material / not; no keep/drop lean | N/A |
| Same-scenario replay | Re-run both outdoors × both modes | Same metrics + material labels | N/A |

</frozen-after-approval>

## Code Map

- `tests/harness/runner.py` — `ClosedLoopSeries`; `run_closed_loop(..., zero_uff=)` (L63: FF-on calls `weather_feedforward`, else `u_ff=0`).
- `tests/harness/plant.py` — `CascadeLagPlant`; outdoor unused by plant.
- `tests/test_plant_lag_harness.py` — verifying pins / `_example_aligned_config` / `_ff_config`; `test_zero_uff_residue_is_command` already locks residue; duplicate pins in R7 module; do not break.
- `apps/ha_smart_hvac/feedforward.py` — `weather_feedforward` (read-only).
- `_bmad-output/initiative-madrc/epic-madrc-decide/spike-metrics-for-jump-madrc-and-ff-decisions.md` — Screen 3 R7 contract; X=30%; residue-at-zero; no keep/drop-lean.
- `tests/test_r1_jump_classification.py` / `tests/test_r3_control_interval_candidates.py` — M1/M2/`delta_pct` formula pattern to copy (not import); R1 deferred M4/M6.
- `tests/test_r7_weather_feedforward_compare.py` — **new**: local M1/M2/M4/M6; cold/hot × FF-on vs zero_uff; Δ%/material asserts; residue rule; replay; artifact citations.
- `_bmad-output/initiative-madrc/epic-madrc-decide/story-compare-weather-feedforward-on-vs-off.md` — **new** R7 evidence artifact (two outdoor rows).
- `_bmad-output/initiative-madrc/epic-madrc-decide/epic-madrc-decide.md` — Notes pointer.

**Reuse:** harness FF hook + verifying pins; spike Screen 3; R3-style artifact/test layout.

**Do not change:** production FF/App/LADRC; harness contract; R1/R3 modules; spike thresholds; YAML/calibration/ADR.

## Tasks & Acceptance

**Execution:**
- [x] `tests/test_r7_weather_feedforward_compare.py` — local M1/M2/M4/M6 + `delta_pct`; cold (`outdoor=0`) and hot (`outdoor=10`) × FF-on vs `zero_uff`; assert finite, residue-at-zero, Δ%/material labels, replay, artifact string checks — unit/sim evidence
- [x] `_bmad-output/initiative-madrc/epic-madrc-decide/story-compare-weather-feedforward-on-vs-off.md` — Never-disclaimer + cold/hot compare table + residue rule + citations — ticket verify
- [x] `_bmad-output/initiative-madrc/epic-madrc-decide/epic-madrc-decide.md` — Notes bullet → FF compare artifact — discoverability

**Acceptance Criteria:**
- Given verifying pins at outdoor ∈ {0, 10}, when FF-on and `zero_uff=True` runs complete for each, then all series are finite, zero-path `u_ff` is all 0, and residue on each zero path equals `command`.
- Given Screen-3 metrics, when M1/M2/M4/M6 are computed with baseline=FF-on per outdoor, then the test asserts the same absolute values, Δ%, and material-vs-X labels the artifact records — relative Δ only, no keep/drop lean.
- Given the FF compare artifact, when opened, then it leads with Never-disclaimer (comparison language for entry 6; not ADR), then the cold/hot on-vs-off table, then the residue-at-zero rule, then `tests/test_r7_weather_feedforward_compare.py` citations.
- Given epic Notes after this story, when read, then a bullet points at `story-compare-weather-feedforward-on-vs-off.md`.
- Given existing harness/R1/R3/CAP-5/FF tests, when the new module is added, then those suites still pass.

## Implementation Notes

- 2026-10-18 — Landed R7 compare: local M1/M2/M4/M6 in `tests/test_r7_weather_feedforward_compare.py`; artifact `story-compare-weather-feedforward-on-vs-off.md` (Never-disclaimer → cold/hot table → residue-at-zero → citations); epic Notes pointer. On verifying pins, clamp band dominates — Δ% ≈ 0 / not material both outdoors; no production/harness/YAML edits.

## Plan Change Log

## Review Triage Log

- 2026-10-18 — quick — medium — `tests/test_r7_weather_feedforward_compare.py` Screen-3 test locks `_M*` constants only; artifact table cells never asserted — AC requires parity with artifact records; drift would still pass — route: patch
- 2026-10-18 — quick — low — `_mode_metrics` / `test_cold_and_hot_…` check `u_ff` only at tick 0; matrix expects constant series (harness already asserts `all(u == …)`) — route: patch
- 2026-10-18 — quick — false — `_bmad-output/party-mode/memories/installed/.memlog.md` in diff — pre-existing dirty tree from party approve-and-stop, not caused by R7 implementer; defer scope noise — route: defer

## Design Notes

**M4:** \(\sum_t \lvert\texttt{reference}-y[t]\rvert\cdot\texttt{dt}\) with `reference` run kwarg and `dt` from `ladrc_config` (spike).

**M6:** sample variance of `command − u_ff`; at `zero_uff`, residue observed as `command`.

**Δ%:** \(100\cdot(M_{\text{FF-on}}-M_{\text{zero}})/|M_{\text{FF-on}}|\) (lower-is-better M1/M2/M4). Material iff ≥ X=30%.

**Artifact skeleton:** Never-disclaimer → cold/hot table → Residue-at-zero → citations.

**Outdoor pins:** cold `0` → `u_ff=25+1.2·(20−0)=49`; hot `10` → `u_ff=37`.

## Verification

**Commands:**
- `uv run pytest tests/test_r7_weather_feedforward_compare.py tests/test_plant_lag_harness.py tests/test_r1_jump_classification.py tests/test_r3_control_interval_candidates.py -q` — expected: all pass
- `uv run ruff check tests/test_r7_weather_feedforward_compare.py` — expected: clean

**Manual checks:**
- Artifact has no keep/drop-lean wording; residue-at-zero stated; epic Notes pointer present; no production/YAML/calibration edits in the diff.
