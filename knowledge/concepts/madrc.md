---
type: Concept
title: MADRC
description: Modified ADRC — delay the ESO’s command input with an inertia compensator so it stays synchronized with a high-order lag plant’s delayed output.
tags: [control, adrc, madrc, observer]
timestamp: 2026-10-19T14:41:00Z
---

# MADRC

**Modified Active Disturbance Rejection Control** keeps first-order [ADRC](/concepts/adrc.md) / linear bandwidth-parameterized structure, but inserts a compensation transfer function before the [ESO](/concepts/extended-state-observer.md) so the observer’s two inputs stay time-aligned on **high-order inertia** plants.

For a plant approximated as \(G_p(s)=K/(Ts+1)^n\), the compensator is

\[
G_{cp}(s)=\frac{1}{(Ts+1)^{n-1}}
\]

The ESO then uses \(u_f = G_{cp}u\) instead of raw \(u\), treating the compensated channel as roughly first-order and folding residual mismatch into [total disturbance](/concepts/total-disturbance.md). Intent: avoid ESO desynchronization that pure time-delay ADRC or Smith-predictor ADRC can worsen under delay mismatch (Wang et al. 2026 citing Wu et al. 2019).

## Adaptive (gain-scheduled) MADRC

Wang et al. (2026) tune \(\omega_o\), \(b_0\), \(k_p\), and plant-linked \(T\), then **schedule \(k_p\) and \(T\) with operating load** while leaving \(b_0\) and \(\omega_o\) fixed — changing \(b_0\) jumps \(u=(u_0-z_2)/b_0\). Field form: piecewise-linear \(k_p(P)\) and \(T(P)\) between 50% / 75% / 100% rated load on a 660 MW unit. Depth and metrics: [/references/wang-2026-madrc-sst.md](/references/wang-2026-madrc-sst.md).

## Vs LADRC

[LADRC](/concepts/ladrc.md) is the linear ESO + linear feedback family (Gao). MADRC is an **input-path structural add-on** aimed at high-order lag; it is usually realized with the same linear observer/controller as first-order LADRC. Huang et al. (2018) apply LADRC to AHU zone temperature **without** this compensator.

## Project note

MADRC is **not** on the live water path — **ADR 0004** (weather-curve-only SWT). House thermal dynamics may still look high-order relative to OpenTherm [Set Water Temperature](/concepts/set-water-temperature.md); this page is prior art only. Paper gains and SST numerics are not copy-paste settings for this Plant.

## Related

- [/concepts/adrc.md](/concepts/adrc.md)
- [/concepts/ladrc.md](/concepts/ladrc.md)
- [/concepts/extended-state-observer.md](/concepts/extended-state-observer.md)
- [/concepts/plant.md](/concepts/plant.md)

# Citations

- [/references/wang-2026-madrc-sst.md](/references/wang-2026-madrc-sst.md) §3, Eqs. (15)–(18), (29)–(30)
