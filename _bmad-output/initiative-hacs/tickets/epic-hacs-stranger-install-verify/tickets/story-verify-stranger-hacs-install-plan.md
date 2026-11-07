---
title: 'Verify stranger HACS install'
type: 'chore'
ticket: '1'
created: '2026-10-17'
status: done
baseline_revision: '31202e2cad15893b54c0d219fecd5cfa049a1618'
route: 'oneshot'
route_source: 'auto'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Initiative Done when #1 still needs evidence that a stranger can install `ha_smart_hvac` from HACS (custom repository + published Release) on a HA instance that is not Exclusive Session and get `HvacApp` loading.

**Approach:** Follow README Install with HACS and stranger `app_dir` on a real (non-Exclusive Session) HA instance using Latest Release `v1.0.0` (or newer). Confirm package path and AppDaemon init logs. Record steps and result in this plan's Implementation Notes and in the epic Notes. Fix README/`apps.yaml.example` only if the install proves them wrong.

**Decision:** HA instance is not Exclusive Session (user confirmed). Guided install (mode A). Target Release `v1.0.0`.

</frozen-after-approval>

## Implementation Notes

Oneshot: HITL verify plus evidence write-up; agent code change expected only if docs fail the install. No pytest/ruff gate for the happy path.

- 2026-10-17: HITL answers — non-Exclusive Session HA; mode A guided; Release v1.0.0. Starting README Install step 1–2.
- 2026-10-17: User confirmed custom repository added (steps 1–2 ok).
- 2026-10-17: HACS install v1.0.0 ok; package at `/config/appdaemon/apps/ha_smart_hvac/`.
- 2026-10-17: User confirmed app_dir + apps.yaml beside package (steps 4–5 ok); AppDaemon restarted.
- 2026-10-17: Verify PASS — AppDaemon logs: `Calling initialize() for hvac` then `hvac: HVAC LADRC app initialized` (16:29:43); subsequent critical-zone ticks. No missing-module / wrong-path errors. Package path `/config/appdaemon/apps/ha_smart_hvac/`; Release v1.0.0; non-Exclusive Session HA.
- 2026-10-17: Wiring evidence — `apps.yaml` beside package from example with house entities filled; `module: ha_smart_hvac`, `class: HvacApp` (app key `hvac` matches AppDaemon log prefix). Live entity IDs not copied into this plan.
- 2026-10-17: Review patch — aligned initiative Done when #1 to `ha_smart_hvac/`; strengthened Notes for module/class and example-based apps.yaml.

## Plan Change Log

## Review Triage Log

- 2026-10-17 quick: module/class not in Notes → medium/patch (notes updated). Example placeholders not recorded → medium/patch (notes updated). status still in-progress mid-pass → false after finalize to built. initiative Done when #1 still `hvac/` → medium/patch (initiative-hacs.md updated).

## Verification

**Manual checks (if no CLI):**
- HACS apps path contains `ha_smart_hvac/` after install from a published Release.
- AppDaemon logs show `HvacApp` initialized without missing-module or wrong-path errors after `apps.yaml` beside the package (`module: ha_smart_hvac`, `class: HvacApp`).
- Epic Notes (or this plan) record the verify steps and result.
