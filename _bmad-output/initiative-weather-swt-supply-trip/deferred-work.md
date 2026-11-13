# Deferred work

- source_plan: `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-weather-curve-swt-restore/tickets/story-detach-pid-rls-from-live-swt-and-example-commissioning-plan.md`
  summary: AGENTS.md / CONTEXT.md / ADR 0005–0006 still describe live PID/∫/RLS SWT after FF detach
  evidence: Intent Always forbids rewriting those agent/domain docs in this story (epic 3 owns supersede); contradiction remains for agents/operators until epic 3.

- source_plan: `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-supply-rise-rate-trip/tickets/story-tracer-supply-rise-rate-trip-plan.md`
  summary: Trip edge-case hardening — dedicated ACs/tests for re-trip no run_in restart, orphan hold-callback idempotency, outdoor-miss-while-latched clear, and CZ-only non-trip
  evidence: Split from 2.1 tracer to keep the plan in the 900–1600 token band; core hold-from-first-latch and _go_idle/_hands_off clear hooks stay in the tracer Always, but the expanded matrix/AC/test suite for those edges is deferred.

## Deferred from: code review of story-tracer-supply-rise-rate-trip-plan (2026-11-13)

- run_in None after latch is unverified: If run_in can return None, latch sticks with no hold expiry until idle/plant-off. — Unverified medium/high — settle by confirming whether AppDaemon run_in can return None on failure; if yes, treat as medium+ and guard.
- Critical Zone non-trip Always rule unverified in this change: no CZ×trip test — deferred: deferred-work already scoped CZ×trip suite out of 2.1 tracer band
