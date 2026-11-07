---
tracker_id: ""
key: ""
type: epic
title: "Fix LADRC u_track blow-up"
parent: initiative-fix-ladrc-blow-up
covers: [CAP-1, CAP-2, CAP-3, CAP-4, CAP-5]
after: []
assignee: ""
risk: high
estimate: ""
estimate_basis: ""
status: done
---

# Fix LADRC u_track blow-up

## Description

Replace the production `exp_map` ESO discretization with a continuous-form observer at `dt=60`, advance the ESO with post-clamp tracking residue `(command − u_ff)`, retune example `b0`/`omega_o`, add an `hvac_app`-only finite/magnitude blow-up guard (`u_track_max` default 100 °C), lock behavior with regression tests, and amend ADR 0002. Spec: `spec-fix-ladrc-blow-up/` beside this file.

## Outcome

Under heating demand the plant no longer bang-bangs 40↔55 from exploded `u_track`; the spec Success signal is the check.

## Requirements

- CAP-1: Plant-channel example defaults (`b0`, `omega_o`) stay stable with continuous-form ESO and tracking-residue known input. (spec Capabilities)
- CAP-2: `hvac_app` detects non-finite or over-threshold `|u_track|`, resets ESO, issues `clamp(u_ff)`, logs WARNING once per episode. (spec Capabilities)
- CAP-3: Tests reproduce old `exp_map`/Huang divergence, assert new-path boundedness, and cover the guard. (spec Capabilities)
- CAP-4: ADR 0002 amended (discretization, C known-input, Huang forbidden, house calibration); ADR 0003 remains ωc-only. (spec Capabilities)
- CAP-5: `LadrcState` uses continuous-form ESO advance, not `α = 1 − exp(−ωo·dt)`. (spec Capabilities)

## Done when

1. Continuous-form ESO + thermal-band defaults + C known-input keep `u_track`/`z` finite with `|u_track|` in tens of °C over multi-tick runs (`y≈21`, clamp 40..55).
2. Poisoned or exploded `u_track` yields feedforward-only command + ESO reset + WARNING; loop recovers without waiting for zone change / idle / plant-off.
3. Regression suite fails on `exp_map`, Huang defaults, or missing guard and passes on the fixed path (`uv run pytest`).
4. ADR 0002 carries exp_map/`dt=60`, continuous-form ESO, C known-input, Huang warning, and house-calibration note; ADR 0003 unchanged ωc-only.

## Boundaries

HVAC AppDaemon LADRC + example/config wiring + ADR 0002 prose. Not feedforward redesign, Critical Zone selection, online `b0`/`omega_o` adaptation, setpoint min/max changes, MADRC/inertia compensator, changing `control_interval` as the fix, or a guard API inside `LadrcState` (spec Non-goals).

## References

- parent — _bmad-output/initiative-fix-ladrc-blow-up/initiative-fix-ladrc-blow-up.md
- spec — _bmad-output/initiative-fix-ladrc-blow-up/tickets/epic-fix-ladrc-blow-up/spec-fix-ladrc-blow-up/spec-fix-ladrc-blow-up.md
- constraint — the same spec, section Constraints
- adr — docs/adr/0002-ladrc-critical-zone-control.md
- adr — docs/adr/0003-online-ladrc-omega-c-auto-tune.md (ωc-only; unchanged)

## Notes

- Decision: blow-up guard in `hvac_app` only; magnitude threshold is config default 100 °C (spec Q&A, 2026-10-16).
- Decision: no platform-baseline epic; brownfield (2026-10-16).
- Decision: optional refuse-to-advance after guard trip is in scope for the guard story (2026-10-16).
- Decision: 2026-10-16 re-slice after party+spikes — primary fix continuous-form ESO (CAP-5); companion C known-input `(command − u_ff)`; MADRC out; Huang still invalid. Tracer = entry 1. Build order 1→2→3→4; entry 5 refactor sweep kept. Story 2 kept standalone (not merged). Prior retune→guard inception superseded; blocked plan for old story 1.1 is obsolete. Build-auto/loop: `plan_checkpoint` and `done_checkpoint` on all five entries.
- Decision: 2026-10-17 closed epic (AI-8) after retro `accepted-with-open-items` and AI-1…AI-7 shipped; Done when #1–#4 met (pytest 54 green on ladrc/hvac_app/tuner). Default `u_track_max` is now 250 (package A), superseding the Notes line that said 100.
