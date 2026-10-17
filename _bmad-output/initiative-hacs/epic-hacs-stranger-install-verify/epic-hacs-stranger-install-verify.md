---
tracker_id: ""
key: ""
type: epic
title: "Stranger HACS install verify"
parent: initiative-hacs
covers: [R4]
after: []
assignee: ""
status: done
risk: medium
estimate: ""
estimate_basis: ""
---

# Stranger HACS install verify

## Description

Proves the HACS publish surface end to end: a person installs `ha_smart_hvac` from a published GitHub Release via HACS custom repository on a Home Assistant instance (not Exclusive Session) and loads the HVAC app with wiring from root `apps.yaml.example` (`module: ha_smart_hvac`).

## Outcome

An operator following the README stranger path gets a running `HvacApp` from HACS; the signal is AppDaemon loading `ha_smart_hvac` under the HACS apps path without missing-module errors.

## Requirements

- E1 (R4): Stranger install — add this repo as a HACS AppDaemon custom repository, install from a published Release, set `app_dir` when the add-on default differs from the HACS download path, create `apps.yaml` beside `ha_smart_hvac/` from the example placeholders, and confirm the app loads. (parent Done when #1 / R4 publish surface)

## Done when

1. On a HA instance that is not Exclusive Session, HACS install from a published Release places `ha_smart_hvac/` under the AppDaemon apps path used by that instance.
2. With `app_dir` set per README when needed and `apps.yaml` from the example (placeholders replaced with that house’s entities), AppDaemon initializes `HvacApp` without missing-module or wrong-path errors.
3. The verify steps and result are recorded in this epic’s Notes (or the story plan) so the initiative Done when #1 has evidence.

## Boundaries

Human install verification and docs-only `app_dir` touch for Production/stranger paths. Not dual-layout rework, not history rewrite, not release-train changes, not `hacs/default` inclusion, not LADRC/algorithm work. Validate CI on PR refs is parked at the initiative (main/schedule Validate remains the gate).

## References

- parent — _bmad-output/initiative-hacs/initiative-hacs.md, Requirements R4 and Done when #1
- forge — _bmad-output/forge-hacs-packaging-meaning/forge-hacs-packaging-meaning.md, Locked ceiling
- doc — README.md, Install with HACS and `app_dir` examples
- example — apps.yaml.example
- constraint — custom repository only; not `hacs/default`

## Notes

- Decision: 2026-10-17 inception — one hitl story (tracer = whole epic); no Validate PR triage entry; no refactor sweep (<3 entries).
- Assumption: a published Release on `main` and README/`apps.yaml.example` on that Release are sufficient prerequisites (already on `main`).
- Decision: 2026-10-17 refine 1.1 — Done when #1–#2 package path is `ha_smart_hvac/` (not `hvac/`).
- Verify 2026-10-17 (story 1.1): non-Exclusive Session HA; HACS custom repo → install Release `v1.0.0`; package at `/config/appdaemon/apps/ha_smart_hvac/`; `apps.yaml` beside package from `apps.yaml.example` with house placeholders replaced; wiring `module: ha_smart_hvac`, `class: HvacApp` (apps.yaml key `hvac`); AppDaemon log `HVAC LADRC app initialized` then control ticks. Done when #1–#3 met.
- Decision: 2026-10-17 — epic closed; closure check SAFE_TO_CLOSE (Done when #1–#3 MET; child 1.1 done).
