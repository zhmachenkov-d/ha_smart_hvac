## Deferred from: code review of story-tracer-fixed-gain-pid-swt-law-plan (2026-11-07)

- Plan Tasks checkboxes still open despite status built — Execution tasks remain `[ ]` while frontmatter says `built`; deferred because the fix edits the plan/ticket artifact, not runtime code.

## Deferred from: code review of story-tick-owned-pid-advance-and-event-clear-only-plan (2026-11-07)

- AGENTS.md / ADR 0004 / CONTEXT.md still describe CAP-8 — demand events writing `clamp(u_ff)` and Outdoor Temperature as a control listener — while runtime is tick-only PID demand with event clear-only and no Outdoor listener; deferred because these are agent-context/ADR edits owned by epic 2 (R4 docs, `epic-pid-domain-docs`).

- source_plan: `_bmad-output/initiative-pid/tickets/epic-fixed-pid-swt/tickets/story-remove-outdoor-weather-feedforward-and-cap-7-from-the-app-plan.md`
  summary: AGENTS.md conventions (lines 32, 34, 35) still describe `ff_auto_correct_state.json`, `weather_feedforward.auto_correct` / CAP-7 defaults, and event `clamp(u_ff)` writes, all of which 1.3 deleted from the package; README.md and docs/house-calibration.md likewise still point operators at feedforward / rise-rate calibration.
  evidence: 1.3 removed `feedforward.py`, `ff_auto_correct.py`, and the FF / auto-correct config; `rg` over `apps/ha_smart_hvac` finds no `u_ff` / `ff_auto`; doc edits are owned by epic 2 (`epic-pid-domain-docs`).
