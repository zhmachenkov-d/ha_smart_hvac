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

- source_plan: `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-trv-idle-max-close/tickets/story-tracer-trv-idle-max-close-soft-close-plan.md`
  summary: Accuracy-only soft-close re-apply (listen to accuracy entity; AC that accuracy state change alone re-runs TRV law without waiting for tick)
  evidence: Split from oversized 4.1 plan; ticket verify does not require accuracy-driven events — zone/climate/plant/tick still re-apply.

- source_plan: `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-trv-idle-max-close/tickets/story-tracer-trv-idle-max-close-soft-close-plan.md`
  summary: TRV prelude-isolation edge ACs (Outdoor-fail / empty-zone prelude / sibling zone T unreadable dedicated tests)
  evidence: Split from oversized 4.1 plan; before-prelude call graph stays in tracer Always, but expanded isolation ACs deferred to keep plan in token range.

- source_plan: `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-trv-idle-max-close/tickets/story-tracer-trv-idle-max-close-soft-close-plan.md`
  summary: Expanded multi-TRV / mixed-list / cold-start / idle-overshoot golden ACs beyond ticket verify
  evidence: Split from oversized 4.1 plan; core hysteresis + plant-off + plain-string remain in tracer; extra goldens can land in epic entry 3 or a follow-on test story.

- source_plan: `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-trv-idle-max-close/tickets/story-tracer-trv-idle-max-close-soft-close-plan.md`
  summary: `_entity_id` accepts whitespace-only strings for TRV (and other) entity fields
  evidence: Pre-existing `_entity_id` checks `isinstance(str) and not raw` only; settle by requiring `raw.strip()` (or equivalent) across entity-id parse, not TRV-only.
