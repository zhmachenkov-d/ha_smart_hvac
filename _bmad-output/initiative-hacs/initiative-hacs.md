---
tracker_id: ""
key: ""
type: initiative
title: "HACS AppDaemon custom repository"
parent: none
covers: [R1, R2, R3, R4, R5, R6]
after: []
assignee: ""
risk: medium
estimate: ""
estimate_basis: ""
---

# HACS AppDaemon custom repository

## Description

Ship ha-smart-hvac as a public GitHub repository that strangers can add in HACS as an AppDaemon custom repository — same monorepo as Exclusive Session, no extract/mirror. Intent and ceiling are locked in `_bmad-output/forge-hacs-packaging-meaning/`. Dual-layout prep, publish knobs, history hygiene, public flip, and release automation already landed (see Notes). Remaining tree work is stranger-install verify under epic-hacs-stranger-install-verify.

## Outcome

A Home Assistant operator can install ha-smart-hvac from HACS (custom repository, AppDaemon category) onto a published Release and run the HVAC app with their own `apps.yaml`; the signal is a clean stranger install path without house entity IDs in the published tree or GitHub-served history.

## Requirements

- R1 — Dual layout: canonical Python at repo-root `apps/ha_smart_hvac/`; Exclusive Session loads it via `app_dir` (no symlink, no `appdaemon/apps/` nest). `apps/` contains only that package directory (HACS AppDaemon rule).
- R2 — House wiring is config, not package: real `apps/apps.yaml` gitignored; root `apps.yaml.example` placeholders only (not under `apps/`); no live house entity IDs in the tracked tree.
- R3 — History hygiene: live house `apps.yaml` content absent from refs GitHub serves when the repo is public (`main`, pushed branches, tags).
- R4 — HACS publish surface: root `hacs.json`, HACS Validate Action (`category: appdaemon`), install-first README with concrete Production add-on vs stranger HACS `app_dir` examples.
- R5 — Releases: published GitHub Releases (HACS install/update path); after baseline, automated train on Conventional Commits to `main`.
- R6 — Ceiling: public custom repository only — not `hacs/default` inclusion.

## Done when

1. A stranger can add this repo in HACS as AppDaemon, install from a published Release, and find `ha_smart_hvac/` under their AppDaemon apps path.
2. README (or linked example) shows concrete `app_dir` for Exclusive Session, Production add-on, and stranger HACS path, including the add-on vs `<config>/appdaemon/apps` mismatch.
3. Tracked tree and GitHub-served history carry no live house entity IDs from `apps.yaml`.
4. `hacs.json` + Validate workflow stay green on the default branch; Releases continue to cut for releasing changes on `main`.
5. Docs and agent context never claim `hacs/default` inclusion or that packaging is an extract/mirror repo.

## Boundaries

Capability / distribution boundary: AppDaemon HACS packaging and public-repo readiness for this monorepo. Not algorithm changes, not MADRC/`b0`/`ωo` adaptation, not Production Exclusive Session policy beyond layout/`app_dir`, not default-store inclusion. Tracer path across epics: stranger-install verify only (delivery already shipped outside the ticket tree).

- Touch point: Production AppDaemon add-on config — `app_dir` docs used by stranger verify; owner: epic-hacs-stranger-install-verify
- Touch point: GitHub Releases / branch protection secrets — release train already delivered; not owned by the remaining epic

## References

- forge — _bmad-output/forge-hacs-packaging-meaning/forge-hacs-packaging-meaning.md
- forge — _bmad-output/forge-hacs-release-automation/forge-hacs-release-automation.md
- research — _bmad-output/research-hacs-appdaemon-feasibility-for-ha-smart/research-hacs-appdaemon-feasibility-for-ha-smart.md
- plan — _bmad-output/plan-hacs-packaging.md (dual layout + history hygiene; status built)
- plan — _bmad-output/plan-hacs-publish.md (publish knobs; status built)
- plan — _bmad-output/plan-hacs-release-automation.md
- deferred — _bmad-output/deferred-work.md (HACS publish + release train marked done 2026-10-03)
- constraint — forge-hacs-packaging-meaning Locked/Rejected (custom-repo ceiling; no extract/mirror)

## Notes

- Assumption: initiative slug `initiative-hacs` matches the user’s “hacs” label; title is the forge outcome, not a new product name.
- Decision: repo ticketing store; active initiative switched here (2026-10-17).
- Parked: `hacs/default` inclusion (R6 / forge Rejected).
- Parked: Validate workflow failures on some PR refs (`Repository not loaded properly in HACS`) while `main`/schedule Validate is green — treated as Action noise; gate remains default-branch Validate (2026-10-17).
- Decision: 2026-10-17 audit — R1–R3, R5–R6, and R4 *delivery* (hacs.json, Validate on main, README, Releases, public repo, history hygiene) satisfied by prior shipped plans outside this ticket tree; no platform-baseline epic.
- Decision: 2026-10-17 — option 2: one hitl epic for stranger-install verify; initiative Done when #2–#5 treated as already met; #1 owned by epic-hacs-stranger-install-verify.
- Decision: 2026-10-17 slice+inception approved — epic covers [R4]; one hitl story; Validate PR triage parked; no refactor sweep.
- Decision: 2026-10-17 — HACS install broken: `apps.yaml.example` under `apps/` stole first contents slot; HACS local path = repo name so package/repo must be valid Python id. Rename package + GitHub repo to `ha_smart_hvac`; move example to repo root.
- Decision: 2026-10-17 verify 1.1 — Done when #1 package path is `ha_smart_hvac/` (aligned with rename).
