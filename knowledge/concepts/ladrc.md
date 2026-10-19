---
type: Concept
title: LADRC
description: Linear Active Disturbance Rejection Control — linear ESO plus linear state feedback; practical ADRC form with fewer tuning knobs.
tags: [control, adrc, ladrc]
timestamp: 2026-10-19T14:41:00Z
---

# LADRC

**Linear Active Disturbance Rejection Control** simplifies nonlinear [ADRC](/concepts/adrc.md): a linear [ESO](/concepts/extended-state-observer.md) estimates output and [total disturbance](/concepts/total-disturbance.md); a linear outer law drives the compensated plant. [MADRC](/concepts/madrc.md) typically uses this same linear core plus an inertia compensator on the ESO’s \(u\) channel.

Huang et al. (2018) use a **first-order ESO** and **second-order linear controller** for winter AHU zone temperature:

\[
\begin{aligned}
\dot z_1 &= z_2 + \beta_1(y - z_1) + b_0 u \\
\dot z_2 &= \beta_2(y - z_1)
\end{aligned}
\]

\[
u_0 = k_p(T_r - z_1),\quad u = (u_0 - z_2)/b_0
\]

(with symbols as in the paper; \(y\) measured zone temperature, \(u\) actuator command). Their tuned set: \(b_0=2.8\), \(k_p=0.053\), \(\beta_1=15\), \(\beta_2=380\). Simulation beat PID and integral-fuzzy on rise time, overshoot, and post-disturbance recovery — see [/references/huang-2018-ladrc-hvac.md](/references/huang-2018-ladrc-hvac.md).

## Project note

LADRC-on-Critical-Zone water control is **removed** — **superseded by ADR 0004** (ADR 0002 is historical). Live SWT is weather-curve-only; Huang’s plant (coil water **flow**) and gains remain literature only, not the App path.

## Related

- [/concepts/madrc.md](/concepts/madrc.md)
- [/references/wang-2026-madrc-sst.md](/references/wang-2026-madrc-sst.md)

# Citations

- [/references/huang-2018-ladrc-hvac.md](/references/huang-2018-ladrc-hvac.md) §3.1, Tables 6–7
