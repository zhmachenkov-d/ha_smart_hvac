---
type: Reference
title: Huang et al. 2018 — LADRC for HVAC zone temperature
description: Open-access simulation study comparing LADRC, PID, and integral-fuzzy on a winter AHU zone model.
tags: [adrc, ladrc, hvac, simulation, literature]
timestamp: 2026-07-08T15:45:00Z
resource: raw/huang-2018-ladrc-hvac/
---

# Huang et al. 2018 — LADRC for HVAC zone temperature

Huang, C.-E., Li, C.W., Ma, X.J. (2018). Active-Disturbance-Rejection-Control for Temperature Control of the HVAC System. *Intelligent Control and Automation*, 9, 1–9. DOI: [10.4236/ica.2018.91001](https://doi.org/10.4236/ica.2018.91001). CC BY 4.0.

Immutable copy: [`raw/huang-2018-ladrc-hvac/ica_2018020914354683.pdf`](/raw/huang-2018-ladrc-hvac/ica_2018020914354683.pdf).

## Status

Ingested (first pass) — algorithm ideas extracted; plant numerics left in the PDF.

## What the paper does

Winter AHU control: keep zone air at 20 °C by adjusting **water flow** through an internal heating coil. Builds first-order models for zone, fan (+1–2 °C), heating coil, and sensor; designs a **first-order ESO + second-order linear controller** ([LADRC](/concepts/ladrc.md)); compares Matlab/Simulink response to PID and integral-fuzzy, including a step disturbance at t = 500 s.

Reported simulation metrics (Table 7):

| Controller | Rising time (s) | Overshoot (°C) | Recovery after step (s) |
|------------|-----------------|----------------|-------------------------|
| PID | 240 | 1.04 | 180 |
| Integral-fuzzy | 340 | 0.27 | 235 |
| LADRC | 150 | 0 | 80 |

LADRC tuned parameters (Table 6): \(b_0 = 2.8\), \(k_p = 0.053\), \(\beta_1 = 15\), \(\beta_2 = 380\).

## Fit to this project

Useful as **prior art that LADRC can beat PID on HVAC air-temperature loops under disturbance**. Not a drop-in blueprint:

- Paper plant: AHU coil **water flow** → supply air → zone.
- This repo: [Plant](/concepts/plant.md) OpenTherm **[Set Water Temperature](/concepts/set-water-temperature.md)** is weather-curve-only under ADR 0004 — no LADRC / ADRC Controller on water. The [Multi-Zone Coordinator](/concepts/multi-zone-coordinator.md) feeds CAP-7 only.

## Key sections (PDF)

1. Introduction — ADRC → LADRC motivation; HVAC nonlinearity / coupling
2. HVAC model — zone (Eq. 1–2), fan/sensor, heating coil (Eq. 3–4), Table 3 parameters
3. Control — LADRC ESO/controller (Eq. 5–6); integral-fuzzy alternate; Simulink comparison
4. Conclusion — rise time, zero overshoot, disturbance rejection

## Related literature

- [/references/wang-2026-madrc-sst.md](/references/wang-2026-madrc-sst.md) — adaptive [MADRC](/concepts/madrc.md) on high-order SST (field), complementary plant/regime.

## Linked concepts

- [/concepts/adrc.md](/concepts/adrc.md)
- [/concepts/ladrc.md](/concepts/ladrc.md)
- [/concepts/madrc.md](/concepts/madrc.md)
- [/concepts/extended-state-observer.md](/concepts/extended-state-observer.md)
- [/concepts/total-disturbance.md](/concepts/total-disturbance.md)
- [/concepts/zone.md](/concepts/zone.md)

# Citations

- Raw PDF: `/raw/huang-2018-ladrc-hvac/ica_2018020914354683.pdf`
