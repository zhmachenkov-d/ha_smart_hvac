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

## Deferred from: story-tracer-replace-supply-trip-with-flame-short-on-plan (2026-11-16 token split)
- source_plan: `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-replace-supply-trip-with-flame/tickets/story-tracer-replace-supply-trip-with-flame-short-on-plan.md`
  summary: Expanded U1/S1 arm-edge goldens (None/unavailable→on, restart mid-flame, already-on at gate open as dedicated ACs)
  evidence: Token split from 5.1 tracer; Always still requires rising-only strict binary arm — dedicated goldens not needed to ship the law
- source_plan: `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-replace-supply-trip-with-flame/tickets/story-tracer-replace-supply-trip-with-flame-short-on-plan.md`
  summary: apps.yaml.example E1 short comments for flame_on_min_s vs flame_trip_hold_s
  evidence: Token split; tracer still requires YOUR_* flame placeholders and trip-key removal
- source_plan: `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-replace-supply-trip-with-flame/tickets/story-tracer-replace-supply-trip-with-flame-short-on-plan.md`
  summary: Expanded named supply-analogue test ports (orphan_hold_callback; separate plant_off/no_demand ACs beyond matrix rows)
  evidence: Token split; Plant off / Gate closed / Hold expiry orphan behavior stay in core matrix
- source_plan: `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-replace-supply-trip-with-flame/tickets/story-tracer-replace-supply-trip-with-flame-short-on-plan.md`
  summary: Dedicated V1 flame_trip_hold_s 900.9→900 truncate AC and example-comment assert
  evidence: Token split; Always still requires fractional truncate to int ≥1 like former hold
- source_plan: `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-replace-supply-trip-with-flame/tickets/story-tracer-replace-supply-trip-with-flame-short-on-plan.md`
  summary: Dedicated latched flame/ch_active no-SWT AC and meta house-yaml-not-in-verify AC
  evidence: Token split; Always A (handlers wipe since only) and D1 (entry id=2 owns house yaml) remain
