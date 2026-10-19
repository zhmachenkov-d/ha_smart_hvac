---
type: Reference
title: Wang et al. 2026 — Adaptive MADRC for superheated steam temperature
description: Open-access field + simulation study of gain-scheduled MADRC on a 660 MW unit SST cascade loop.
tags: [adrc, madrc, cascade, gain-scheduling, literature, thermal-power]
timestamp: 2026-07-08T15:45:00Z
resource: raw/wang-2026-madrc-sst/
---

# Wang et al. 2026 — Adaptive MADRC for superheated steam temperature

Wang, H., Tong, Z., Wu, Z., Zheng, H., Li, B., Jia, Y. (2026). Adaptive Modified Active Disturbance Rejection Control for the Superheated Steam Temperature System Under Wide Load Conditions. *Processes*, 14(2), 308. DOI: [10.3390/pr14020308](https://doi.org/10.3390/pr14020308). CC BY 4.0.

Immutable copy: [`raw/wang-2026-madrc-sst/processes-14-00308.pdf`](/raw/wang-2026-madrc-sst/processes-14-00308.pdf). Provenance: [`raw/wang-2026-madrc-sst/SOURCE.md`](/raw/wang-2026-madrc-sst/SOURCE.md).

## Status

Ingested (first pass) — [MADRC](/concepts/madrc.md) idea, tuning/adaptation rules, and field outcomes extracted; SST transfer-function tables left in the PDF.

## What the paper does

Controls **superheated steam temperature (SST)** on a thermal power unit with a **cascade** structure: inner-loop proportional (on-site: PI noted in conclusions) on the leading zone; outer-loop **[MADRC](/concepts/madrc.md)** on the inert zone. MADRC adds an inertia compensation block \(G_{cp}(s)=1/(Ts+1)^{n-1}\) so the [ESO](/concepts/extended-state-observer.md) sees a delayed command \(u_f\) matched to the delayed measurement \(y\).

Plant models at 100% / 75% / 50% load are high-order inertias \(K/(Ts+1)^n\) (Table 1 in PDF). Fixed-parameter MADRC is extended with **linear gain scheduling** of controller gain \(k_p\) and compensation time constant \(T\) vs unit load \(P\); \(b_0\) and \(\omega_o\) are held fixed (\(b_0=0.06\), \(\omega_o=0.3\) in their sims) because changing \(b_0\) jumps the control law.

Compared in simulation to integral-gain-adaptive PID, fruit-fly-tuned second-order ADRC, and nonlinear ADRC (NLADRC): setpoint + step/ramp/sine disturbances; Monte Carlo ±10% parameter uncertainty; \(M_s\) robustness; high-frequency noise on the TDOF equivalent.

**Field (660 MW supercritical unit, DCS, 250 ms sample):** after deployment, A/B-side SST fluctuation range fell to **34.0% / 53.0%** of baseline; fluctuation variance to **28.5% / 43.3%** (Table 5 / abstract).

## Tuning rules (their plant)

1. Fix \(b_0 \in [K/(2T),\infty)\).
2. Start small \(k_p\), \(\omega_o\); raise \(\omega_o\) until output barely changes; they settle near \(\omega_o \in [0.3,0.6]\).
3. Raise \(k_p\) for tracking; schedule \(k_p\) (and \(T\)) across load points — **not** \(b_0\).

Treat numbers as **literature examples**, not OpenTherm HVAC settings.

## Fit to this project

Prior art for **large-inertia temperature loops** and for **adapting ADRC gains across operating regimes**. Not a drop-in blueprint:

| This paper | This repo |
|------------|-----------|
| Attemperation water valve → steam temperature | OpenTherm [Set Water Temperature](/concepts/set-water-temperature.md) → zone/plant water |
| Cascade leading + inert zones of a superheater | Single [Plant](/concepts/plant.md) + [Zones](/concepts/zone.md); coordinator selects Critical Zone for CAP-7 only (ADR 0004) |
| Schedule vs **electrical load** | Live water path is weather-curve FF (+ CAP-7 rise-rate), not MADRC — this paper is prior art only |

Complements [/references/huang-2018-ladrc-hvac.md](/references/huang-2018-ladrc-hvac.md) (LADRC on AHU zone air; no inertia-compensation MADRC).

## Key sections (PDF)

1. Introduction — SST under deep peak shaving; ADRC variants; MADRC motivation
2. SST structure & multi-load models (Table 1)
3. First-order ADRC → MADRC compensation → tuning flowchart → adaptive \(k_p\)
4. Simulations: nominal, Monte Carlo, \(M_s\), noise (TDOF form)
5. Field application on 660 MW unit (Eqs. 29–30 scheduling)
6. Conclusions

## Linked concepts

- [/concepts/madrc.md](/concepts/madrc.md)
- [/concepts/adrc.md](/concepts/adrc.md)
- [/concepts/ladrc.md](/concepts/ladrc.md)
- [/concepts/extended-state-observer.md](/concepts/extended-state-observer.md)
- [/concepts/total-disturbance.md](/concepts/total-disturbance.md)
- [/concepts/plant.md](/concepts/plant.md)

# Citations

- Raw PDF: `/raw/wang-2026-madrc-sst/processes-14-00308.pdf`
