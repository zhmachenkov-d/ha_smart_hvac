---
title: 'Metrics for jump, MADRC, and FF decisions'
type: 'feature'
ticket: '2'
created: '2026-10-17'
status: 'built'
baseline_revision: 'd9c6959020ac9ba35588404706f6d3feb63f0294'
route: 'full'
route_source: 'auto'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - '{project-root}/knowledge/concepts/madrc.md'
  - '{project-root}/knowledge/references/wang-2026-madrc-sst.md'
  - '{project-root}/_bmad-output/initiative-madrc/initiative-madrc.md'
  - '{project-root}/_bmad-output/initiative-madrc/epic-madrc-decide/story-plant-lag-multi-tick-sim-harness-plan.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Stories 1.3 (R1 jump classes), 1.5 (R7 FF on vs off), and the later R2 \(G_{cp}\) go/no-go lack agreed measurable metrics and pass/fail thresholds; harness series alone are not decision evidence.

**Approach:** Produce a HITL-accepted spike note that names metrics + starter relative thresholds, maps each to R1/R2/R7, and states how factorial harness ablations separate ESO lag-mismatch from tuning vs `control_interval` — no classification text and no ADR prose.

**Decisions:**
- Artifact: dedicated `_bmad-output/initiative-madrc/epic-madrc-decide/spike-metrics-for-jump-madrc-and-ff-decisions.md` + short epic Notes pointer.
- Doc-only this spike — no `tests/harness/metrics.py`; 1.3/1.5 implement formulas from the note.
- R1 separation: factorial one-knob ablations; **lexicographic ranking M1 → M2 → M5**; elevated M3 (latch duty ≥ **Z = 0.2**) → class (d) before lag claims; if top-two relative moves on the active metric differ by **&lt; ε = 10 pp**, or M1/M2/M5 disagree on the winner after lex, mark **inseparable**.
- Thresholds: relative-to-baseline only; starter material bar **X = 30%** for M1/M2 — labeled in the note as **pre-ablation placeholders** (HITL may edit on accept); no absolute SWT °C caps; Wang field % is analogy only.
- M4 uses `reference` as the run kwarg (constant recorded in the ablation table), not a `ClosedLoopSeries` field.
- M5 primary = Pearson `corr(z1, y)` over the run; peak `|z2|` is optional appendix only.
- Never-disclaimer in the spike note: metrics are comparison language for later stories — **not** ADR go/no-go (1.6) and **not** an R1 classification verdict.
- HITL accept ritual: epic Notes bullet `metrics spike: accepted YYYY-MM-DD; X=…; ε=…; Z=…` (overrides if edited).

## Boundaries & Constraints

**Always:**
- Metrics use harness `ClosedLoopSeries` fields plus documented out-of-band run knobs (`reference`, `ladrc_config`, `dt`/`control_interval`, plant `n`/`T`, `zero_uff`) listed in the ablation table.
- Map every chosen metric to at least one of R1, R2 (\(G_{cp}\) evidence), R7.
- Note states concrete starters **X = 30%**, **ε = 10 pp**, **Z = 0.2** with the placeholder label, plus relative compare-better rules — 1.3/1.5 must not invent thresholds.
- Spike note opens with Never-disclaimer; R7 section reports relative Δ only (no keep/drop-lean wording).
- Residue semantics for \(u_{ff}=0\): `command − 0` as an R7 observation rule, not ADR outdoor-vs-scheduling prose.
- Wang SST % / variance stay literature context only.

**Never:**
- No R1 classification narrative, no ADR go/no-go wording, no `control_interval` recommendation (1.4/1.6).
- No production MADRC \(G_{cp}\), scheduling, AppDaemon, or FF enable-flag changes.
- No Python metrics helper or harness runner changes in this spike.
- Do not treat harness verifying-test pins (`K=0.45`, etc.) as house-calibrated truth.
- Do not treat metric deltas or “material” passes as initiative go/no-go.
- Do not modify CAP-5 / locked `test_ladrc.py` scenarios or production ESO math.
- Do not invent Exclusive Session / field metrics as gates.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Spike note complete | Metrics table + R-map + X/ε/Z + Never-disclaimer + protocols | Dedicated note + epic Notes pointer; user accept/reject | HALT on reject; revise note |
| R1 ablation protocol | One-knob vary tuning / `dt` / plant `n`/`T` | Lex M1→M2→M5 picks winner if lead ≥ ε and metrics agree; else inseparable; M3≥Z → class (d) first | Inseparable pair named for 1.3 |
| R7 compare rule | Same scenario FF-on vs `zero_uff=True` | Relative Δ vs X on named metrics; residue-at-zero stated | No keep/drop-lean language |
| R2 \(G_{cp}\) stub | Metrics before \(G_{cp}\) in code | Baseline-vs-compensated relative compare using X; impl deferred | No code this spike |
| HITL accept | User accepts note (optional X/ε/Z edits) | Epic Notes: `metrics spike: accepted YYYY-MM-DD; X=…; ε=…; Z=…` | Pending until that bullet exists |

</frozen-after-approval>

## Code Map

- `tests/harness/runner.py` — `ClosedLoopSeries`: `command`, `y`, `u_track`, `z1`, `z2`, `u_ff`, `tripped`, `latch`; `run_closed_loop(..., reference=..., zero_uff=False)`. Series source for M1–M3, M5–M6; **`reference` is a run kwarg**, not logged — M4 uses ablation-table constant.
- `tests/harness/plant.py` — `CascadeLagPlant`; plant `n`/`T` are R1 lag-mismatch knobs.
- `tests/test_plant_lag_harness.py` — pinned defaults / `_example_aligned_config`; do not break.
- `_bmad-output/initiative-madrc/epic-madrc-decide/epic-madrc-decide.md` — Notes pointer + HITL accept ritual.
- `_bmad-output/initiative-madrc/initiative-madrc.md` — R1 classes (a–d); R2 milder SWT / observer alignment; R7 tracking + SWT motion + residue at \(u_{ff}=0\).
- `knowledge/references/wang-2026-madrc-sst.md` — field fluctuation %; literature only.
- `knowledge/concepts/madrc.md` — \(G_{cp}\) intent; no HVAC thresholds.
- Continuity from story 1 plan: series legend; Never-disclaimer; classification/keep-drop deferred.

**Reuse:** harness series + ablation knobs; initiative R wording.

**Do not change:** production App/LADRC/FF; harness tick contract; no new Python in this spike.

## Tasks & Acceptance

**Execution:**
- [x] `_bmad-output/initiative-madrc/epic-madrc-decide/spike-metrics-for-jump-madrc-and-ff-decisions.md` — write spike note: Never-disclaimer; one-screen table (ID → primary formula → R-map → rule); starters X/ε/Z as pre-ablation placeholders; lex ranking + inseparable; R7 relative-Δ + residue-at-zero; short R2 baseline-vs-\(G_{cp}\) contract — HITL accept surface
- [x] `_bmad-output/initiative-madrc/epic-madrc-decide/epic-madrc-decide.md` — append Notes bullet pointing at the spike note (`accept pending` until HITL ritual fires) — discoverability for 1.3/1.5/1.6

**Acceptance Criteria:**
- Given the spike note, when opened, then it leads with Never-disclaimer and a one-screen table where every metric has one primary formula, an R-map, and a relative rule; M1/M2 material uses starter X=30% labeled pre-ablation placeholder.
- Given the R1 protocol, when one-knob ablations run, then lex order M1→M2→M5 (M3≥Z=0.2 → class (d) first) picks a dominant class only if the lead is ≥ ε (10 pp) and metrics do not conflict; otherwise the note requires inseparable.
- Given R7, when FF-on is compared to `u_ff=0`, then the note names deciding metrics, reports relative Δ vs X only (no keep/drop-lean), and states residue = `command − 0` on the zero path.
- Given R2, when \(G_{cp}\) is absent from code, then the note defines the baseline-vs-compensated relative contract (vs X) without production \(G_{cp}\).
- Given user HITL accept, when recorded, then epic Notes contains `metrics spike: accepted YYYY-MM-DD; X=…; ε=…; Z=…`.

## Implementation Notes

- 2026-10-17 — Doc-only spike landed: wrote `spike-metrics-for-jump-madrc-and-ff-decisions.md` (Never-disclaimer; M1–M6 table; X=30%/ε=10 pp/Z=0.2 placeholders; R1 lex+inseparable; R7 relative-Δ + residue-at-zero; R2 \(G_{cp}\) stub). Epic Notes pointer with **accept pending**. No Python / harness / production changes. HITL accept ritual still open.
- 2026-10-17 — Review fixes on spike note only: M6 = sample var of residue; M1 domain t=1..N-1; M4 discrete IAE·dt; sample period = `ladrc_config.dt`; material-X = improvement Δ%; R1 ranks on |Δ%|; ε/inseparable + executable fallthrough + class map a/b/c on Screen 2 only.

## Plan Change Log

## Review Triage Log

- 2026-10-17 quick: high=0 medium=7 low=1 false=1 maybe-false=0
  - false → rejected — M3/M5/M6 lack relative-Δ rules: Intent Decisions assign absolute Z (M3), lex (M5), document/residue (M6); AC “relative rule” over-read against frozen Decisions — note matches Intent
  - medium → patch — M6 “stats of” is not one primary formula — pick discrete primary (e.g. sample variance of `command−u_ff`)
  - medium → patch — Screen 2 names knob family but AC wants class path — add one-line map Tuning→(a), Sample/`ladrc_config.dt`→(b), Plant lag→(c) without writing a verdict
  - medium → patch — improvement-oriented Δ% used for R1 ranking so worsening knobs cannot win — use |Δ%| magnitude for R1 ranking; keep signed/improvement Δ only for material-X compares
  - medium → patch — lex / “active metric” / “disagree after lex” not jointly executable — write fallthrough lex + post-lex disagreement → inseparable
  - medium → patch — ε stated in global Compare-better block — scope ε/inseparable to Screen 2 (R1) only
  - medium → patch — note lists `dt`/`control_interval` as run knob but harness exposes sample period only via `ladrc_config.dt` — say that explicitly
  - medium → patch — M4 IAE underspec — discrete \(\sum |e|\,dt\) with `dt` from `ladrc_config`
  - low → patch — M1 `t-1` undefined at first sample — domain `t = 1..N-1`

## Design Notes

**Primary metric formulas (one each; footnotes optional):**

| ID | Primary formula | R-map | Rule |
|----|-----------------|-------|------|
| M1 | `max_t |command[t]−command[t−1]|` | R1, R2, R7 | material if ≥X% better vs baseline |
| M2 | sample variance of `command` | R1, R2, R7 | material if ≥X% better vs baseline |
| M3 | mean(`latch`) over run (duty) | R1 (d) | if ≥ Z → class (d) before lag/tuning claims |
| M4 | IAE of `(reference − y)` with `reference` from run kwarg / ablation table | R7, R2 secondary | relative Δ vs X in FF compares |
| M5 | Pearson `corr(z1, y)` over the run | R1 (c), R2 | lex rank after M1/M2; \|z2\| peak optional appendix |
| M6 | stats of `command − u_ff` | R7 | always document; at `zero_uff` residue = `command` |

**R1:** one-knob ablations; lex M1→M2→M5; lead &lt; ε or cross-metric conflict → inseparable; M3≥Z first.

**Starters (placeholders):** X=30%, ε=10 pp, Z=0.2 — HITL may edit on accept.

**Note layout:** screen 1 = Never-disclaimer + table; screen 2 = R1 protocol; screen 3 = R7 + R2 stubs (short).

## Verification

**Manual checks:**
- Spike note: Never-disclaimer; primary formulas; X/ε/Z placeholders; lex + inseparable; R7 relative-Δ + residue; R2 \(G_{cp}\) contract; no keep/drop-lean.
- Epic Notes: pointer (`accept pending`); after HITL, ritual bullet with date and X/ε/Z.
