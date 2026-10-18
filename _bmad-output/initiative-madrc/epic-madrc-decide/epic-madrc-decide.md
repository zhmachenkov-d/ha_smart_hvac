---
tracker_id: ""
key: ""
type: epic
title: "Diagnose jumps, interval, MADRC and FF go/no-go"
parent: initiative-madrc
covers: [R1, R2, R3, R6, R7, R8]
after: []
assignee: ""
risk: high
estimate: ""
estimate_basis: ""
---

# Diagnose jumps, interval, MADRC and FF go/no-go

## Description

Classify commanded Set Water Temperature jumps, choose `control_interval`, and record ADR go/no-go for MADRC \(G_{cp}\), \(k_p\)/\(T\) scheduling, and Weather Feedforward keep vs drop — with unit/sim evidence. If FF is dropped, remove or disable it here. Refuse-path and ADR-outcome docs (R6) land here so the initiative can close on dual MADRC no-go without later epics.

## Outcome

Maintainers have an ADR and unit/sim artifacts that settle jumps, interval, MADRC structure gates, and Weather Feedforward policy before any compensator or scheduling code; the signal is those decisions written and, on FF-drop, FF absent from the App path under test.

## Requirements

- E1 (R1): Jump classification — unit/sim evidence naming dominant causes among tuning, `control_interval`, ESO lag mismatch, other.
- E2 (R2): ADR go/no-go for \(G_{cp}\) and for \(k_p\)/\(T\) scheduling; online \(b_0\)/ωo stay closed unless explicitly opened; settle whether scheduling may ship without \(G_{cp}\); name ωc auto-tune coexistence or replace; name regime signal for scheduling.
- E3 (R3): Choose and document `control_interval` and Euler/ωo/substep coupling; update example/calibration when changed.
- E4 (R7): ADR go/no-go keep vs drop Weather Feedforward; unit/sim with vs without FF; residue semantics when \(u_{ff}=0\); outdoor vs scheduling if FF dropped.
- E5 (R8): If drop — remove/disable FF in App, config, docs with unit/sim gates; if keep — no removal, calibration still documents manual FF.
- E6 (R6): Refuse / ADR-outcome CONTEXT, house-calibration, and agent-context updates for closed doors and chosen interval/FF policy (ship-path MADRC docs wait on later epics when go).

## Done when

1. R1 classification artifact exists and is cited from the ADR or epic Notes.
2. ADR records go/no-go for \(G_{cp}\), scheduling (including without-\(G_{cp}\) rule), and Weather Feedforward keep/drop, with \(b_0\)/ωo policy explicit.
3. `control_interval` (and ωo/substep band) is documented in house-calibration / example config.
4. R8 matches R7: FF removed under green unit/sim, or retained with calibration text; no FF auto-tune.
5. R6 refuse/ADR-outcome docs match the ADR for MADRC undecided→decided and FF policy.
6. Downstream handoffs named: go flags, interval, regime signal, ωc rule, sim harness location — so epics 2–3 do not reinvent them.

## Boundaries

Diagnosis, ADR decisions, `control_interval`, Weather Feedforward keep/drop implementation, and refuse-path docs. Not \(G_{cp}\) production structure (epic-madrc-compensator). Not \(k_p\)/\(T\) scheduling implementation (epic-madrc-scheduling). Not Exclusive Session field trials. Not FF auto-tune. Not online \(b_0\)/ωo unless this epic’s ADR opens them.

## References

- parent — _bmad-output/initiative-madrc/initiative-madrc.md, Requirements R1–R3, R6–R8
- concept — knowledge/concepts/madrc.md
- reference — knowledge/references/wang-2026-madrc-sst.md
- constraint — docs/adr/0002-ladrc-critical-zone-control.md
- constraint — docs/adr/0003-online-ladrc-omega-c-auto-tune.md
- calibration — docs/house-calibration.md

## Notes

- Decision: 2026-10-17 — opening epic; no platform-baseline (initiative Notes).
- Decision: 2026-10-17 — R7/R8 owned here; no separate FF epic (user confirmed).
- Decision: 2026-10-17 — whether scheduling may ship without \(G_{cp}\) is settled in this epic’s ADR (R2), not presupposed. Settled in ADR 0004: without-\(G_{cp}\) **forbidden** (epic-madrc-scheduling stays gated on epic 2; no skip).
- Decision: 2026-10-17 — inception approved: nine entries (harness → metrics spike → classify ∥ interval ∥ FF → ADR → FF apply → interval/docs → refactor sweep); outdoor is a harness input; user confirmed outdoor=yes.
- Decision: 2026-10-17 — tracer bullet is entry 1 (plant-lag multi-tick harness through LADRC track/guard/residue with FF toggle and outdoor input); classification and ADR follow that path.
- Decision: 2026-10-17 — refactor sweep kept (default for >3 entries).
- Assumption: unit/sim harness from entry 1 is the shared setup later epics reuse.
- Sequencing: entries 3, 4, 5 may run in parallel after spike 2; partition test modules to avoid harness API collisions.
- Metrics for R1/R2/R7: `spike-metrics-for-jump-madrc-and-ff-decisions.md`
- metrics spike: accepted 2026-10-17; X=30%; ε=10; Z=0.2
- R1 classification: `story-classify-swt-command-jumps.md` (Screen-2 class (c); evidence in `tests/test_r1_jump_classification.py`)
- R3 control_interval candidates: `story-compare-control-interval-candidates.md` (recommend 30; evidence in `tests/test_r3_control_interval_candidates.py`)
- R7 weather feedforward compare: `story-compare-weather-feedforward-on-vs-off.md` (cold/hot FF-on vs zero_uff; evidence in `tests/test_r7_weather_feedforward_compare.py`)
- ADR go/no-go (R2/R3/R7): `docs/adr/0004-madrc-ff-interval-go-no-go.md` (thin see-0004 pointers in 0002/0003); stub follow-on `epic-online-b0` in initiative `tickets.toml`
