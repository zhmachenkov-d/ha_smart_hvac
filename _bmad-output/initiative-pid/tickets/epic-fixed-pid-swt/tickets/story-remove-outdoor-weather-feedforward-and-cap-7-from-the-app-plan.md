---
title: '1.3 Remove Outdoor, Weather Feedforward, and CAP-7 from the App'
type: 'refactor'
ticket: '3'
created: '2026-11-07'
status: 'built'
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
