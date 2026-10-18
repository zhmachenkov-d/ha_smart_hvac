# Knowledge log

Append-only history of OKF ingest and lint passes.

## 2026-10-18 — Ingest Sonoff TRVZB Zigbee protocol

- **Source:** `raw/sonoff-trvzb/` (Zigbee2MQTT device page, ZHA quirk `trvzb.py`, interview signature from zha-device-handlers#2772, SONOFF product help).
- **Created:** reference `sonoff-trvzb-zigbee`; concept `sonoff-trvzb`.
- **Updated:** `zone`, `zone-error` cross-links; root `index.md` recent ingest.
- **House fit:** TRVZB climate entities supply setpoint + heating/idle for Zone Error; App does not write TRV valve/`0xFC11`; zone air for LADRC stays on separate sensors.

## 2026-07-08 — Ingest Wang et al. 2026 (adaptive MADRC SST)

- **Source:** `raw/wang-2026-madrc-sst/processes-14-00308.pdf` (Wang, Tong, Wu, Zheng, Li, Jia; *Processes* 14(2):308; DOI [10.3390/pr14020308](https://doi.org/10.3390/pr14020308)). HTML/`mdpi.com` PDF endpoints 403 from this environment; full PDF fetched from `mdpi-res.com` CDN.
- **Created:** reference page; concept `madrc`.
- **Updated:** `adrc`, `ladrc`, `extended-state-observer`, `total-disturbance`, `plant`; Huang 2018 reference cross-link; `CONTEXT.md` MADRC glossary line; root `index.md`.
- **Not decided:** whether house ADRC uses MADRC-style inertia compensation or gain scheduling vs outdoor/demand; SST valve/cascade ≠ OpenTherm water-setpoint plant.

## 2026-07-08 — Ingest Huang et al. 2018 (LADRC HVAC)

- **Source:** `raw/huang-2018-ladrc-hvac/ica_2018020914354683.pdf` (Huang, Li, Ma; *Intelligent Control and Automation* 9:1–9; DOI [10.4236/ica.2018.91001](https://doi.org/10.4236/ica.2018.91001)). Host path was unavailable inside the container; PDF fetched from SCIRP open access.
- **Created:** bundle scaffold (`index.md`, type dirs, ingest playbook); reference page; concepts `adrc`, `ladrc`, `extended-state-observer`, `total-disturbance`.
- **Glossary:** `CONTEXT.md` — LADRC and Extended State Observer one-liners; ADRC Controller wording aligned.
- **Not decided:** whether this project's ADRC Controller is LADRC, nonlinear ADRC, or another form; OpenTherm water-setpoint plant ≠ paper's AHU coil-flow plant.
