---
title: 'Remove LADRC and ωc from the water path'
type: 'feature'
ticket: '2'
created: '2026-10-18'
status: done
baseline_revision: '6bf761e53fa5c52198f3a6235898c027764fa89f'
route: 'full'
route_source: 'auto'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/initiative-weather-curve-zone-actuators/spec-weather-curve-swt-only/spec-weather-curve-swt-only.md'
  - '{project-root}/_bmad-output/initiative-weather-curve-zone-actuators/epic-weather-curve-swt-only/story-tracer-weather-curve-swt-law-plan.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** After story 1.1, water-path LADRC/ωc and CZ-as-SWT symbols still sit dormant — CAP-4 requires removal, not dormancy.

**Approach:** Delete LADRC + ωc tuner/persistence + blow-up helpers, strip ladrc/tune yaml/config, purge `select_critical_zone`/`ControlDecision`; rewrite tests so CAP-5 and keepers stay green. ADR/CONTEXT → entry 1.3.

## Boundaries & Constraints

**Always:**
- FF law unchanged: PM on + demand → `clamp(u_ff)`; plant-on idle → `0`; plant-off → no write; `setpoint_min` 40; reuse `has_heating_demand` + `weather_feedforward`.
- Delete `ladrc.py`/`ladrc_tuner.py` (ωc load/persist/`publish_sensor`/tune-state gone), all `hvac_app` residue/guard/blow-up/ωc helpers, `_ladrc`/`_tuner`/`_blow_up_*`.
- Strip `ladrc`/`tune_state_path` from models, `parse_config`, `apps.yaml.example`.
- Delete `select_critical_zone` + `ControlDecision` (CAP-7 may later ID max-error zone for rise-rate only).
- `test_ladrc.py` / `test_ladrc_tuner.py` gone or absence-only; slim `_tick_*` and rewrite **all** keepers on them; suite green.
- No house entity-ID commits; operator strips leftover `ladrc:` from gitignored `apps/apps.yaml` before Exclusive Session (no warn-on-unknown).

**Never:**
- Touch ADR/CONTEXT/AGENTS/house-calibration/`knowledge/`.
- Reintroduce air→SWT tracking, lower `setpoint_min`, CAP-6/CAP-7, or leave dormant LADRC/tuner/CZ-driver/ωc-persist API.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Demand | PM on, demand | `clamp(u_ff)`; no `_ladrc`/`_tuner`/`_blow_up_*` | No error expected |
| Plant-on idle | PM on, no demand | Write `0`; no `_ladrc`/`_tuner`/`_blow_up_*` | No error expected |
| Plant-off | PM off | No `set_value`; no `_ladrc`/`_tuner`/`_blow_up_*` | No error expected |
| Config / example | args or `apps.yaml.example` w/o ladrc | `parse_config` OK; no ladrc/tune/omega_c keys | Existing ConfigError rules |
| Modules / CZ | import / search | no `ladrc`/`ladrc_tuner`/`select_critical_zone`/`ControlDecision` | ModuleNotFoundError / no symbol |
| House yaml | leftover `ladrc:` in gitignored apps.yaml | Operator strips before Exclusive Session; parse ignores unknown keys | N/A (ops) |

</frozen-after-approval>

## Code Map

- `hvac_app.py` — Delete helpers ~L24–161; drop Ladrc; no construct/clear of `_ladrc`/`_tuner`/`_blow_up_*`; keep FF write + `_write_setpoint`/readers; de-LADRC log/docstring.
- `ladrc.py`, `ladrc_tuner.py` — delete.
- `models.py` / `config.py` — Drop Ladrc*, `ControlDecision`, `ladrc`/`tune_state_path` parse.
- `coordinator.py` — Drop `select_critical_zone`; keep `has_heating_demand`.
- `__init__.py`, `apps.yaml.example` — Drop LADRC docstring / ladrc block.
- `tests/test_ladrc.py`, `test_ladrc_tuner.py` — delete or absence-only.
- `tests/test_hvac_app.py` (or slim `test_config.py`) — Migrate parse-without-ladrc + example smoke from tuner tests; slim `_tick_args`/`_tick_app`; rewrite **all** keepers (CAP-5 a–e, fail-write, outdoor/zones matrix, `write_setpoint_*`); delete leave-list residue/guard/latch/ωc tests.
- `tests/test_coordinator.py` — Drop picker tests; keep `has_heating_demand_*`.
- Out of scope: ADR/CONTEXT, house entity IDs, `knowledge/`.

## Tasks & Acceptance

**Execution:**
- [x] `apps/ha_smart_hvac/ladrc.py` + `ladrc_tuner.py` -- Delete (ωc persist/load/publish gone) -- CAP-4
- [x] `apps/ha_smart_hvac/models.py` + `config.py` -- Strip Ladrc*/ControlDecision + ladrc/tune parse -- contract
- [x] `apps/ha_smart_hvac/coordinator.py` -- Delete `select_critical_zone` -- CZ API
- [x] `apps/ha_smart_hvac/hvac_app.py` + `__init__.py` -- Remove helpers/construct/clear -- runtime
- [x] `apps.yaml.example` -- Remove ladrc/tune keys -- verify
- [x] `tests/test_ladrc.py` + `test_ladrc_tuner.py` -- Delete or absence-only -- verify
- [x] `tests/test_hvac_app.py` (+ optional `test_config.py`) + `test_coordinator.py` -- Slim `_tick_*`; rewrite all keepers; migrate parse/example smoke; drop CZ tests -- green

**Acceptance Criteria:**
- Given import of `ha_smart_hvac.ladrc` or `ladrc_tuner`, when resolved, then modules are absent (no ωc persist/load/publish left).
- Given `tests/test_ladrc.py` / `test_ladrc_tuner.py`, when listed, then gone or absence-only.
- Given args/`apps.yaml.example` without ladrc/tune keys, when `parse_config` runs, then success with no LADRC/tune fields.
- Given PM on + demand, when `control_tick` runs, then `clamp(u_ff)` and no `_ladrc`/`_tuner`/`_blow_up_*`.
- Given PM on idle or PM off, when `control_tick` runs, then I/O matrix write behavior and no `_ladrc`/`_tuner`/`_blow_up_*`.
- Given search for `select_critical_zone`/`ControlDecision`/`guard_u_track`/`sticky_blow_up_latch`/`should_apply_omega_c`/…, when run, then gone (`has_heating_demand` remains).
- Given house `apps/apps.yaml`, when Exclusive Session is prepared, then operator stripped leftover `ladrc:` (not committed here).
- Given the suite, when `uv run pytest` and ruff run, then they pass.

## Implementation Notes

2026-10-18: CAP-4 removal complete. Deleted `ladrc.py`/`ladrc_tuner.py` and `test_ladrc.py`/`test_ladrc_tuner.py`. Stripped `Ladrc*`/`ControlDecision`/`tune_state_path` from models+config; deleted all blow-up/ωc helpers and `_ladrc`/`_tuner`/`_blow_up_*` from `hvac_app`; deleted `select_critical_zone`. `_tick_app` is `_config` only; idle/off no longer clear gone objects. Migrated parse/example smoke (+ module absence) into `tests/test_config.py`. Left `ZoneSnapshot.reference_setpoint` for possible CAP-7. Operator must strip leftover `ladrc:` from gitignored `apps/apps.yaml` before Exclusive Session. Verified: `uv run pytest` 78 passed; ruff check/format clean; plan `rg` has no matches in package/example.

## Plan Change Log

## Review Triage Log

| Pass | high | medium | low | false | maybe-false | Notes |
|------|------|--------|-----|-------|-------------|-------|
| quick (loop 0) | 0 | 0 | 0 | 0 | 0 | No findings reported |

## Design Notes

Idle/off: drop clears with the objects. `_tick_app`: `_config` only. Migrate parse/example smoke off deleted tuner tests.

## Verification

**Commands:**
- `uv run pytest` -- expected: pass
- `uv run ruff check apps/ha_smart_hvac tests` && `uv run ruff format --check apps/ha_smart_hvac tests` -- expected: clean
- `rg -n "LadrcState|LadrcTuner|select_critical_zone|ControlDecision|tune_state_path|guard_u_track|sticky_blow_up_latch|should_apply_omega_c|format_blow_up_warning|advance_with_tracking_residue|next_decayed_omega_c" apps/ha_smart_hvac apps.yaml.example` -- expected: no matches
