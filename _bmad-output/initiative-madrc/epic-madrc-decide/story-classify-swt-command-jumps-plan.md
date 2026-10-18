---
title: 'Classify SWT command jumps'
type: 'feature'
ticket: '3'
created: '2026-10-18'
status: done
baseline_revision: '51dbb55c858be1a97844ef57a5ce1c3875a1cd60'
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

**Problem:** R1 has no written classification of commanded SWT jumps with cited unit/sim evidence.

**Approach:** Run one-knob harness ablations (tuning / `ladrc_config.dt` / plant lag), apply accepted Screen-2 ranking (M1/M2/M3/M5), and write a classification artifact that cites those outputs — MADRC is not the default fix.

**Decisions:**
- Thresholds (HITL-accepted spike): ε=10 pp and Z=0.2 for Screen 2; X=30% is material-compare language only — **not** an R1 pick gate.
- Sample-period knob = `ladrc_config.dt` only (plant shares `dt`).
- Outcome may be (a)/(b)/(c)/(d) or **inseparable** (conflict: name the pair; no-pick: say fallthrough exhausted); both OK when cited.
- R1 metrics + ranker live in the R1 test module (not a shared harness package this story).
- Baseline = story-1 verifying pins from `tests/test_plant_lag_harness.py` / `_example_aligned_config` shape (FF-on).

## Boundaries & Constraints

**Always:**
- Screen 2: M3≥Z → (d); else lex M1→M2→M5 with |Δ%| lead ≥ ε; **inseparable** if no metric has a pick (fallthrough exhausted) **or** cross-metric conflict after a provisional pick (then name the conflicting families).
- One knob at a time vs that verifying baseline; record every knob in the ablation table; same recorded knobs must reproduce the same Screen-2 outcome.
- Classification artifact: Never-disclaimer (incl. sample period = `ladrc_config.dt` only; AppDaemon `control_interval` unchanged) → one human-readable R1 verdict line (class, conflict-pair, or no-pick inseparable; no ADR advice) → ablation table → citations; epic Notes points at the artifact.
- Own test module; do not break `tests/test_plant_lag_harness.py`.

**Never:**
- No production MADRC/AppDaemon/Exclusive Session; no ADR / `control_interval` / R7 keep-drop prose.
- No shared `tests/harness/metrics.py` or M4/M6 (deferred); no synthetic ranker-only edge suite (deferred).
- Do not default to class (c)/MADRC when evidence is weak.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Tuning / dt / plant-lag ablations | Verifying baseline vs one knob each (plant `n` at least once) | Ablation table + |Δ%|; Screen-2 pick or inseparable (conflict or no-pick) | Series finite |
| Written classification | Protocol result + citations | Human-readable R1 verdict + dt≠YAML disclaimer + linked cases | N/A |
| Re-run same knobs | Ablation table values replayed in test module | Same Screen-2 outcome as cited | N/A |

</frozen-after-approval>

## Code Map

- `tests/harness/runner.py` — `run_closed_loop` / `ClosedLoopSeries`; reuse as-is (`reference` kwarg, not series).
- `tests/harness/plant.py` — `CascadeLagPlant`; plant `n`/`T` are lag-mismatch knobs.
- `tests/test_plant_lag_harness.py` — verifying baseline pins / `_example_aligned_config`; do not break; duplicate pins in R1 module if helpers stay private.
- `tests/test_r1_jump_classification.py` — **new**: M1/M2/M3/M5 + Screen-2 ranker + one-knob ablations; assert Screen-2 outcome and same-knobs replay; evidence source for the artifact.
- `_bmad-output/initiative-madrc/epic-madrc-decide/spike-metrics-for-jump-madrc-and-ff-decisions.md` — Screen 1–2 authority (X/ε/Z).
- `_bmad-output/initiative-madrc/epic-madrc-decide/story-classify-swt-command-jumps.md` — **new** classification artifact.
- `_bmad-output/initiative-madrc/epic-madrc-decide/epic-madrc-decide.md` — Notes pointer.
- Continuity (1.2): Never-disclaimer; 1.3 applies protocol and may name inseparable.

**Do not change:** production App/LADRC/FF; harness tick contract; spike thresholds.

## Tasks & Acceptance

**Execution:**
- [x] `tests/test_r1_jump_classification.py` — M1/M2/M3/M5 + Screen-2; one-knob ablations (tuning, `dt`, plant `n`/`T`) vs verifying baseline; assert finite series, Screen-2 outcome, and same-knobs replay; record knobs — unit/sim evidence
- [x] `_bmad-output/initiative-madrc/epic-madrc-decide/story-classify-swt-command-jumps.md` — verdict (class or inseparable) + ablation table + test citations — ticket verify
- [x] `_bmad-output/initiative-madrc/epic-madrc-decide/epic-madrc-decide.md` — Notes bullet → classification artifact — discoverability

**Acceptance Criteria:**
- Given accepted spike thresholds (ε, Z for ranking; X not used as pick gate), when ablations run, then Screen 2 yields exactly one of (a)/(b)/(c)/(d) or inseparable (conflict → name families; no-pick → fallthrough exhausted) — never a silent MADRC/(c) default.
- Given the knobs recorded in the ablation table, when the same runs are repeated in the test module, then Screen 2 yields the same outcome as cited in the artifact.
- Given the classification artifact, when opened, then it leads with Never-disclaimer (sample period via `ladrc_config.dt` only; AppDaemon `control_interval` unchanged), then one human-readable R1 verdict line (class letter, conflict-pair, or no-pick inseparable; no ADR / keep-drop / interval advice), then the ablation table and `tests/test_r1_jump_classification.py` case citations.
- Given epic Notes after this story, when read, then a bullet points at `story-classify-swt-command-jumps.md`.
- Given existing harness/CAP-5/FF tests, when the new module is added, then those suites still pass.

## Implementation Notes

## Plan Change Log

## Review Triage Log

- 2026-10-18 quick: high=0 medium=0 low=0 false=0 maybe-false=0

## Design Notes

**Class map (knob family → letter after Screen-2 pick — not “changed knob ⇒ class”):** Tuning→(a); `ladrc_config.dt`→(b); plant `n`/`T`→(c); M3≥Z→(d).

**Δ%:** \(100\cdot(M_b-M_c)/|M_b|\) (invert if higher-is-better); R1 ranks on \(|\Delta_{\%}|\) and ε — do not gate picks on X.

**Ablation deltas:** pick concrete finite-series values; record all in the artifact (spike does not pin magnitudes). Reproducibility is enforced by AC (same knobs → same Screen-2 outcome in the test module), not by freezing starter deltas in Intent. If real runs hit M3≥Z or inseparable, report that — do not engineer synthetic edges here.

**Artifact:** Never-disclaimer (incl. dt≠YAML) → one human-readable R1 verdict line → ablation table → |Δ%| summary → case citations.

## Verification

**Commands:**
- `uv run pytest tests/test_r1_jump_classification.py tests/test_plant_lag_harness.py -q` -- expected: all pass
- `uv run pytest tests/test_ladrc.py tests/test_feedforward.py -q` -- expected: still pass
- `uv run ruff check tests/test_r1_jump_classification.py` -- expected: clean

**Manual checks:**
- Artifact: dt≠YAML Never-disclaimer; human-readable verdict (class / conflict-pair / no-pick); citations; no ADR / keep-drop / interval *recommendation* language.
- Epic Notes points at the artifact.
