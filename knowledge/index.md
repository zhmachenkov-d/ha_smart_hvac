---
okf_version: "0.1"
title: Smart HVAC knowledge
description: Domain depth for AppDaemon HVAC control — OpenTherm plant, weather-curve SWT, multi-zone coordination; ADRC literature retained as prior art.
timestamp: 2026-10-19T14:41:00Z
---

# Smart HVAC knowledge

OKF bundle for this repo. Short glossary terms live in [`CONTEXT.md`](../CONTEXT.md); irreversible choices in [`docs/adr/`](../docs/adr/) (live water path: **ADR 0004**); depth here. ADRC/LADRC/MADRC notes are literature — not the live SWT stack.

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
