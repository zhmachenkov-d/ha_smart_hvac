---
tracker_id: ""
key: ""
type: epic
title: "Gate ωc on saturation"
parent: initiative-gate-omega-c-on-saturation
covers: [CAP-1, CAP-2, CAP-3, CAP-4, CAP-5, CAP-6]
after: []
assignee: ""
risk: medium
estimate: ""
estimate_basis: ""
status: done
---

# Gate ωc on saturation

## Description

Delivers the full SPEC-gate-omega-c-on-saturation contract in the HVAC AppDaemon control tick: directional ωc commit clamp with strict apply, write-on-change plant writes, latched ωc decay with adapt skipped, documentation under criterion A, and regression tests.

## Outcome

The live soft-kill-after-underheat path no longer re-enters via saturated ωc ratchet, and a latched loop can step ωc down on real `|u_track|` without ops-only recovery; signal is the parent initiative / spec Success signal.

## Requirements

- CAP-1: Directional clamp — skip commit when `(command ≥ max ∧ ωc↑)` or `(command ≤ min ∧ ωc↓)`; still skip on guard trip; allow relieving moves. (spec Capabilities)
- CAP-2: Strict apply — blocked proposed ωc must not enter `with_omega_c` / `compute_tracking`. (spec Capabilities)
- CAP-3: Write-on-change — skip `number/set_value` when desired equals entity float; continue tick; unreadable entity fail-closed abort. (spec Capabilities)
- CAP-4: Latch decay — while latch already active at tick start, skip `maybe_adapt`; step ωc down by `max_rate_fraction` when `|u_track| > 0.8 · u_track_max` or non-finite; persist; stop at ≤ band. (spec Capabilities)
- CAP-5: Docs — ADR 0003 Guards and house-calibration §5 describe criterion A and these behaviors. (spec Capabilities)
- CAP-6: Tests lock directional matrix, strict-apply no-ratchet, write-on-change vs fail-closed, and latched decay. (spec Capabilities)

## Done when

1. CAP-1 and CAP-2 hold under a Hass-free saturated upward-proposal scenario (ωc does not climb; tracking uses current ωc when blocked).
2. CAP-3 holds: same float skips HA write without aborting tick side effects; unreadable entity aborts.
3. CAP-4 holds: latched ticks skip adapt and decay persisted ωc until `|u_track| ≤ 0.8 · u_track_max`.
4. CAP-5 docs match criterion A (not headroom-only freeze).
5. CAP-6 test suite for this epic is green under `uv run pytest` on the touched test modules.

## Boundaries

AppDaemon HVAC app tick path and ωc tuner persistence. Spec non-goals: full freeze, ESO anti-windup, changing `u_track_max`/plant limits, hard reset / one-shot safe ωc, online b0/ωo/MADRC.

## References

- parent — _bmad-output/initiative-gate-omega-c-on-saturation/initiative-gate-omega-c-on-saturation.md
- spec — _bmad-output/initiative-gate-omega-c-on-saturation/spec-gate-omega-c-on-saturation/spec-gate-omega-c-on-saturation.md, section Capabilities
- companion — _bmad-output/initiative-gate-omega-c-on-saturation/spec-gate-omega-c-on-saturation/control-tick-behaviors.md
- companion — _bmad-output/initiative-gate-omega-c-on-saturation/spec-gate-omega-c-on-saturation/architecture-diagrams.md
- constraint — the same spec, section Constraints
- adr — docs/adr/0003-online-ladrc-omega-c-auto-tune.md, Guards
- doc — docs/house-calibration.md, §5

## Notes

- Decision: envelope approved with one-epic initiative split (2026-10-17).
- Decision: 2026-10-17 inception — tracer = directional+strict (1); then latch decay (2); write-on-change (3); docs (4); refactor sweep (5). No parallel lanes (shared hvac_app). No deferred CAP scope.
