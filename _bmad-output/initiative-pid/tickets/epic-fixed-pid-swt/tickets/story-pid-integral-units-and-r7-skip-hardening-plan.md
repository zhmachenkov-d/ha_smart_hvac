---
title: '1.5 PID integral units and R7 skip hardening'
type: 'bugfix'
ticket: '5'
created: '2026-11-07'
status: 'built'
baseline_revision: '94880392184ee414fcf31aa130418be82a5dcd41'
route: 'full'
route_source: 'auto'
risk: 'high'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The shipped PI law integrates with `dt = control_interval` in seconds against `±50` integral bounds, so ∫ rails in one tick and the I-term acts as a ±5 °C relay (retro SR1). The R7 skip compares against `last_commanded`, so it never repairs external plant drift and advances ∫ without reading the plant (SR2). Kp, ∫ carry across ticks, the lower ∫ clamp, and an off-grid skip are untested (VG1–VG4).

**Approach:** Integrate in °C·h (`dt = control_interval / 3600`, `ki` in 1/h) and bound the I-term `ki·∫` in °C of water via `pid.i_term_min` / `pid.i_term_max` (replacing `integral_min` / `integral_max`); C4 defaults `kp 1.0`, `ki 1.0`, I-term `[−10, +15]`. Skip the plant call only when the plant entity already reads the rounded command; never advance ∫ when the plant entity is unavailable. Update example yaml and calibration doc; close the test gaps.

## Boundaries & Constraints

**Always:** Command stays `round(clamp(base + kp·e + ki·∫_pre, setpoint_min, setpoint_max), 1)` using ∫ before this tick's step. Same-sign SWT-saturation freeze is unchanged. ∫ advances only on the periodic tick, and only when the plant entity is readable (written, or already at the command). `ki = 0` keeps ∫ and the I-term at 0. Idle / plant-off clear inventory unchanged.

**Never:** No ConfigError for non-finite values, negative gains, or an I-term range excluding 0 and no legacy-key WARNING (entry 7). Do not edit house `apps/apps.yaml` (entry 6). Do not delete `_last_commanded` state (entry 8, D22) — it may stay assigned but must not be read for skipping. No AGENTS/CONTEXT/ADR/knowledge edits (epic 2). No change to listeners or event clear-only behaviour.

**Assumes:** plant `number` step 0.1 (verified in HA 2026-11-07 on `number.opentherm_bridge_control_setpoint`); a coarser step would cause a known write-repeat each tick and is out of scope. A plant that echoes a boiler-clamped value (e.g. reads 55 while the command is 58) likewise causes a write every tick; accepted under R7 and out of scope (user, 2026-11-07).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Small e, 3 ticks | e = 0.2, interval 300, ki 1.0 | I-term 0.05 °C after 3 steps | — |
| Full hour | e = 1, 12 ticks | I-term +1.0 °C; no single tick reaches a rail | — |
| Lower rail | sustained e < 0, not saturated low | I-term stops at `i_term_min` | — |
| ki = 0 | any e | ∫ and I-term stay 0 | — |
| Off-grid equal | raw 41.96 → 42.0, plant reads 42.0 | no `number/set_value`; ∫ advances | — |
| Drift | `_last_commanded` 42.0, plant reads 50 | writes 42.0; ∫ advances | — |
| Plant unavailable | plant `unavailable`, `_last_commanded` equal to command | no write; ∫ unchanged; WARNING | existing "Plant setpoint unavailable" WARNING |

</frozen-after-approval>

## Code Map

- `apps/ha_smart_hvac/pid.py` -- `evaluate_demand`: replace `integral_min/integral_max` with `i_term_min/i_term_max`; `dt` → `dt_hours`. Step: `cand = ∫ + e·dt_hours`; `ki == 0` → ∫ = 0; else ∫ = `clamp(ki·cand, i_term_min, i_term_max) / ki`. Freeze branch untouched. Update module/func docstrings for units.
- `apps/ha_smart_hvac/models.py:53-58` -- `PidConfig`: `kp 1.0`, `ki 1.0`, `i_term_min -10.0`, `i_term_max 15.0`; drop `integral_*`.
- `apps/ha_smart_hvac/config.py:57-72` -- `_parse_pid` reads `i_term_min` / `i_term_max` (min < max check, message names i_term); `integral_*` no longer read (silently ignored until entry 7).
- `apps/ha_smart_hvac/hvac_app.py:96-128` -- `_run_demand`: pass `dt_hours=control_interval/3600` and I-term keys; delete the `_last_commanded` equal-skip branch; rely on `_write_setpoint` (already returns True without a call when `current == value`, False when unavailable); set `_integral` / `_last_commanded` only when it returns True.
- `apps.yaml.example`, `docs/house-calibration.md` §3 and "Upgrading" -- new keys, units (∫ in °C·h, `ki` 1/h, I-term bounds °C water; changing `control_interval` does not rescale effective Ki), C4 values; `integral_min/max` replaced. "Upgrading" states: a yaml without `pid:` picks up the new defaults on update, and the I-term now builds over hours (°C·h), not per tick.
- `tests/test_pid.py` -- `_eval` helper on new kwargs (`dt_hours` default `300/3600`, `ki` default 1.0); existing ∫ expectations are in old units and must be recomputed, not deleted. `test_no_freeze_when_sat_opposite_sign` (~142) uses ∫ 300 / dt 1.0, impossible under a 15 °C cap: redesign (e.g. base 54, ∫ 5, e = −1 → ∫ 4.9167).
- `tests/test_config.py:40-110` -- defaults and override tests to new keys; rejection test to `i_term_min/max`.
- `tests/test_hvac_app.py` -- `_tick_args` to new keys, `_KI` = 1.0; ∫ assertions at lines ~197, ~217, ~234 recomputed in °C·h; `test_equal_rounded_skip_no_set_value` (~462) rewritten off-grid with `_last_commanded` None (it locks VG4, the post-rounding compare; the drift and plant-unavailable rows are what fail on the old `_last_commanded` branch).
- Fixtures use base 40 = `setpoint_min` 40, so any e < 0 with I ≤ 0 is saturated low and freezes ∫: the lower-rail test needs its own fixture (e.g. base 52, bounds 40–60, e = −1, or ∫ seeded near `i_term_min`).

## Tasks & Acceptance

**Execution:**
- [x] `apps/ha_smart_hvac/models.py`, `apps/ha_smart_hvac/config.py` -- new PidConfig fields/defaults and parsing -- C4 commission.
- [x] `apps/ha_smart_hvac/pid.py` -- hour-based step with I-term clamp and ki = 0 hold -- SR1.
- [x] `apps/ha_smart_hvac/hvac_app.py` -- wire `dt_hours`; plant-read-only skip; ∫ only on readable plant -- SR2 / R7.
- [x] `tests/test_pid.py` -- I/O matrix rows 1–4, `kp = 2` changes `u_pid`, and a multi-tick trace (see Design Notes) -- VG1, VG3, retro A1.
- [x] `tests/test_hvac_app.py` -- matrix rows 5–7 and a two-tick test where ∫ from tick 1 appears in tick 2's written SWT (plant state updated between ticks) -- VG2, VG4.
- [x] `tests/test_config.py` -- defaults, overrides, rejection on new keys; old `integral_*` keys do not affect parsed config.
- [x] `apps.yaml.example`, `docs/house-calibration.md` -- keys, units, values.

**Acceptance Criteria:**
- Given the example yaml, when parsed, then `pid` is `kp 1.0, ki 1.0, i_term_min -10, i_term_max 15`.
- Given C4 defaults and constant e = 1 at 300 s, when the tick runs repeatedly, then the commanded SWT rises by about 1/12 °C per tick rather than jumping to a rail.
- Given any change, when `uv run pytest` and `uv run ruff check` run, then both are clean.

## Implementation Notes

Full route via implementation subagent. Matrix audit: rows 1–7 covered by 12 passing tests; mutation check (old `_last_commanded` skip re-inserted) fails the drift and plant-unavailable tests, so R7 is locked.

## Plan Change Log

## Review Triage Log

### 2026-11-07 (quick)
**Triage:** 0 high, 0 medium, 1 low → patched, 1 false.

- low — `docs/house-calibration.md` §3 says ∫ freezes while the command is "pinned" at a bound; `pid.py` freezes only when unclamped `raw` is strictly past a bound with same-sign e (raw 54.96 → 55.0 still steps) → patched: sentence reworded to the raw-past-bound rule.
- false — `BREAKING CHANGE:` footer (retro A10) not verifiable in an uncommitted diff: no defect in the diff; the footer is applied when the commit is made (step 05).

## Design Notes

Clamping the I-term then dividing by `ki` keeps ∫ in °C·h while the yaml bound stays in °C of water, and stays correct for any nonzero `ki` (entry 7 rejects negatives).

Multi-tick trace test (parametrized): constant e = 1, C4 defaults, 200 ticks at 300 s.
- Example bounds `40–55`, base 40: the saturation freeze stops growth once `raw > 55`; I-term lands at 14.0 + float noise (assert `approx(14.0, abs=0.1)` and `< 15`, never `> 14`); command stays 55.0.
- High bounds `42–60`, base 42 (saturation arithmetic, not the house config): I-term reaches `i_term_max` 15; command 58.0.
- Both: per-tick command step ≤ `ki·e·dt_hours + 0.1` (with float tolerance); never outside bounds.

Release: the commit changes defaults and stops reading `integral_*`, so it carries a `BREAKING CHANGE:` footer (retro A10).

Under the example commission (base = `setpoint_min`) `i_term_min` is reachable only when base sits above `setpoint_min`; the calibration doc says so.

## Verification

**Commands:**
- `uv run pytest` -- expected: all green
- `uv run ruff check apps tests && uv run ruff format --check apps tests` -- expected: clean
- `rg -n "integral_min|integral_max" apps tests apps.yaml.example docs` -- expected: only the test asserting old keys are ignored and the doc's upgrade note
