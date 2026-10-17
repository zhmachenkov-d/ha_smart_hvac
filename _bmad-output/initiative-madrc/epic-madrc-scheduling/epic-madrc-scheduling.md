---
tracker_id: ""
key: ""
type: epic
title: "Schedule kp and T by regime"
parent: initiative-madrc
covers: [R5, R6]
after: []
assignee: ""
risk: high
estimate: ""
estimate_basis: ""
---

# Schedule kp and T by regime

## Description

If epic-madrc-decide records go on adaptive scheduling, implement \(k_p\) and \(T\) schedules vs the ADR’s regime signal, leaving \(b_0\) and ωo fixed online, and apply the ADR’s coexistence or replace rule for ωc auto-tune. If no-go, drop this epic. The after-link to epic-madrc-compensator applies only when the ADR schedules \(T\) on \(G_{cp}\) (or otherwise requires the compensator); if the ADR allows scheduling without \(G_{cp}\), that gate is skipped.

## Outcome

Controller gain and compensation time-constant track the chosen operating regime when scheduling is go; the signal is green unit/sim gates plus ship-path docs, without online \(b_0\)/ωo changes.

## Requirements

- E1 (R5): Schedule \(k_p\) and \(T\) vs regime; \(b_0\)/ωo fixed online; ωc auto-tune coexist or replace per ADR; absent on no-go.
- E2 (R6): Ship-path docs for scheduling when go; skipped when epic dropped.

## Done when

1. On go: scheduling is in the App with the ADR regime signal and green unit/sim gates from R5.
2. On go: ωc auto-tune behavior matches the ADR (coexist or replace) under unit/sim.
3. On go: ship-path R6 docs describe the schedule and regime.
4. On no-go: epic dropped; no scheduling code claiming it shipped.
5. Prerequisites respected: decide-epic go + rules; compensator \(T\) only when the ADR requires \(G_{cp}\).

## Boundaries

Gain/\(T\) scheduling only. Not \(G_{cp}\) structure (compensator epic). Not FF keep/drop (decide epic). Not online \(b_0\)/ωo. Not field trials.

## References

- parent — _bmad-output/initiative-madrc/initiative-madrc.md, Requirements R5, R6
- upstream — _bmad-output/initiative-madrc/epic-madrc-decide/epic-madrc-decide.md (go on scheduling; regime; ωc rule; without-\(G_{cp}\) rule)
- upstream — _bmad-output/initiative-madrc/epic-madrc-compensator/epic-madrc-compensator.md (conditional \(T\) on \(G_{cp}\))
- reference — knowledge/references/wang-2026-madrc-sst.md (scheduling idea; not drop-in gains)
- constraint — docs/adr/0003-online-ladrc-omega-c-auto-tune.md

## Notes

- Waits on epic-madrc-decide because: go on scheduling, regime signal, ωc coexistence, without-\(G_{cp}\) rule.
- Waits on epic-madrc-compensator because: \(T\) on \(G_{cp}\) when ADR requires it; skip if ADR allows scheduling without \(G_{cp}\).
- Decision: 2026-10-17 — envelope only; inception deferred until selected after decide (and compensator if needed).
