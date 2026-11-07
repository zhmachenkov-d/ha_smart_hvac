## Deferred from: code review of story-tracer-fixed-gain-pid-swt-law-plan (2026-11-07)

- Plan Tasks checkboxes still open despite status built — Execution tasks remain `[ ]` while frontmatter says `built`; deferred because the fix edits the plan/ticket artifact, not runtime code.

## Deferred from: code review of story-tick-owned-pid-advance-and-event-clear-only-plan (2026-11-07)

- AGENTS.md / ADR 0004 / CONTEXT.md still describe CAP-8 — demand events writing `clamp(u_ff)` and Outdoor Temperature as a control listener — while runtime is tick-only PID demand with event clear-only and no Outdoor listener; deferred because these are agent-context/ADR edits owned by epic 2 (R4 docs, `epic-pid-domain-docs`).

## Deferred from: code review of story-remove-outdoor-weather-feedforward-and-cap-7-from-the-app-plan (2026-11-07)

- AGENTS.md conventions (Plant Management off leaving `ff_auto_correct_state.json` untouched; `weather_feedforward.auto_correct` CAP-7 defaults; CAP-8 event `clamp(u_ff)` writes), ADR 0004, CONTEXT.md, and `knowledge/` still describe Outdoor / Weather Feedforward / CAP-7, which 1.3 deleted from the package; deferred because these are agent-context/ADR edits owned by epic 2 (`epic-pid-domain-docs`). README.md and docs/house-calibration.md were updated in 1.3.
- `select_max_error_demand_zone(previous_name)` sticky tie-break is CAP-7 residue — the only caller (`hvac_app.py`) passes `None`; deferred to 1.4 refactor sweep by user decision.
