# Deferred work

- source_plan: `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-weather-curve-swt-restore/tickets/story-detach-pid-rls-from-live-swt-and-example-commissioning-plan.md`
  summary: AGENTS.md / CONTEXT.md / ADR 0005–0006 still describe live PID/∫/RLS SWT after FF detach
  evidence: Intent Always forbids rewriting those agent/domain docs in this story (epic 3 owns supersede); contradiction remains for agents/operators until epic 3.

- source_plan: `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-supersede-pid-domain-docs/tickets/story-delete-dead-pid-rls-modules-plan.md`
  summary: Epic-1 deferred-work bullet still frames AGENTS/CONTEXT/ADR PID supersede as outstanding after epic 3.1 already rewrote those surfaces
  evidence: Pre-existing defer from detach story; not caused by pid/rls file delete — settle or prune in entry 4 refactor sweep

- source_plan: `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-supersede-pid-domain-docs/tickets/story-delete-dead-pid-rls-modules-plan.md`
  summary: docs/decisions/adr-cap8-shared-ff-demand-writer.md still warns about AGENTS sticky-latch prose until epic 3
  evidence: Historical CAP-8 note; AGENTS already updated in 3.1 — cosmetic lag, not caused by module delete

- source_plan: `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-supersede-pid-domain-docs/tickets/story-delete-dead-pid-rls-modules-plan.md`
  summary: AGENTS.md still says knowledge/ may lag until story 3.2 after 3.2 merged
  evidence: Agent-context stale pointer; Intent Never forbids AGENTS rewrite in 3.3 — entry 4 / docs hygiene

## Deferred from: code review of story-delete-dead-pid-rls-modules-plan (2026-11-14)
- Stale epic-1 deferred-work bullet still frames AGENTS/CONTEXT/ADR PID supersede as outstanding — pre-existing; not caused by module delete; settle/prune in entry 4

## Settled: epic-4 TRV soft-close leftovers (story-refactor-sweep)
- Expanded-goldens idle-overshoot half already covered by 4.1 `test_trv_independent_of_heating_demand` (+ core overshoot); remaining A–D closed in this sweep.

## Deferred from: code review of story-refactor-sweep-plan (2026-11-16, walkthrough slice Accuracy listen + `_entity_id`)
- AGENTS.md / CONTEXT.md listener inventories still omit commissioned TRV `accuracy` as a `control_event` listen (can re-enter demand SWT via shared handler); Intent Never forbids agent-context rewrite in 4.3 — settle in epic-6 / docs hygiene

## Deferred from: code review of story-refactor-sweep-plan (2026-11-16, walkthrough slice Prelude-isolation + expanded goldens)
- No accuracy `control_event` + Outdoor-fail isolation test — deferred: tick shared-path / prior Intent Formal review
- Empty-zone isolation pins law-ran only via spy — deferred: plan matrix spy+skip+idle; countable isolation on Outdoor-fail

## Settled: epic-5 flame short-on leftovers (story-refactor-sweep)
- U1/S1 arm edges: `test_flame_none_to_on_does_not_arm`, `test_flame_unreadable_to_on_does_not_arm`, `test_ch_active_off_to_on_while_flame_already_on_does_not_arm`, plus 5.3 `test_restart_mid_flame_does_not_arm_or_latch_on_fall` (mid-burn since wipe + on→on no-rearm + fall without latch).
- E1 example comment: `apps.yaml.example` L14 combined min/hold comment.
- Named supply-analogue ports: `test_orphan_hold_callback_*`, `test_plant_off_*flame*`, `test_idle_*flame*` / armed-since wipes.
- V1 truncate: `test_parse_flame_trip_hold_truncates_fractional_seconds` covers 90.9→90 and 900.9→900.
- Latched flame/ch_active no-SWT: `test_already_latched_flame_observe_wipes_since_no_reassert`, `test_ch_active_off_while_latched_keeps_latch_and_zero`; house-yaml meta settled by 5.2 + `tests/test_dual_layout.py`.
- source_plan: `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-docs-trv-flame-water-law/tickets/story-tracer-adr-agents-context-for-trv-flame-water-law-plan.md`
  summary: house-calibration §1 wiring table still lists only Outdoor/plant/zones and describes plant-off as leaving SWT untouched, without flame/`ch_active`/TRV rows or flame-clear wording.
  evidence: Pre-existing §1; story 6.1 Intent Always limited calibration edits to live-pointer + 1–2 anti-cycle sentences and Never forbids full TRV/flame commissioning tables, so the intro/§1 mismatch remains after this tracer.
