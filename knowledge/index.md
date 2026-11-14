---
okf_version: "0.1"
title: Smart HVAC knowledge
description: Domain depth for AppDaemon HVAC control — OpenTherm plant, weather-curve SWT with supply rise-rate trip (ADR 0007), multi-zone coordination; PID/RLS and ADRC literature as historical prior art.
timestamp: 2026-11-14T14:53:00Z
---

# Smart HVAC knowledge

OKF bundle for this repo. Short glossary terms live in [`CONTEXT.md`](../CONTEXT.md); irreversible choices in [`docs/adr/`](../docs/adr/) (live water path: **ADR 0007** — weather-curve SWT + supply trip; ADR 0005 / 0006 historical); depth here. ADRC/LADRC/MADRC and RLS adaptive PID notes retain literature or historical mechanics — not the live SWT stack.

## Start here

| Area | Index |
|------|-------|
| Domain entities & algorithms | [/concepts/index.md](/concepts/index.md) |
| Architectural choices | [/decisions/index.md](/decisions/index.md) |
| External specs & papers | [/references/index.md](/references/index.md) |
| Repeatable workflows | [/playbooks/index.md](/playbooks/index.md) |

## Recent ingest

- [/references/wang-2026-madrc-sst.md](/references/wang-2026-madrc-sst.md) — adaptive MADRC on superheated steam temperature (simulation + 660 MW field).
- [/references/huang-2018-ladrc-hvac.md](/references/huang-2018-ladrc-hvac.md) — LADRC vs PID/fuzzy for AHU zone temperature (simulation).
