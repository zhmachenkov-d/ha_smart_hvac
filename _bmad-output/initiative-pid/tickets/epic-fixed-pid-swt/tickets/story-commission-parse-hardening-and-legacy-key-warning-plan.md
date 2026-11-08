---
title: '1.7 Commission parse hardening and legacy-key warning'
type: 'bugfix'
ticket: '7'
created: '2026-11-07'
status: 'built'
baseline_revision: 'c642f92101fb76516cede527e994f62e56094ef9'
route: 'full'
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

**Problem:** `parse_config` lets bad commission values through: `float("abc")` raises a raw `ValueError` that escapes `initialize` (the App crashes instead of logging); NaN/inf, negative gains, an I-term range without 0, and `base_water_temp` outside the clamp are accepted; a NaN zone weight reaches the law and `clamp(nan) == setpoint_max`. Leftover `outdoor_temperature` / `weather_feedforward` / `pid.integral_*` keys are silently ignored, so an operator never learns the yaml is stale (retro A3, A5 code; C5 / D20).

**Approach:** One numeric helper raises `ConfigError` on non-numeric or non-finite input for every commission number and zone weight; add the C5 range checks; `parse_config` returns `ignored_keys` (unknown top-level and `pid.*` keys, AppDaemon's reserved app keys excepted) and `initialize` logs them as one WARNING; docs say so.

## Boundaries & Constraints

**Always:** Every rejection is a `ConfigError`, so `initialize` logs `HVAC config error: …` and returns. Valid commissions parse to the same values as today, except an omitted `base_water_temp` (see matrix). `config.py` imports without AppDaemon. Reserved AppDaemon keys never appear in `ignored_keys`.

**Never:** No change to the control law (`pid.py`), listeners, or the house `apps/apps.yaml` (entry 6). No validation of other zone sub-keys. No auto-migration of legacy keys. The runtime non-finite-`e` guard is deferred to entry 8 (deferred-work, 2026-11-07).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected | Error Handling |
|----------|--------------|----------|----------------|
| Non-numeric | `setpoint_min`, `setpoint_max`, `control_interval`, `base_water_temp`, `pid.kp/ki/i_term_min/i_term_max` = `"abc"`, `None`, `[1]`, or `true` | rejected, message names the key | `ConfigError` → initialize logs `HVAC config error`, no raise, no `run_every` |
| Non-finite | same keys, or a zone `weight`, = `nan` / `inf` / `-inf` | rejected, names the key (zone name for weight) | `ConfigError` |
| Negative gain | `pid.kp = -1` or `pid.ki = -0.1` | rejected | `ConfigError` |
| Fractional interval | `control_interval` `60.7` or `0.5` | rejected: `control_interval must be a whole number of seconds`; `60.0` and `"60"` → 60 | `ConfigError` |
| Zero gains | `kp = 0`, `ki = 0` | accepted | none |
| I-term excludes 0 | `i_term_min/max` = `1, 5` or `-5, -1` | rejected | `ConfigError` |
| I-term edge | `0, 5` | accepted | none |
| Base outside clamp | explicit `base_water_temp` 39.9 or 55.1, bounds 40–55 | rejected | `ConfigError` |
| Base on bound | 40 or 55 | accepted | none |
| Base omitted | bounds 42–60 (house today); bounds 30–35 | base 42; base 35 (40 clamped into bounds) | none |
| Legacy keys | `outdoor_temperature`, `weather_feedforward`, `pid.integral_min`, `foo` | `ignored_keys = ("foo", "outdoor_temperature", "pid.integral_min", "weather_feedforward")` | one WARNING naming all; app starts |
| AppDaemon keys | example yaml with `module`, `class`, plus `name`, `priority`, `log_level`, `constrain_*` | `ignored_keys == ()` | no WARNING |
| Overflow / odd keys | a number `10**400`; a non-string key (top-level `60: x`, `pid: {1: 2}`) | overflow rejected; odd keys reported as `"60"`, `"pid.1"` | `ConfigError` for overflow; never a raw `OverflowError` / `TypeError` |

</frozen-after-approval>

## Code Map

- `apps/ha_smart_hvac/config.py` -- add `_number(mapping, key, default, label)`: reject `bool`, `TypeError`/`ValueError`/`OverflowError`, `not math.isfinite`. Use it for `setpoint_min/max` (via `_require`), `control_interval` (then non-integral → the whole-seconds error, `int()`, keep `<= 0`), `base_water_temp`, every `pid.*` in `_parse_pid`, and `weight` in `_parse_zone` (keep the existing `>= 0` check and messages). Checks: `kp < 0` / `ki < 0`; `not (i_term_min <= 0 <= i_term_max)` after the existing `min < max`; explicit base in `[setpoint_min, setpoint_max]`; omitted base = `min(max(40.0, setpoint_min), setpoint_max)`. Constants `_KNOWN_KEYS`, `_PID_KEYS`, `_APPDAEMON_KEYS` (+ prefix `constrain_`); `ignored_keys` built from `str(k)`, sorted, `pid.` prefix for nested keys.
- `apps/ha_smart_hvac/models.py:66-74` -- `HvacConfig`: `ignored_keys: tuple[str, ...] = ()` last.
- `apps/ha_smart_hvac/hvac_app.py:21-36` -- after a successful parse, one `level="WARNING"` line if `ignored_keys`, then normal init.
- `docs/house-calibration.md` -- §2 (~line 29): `control_interval` must be a whole number of seconds. §3: replace the "base below `setpoint_min`" paragraph with the in-bounds rule (explicit out-of-bounds = config error; omitted = 40 clamped into bounds). Lines ~76 and ~80 ("are ignored"): leftover keys are ignored and logged as one WARNING at startup. One short list of the rejections.
- `tests/test_config.py` -- matrix rows as parametrized tests. `test_parse_apps_yaml_example` stops popping `module`/`class`, asserts `ignored_keys == ()`. `test_legacy_outdoor_and_feedforward_keys_ignored` and `test_parse_ignores_legacy_integral_keys` assert names in `ignored_keys` (compare configs with `ignored_keys` replaced). `test_parse_rejects_non_numeric_zone_weight` keeps its message. Drift guard: for each field in `AppConfig.model_fields` (`appdaemon.models.config.app`), `field.alias or name` is in `_APPDAEMON_KEYS` (the keys `by_alias` dumps; `module_name`/`class_name` are not).
- `tests/test_hvac_app.py` -- reuse `_init_app`, `_warn_msgs`: parametrized over one case per rejection row (non-numeric, non-finite, negative gain, fractional interval, I-term excludes 0, base out of bounds, non-finite weight, overflow) → ERROR containing `HVAC config error`, no `run_every`, no exception; legacy keys → exactly one WARNING naming them, `run_every` called; clean args → no WARNING.

## Tasks & Acceptance

**Execution:**
- [x] `apps/ha_smart_hvac/models.py` -- `ignored_keys` on `HvacConfig` -- entry 6 checks through it.
- [x] `apps/ha_smart_hvac/config.py` -- numeric helper, C5 checks, weight finiteness, base default, ignored keys -- C5.
- [x] `apps/ha_smart_hvac/hvac_app.py` -- one WARNING at initialize -- C5 / retro A5.
- [x] `tests/test_config.py` -- matrix rows, drift guard, three updated tests -- C5.
- [x] `tests/test_hvac_app.py` -- initialize error-log and WARNING tests -- ticket verify.
- [x] `docs/house-calibration.md` -- WARNING sentence, rejection list, base rule -- ticket description.

**Acceptance Criteria:**
- Given the example yaml with `module` and `class`, when `parse_config` runs, then `ignored_keys == ()`.
- Given plain Python outside AppDaemon and args with legacy keys, when `parse_config` runs, then `ignored_keys` lists them (entry 6's check).
- Given any change, when `uv run pytest` and `uv run ruff check` run, then both are clean.

## Implementation Notes

Full route via implementation subagent; 268 tests green, ruff clean, example yaml → `ignored_keys == ()`. Matrix audit: all 12 rows covered by passing tests (config parametrized rows + `test_initialize_logs_config_error_without_raising` over 8 rejection kinds, WARNING / no-WARNING initialize tests, drift guard on `AppConfig.model_fields`). `ha_smart_hvac/__init__.py` imports `HvacApp`, so `from ha_smart_hvac.config import …` still loads AppDaemon (pre-existing; entry 6's check runs in the uv env where it is installed).

## Plan Change Log

- 2026-11-07 (party, human lock A): omitted `base_water_temp` = 40 clamped into the bounds; in-bounds check for explicit values only.
- 2026-11-07 (party, human lock A): `control_interval` rejects non-integral values instead of truncating.
- 2026-11-07 (party, human lock C, then split by user at the token gate): the runtime non-finite-`e` guard in `pid.py` moved to deferred-work for entry 8; 1.7 instead rejects a non-finite zone `weight` at parse time, closing the yaml path to `clamp(nan) == setpoint_max`.

## Review Triage Log

### 2026-11-08 (quick)
**Triage:** 0 high, 0 medium, 2 low → 1 patched, 1 rejected; 0 false.

- low, rejected — huge finite `control_interval` (e.g. `1e15`) passes parsing and `run_every` → `timedelta(seconds=…)` raises a raw `OverflowError` in `initialize` (confirmed: `timedelta(seconds=1e15)` overflows). Pre-existing (`int(1e15)` was accepted before); no realistic commission sets an interval of ~3 million years, and the fix adds a new upper-bound guard → rejected under the unlikely-low rule.
- low, patch — `deferred-work.md` still lists two entries 1.7 resolves (house base 40 vs `setpoint_min` 42 lag, whose "accept the lag" advice is now wrong; I-term range excluding 0) → patched: "Resolved in 1.7" section added, originals kept.

## Design Notes

Reserved AppDaemon keys (4.5.13 `BaseApp`/`AppConfig`/`GlobalModule`; `self.args` is `model_dump(by_alias=True, exclude_unset=True)` and AppDaemon injects `name`): `name`, `config_path`, `module`, `class`, `dependencies`, `global_dependencies`, `disable`, `priority`, `pin_app`, `pin_thread`, `log`, `log_level`, and any `constrain_*`. Hard-coded so `config.py` imports without AppDaemon; the drift guard catches an upgrade that adds a field.

YAML `true` is rejected (`float(True) == 1.0` would pass silently). Intended accepts: numeric strings Python `float` takes (`" 60 "`, `"6_0"` → 60.0) and PyYAML 1.1 sexagesimal `1:00` (= 60); `pid: null` means defaults, while `pid.kp: null` is rejected. Whole-seconds `control_interval` is beyond C5's letter, in its reject-don't-coerce spirit.

Warning shape: `HVAC config: ignoring legacy or unknown keys: foo, outdoor_temperature, pid.integral_min, weather_feedforward`.

Omitted base follows the clamp because the order 5 → 7 → 6 ships 7 before the house commission: the house has `setpoint_min: 42` and no `base_water_temp`, so a strict check on the default would brick the house App on deploy. The house base moves 40 → 42, removing the ~3 h I-term dead zone in deferred-work. An explicit out-of-bounds base now fails to start: the commit carries a `BREAKING CHANGE:` footer (retro A10) and the doc's upgrade note says so.

## Verification

**Commands:**
- `uv run pytest` -- expected: all green
- `uv run ruff check apps tests && uv run ruff format --check apps tests` -- expected: clean
- `PYTHONPATH=apps uv run python -c "import yaml; from ha_smart_hvac.config import parse_config; print(parse_config(yaml.safe_load(open('apps.yaml.example'))['hvac']).ignored_keys)"` -- expected: `()`
