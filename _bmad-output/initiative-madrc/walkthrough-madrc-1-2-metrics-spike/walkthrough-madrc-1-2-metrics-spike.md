# Walkthrough — Branch docs/madrc-1-2-metrics-spike: Metrics for jump, MADRC, and FF decisions

Target: branch `docs/madrc-1-2-metrics-spike` @ `0a83c15` (feature commits `f969c67` spike note, `33d23cd` HITL accept, `0a83c15` party memlog)
Focus: human review of accepted metrics spike (story 1.2 / decide epic)
Current block: closed — wrap-up in progress (commit walkthrough + push + open PR)

## Blocks

- [x] **Intent** — done
- [x] **Broad strokes** — done
- [x] **Metric table (M1–M6)** — done
- [x] **R1 separation protocol** — done
- [x] **R7 / R2 contracts + HITL** — done
- [x] **Periphery** — done

## Intent

Source: [spike-metrics-for-jump-madrc-and-ff-decisions-plan.md](../epic-madrc-decide/spike-metrics-for-jump-madrc-and-ff-decisions-plan.md) (frozen-after-approval Intent).

**Problem:** Stories 1.3 (R1 jump classes), 1.5 (R7 FF on vs off), and the later R2 \(G_{cp}\) go/no-go lack agreed measurable metrics and pass/fail thresholds; harness series alone are not decision evidence.

**Approach:** Produce a HITL-accepted spike note that names metrics + starter relative thresholds, maps each to R1/R2/R7, and states how factorial harness ablations separate ESO lag-mismatch from tuning vs `control_interval` — no classification text and no ADR prose.

**Decisions:**
- Artifact: dedicated `_bmad-output/initiative-madrc/epic-madrc-decide/spike-metrics-for-jump-madrc-and-ff-decisions.md` + short epic Notes pointer.
- Doc-only this spike — no `tests/harness/metrics.py`; 1.3/1.5 implement formulas from the note.
- R1 separation: factorial one-knob ablations; **lexicographic ranking M1 → M2 → M5**; elevated M3 (latch duty ≥ **Z = 0.2**) → class (d) before lag claims; if top-two relative moves on the active metric differ by **< ε = 10 pp**, or M1/M2/M5 disagree on the winner after lex, mark **inseparable**.
- Thresholds: relative-to-baseline only; starter material bar **X = 30%** for M1/M2 — labeled in the note as **pre-ablation placeholders** (HITL may edit on accept); no absolute SWT °C caps; Wang field % is analogy only.
- M4 uses `reference` as the run kwarg (constant recorded in the ablation table), not a `ClosedLoopSeries` field.
- M5 primary = Pearson `corr(z1, y)` over the run; peak `|z2|` is optional appendix only.
- Never-disclaimer in the spike note: metrics are comparison language for later stories — **not** ADR go/no-go (1.6) and **not** an R1 classification verdict.
- HITL accept ritual: epic Notes bullet `metrics spike: accepted YYYY-MM-DD; X=…; ε=…; Z=…` (overrides if edited).

**Review notes (Intent):**
1. Frozen Intent matches shipped spike note — dedicated artifact, doc-only, Never-disclaimer, lex M1→M2→M5 + inseparable, X/ε/Z placeholders, M4=`reference` kwarg, M5=corr(z1,y); no Intent renegotiation needed.
2. HITL ritual present on [epic Notes](../epic-madrc-decide/epic-madrc-decide.md): `metrics spike: accepted 2026-10-17; X=30%; ε=10; Z=0.2`.
3. Soft: Approach says “tuning vs `control_interval`”; Screen 2 maps sample period to `ladrc_config.dt` and forbids recommending `control_interval` — consistent with Boundaries, not a gap.
4. Soft: epic Notes writes `ε=10` without unit `pp`; note/plan use 10 pp — same value.

## Broad strokes

What the change is: doc-only spike note naming M1–M6 + starters \(X\)/\(\varepsilon\)/\(Z\), R1 ablation ranking, R7/R2 relative contracts, plus epic Notes HITL accept pointer — no harness/Python/production changes.

Entry points (open in this order):

1. [spike-metrics-for-jump-madrc-and-ff-decisions.md](../epic-madrc-decide/spike-metrics-for-jump-madrc-and-ff-decisions.md) — accepted comparison language (Never-disclaimer + Screens 1–3)
2. [spike-metrics-for-jump-madrc-and-ff-decisions-plan.md](../epic-madrc-decide/spike-metrics-for-jump-madrc-and-ff-decisions-plan.md) — frozen Intent / Boundaries / status done
3. [epic-madrc-decide.md](../epic-madrc-decide/epic-madrc-decide.md) Notes — pointer + `metrics spike: accepted 2026-10-17; X=30%; ε=10; Z=0.2`
4. [`ClosedLoopSeries`](../../../tests/harness/runner.py) — series field source cited by the note (unchanged this branch)
5. [party-mode `.memlog.md`](../../party-mode/memories/installed/.memlog.md) — optional review trail for party patches

**Review notes (Broad strokes):**
1. Mechanism readable via note → plan → epic Notes → [`ClosedLoopSeries`](../../../tests/harness/runner.py) citation; Screens 1–3 are the substance, not a code diff.
2. Series fields in Never-disclaimer match `ClosedLoopSeries` (`command`, `y`, `u_track`, `z1`, `z2`, `u_ff`, `tripped`, `latch`); `reference` / `zero_uff` are run kwargs as stated.
3. Soft: entry #5 party [`.memlog.md`](../../party-mode/memories/installed/.memlog.md) is optional trail — spike 1.2 lines are near the end amid older parties; not required to understand the mechanism.

## Metric table (M1–M6)

Screen 1 defines six metrics over harness series plus out-of-band run knobs, with relative \(\Delta_{\%}\) against material bar \(X = 30\%\), R1 lead \(\varepsilon = 10\) pp, and latch-duty floor \(Z = 0.2\). Formulas are comparison language only — no Python helper on this branch. Never-disclaimer bars treating material passes as ADR or R1 verdicts.

- [Never-disclaimer](../epic-madrc-decide/spike-metrics-for-jump-madrc-and-ff-decisions.md) — comparison language only; not ADR / R1 verdict / `control_interval`
- [Starters \(X\)/\(\varepsilon\)/\(Z\) + \(\Delta_{\%}\)](../epic-madrc-decide/spike-metrics-for-jump-madrc-and-ff-decisions.md) — pre-ablation placeholders and material-X rule
- [M1–M6 table](../epic-madrc-decide/spike-metrics-for-jump-madrc-and-ff-decisions.md) — M1 jump max; M2 command variance; M3 latch duty; M4 discrete IAE; M5 \(\mathrm{corr}(z_1,y)\); M6 residue variance

**Review notes (Metric table (M1–M6)):**
1. M1–M6 formulas bind to [`ClosedLoopSeries`](../../../tests/harness/runner.py) plus `reference` / `ladrc_config.dt` kwargs; M4 `reference` is not a series field — matches Intent.
2. \(\Delta_{\%}\) split is clear: signed improvement for material-\(X\); absolute \(\Delta_{\%}\) for R1 ranking (worsening knobs can win separation).
3. Soft: Pearson M5 undefined if `z1` or `y` constant; M1 empty if \(N=1\); sample-variance ddof unspecified — leave to 1.3/1.5 implementers.
4. Soft: at `zero_uff`, M6=var(`command`) coincides with M2 — intentional residue-at-zero observation, not a bug.
5. Soft: plan Design Notes table still says M6 “stats of”; spike note primary is sample variance — note wins.

## R1 separation protocol

Screen 2 is an executable factorial protocol: one-knob ablations (tuning / `ladrc_config.dt` / plant lag), M3≥\(Z\) gates class (d) first, then lexicographic fallthrough M1→M2→M5 by \(|\Delta_{\%}|\) with \(\varepsilon\) lead; cross-metric conflict → inseparable. Not a classification verdict — story 1.3 applies it.

- [Class map + knob table](../epic-madrc-decide/spike-metrics-for-jump-madrc-and-ff-decisions.md) — Tuning→(a); Sample period→(b); Plant lag→(c)
- [Procedure steps 1–4](../epic-madrc-decide/spike-metrics-for-jump-madrc-and-ff-decisions.md) — M3 gate, picks, fallthrough, conflict → inseparable
- [Plan Boundaries](../epic-madrc-decide/spike-metrics-for-jump-madrc-and-ff-decisions-plan.md) — forbid R1 narrative, ADR go/no-go, and code changes this spike

**Review notes (R1 separation protocol):**
1. Fallthrough steps 1–4 are executable: M3 gate → picks by \(|\Delta_{\%}|\) lead ≥ \(\varepsilon\) → lex M1→M2→M5 → cross-metric conflict → inseparable; explicitly not a verdict / not a `control_interval` recommendation.
2. Class map Tuning→(a), `ladrc_config.dt`→(b), plant lag→(c) matches initiative R1 letters; (b) stays `dt` here while R3/1.4 owns `control_interval` wording.
3. Soft: step 1 “any compared run” underspecifies the compared set (baseline vs all arms) — 1.3 should name which runs enter the M3 gate.
4. Soft: Tuning family bundles many fields; protocol ranks families not sub-knobs — 1.3 must choose concrete one-knob examples per family.
5. Soft: optional plant \(K\) under lag family can confound gain vs lag — keep optional / document if used.

## R7 / R2 contracts + HITL

Screen 3 locks relative-only FF and \(G_{cp}\) contracts: R7 reports \(\Delta\) on M1/M2/M4/M6 with residue-at-zero = `command`; R2 is a stub until compensated harness exists; HITL accept ritual is already on the epic Notes bullet.

- [R7 FF-on vs `zero_uff`](../epic-madrc-decide/spike-metrics-for-jump-madrc-and-ff-decisions.md) — relative \(\Delta\) only; no keep/drop-lean wording
- [R2 baseline vs \(G_{cp}\) stub](../epic-madrc-decide/spike-metrics-for-jump-madrc-and-ff-decisions.md) — deferred impl; same material bar \(X\)
- [HITL accept ritual](../epic-madrc-decide/spike-metrics-for-jump-madrc-and-ff-decisions.md) + [epic Notes](../epic-madrc-decide/epic-madrc-decide.md) — `metrics spike: accepted 2026-10-17; X=30%; ε=10; Z=0.2`

**Review notes (R7 / R2 contracts + HITL):**
1. R7 contract is relative-only (M1/M2/M4/M6); residue-at-zero matches harness `zero_uff` path; no keep/drop-lean — ready for 1.5 tables.
2. R2 correctly stubbed: same \(X\) bar, M1/M2 primary + M4/M5 secondary; no production \(G_{cp}\) / ADR prose.
3. HITL ritual satisfied: epic Notes accepted 2026-10-17 with \(X=30\%\) \(\varepsilon=10\) \(Z=0.2\); note Status line mirrors it; overrides rule stated.
4. Soft: \(\varepsilon=10\) in Notes omits pp unit (same as Intent soft); M6 on zero path equals M2 numerically — document both per contract.
6. Test: HITL bullet matches note Status and starters \(X=30\%\) / \(\varepsilon=10\) (pp in table) / \(Z=0.2\); `test_zero_uff_residue_is_command` passed (residue==command on `zero_uff`); R7 section has no keep/drop-lean claim.

## Periphery

- [spike plan](../epic-madrc-decide/spike-metrics-for-jump-madrc-and-ff-decisions-plan.md) — `status: done` + Execution trail
- [epic Notes](../epic-madrc-decide/epic-madrc-decide.md) — metrics spike pointer + accept bullet
- [party `.memlog.md`](../../party-mode/memories/installed/.memlog.md) — 1.2 review trail
- [this walkthrough](./walkthrough-madrc-1-2-metrics-spike.md) — review narrative (new)

**Review notes (Periphery):**
1. Plan status done + Execution checkboxes checked; epic Notes pointer + HITL accept present.
2. Soft: plan Design Notes still say M6 “stats of” while spike note has sample variance — note wins (already flagged in Metric table).
3. Soft: walkthrough folder untracked — commit on wrap-up if desired; party memlog already on branch.
