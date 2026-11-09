## Deferred from: code review of story-tracer-fixed-gain-pid-swt-law-plan (2026-11-07)

- Plan Tasks checkboxes still open despite status built — Execution tasks remain `[ ]` while frontmatter says `built`; deferred because the fix edits the plan/ticket artifact, not runtime code.

## Deferred from: code review of story-tick-owned-pid-advance-and-event-clear-only-plan (2026-11-07)

- ADR 0004 / CONTEXT.md still describe CAP-8 — demand events writing `clamp(u_ff)` and Outdoor Temperature as a control listener — while runtime is tick-only PID demand with event clear-only and no Outdoor listener; deferred because these are ADR/CONTEXT edits owned by epic 2 (R4 docs, `epic-pid-domain-docs`). AGENTS.md conventions were rewritten in story 2.1.

## Deferred from: code review of story-remove-outdoor-weather-feedforward-and-cap-7-from-the-app-plan (2026-11-07)

- ADR 0004, CONTEXT.md, and `knowledge/` still describe Outdoor / Weather Feedforward / CAP-7, which 1.3 deleted from the package; deferred because these are ADR/CONTEXT/`knowledge/` edits owned by epic 2 (`epic-pid-domain-docs`). AGENTS.md conventions were rewritten in story 2.1. README.md and docs/house-calibration.md were updated in 1.3.
- `select_max_error_demand_zone(previous_name)` sticky tie-break is CAP-7 residue — the only caller (`hvac_app.py`) passes `None`; deferred to 1.4 refactor sweep by user decision.

## Resolved in 1.4 refactor sweep (2026-11-07)

- Resolved: 1.1 "Plan Tasks checkboxes still open despite status built" — the five Execution boxes in `story-tracer-fixed-gain-pid-swt-law-plan.md` are ticked.
- Resolved: `select_max_error_demand_zone(previous_name)` sticky tie-break — parameter removed; ties break by lexicographic name only.

## Deferred from: code review of story-refactor-sweep-plan (2026-11-07)

- ADR 0004, CONTEXT.md, and `knowledge/` still describe Weather Feedforward / CAP-7 / CAP-8 (demand events writing `clamp(u_ff)`, `ff_auto_correct_state.json`, `weather_feedforward.auto_correct`) while runtime is tick-only fixed PID with event clear-only; pre-existing from 1.2/1.3, ADR/CONTEXT/`knowledge/` edits owned by epic 2 (`epic-pid-domain-docs`). AGENTS.md conventions were rewritten in story 2.1.

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

## Resolved in 1.8 refactor sweep 2 (2026-11-08)

- Resolved: runtime non-finite `e` (plan-split from 1.7) — `weighted_error` returns `None` when `e` is not finite, so `evaluate_demand` takes the existing weights-unusable idle path instead of `clamp(nan) == setpoint_max`.
- Resolved: overflowing finite zone weights (~1e308) — covered by the non-finite-`e` guard; the plant receives 0 and ∫ clears, never `setpoint_max`.
- Resolved: misspelled / leftover zone sub-keys (e.g. `weigth: 3`) — `_ignored_keys` reports them as `zones[<name>].<key>` and initialize logs one WARNING naming the key.

## Deferred from: code review of story-agents-md-fixed-pid-swt-conventions-plan (2026-11-08)

- Event "fail" left undefined in AGENTS.md `control_event` clear path — deferred: точный каталог fail — в ADR 2.2.

## Deferred from: code review of story-knowledge-concept-pages-for-pid-swt-plan (2026-11-08)

- source_plan: `_bmad-output/initiative-pid/tickets/epic-pid-domain-docs/tickets/story-knowledge-concept-pages-for-pid-swt-plan.md`
  summary: `adrc.md` Related still links `ladrc.md` / `madrc.md` whose Project notes commission weather-curve SWT under ADR 0004
  evidence: Live ADRC page cites ADR 0005 correctly; sibling literature pages were left out of 2.4 scope for story 2.5 refactor sweep

## Resolved in 2.5 refactor sweep (2026-11-08)

- Resolved: `adrc.md` Related → ladrc/madrc still commission weather-curve under ADR 0004 — Project notes cite ADR 0005 fixed-PID; Related caveat removed.

## Deferred from: retrospective of epic-fixed-pid-swt (2026-11-08)

- Two-tick plant-drift R7 test (VG5 / B4): `tests/test_hvac_app.py` `test_plant_drift_rewrites_command` is a single tick with plant already at 50; a restored `_last_commanded` short-circuit before `_write_setpoint` would still pass. Prefer echo plant → command 42, mutate plant to 50, second tick asserts rewrite. Optional test hygiene; not owned by a ticket — party locked defer (no new epic-1 story).
- Legacy-scale `pid.ki` footgun (SR8 / B6): an upgraded yaml that keeps a pre-migration numeric `ki` (e.g. `0.1` per-second) is accepted as 1/h with no ConfigError; only `integral_min`/`integral_max` land in `ignored_keys`. Documented in `docs/house-calibration.md`; this house was re-commissioned in 1.6. Optional WARN/migrate — candidate for a future tune story or epic 3; party locked defer.

## Deferred from: code review of story-adapted-gain-rails-and-unhealthy-rls-fallback-plan (2026-11-09)

- Entry-1 `tickets.toml` description still says clears keep "last-good adapted gains" without the entry-2 IMC-invalid → YAML fixed override (verify/notes already updated); deferred because the fix edits a ticket file.

## Resolved in 3.5 refactor sweep (2026-11-09)

- Resolved: Entry-1 `tickets.toml` description — now says parked adapted gains across clears and points unhealthy/rails latch → YAML fixed at entry 2.
- Owned wontfix (entry-2 review): hysteresis/dwell before clearing latch — W1+ sufficient; no further work.
- Owned wontfix (entry-2 review): parse INFO when fixed `kp`/`ki` sit outside rails — OQ7 R1 intentional; no further work.
- Owned wontfix (entry-2 review): structure mega-MERGE of plan sections — clarity nits only; no further work.
- Resolved: companion orphan `rls-adaptive-algorithm.md` Persistence — last-good → parked adapted + latch→YAML while latched.
