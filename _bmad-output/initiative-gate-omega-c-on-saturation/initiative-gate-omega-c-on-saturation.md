---
tracker_id: ""
key: ""
type: initiative
title: "Gate ωc on saturation"
parent: none
after: []
assignee: ""
risk: medium
estimate: ""
estimate_basis: ""
status: done
sources: [forge-gate-omega-c-on-saturation/forge-gate-omega-c-on-saturation.md, /home/vscode/.cursor/plans/gate_omega_c_on_saturation_2ead8ef3.plan.md]
companions: [_bmad-output/initiative-gate-omega-c-on-saturation/control-tick-behaviors.md, _bmad-output/initiative-gate-omega-c-on-saturation/architecture-diagrams.md, ../../../../docs/adr/0003-online-ladrc-omega-c-auto-tune.md, ../../../../docs/house-calibration.md]
---

# Gate ωc on saturation

## Description

After sustained Critical Zone underheat with Set Water Temperature at clamp, healthy-but-saturated ticks still ratchet online ωc upward until a later ESO reset latches soft-kill. This initiative delivers `_bmad-output/initiative-gate-omega-c-on-saturation/initiative-gate-omega-c-on-saturation.md` — directional commit clamp, strict apply, write-on-change, latched ωc decay with adapt skipped, docs under criterion A, and regression tests.

## Outcome

Operators keep a recoverable LADRC loop under winter max-SWT underheat; the signal is the spec's Success signal (no upward ωc ratchet at max, latched decay on real `|u_track|`, redundant SWT writes skipped without freezing the tick).

## Requirements

- R1 (CAP-1): The control tick can refuse to commit an ωc adaptation that would push further into the saturated plant direction, while still allowing ωc moves that relieve saturation. Success: With command at `setpoint_max`, an upward proposed ωc is not committed; a downward proposed ωc may commit. Symmetric at `setpoint_min`. Guard trip still blocks commit. Full freeze on any clamp does not occur.
- R2 (CAP-2): When a directional (or guard) block prevents commit, that tick’s tracking computation cannot use the blocked proposed ωc. Success: On a blocked tick, `compute_tracking` runs with the current committed ωc; a Hass-free ratchet scenario that previously climbed ωc via one-tick proposed apply no longer increases committed or applied ωc across saturated upward proposals.
- R3 (CAP-3): The app can avoid redundant Home Assistant `number/set_value` calls when the desired Set Water Temperature already matches the plant entity, without stalling the rest of the control tick when a float state was read. Success: When desired equals the entity float state, no `number/set_value` is issued and the tick continues (ESO reset/advance and adapt/gate/decay). When entity state is unavailable/unknown/unparseable, behavior stays fail-closed: no write, `_write_setpoint` false, tick aborts. Applies on demand and idle/0 paths inside `_write_setpoint`.
- R4 (CAP-4): While the blow-up soft-kill latch is held, the system can step ωc down over successive ticks until tracking residue leaves the latch-stick band, persist those steps, and not run normal adapt during that recovery. Success: With latch already active at tick start, `maybe_adapt` is not called. If `|u_track| > 0.8 · u_track_max` (or non-finite `u_track`), each such tick reduces committed ωc by existing tuner `max_rate_fraction` (≥ `omega_c_min`) and persists; decay stops once finite `|u_track| ≤ 0.8 · u_track_max`. Guard-trip skip of `commit_omega_c` does not prevent decay persist. Criterion uses actual tick `|u_track|`, not `|ωc·e/b0|`.
- R5 (CAP-5): Maintainers reading ADR 0003 Guards and house-calibration §5 understand the directional clamp and latch decay under criterion A. Success: Those docs describe skip of upward commit at max / downward at min, strict apply, latched `|u_track|` decay with adapt skipped while latched, and fail-closed unreadability — not a headroom-only full freeze or “ops reset only” recovery story.
- R6 (CAP-6): Automated tests lock the directional matrix, strict-apply no-ratchet path, write-on-change skip vs fail-closed unreadability, and latched decay exit so regressions cannot return silently. Success: Tests cover (a) commit helper/matrix for None / tripped / max+up / max+down / min+down / min+up / interior, (b) saturated upward proposals do not raise applied or committed ωc, (c) identical entity state skips `set_value` without aborting tick side effects, (d) unreadable entity aborts the tick, (e) while latched, adapt is skipped and multi-tick `|u_track|` above threshold decays ωc until below `0.8 · u_track_max`.

## Constraints

- Directional clamp and strict apply are both required; persistence-only gating is forbidden.
- Write-on-change baseline is **current plant entity float state** with exact equality; not a last-written cache. Equality-skip continues the tick; unreadability stays **fail-closed** (abort tick).
- While latch is already active at tick start: **skip `maybe_adapt` entirely**; only decay+persist when residue condition holds — no propose-then-override.
- Latch decay persists even when guard trip blocks normal `commit_omega_c`.
- Decay / commit gates use actual tick `|u_track|` (and non-finite); predicted `|ωc·e/b0|` is not a gate or decay criterion.
- Threshold `0.8 · u_track_max` is a fixed code constant (not a yaml knob). Decay step/floor reuse existing tuner `max_rate_fraction` / `omega_c_min`.
- Online auto-tune remains **ωc only** (ADR 0003); no online `b0` / `ωo` / MADRC work here.
- Do not change `setpoint_min` / `setpoint_max` or `u_track_max` as the fix.
- Docs must frame criterion **A**, not headroom-only philosophy.

## Done when

1. At `setpoint_max`, upward ωc is not committed and downward may be; symmetric at `setpoint_min`; guard trip still blocks commit.
2. On a blocked tick, tracking uses current committed ωc only (no one-tick proposed-ωc ratchet).
3. Identical plant entity float skips `number/set_value` while the tick continues; unreadable entity stays fail-closed (abort).
4. With latch already active, adapt is skipped and ωc decays by `max_rate_fraction` while `|u_track| > 0.8 · u_track_max` (or non-finite) until residue is at or below that band.
5. ADR 0003 Guards and house-calibration §5 describe criterion A and these behaviors (not headroom-only full freeze).
6. R6 automated tests pass and fail if the ratchet, equality-skip abort, or missing latched decay return.

## Boundaries

Capability boundary: HVAC AppDaemon LADRC ωc auto-tune and plant write path. Not full freeze on any clamp, not ESO anti-windup, not changing `u_track_max` or 40/55 limits, not online `b0`/`ωo`/MADRC. One epic owns the whole fix. Tracer path: directional+strict → write-on-change → latch decay → docs → sweep.

- Touch point: `LadrcTuner` persist/rate limits — consumed for decay step/floor; owner: epic-gate-omega-c-on-saturation
- Touch point: ADR 0003 + house-calibration — amended in place; owner: epic-gate-omega-c-on-saturation
- Non-goal: Full freeze of ωc commit whenever SWT is at either clamp.
- Non-goal: ESO anti-windup redesign or changing package-A / `u_track_max` defaults.
- Non-goal: Hard reset of ωc to `config.omega_c` on trip, or a one-shot “safe ωc” jump as the sole recovery.
- Non-goal: Treating a one-time ops delete of `ladrc_tune_state.json` as the product fix (ops may still help a stuck file before this ships).
- Non-goal: Online adaptation of `b0`, `ωo`, or MADRC.

## References

- constraint — the same spec, section Constraints
- companion — _bmad-output/initiative-gate-omega-c-on-saturation/control-tick-behaviors.md
- forge — _bmad-output/initiative-gate-omega-c-on-saturation/forge-gate-omega-c-on-saturation/forge-gate-omega-c-on-saturation.md
- companion — control-tick-behaviors.md
- companion — architecture-diagrams.md
- companion — ../../../../docs/adr/0003-online-ladrc-omega-c-auto-tune.md
- companion — ../../../../docs/house-calibration.md

## Notes

- Decision: one epic for R1–R6; no platform-baseline epic — brownfield fix on existing app (2026-10-17).
- Decision: repo ticketing store (2026-10-17).
