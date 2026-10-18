---
okf_version: "0.1"
title: Smart HVAC knowledge
description: Domain depth for AppDaemon HVAC control — OpenTherm plant, multi-zone coordination, ADRC.
timestamp: 2026-10-18T10:00:00Z
---

# Smart HVAC knowledge

OKF bundle for this repo. Short glossary terms live in [`CONTEXT.md`](../CONTEXT.md); irreversible choices in [`docs/adr/`](../docs/adr/); depth here.

## Start here

| Area | Index |
|------|-------|
| Domain entities & algorithms | [/concepts/index.md](/concepts/index.md) |
| Architectural choices | [/decisions/index.md](/decisions/index.md) |
| External specs & papers | [/references/index.md](/references/index.md) |
| Repeatable workflows | [/playbooks/index.md](/playbooks/index.md) |

## Recent ingest

- [/references/sonoff-trvzb-zigbee.md](/references/sonoff-trvzb-zigbee.md) — Zigbee clusters / `0xFC11` map for house TRV thermostats ([/concepts/sonoff-trvzb.md](/concepts/sonoff-trvzb.md)).
- [/references/wang-2026-madrc-sst.md](/references/wang-2026-madrc-sst.md) — adaptive MADRC on superheated steam temperature (simulation + 660 MW field).
- [/references/huang-2018-ladrc-hvac.md](/references/huang-2018-ladrc-hvac.md) — LADRC vs PID/fuzzy for AHU zone temperature (simulation).
