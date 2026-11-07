---
id: 1
type: story
title: "Verify stranger HACS install"
parent: epic-hacs-stranger-install-verify
covers: [E1, R4]
after: []
hitl: true
risk: medium
---

# Verify stranger HACS install

## Description

On a Home Assistant instance that is not Exclusive Session, add this GitHub repository as a HACS AppDaemon custom repository, install ha_smart_hvac from a published Release, set app_dir when the add-on default differs from the HACS download path, create apps.yaml beside ha_smart_hvac/ from root apps.yaml.example (module: ha_smart_hvac, class: HvacApp), and confirm HvacApp loads. Record the verify steps and result in the epic Notes or this story's plan so initiative Done when #1 has evidence.

## Acceptance Criteria

Verify: AppDaemon logs show HvacApp initialized without missing-module or wrong-path errors; package directory ha_smart_hvac is under the HACS apps path for that instance; verify steps and result are recorded in the epic Notes or the story plan.

## References

- parent — _bmad-output/initiative-hacs/tickets/epic-hacs-stranger-install-verify/epic-hacs-stranger-install-verify.md
- doc — README.md, Install with HACS and app_dir examples
- example — apps.yaml.example

## Notes

- Source conflict: epic Done when #1–#2 said hvac/; Decision: use ha_smart_hvac/ (README, initiative Notes 2026-10-17 rename).
