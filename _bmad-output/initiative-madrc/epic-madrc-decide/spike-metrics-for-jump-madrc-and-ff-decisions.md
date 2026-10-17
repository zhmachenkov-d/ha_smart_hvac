# Metrics for jump, MADRC, and FF decisions

**Status:** accepted 2026-10-17 (epic Notes: `metrics spike: accepted 2026-10-17; X=30%; ε=10; Z=0.2`).

## Never-disclaimer

These metrics are **comparison language** for later stories (1.3 R1 ablations, 1.5 R7 FF-on vs `zero_uff`, later R2 \(G_{cp}\) evidence). They are **not** an ADR go/no-go (1.6), **not** an R1 classification verdict, and **not** a `control_interval` recommendation. Relative “material” passes do not settle the initiative. Wang et al. 2026 field fluctuation % / variance figures are literature analogy only — not house thresholds.

Harness verifying-test pins (`K=0.45`, etc.) are starter fixtures, not house-calibrated truth. Series source: `ClosedLoopSeries` (`command`, `y`, `u_track`, `z1`, `z2`, `u_ff`, `tripped`, `latch`) plus out-of-band run knobs recorded in the ablation table (`reference`, `ladrc_config`, plant `n`/`T`, `zero_uff`). `reference` is a run kwarg, not a series field. Sample period is varied via `ladrc_config.dt` (plant stepped with the same `dt`).

---

## Screen 1 — Metric table

Starters (**pre-ablation placeholders**; HITL may edit on accept):

| Symbol | Value | Role |
|--------|-------|------|
| \(X\) | **30%** | Material relative improvement bar for M1/M2 (and relative Δ bar where named) |
| \(\varepsilon\) | **10 pp** | R1 only: minimum lead between top-two \(|\Delta_{\%}|\) on the active metric (see Screen 2) |
| \(Z\) | **0.2** | Latch-duty floor for M3 → class (d) before lag/tuning claims |

**Improvement \(\Delta_{\%}\) (material-X compares):** for a candidate vs baseline on metric \(M\),
\[
\Delta_{\%} = 100\cdot\frac{M_{\text{baseline}}-M_{\text{candidate}}}{|M_{\text{baseline}}|}
\]
(higher-is-better metrics invert the numerator). Material iff \(\Delta_{\%} \ge X\). R1 ranking uses \(|\Delta_{\%}|\) magnitude (Screen 2), so a worsening knob can win the separation.

| ID | Primary formula | R-map | Rule |
|----|-----------------|-------|------|
| M1 | \(\max_{t=1..N-1} \lvert\texttt{command}[t]-\texttt{command}[t-1]\rvert\) | R1, R2, R7 | material if improvement \(\Delta_{\%} \ge X\) vs baseline |
| M2 | sample variance of `command` | R1, R2, R7 | material if improvement \(\Delta_{\%} \ge X\) vs baseline |
| M3 | \(\mathrm{mean}(\texttt{latch})\) over run (duty) | R1 (d) | if \(\ge Z\) → class (d) before lag/tuning claims |
| M4 | \(\sum_t \lvert\texttt{reference}-y[t]\rvert\cdot\texttt{dt}\) with `dt` from `ladrc_config`; `reference` from run kwarg / ablation table | R7, R2 secondary | relative improvement \(\Delta_{\%}\) vs \(X\) in FF / \(G_{cp}\) compares |
| M5 | Pearson \(\mathrm{corr}(z_1, y)\) over the run | R1 (c), R2 | lex rank after M1/M2; peak \(\lvert z_2\rvert\) optional appendix only |
| M6 | sample variance of `command − u_ff` | R7 | always document; at `zero_uff` residue = `command` |

Optional appendix (not lex-ranked): peak \(\lvert z_2\rvert\) over the run — observer-magnitude context only.

---

## Screen 2 — R1 separation protocol

**Goal:** factorial one-knob ablations that separate ESO lag-mismatch from tuning vs sample period / plant lag. No classification verdict in this note — only the ranking procedure stories 1.3+ apply.

**Class map (knob family → R1 class letter; not a verdict):** Tuning→(a); Sample period (`ladrc_config.dt`)→(b); Plant lag→(c).

**Ablation knobs (one at a time vs a named baseline run):**

| Knob family | Examples (record every value in the ablation table) |
|-------------|-----------------------------------------------------|
| Tuning | `ladrc_config` fields: `b0`, `omega_c`, `omega_o`, FF slope/base when FF is on |
| Sample period | `ladrc_config.dt` only (plant stepped with the same `dt`) |
| Plant lag | cascade plant `n`, `T` (and optionally \(K\) if varied) |

**Procedure (executable fallthrough):**

1. **M3 gate first.** If any compared run has M3 \(\ge Z\), treat that as class **(d)** (latch/guard path) before attributing the active metric move to lag mismatch, tuning, or sample period.
2. For each of M1, M2, M5, rank knob families by \(|\Delta_{\%}|\) vs the same baseline. On a metric, a family is a **pick** iff its lead over the second-ranked family’s \(|\Delta_{\%}|\) is \(\ge \varepsilon\) (else that metric has no pick).
3. **Fallthrough:** if M1 has a pick → provisional family = that pick; else if M2 has a pick → that pick; else if M5 has a pick → that pick; else **inseparable**.
4. **Cross-metric conflict:** after a provisional pick from step 3, if any other metric among {M1, M2, M5} would pick a *different* family with lead \(\ge \varepsilon\) → **inseparable**. Otherwise keep the provisional pick (still not an R1 classification verdict — story 1.3 names the inseparable pair when this fires).

This protocol does **not** recommend a `control_interval` value and does **not** write an R1 class verdict.

---

## Screen 3 — R7 and R2 contracts

### R7 — FF-on vs `zero_uff=True`

Same scenario, two runs: FF-on (`zero_uff=False`) vs `u_ff=0` (`zero_uff=True`).

| Deciding metrics | Report |
|------------------|--------|
| M1, M2 | improvement \(\Delta_{\%}\) vs \(X\) (material / not) |
| M4 | improvement \(\Delta_{\%}\) vs \(X\) (tracking) |
| M6 | always document; **residue-at-zero rule:** on the zero path, residue observed as `command − 0` (= `command`) |

Report relative \(\Delta\) only. **No keep/drop-lean wording** in this note or in 1.5 metric tables derived from it.

### R2 — baseline vs \(G_{cp}\) (stub; impl deferred)

\(G_{cp}\) is absent from production code in this spike. When a compensated harness path exists later, compare **baseline** (no compensator) vs **compensated** on the same scenario using M1/M2 (primary) and M4/M5 (secondary) with the same relative material bar \(X\) (improvement \(\Delta_{\%}\)). No production \(G_{cp}\), scheduling, or ADR go/no-go text here.

---

## HITL accept ritual

When accepted (optionally after editing \(X\), \(\varepsilon\), \(Z\)), epic Notes must contain:

```text
metrics spike: accepted YYYY-MM-DD; X=…; ε=…; Z=…
```

Until that bullet exists, treat this note as **accept pending**. Overrides in the ritual bullet win over the starters above.
