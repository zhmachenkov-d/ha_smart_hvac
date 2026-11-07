---
tracker_id: ""
key: ""
type: initiative
title: "Stop LADRC SWT bang-bang from ESO blow-up"
parent: none
covers: [CAP-1, CAP-2, CAP-3, CAP-4, CAP-5]
after: []
assignee: ""
risk: high
estimate: ""
estimate_basis: ""
status: done
---

# Stop LADRC SWT bang-bang from ESO blow-up

## Description

Live LADRC tracking is numerically exploding and thrashing Set Water Temperature between plant limits. This initiative delivers the fix in `_bmad-output/initiative-fix-ladrc-blow-up/tickets/epic-fix-ladrc-blow-up/spec-fix-ladrc-blow-up/` — continuous-form ESO at `dt=60`, tracking-residue known input, retuned plant-channel defaults, an app-level blow-up guard, regression tests, and an ADR 0002 amendment.

## Outcome

Operators get stable water commands under demand instead of 40↔55 thrashing; the signal is the spec's Success signal (finite, non-astronomical `u_track` and smooth `clamp(u_ff + u_track)`).

## Done when

1. Continuous-form ESO + example `b0`/`omega_o` + known input `(command − u_ff)` keep multi-tick runs with realistic zone air finite and `|u_track|` in tens of °C, not 1e6+.
2. A non-finite or over-threshold `u_track` yields feedforward-only command, ESO reset, and a HA WARNING once per episode.
3. Automated tests fail on old `exp_map` / Huang defaults / unguarded explode path and pass on the fixed path.
4. ADR 0002 documents exp_map/`dt=60` failure, continuous-form ESO, C known-input, Huang forbidden, and house calibration; ADR 0003 remains ωc-only.

## Boundaries

Capability boundary: LADRC plant channel for OpenTherm Set Water Temperature in the HVAC AppDaemon app. Not feedforward redesign, not Critical Zone selection, not online `b0`/`omega_o` adaptation, not MADRC, not changing 40/55 plant limits or `control_interval` as the fix. One epic owns the whole fix. Tracer path: continuous-form ESO → C known-input → defaults/ADR → guard → sweep.

- Touch point: live HA Plant Management — ops may turn it off until the fix deploys; owner: epic-fix-ladrc-blow-up

## References

- spec — _bmad-output/initiative-fix-ladrc-blow-up/tickets/epic-fix-ladrc-blow-up/spec-fix-ladrc-blow-up/spec-fix-ladrc-blow-up.md, section Capabilities
- constraint — the same spec, section Constraints
- plan — /home/vscode/.cursor/plans/fix_ladrc_blow-up_4f4b86eb.plan.md

## Notes

- Decision: repo ticketing store (2026-10-16).
- Decision: one epic for all CAP-1–CAP-5; no platform-baseline epic — brownfield fix on existing app (2026-10-16).
- Decision: user asked to proceed for build-auto/loop after store setup (2026-10-16).
- Decision: 2026-10-16 re-slice after party+spikes — CAP-5 continuous-form ESO is primary; epic tickets.toml replaced (2026-10-16).
- Decision: 2026-10-17 closed initiative after epic-fix-ladrc-blow-up Done when #1–#4 met and AI-1…AI-8 shipped (same single epic).
