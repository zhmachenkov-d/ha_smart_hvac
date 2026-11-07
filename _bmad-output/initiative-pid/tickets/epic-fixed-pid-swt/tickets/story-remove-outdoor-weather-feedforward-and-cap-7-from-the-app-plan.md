---
title: '1.3 Remove Outdoor, Weather Feedforward, and CAP-7 from the App'
type: 'refactor'
ticket: '3'
created: '2026-11-07'
status: 'done'
baseline_revision: '3d44e49ebafc7828daaeb4bd6cb3673815832ea1'
route: 'oneshot'
route_source: 'auto'
risk: 'medium'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** After 1.2 the PID water path no longer uses Outdoor Temperature, Weather Feedforward, or CAP-7 rise-rate auto-correct, but their modules, config models, required yaml keys (`outdoor_temperature`, `weather_feedforward`), `ff_auto_correct_state.json` handling, and tests remain in the package as dormant code (R4).

**Approach:** Delete `feedforward.py`, `ff_auto_correct.py`, and their tests; drop `WeatherFeedforwardConfig` / `AutoCorrectConfig` and the `outdoor_temperature` / `weather_feedforward` / `auto_correct` fields and parsing; move `clamp` into `pid.py`; strip the keys from `apps.yaml.example`; rewrite tests that referenced those paths as absence checks. PID behavior, gates, and listeners stay unchanged.

</frozen-after-approval>

## Implementation Notes

Oneshot: mostly whole-file deletions (~650 LOC removed); modified/added lines well under 100 across `config.py`, `models.py`, `pid.py`, `apps.yaml.example`, and three test files.

- `clamp` is the only symbol the live path uses from `ff_auto_correct.py` (`pid.py`, `tests/test_hvac_app.py`) → define it in `pid.py`, import from there.
- `select_max_error_demand_zone(previous_name)` stays: it is Critical Zone diagnostics (R9), not CAP-7. Only reword `CAP-7` mentions in `tests/test_coordinator.py` docstrings to Critical Zone.
- Legacy `outdoor_temperature` / `weather_feedforward` keys in an operator's live `apps/apps.yaml` are ignored, matching the parser's existing no-unknown-key-check behavior (AppDaemon passes extra args). Do not edit `apps/apps.yaml` (policy: house wiring).
- Out of scope: `README.md`, `docs/house-calibration.md`, ADR 0004, `AGENTS.md`, `CONTEXT.md`, `knowledge/` (docs — epic 2 / deferred); `CHANGELOG.md` history.

Done:
- Deleted `apps/ha_smart_hvac/feedforward.py`, `ff_auto_correct.py`, `tests/test_feedforward.py`, `tests/test_ff_auto_correct.py`.
- `models.py` / `config.py`: removed FF / auto-correct dataclasses, `outdoor_temperature` field + required key, `_parse_weather_feedforward` / `_parse_auto_correct`.
- `pid.py` owns `clamp`; `hvac_app.py` listener docstring no longer mentions outdoor.
- `apps.yaml.example`: dropped `outdoor_temperature` and `weather_feedforward` (+ commented `auto_correct`).
- Tests: auto-correct config tests replaced by absence checks (modules, fields, model classes, legacy keys ignored, example yaml keys absent); `test_outdoor_missing_still_runs_demand` removed (outdoor no longer read); listener test now passes a stale `outdoor_temperature` key and still asserts it is not listened; coordinator docstrings say Critical Zone.

## Plan Change Log

## Review Triage Log

### 2026-11-07 (oneshot quick)
**Triage:** 0 high, 1 medium→deferred, 0 low, 0 false, 0 maybe-false.

- medium — AGENTS.md lines 32/34/35 still describe `ff_auto_correct_state.json`, `weather_feedforward.auto_correct` CAP-7 defaults, and event `clamp(u_ff)` writes removed by this change → defer (AGENTS/doc edits owned by epic 2; entry added to `deferred-work.md`, with README / house-calibration).

## Verification

**Commands:**
- `uv run pytest` -- expected: all tests green
- `uv run ruff check apps tests` -- expected: clean
- `rg -in "outdoor|weather_feedforward|feedforward|auto_correct|ff_auto|cap-?7|u_ff" apps/ha_smart_hvac apps.yaml.example` -- expected: no matches

## Code Review

### 2026-11-07

**Code review complete.** 3 `decision-needed`, 4 `patch`, 0 `defer`, 5 rejected.

- [x] [Review][Decision] Docs still describe removed outdoor/FF/CAP-7; README and house-calibration have no owning ticket — README.md:14,26 and docs/house-calibration.md (wire `outdoor_temperature`, commission FF, manage `ff_auto_correct_state.json`) are wrong after 1.3; epic 2's description names only ADR/CONTEXT/AGENTS. Options: (1) add README.md and docs/house-calibration.md to epic 2's description in tickets.toml; (2) update both docs in 1.3 now. Recommended: 1 — matches the frozen intent (docs out of scope) and gives the operator docs an owner. **Resolved: option 2 → patched** (README.md, docs/house-calibration.md rewritten for PID).
- [x] [Review][Decision] No operator signal for legacy keys and orphaned `ff_auto_correct_state.json` — stale `outdoor_temperature` / `weather_feedforward` in a live apps.yaml are silently ignored; the JSON has no reader. Options: (1) cover in the docs update (keys ignored, JSON safe to delete); (2) log one WARNING in initialize when legacy keys are present; (3) accept as is. Recommended: 1 — no new code. **Resolved: option 1 → patched** (house-calibration "Upgrading from Weather Feedforward").
- [x] [Review][Defer] `select_max_error_demand_zone` keeps dead CAP-7 sticky tie-break — only caller (hvac_app.py:119) passes `None`; `previous_name` branch came from CAP-7 (03877c7). Options: (1) remove `previous_name` and adjust 3 sticky tests; (2) keep and leave to 1.4 refactor sweep. Recommended: 2 — plan kept it deliberately; harmless; 1.4 is the refactor sweep. — deferred: user chose keep; 1.4 refactor sweep.
- [x] [Review][Patch] deferred-work.md 1.3 entry misfiled under the 1.2 heading, YAML-ish, cites AGENTS.md line numbers [_bmad-output/initiative-pid/deferred-work.md:9]
- [x] [Review][Patch] "outdoor unavailable still demands" (1.1 verify) lost its test — rewrite as stale outdoor key + unavailable outdoor entity, tick still writes [tests/test_hvac_app.py]
- [x] [Review][Patch] Legacy-keys test does not prove keys have no effect — assert equality with `parse_config(_minimal_args())` [tests/test_config.py:157]
- [x] [Review][Patch] `clamp` has no direct unit test [apps/ha_smart_hvac/pid.py:11]

**Rejected**
- false — ADR 0004 trigger-list rule: Outdoor is not a Heating Demand input and its listener was dropped in 1.1; ADR staleness already deferred.
- false — absence tests "pass for wrong reason": test_config.py imports the package at top, so ModuleNotFoundError can only come from the target module.
- false — plan metadata: `ticket: '3'` matches tickets.toml ids; rg `ff_auto` already matches `ff_auto_correct_state`.
- false — listener test weak: exact equality on entity and attribute listener sets already excludes `_OUTDOOR`.
- low — CAP-7 / ff_auto_correct_state absence only in rg gate: a pytest string-grep would duplicate the plan's rg check.
