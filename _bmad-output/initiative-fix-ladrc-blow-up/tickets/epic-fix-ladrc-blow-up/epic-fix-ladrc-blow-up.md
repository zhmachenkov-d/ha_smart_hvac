---
tracker_id: ""
key: ""
type: epic
title: "Fix LADRC u_track blow-up"
parent: initiative-fix-ladrc-blow-up
covers: [R1, R2, R3, R4, R5]
after: []
assignee: ""
risk: high
estimate: ""
estimate_basis: ""
status: done
sources: [/home/vscode/.cursor/plans/fix_ladrc_blow-up_4f4b86eb.plan.md]
companions: [_bmad-output/initiative-fix-ladrc-blow-up/tickets/epic-fix-ladrc-blow-up/architecture-diagrams.md, ../../../../docs/adr/0002-ladrc-critical-zone-control.md, ../../../../docs/adr/0003-online-ladrc-omega-c-auto-tune.md]
---

# Fix LADRC u_track blow-up

## Description

Replace the production `exp_map` ESO discretization with a continuous-form observer at `dt=60`, advance the ESO with post-clamp tracking residue `(command − u_ff)`, retune example `b0`/`omega_o`, add an `hvac_app`-only finite/magnitude blow-up guard (`u_track_max` default 100 °C), lock behavior with regression tests, and amend ADR 0002. Spec folded into this epic (Requirements R1–R5).

## Outcome

Under heating demand the plant no longer bang-bangs 40↔55 from exploded `u_track`; the spec Success signal is the check.

## Requirements

- R1: Plant-channel example defaults (`b0`, `omega_o`) stay stable with continuous-form ESO and tracking-residue known input. (spec Capabilities)
- R2: `hvac_app` detects non-finite or over-threshold `|u_track|`, resets ESO, issues `clamp(u_ff)`, logs WARNING once per episode. (spec Capabilities)
- R3: Tests reproduce old `exp_map`/Huang divergence, assert new-path boundedness, and cover the guard. (spec Capabilities)
- R4: ADR 0002 amended (discretization, C known-input, Huang forbidden, house calibration); ADR 0003 remains ωc-only. (spec Capabilities)
- R5: `LadrcState` uses continuous-form ESO advance, not `α = 1 − exp(−ωo·dt)`. (spec Capabilities)
- R1 (CAP-1): Operators get plant-channel LADRC example defaults (`b0`, `omega_o`) in a thermal starting band that stay numerically stable with the fixed ESO and tracking-residue known input at the app’s 60 s sample time. Success: With the new example defaults (not Huang `2.8` / `19.49`), multi-tick runs at realistic `y≈21`, `T_r` near zone air, plant write `command = clamp(u_ff + u_track)`, and ESO known input `(command − u_ff)` keep `u_track`, `z1`, and `z2` finite with `|u_track|` in a sane band (tens of °C, not 1e6+). `apps/apps.yaml.example` carries the new values.
- R2 (CAP-2): On a bad control tick the app detects non-finite or magnitude-exploded `u_track`, clears diverged ESO state, and still issues a safe feedforward-only water command for that tick. Success: In the `hvac_app` tick path, after `compute_tracking`, when `u_track` is non-finite or `|u_track|` exceeds the configured magnitude threshold (example/default **100** °C), the tick yields `command = clamp(u_ff)`, ESO `reset(measured)`, and a WARNING visible in HA logs once per episode; the loop does not remain bricked until zone change / idle / plant-off.
- R3 (CAP-3): Automated tests lock the blow-up diagnosis and the fix so the broken discrete map, Huang gains, or an unguarded explode path cannot silently return. Success: Tests (a) reproduce divergence under the old `exp_map` discretization and/or Huang-scale gains, (b) assert continuous-form ESO + new defaults + tracking-residue known input stay bounded over N ticks, and (c) assert the guard path resets and returns feedforward-only command.
- R4 (CAP-4): Maintainers reading ADR 0002 know why `exp_map` at `dt=60` fails, that the ESO must use a continuous-form advance and tracking-residue known input, that Huang `b0`/`ωo` must not be used here, and that new defaults need house calibration. Success: ADR 0002 carries that amendment; ADR 0003 remains ωc-only (no claim of online `b0`/`omega_o` adaptation).
- R5 (CAP-5): The LADRC ESO advances with a continuous-form observer (`β1 = 2ωo`, `β2 = ωo²` over the sample) that remains usable at `dt=60` with thermal-band `omega_o`, instead of the production `α = 1 − exp(−ωo·dt)` gain map. Success: With continuous-form advance and known input `(command − u_ff)`, multi-tick runs using thermal-band gains (`b0 ~ 1e-4–1e-3`, `omega_o ~ 0.01–0.05`, including `omega_o` on the order of a few×`omega_c`) keep `u_track`/`z` finite with `|u_track|` in tens of °C; the same scenario under `exp_map` diverges. Integrator choice (RK, substeps, matrix-exp equivalent) is free if these tests pass.

## Constraints

- Plant write stays `command = clamp(u_ff + u_track)` (absolute SWT). After clamp, ESO known input is **`(command − u_ff)`**, not absolute `command` and not pre-clamp `u_track`.
- `LadrcState.advance` must **not** use the `α = 1 − exp(−ωo·dt)` gain map at `dt=60`; use continuous-form integration locked by R5 tests. Integrator choice (RK, matrix-exp, or equivalent) and substep count are free if those tests pass.
- Online auto-tune remains **ωc only** (ADR 0003); this work must not introduce online `b0` or `omega_o` adaptation.
- Do not change `setpoint_min`/`setpoint_max` (plant limits 40/55); bang-bang was clamp thrashing from diverged `u_track`, not a limits bug.
- Exact numeric example defaults are locked by R3 boundedness tests. Starting-point band: `b0 ~ 1e-4–1e-3` °C_air/(°C_water·s); `omega_o ~ 0.01–0.05`. **`omega_o > omega_c` is not a hard constraint** at this sample time.
- The `|u_track|` magnitude blow-up threshold is a **config field** with example/default **100** (°C); non-finite `u_track` always trips regardless of that value.
- Blow-up guard lives in **`hvac_app` only** (after `compute_tracking`); `LadrcState` stays a pure tracker/ESO and does not grow a guard API.
- Optionally refuse to `advance` with non-finite state after a guard trip.

## Done when

1. Continuous-form ESO + thermal-band defaults + C known-input keep `u_track`/`z` finite with `|u_track|` in tens of °C over multi-tick runs (`y≈21`, clamp 40..55).
2. Poisoned or exploded `u_track` yields feedforward-only command + ESO reset + WARNING; loop recovers without waiting for zone change / idle / plant-off.
3. Regression suite fails on `exp_map`, Huang defaults, or missing guard and passes on the fixed path (`uv run pytest`).
4. ADR 0002 carries exp_map/`dt=60`, continuous-form ESO, C known-input, Huang warning, and house-calibration note; ADR 0003 unchanged ωc-only.

## Boundaries

HVAC AppDaemon LADRC + example/config wiring + ADR 0002 prose. Not feedforward redesign, Critical Zone selection, online `b0`/`omega_o` adaptation, setpoint min/max changes, MADRC/inertia compensator, changing `control_interval` as the fix, or a guard API inside `LadrcState` (spec Non-goals).

- Non-goal: Changing feedforward structure or Critical Zone selection.
- Non-goal: Adapting `b0` / `omega_o` online.
- Non-goal: Changing Set Water Temperature min/max (40/55).
- Non-goal: Treating the `omega_c` tuner as the fault or changing its bounds.
- Non-goal: Putting the blow-up guard inside `LadrcState`.
- Non-goal: Adding MADRC / inertia-compensator on the ESO u-path.
- Non-goal: Changing `control_interval` away from 60 s as the fix.

## References

- parent — _bmad-output/initiative-fix-ladrc-blow-up/initiative-fix-ladrc-blow-up.md
- constraint — the same spec, section Constraints
- adr — docs/adr/0002-ladrc-critical-zone-control.md
- adr — docs/adr/0003-online-ladrc-omega-c-auto-tune.md (ωc-only; unchanged)
- companion — architecture-diagrams.md
- companion — ../../../../docs/adr/0002-ladrc-critical-zone-control.md
- companion — ../../../../docs/adr/0003-online-ladrc-omega-c-auto-tune.md

## Notes

- Decision: blow-up guard in `hvac_app` only; magnitude threshold is config default 100 °C (spec Q&A, 2026-10-16).
- Decision: no platform-baseline epic; brownfield (2026-10-16).
- Decision: optional refuse-to-advance after guard trip is in scope for the guard story (2026-10-16).
- Decision: 2026-10-16 re-slice after party+spikes — primary fix continuous-form ESO (R5); companion C known-input `(command − u_ff)`; MADRC out; Huang still invalid. Tracer = entry 1. Build order 1→2→3→4; entry 5 refactor sweep kept. Story 2 kept standalone (not merged). Prior retune→guard inception superseded; blocked plan for old story 1.1 is obsolete. Build-auto/loop: `plan_checkpoint` and `done_checkpoint` on all five entries.
- Decision: 2026-10-17 closed epic (AI-8) after retro `accepted-with-open-items` and AI-1…AI-7 shipped; Done when #1–#4 met (pytest 54 green on ladrc/hvac_app/tuner). Default `u_track_max` is now 250 (package A), superseding the Notes line that said 100.
