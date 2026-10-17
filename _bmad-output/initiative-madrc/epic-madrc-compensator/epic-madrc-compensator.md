---
tracker_id: ""
key: ""
type: epic
title: "MADRC inertia compensator G_cp"
parent: initiative-madrc
covers: [R4, R6]
after: []
assignee: ""
risk: high
estimate: ""
estimate_basis: ""
---

# MADRC inertia compensator G_cp

## Description

If epic-madrc-decide records go on \(G_{cp}\), implement the inertia compensator on the ESO command path (\(u_f = G_{cp}u\)) with configurable order/time-constant, proven by unit/sim on a high-order lag plant model. If no-go, this epic is dropped — no production \(G_{cp}\) stubs.

## Outcome

The ADRC Controller feeds the ESO a lag-aligned command when MADRC is go; the signal is green unit/sim gates for observer alignment and/or milder SWT command motion vs the decide-epic baseline, plus ship-path docs for \(G_{cp}\).

## Requirements

- E1 (R4): \(G_{cp}\) on ESO \(u\) path; config for \(n\)/\(T\); unit/sim vs baseline; absent entirely on no-go.
- E2 (R6): Ship-path docs for the compensator (CONTEXT / calibration / agent context) when go; skipped when epic dropped.

## Done when

1. On go: \(G_{cp}\) is in the App plant channel with configurable parameters and green unit/sim gates from R4.
2. On go: ship-path R6 docs describe the compensator and how it sits next to known-input residue / FF policy from the ADR.
3. On no-go: epic dropped; no \(G_{cp}\) code or docs claiming it shipped.
4. Handoff for scheduling: when \(T\) is scheduled on \(G_{cp}\), the \(T\) parameter exists on the plant channel for epic-madrc-scheduling.

## Boundaries

ESO \(u\)-path compensator only. Not jump diagnosis, not interval choice, not FF policy (decide epic). Not \(k_p\)/\(T\) scheduling implementation. Not online \(b_0\)/ωo. Not field trials.

## References

- parent — _bmad-output/initiative-madrc/initiative-madrc.md, Requirements R4, R6
- upstream — _bmad-output/initiative-madrc/epic-madrc-decide/epic-madrc-decide.md (go on \(G_{cp}\); interval; harness)
- concept — knowledge/concepts/madrc.md
- constraint — docs/adr/0002-ladrc-critical-zone-control.md (known-input residue must remain coherent with \(u_f\))

## Notes

- Waits on epic-madrc-decide because: go on \(G_{cp}\), control_interval / plant-channel constraints, and unit/sim harness.
- Decision: 2026-10-17 — envelope only; inception deferred until decide epic is selected.
