## Deferred from: code review of story-tracer-fixed-gain-pid-swt-law-plan (2026-11-07)

- Plan Tasks checkboxes still open despite status built — Execution tasks remain `[ ]` while frontmatter says `built`; deferred because the fix edits the plan/ticket artifact, not runtime code.

## Deferred from: code review of story-tick-owned-pid-advance-and-event-clear-only-plan (2026-11-07)

- AGENTS.md / ADR 0004 / CONTEXT.md still describe CAP-8 — demand events writing `clamp(u_ff)` and Outdoor Temperature as a control listener — while runtime is tick-only PID demand with event clear-only and no Outdoor listener; deferred because these are agent-context/ADR edits owned by epic 2 (R4 docs, `epic-pid-domain-docs`).

## Deferred from: code review of story-remove-outdoor-weather-feedforward-and-cap-7-from-the-app-plan (2026-11-07)

- AGENTS.md conventions (Plant Management off leaving `ff_auto_correct_state.json` untouched; `weather_feedforward.auto_correct` CAP-7 defaults; CAP-8 event `clamp(u_ff)` writes), ADR 0004, CONTEXT.md, and `knowledge/` still describe Outdoor / Weather Feedforward / CAP-7, which 1.3 deleted from the package; deferred because these are agent-context/ADR edits owned by epic 2 (`epic-pid-domain-docs`). README.md and docs/house-calibration.md were updated in 1.3.
- `select_max_error_demand_zone(previous_name)` sticky tie-break is CAP-7 residue — the only caller (`hvac_app.py`) passes `None`; deferred to 1.4 refactor sweep by user decision.

## Resolved in 1.4 refactor sweep (2026-11-07)

- Resolved: 1.1 "Plan Tasks checkboxes still open despite status built" — the five Execution boxes in `story-tracer-fixed-gain-pid-swt-law-plan.md` are ticked.
- Resolved: `select_max_error_demand_zone(previous_name)` sticky tie-break — parameter removed; ties break by lexicographic name only.

## Deferred from: code review of story-refactor-sweep-plan (2026-11-07)

- AGENTS.md conventions, ADR 0004, CONTEXT.md, and `knowledge/` still describe Weather Feedforward / CAP-7 / CAP-8 (demand events writing `clamp(u_ff)`, `ff_auto_correct_state.json`, `weather_feedforward.auto_correct`) while runtime is tick-only fixed PID with event clear-only; pre-existing from 1.2/1.3, agent-context/ADR edits owned by epic 2 (`epic-pid-domain-docs`).

## Deferred from: party review of story-pid-integral-units-and-r7-skip-hardening-plan (2026-11-07)

- House `apps/apps.yaml` sets no `base_water_temp` (default 40) while `setpoint_min` is 42: with D15 `ki 1.0/h` the I-term must climb ~(2 − kp·e) °C before the command leaves the minimum — about 3 h at e = 0.5 °C. Commission `base_water_temp ≥ setpoint_min` (or accept the lag) in entry 6 (hitl house yaml); not a code defect, out of scope for entry 5.

## Deferred from: code review of story-pid-integral-units-and-r7-skip-hardening-plan (2026-11-07)

- `evaluate_demand` (`apps/ha_smart_hvac/pid.py`) uses ∫ as passed for the command, so with an I-term range that excludes 0 (e.g. `i_term_min > 0`) the command applies I = 0 (start/after clear) or a frozen value outside `[i_term_min, i_term_max]`. Pre-existing with `integral_min/max`; entry 1.7 (C5/D20) rejects such ranges at parse time.

## Deferred from: plan split of story-commission-parse-hardening-and-legacy-key-warning-plan (2026-11-07)

- source_plan: `_bmad-output/initiative-pid/tickets/epic-fixed-pid-swt/tickets/story-commission-parse-hardening-and-legacy-key-warning-plan.md`
  summary: Runtime guard in `apps/ha_smart_hvac/pid.py` — `weighted_error` returns `None` when the weighted error is not finite, so `evaluate_demand` takes the existing "Demand zone weights unusable; setpoint 0" idle path instead of `clamp(nan) == setpoint_max` (party lock C), with `tests/test_pid.py` and `tests/test_hvac_app.py` cases; owner: refactor sweep 2 (entry 8).
  evidence: Split by user at the 1.7 token gate (~2400 tokens); independent of config parsing. 1.7 closes the yaml entry point instead (`_parse_zone` rejects a non-finite `weight`); the runtime guard still covers non-finite zone readings and float overflow in the weighted sums.

## Resolved in 1.7 commission parse hardening (2026-11-08)

- Resolved: house yaml without `base_water_temp` and `setpoint_min: 42` (~3 h I-term lag) — an omitted `base_water_temp` now defaults to 40 clamped into `setpoint_min`…`setpoint_max`, so the house base becomes 42 and the lag is gone; an explicit base below `setpoint_min` is now a config error, so "accept the lag" is no longer an option.
- Resolved: I-term range excluding 0 in `evaluate_demand` — `_parse_pid` (`apps/ha_smart_hvac/config.py`) rejects `not i_term_min <= 0 <= i_term_max` with `ConfigError`, so such a range never reaches the law.

## Deferred from: code review of story-commission-parse-hardening-and-legacy-key-warning-plan (2026-11-08)

- Huge finite zone `weight` (~1e307, or several near `1e308`) passes `_parse_zone`; in `weighted_error` (`apps/ha_smart_hvac/pid.py`) `w*tair` / the weight sum overflow to `inf`, `e` becomes `nan`, and `clamp(nan)` silently commands `setpoint_max`. Pre-existing; the plan-split entry above (runtime non-finite-`e` guard, owner entry 8) already covers it — entry 8's tests should include an overflowing-weight case.
- Misspelled or leftover zone sub-keys (e.g. `weigth: 3`) are silently ignored and the weight falls back to `1.0`; `_ignored_keys` (`apps/ha_smart_hvac/config.py`) reports only top-level and `pid.*` keys. Pre-existing and outside 1.7's frozen scope; candidate for entry 8 (report as `zones[<name>].<key>` in `ignored_keys`).

## Resolved in 1.6 commission house apps.yaml (2026-11-08)

- Resolved: house `base_water_temp ≥ setpoint_min` (entry-5 party deferral, first closed by 1.7's default clamp) — the house `apps/apps.yaml` now sets `base_water_temp: 42` explicitly, with `pid`, `control_interval: 300`, and no legacy keys (`ignored_keys == ()`).
