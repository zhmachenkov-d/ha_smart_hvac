# Deferred work

## Settled: epic-4 TRV soft-close leftovers (story-refactor-sweep)
- Expanded-goldens idle-overshoot half already covered by 4.1 `test_trv_independent_of_heating_demand` (+ core overshoot); remaining A–D closed in this sweep.

## Deferred from: code review of story-refactor-sweep-plan (2026-11-16, walkthrough slice Prelude-isolation + expanded goldens)
- No accuracy `control_event` + Outdoor-fail isolation test — deferred: tick shared-path / prior Intent Formal review
- Empty-zone isolation pins law-ran only via spy — deferred: plan matrix spy+skip+idle; countable isolation on Outdoor-fail

## Settled: epic-5 flame short-on leftovers (story-refactor-sweep)
- U1/S1 arm edges: `test_flame_none_to_on_does_not_arm`, `test_flame_unreadable_to_on_does_not_arm`, `test_ch_active_off_to_on_while_flame_already_on_does_not_arm`, plus 5.3 `test_restart_mid_flame_does_not_arm_or_latch_on_fall` (mid-burn since wipe + on→on no-rearm + fall without latch).
- E1 example comment: `apps.yaml.example` L14 combined min/hold comment.
- Named supply-analogue ports: `test_orphan_hold_callback_*`, `test_plant_off_*flame*`, `test_idle_*flame*` / armed-since wipes.
- V1 truncate: `test_parse_flame_trip_hold_truncates_fractional_seconds` covers 90.9→90 and 900.9→900.
- Latched flame/ch_active no-SWT: `test_already_latched_flame_observe_wipes_since_no_reassert`, `test_ch_active_off_while_latched_keeps_latch_and_zero`; house-yaml meta settled by 5.2 + `tests/test_dual_layout.py`.

## Settled: epic-6 docs hygiene (story-refactor-sweep)
- A — AGENTS/CONTEXT/ADR live-PID-after-detach claim: obsolete after epic 3 + ADR 0008; pruned (no ADR 0005/0006 body demotion). Covering: stories 3.1 / 6.1.
- B — Meta “epic-1 bullet still outstanding after 3.1”: pruned with A. Covering: epic-3 tracer + this sweep.
- C — CAP-8 AGENTS sticky-latch lag claim: reworded in `docs/decisions/adr-cap8-shared-ff-demand-writer.md` (story 6.3); deferred bullet pruned.
- D — AGENTS «knowledge/ may lag until 3.2»: already gone from AGENTS (live law = ADR 0008 + CONTEXT + `knowledge/` via 6.1/6.2); pruned.
- E — Code-review duplicate of B (2026-11-14 delete-dead): pruned; empty header removed.
- F — AGENTS/CONTEXT omit accuracy `control_event` listen: fixed in story 6.1 rewrite; pruned.
- I — house-calibration §1 table vs intro flame/`ch_active`/TRV: prune-with-cite — intro anti-cycle sentences + `## 1. House wiring` unchanged four-row Outdoor/plant/zones checklist; entity nests in `apps.yaml.example` (`flame_on`, `ch_active`, Sonoff TRV). Known checklist gap: §1 `plant_management` row is SWT-only while intro says plant-off clears flame latch. Covering: story 6.1 intro + this Settled note (Decision B).
