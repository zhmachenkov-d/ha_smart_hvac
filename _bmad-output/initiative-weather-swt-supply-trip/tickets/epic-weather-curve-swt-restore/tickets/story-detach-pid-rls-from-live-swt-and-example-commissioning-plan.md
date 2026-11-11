---
title: 'Detach PID/RLS from live SWT and example commissioning'
type: 'story'
ticket: '2'
created: '2026-11-11'
status: 'built'
risk: 'high'
route: 'full'
route_source: 'auto'
lenses_ran: [blind-hunter, edge-case-hunter, verification-gap, intent-alignment]
review_source: 'auto'
review: 'thorough'
context: []
baseline_revision: '4d921dd2f68ccd9ef4223148abd37e16b9d50a48'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent
**Problem:** After the weather-curve tracer, demand SWT is FF-only, but `hvac_app` still initializes PID ∫ / RLS overlay (`rls_state.json`), keeps dead RLS helpers, imports `quantize_command` from `pid.py`, and `apps.yaml.example` still commissions `base_water_temp` / `pid` / adaptive rails as if they drove water.

**Approach:** Fully detach PID/RLS from the live App + example commissioning: strip app runtime state/helpers/imports, stop parsing water-law PID nests into `HvacConfig`, remove them from `apps.yaml.example`, relocate `quantize_command` to `feedforward.py`, and rewrite/delete app/config tests that assert the removed surface — leave `pid.py` / `rls.py` and their unit tests on disk for epic 3.

## Boundaries & Constraints
**Always:**
- Keep FF demand law and gates from entry 1: `_gate_prelude` → `_run_demand` → `weather_feedforward` → `quantize_command(u_ff, min, max)`; idle write `0`; plant-off no write; Outdoor listener; CZ log-only; CAP-8 shared writer.
- Move `quantize_command` to `feedforward.py` (OQ1-A). `hvac_app` / `test_hvac_app` / `test_pid` import from `feedforward`; `pid.py` imports from `feedforward` only for `evaluate_demand` — no re-export (F6-B).
- Remove from live App: `_integral`, all `_rls*` / fallback latch, `_load_rls_overlay`, `_maybe_persist_rls`, `_gains_for_demand`, `_maybe_rls_step`, `_enter_rls_fallback` / `_clear_rls_fallback`, `rls` imports, adaptive init, legacy `pid.ki` WARNING, PID-branded init log.
- After ∫ / `y_prev` are gone, drop `_clear_pid_ephemeral`; plant-off / idle keep write/no-write semantics only — vacuous "clear" until epic-2 trip state (F1-A). Do not leave a no-op clear helper; epic R2/R3 wording stays for now.
- Strip `base_water_temp`, `pid`, `boiler_water` from `HvacConfig` and `parse_config` (`_parse_pid` / `_parse_boiler_water` / `_KNOWN_KEYS` / `_PID_KEYS` as needed). Delete `PidConfig` with that strip — do not relocate to `pid.py` (`evaluate_demand` / `test_pid` never used it) (F2-A).
- Leftover house keys `pid` / `base_water_temp` / `boiler_water` are ignored + init WARN as **top-level** `ignored_keys` entries after drop from `_KNOWN_KEYS` (OQ2-A, F3-A); drop nested `pid.*` walker with `_PID_KEYS`. Entry 3 HITL removes them. Do not `ConfigError` solely for their presence.
- `apps.yaml.example`: delete `base_water_temp`, entire `pid` nest, adaptive/`boiler_water`/rails comments about `rls_state.json`; refresh header so FF is the only water-law commission; keep Outdoor + FF + rails 50/60 + mild-pin note.
- House `apps/apps.yaml` entity IDs unchanged (entry 3 HITL). Do not edit house yaml here.
- Keep `pid.py` / `rls.py` on disk; keep `tests/test_pid.py` / `tests/test_rls.py`.
- Demand / app tests must not invoke PID/RLS or write `rls_state.json` on the demand path; delete hvac tests that only lock removed app surface (RLS init/load/persist, ∫ clear matrix, adaptive init) (F4-A).
- Stay inside AppDaemon `ha_smart_hvac` writing existing `plant_setpoint`. No ADR/CONTEXT/AGENTS/`knowledge/` rewrite (epic 3).

**Never:**
- Delete `pid.py` / `rls.py` (epic 3).
- Restore CAP-7 / `ff_auto_correct_state.json`.
- Change Exclusive Session, Heating Demand definition, or house entity IDs.
- Drive SWT from Critical Zone or zone air error.
- Re-wire RLS step/persist onto the FF demand path.

## I/O & Edge-Case Matrix
| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| Happy demand | Plant on + Heating Demand + finite Outdoor | `quantize_command(u_ff)` from `feedforward`; no PID/RLS on path; no `rls_state.json` write | — |
| Idle / plant-off | No demand / plant off | Write `0` / no write; vacuous clear (no `_clear_pid_ephemeral`) | — |
| Example yaml | Parse `apps.yaml.example` | Outdoor+FF only water law; no `pid` / `base_water_temp` | — |
| Legacy house keys | House yaml still has `pid` / `base_water_temp` / `boiler_water` | Ignored as top-level `ignored_keys`; init WARN (OQ2-A, F3-A) | No ConfigError for presence alone |
| Module unit tests | `test_pid` / `test_rls` | Still pass against on-disk modules | — |
| Adaptive yaml | `pid.adaptive` / `boiler_water` in args | Treated as ignored legacy keys; not parsed into `HvacConfig` | Init WARN |

</frozen-after-approval>

## Code Map
Continuity (entry 1): FF demand already live; PID/RLS is zombie init/helpers/config/example. Entry 1 left `quantize_command` in `pid.py` and `pid` nest in example for this story. Until epic 3, **this plan overrides** AGENTS.md / CONTEXT.md bullets that still describe PID SWT, ∫/RLS on the water path, or ban Outdoor/FF.

- `apps/ha_smart_hvac/feedforward.py` — host `clamp` + `quantize_command` (move both from `pid.py` to avoid pid↔feedforward cycle); keep `weather_feedforward`.
- `apps/ha_smart_hvac/pid.py` — keep on disk; import `clamp` / `quantize_command` from `feedforward` for `evaluate_demand` only (no re-export).
- `apps/ha_smart_hvac/rls.py` — leave on disk; no App callers after strip.
- `apps/ha_smart_hvac/hvac_app.py` — strip `_integral`, all `_rls*` / latch consts, `_seed_last_saved` / `_apply_loaded_adapted` / `_load_rls_overlay` / `_maybe_persist_rls` / `_gains_for_demand` / `_maybe_rls_step` / `_enter_rls_fallback` / `_clear_rls_fallback`, `_state_path` + unused `Path` import, `rls` imports, adaptive init, legacy `pid.ki` WARN, `_clear_pid_ephemeral` + call sites in prelude/`_go_idle`. Import `quantize_command` from `feedforward`. Replace PID init log with `HVAC weather-curve SWT app initialized`. Drop stale `_run_demand` comment about frozen `last_u` / adaptive. Keep FF `_run_demand`, Outdoor listener, CAP-8 writer, CZ log-only.
- `apps/ha_smart_hvac/models.py` — delete `PidConfig`; drop `HvacConfig.base_water_temp` / `.pid` / `.boiler_water`; keep Outdoor/FF/zones/plant/rails/`ignored_keys`.
- `apps/ha_smart_hvac/config.py` — remove `_parse_pid` / `_parse_adaptive` / `_parse_boiler_water` / `_parse_rail` (adaptive-only) / `_PID_KEYS` / `_DEFAULT_BASE_WATER_TEMP`; drop pid/base/boiler from `_KNOWN_KEYS` → top-level `ignored_keys`; remove nested `pid.*` walker; stop wiring those fields in `parse_config`.
- `apps.yaml.example` — delete `base_water_temp`, `pid` nest, adaptive/`boiler_water`/`rls_state` comments; FF-only water-law header; keep Outdoor + FF + rails 50/60 + mild-pin note.
- `tests/test_hvac_app.py` — slim `_tick_args` / fixtures: **no** `pid` / `base_water_temp` / adaptive / `RlsState` (else `ignored_keys` breaks clean-args WARN tests). DELETE RLS-init/load/persist, ∫-clear-only, legacy-ki tests. REWRITE all gate/FF survivors: drop `_integral`/`_rls` seed+assert (incl. tests that mutate `app._rls`). Prove FF command + no `rls_state.json`. Import-lock: source/AST scan that `hvac_app` module ⊬ `rls` and ⊬ `quantize_command` from `pid`.
- `tests/test_config.py` — DELETE: adaptive/rails/boiler/`base_water_temp` clamp, `PidConfig` commission, omitted-pid defaults, pid/weight overrides, i-term reject/accept, gains, legacy-ki. REWRITE: example parse (assert `"pid"` / `"base_water_temp"` absent from example args; no `PidConfig`); ignored-keys → top-level `"pid"` / `"base_water_temp"` / `"boiler_water"` (nested `pid.*` walker gone); trim `_ALL_NUMERIC_KEYS` / `_TOP_NUMERIC_KEYS` of pid/base keys **without** dropping setpoint/interval coverage. KEEP Outdoor/FF locks. Optional: leftover top-level keys → init WARNING path.
- `tests/test_pid.py` — KEEP; import `clamp` / `quantize_command` from `feedforward`. `tests/test_rls.py` — KEEP.
- Do not change: `coordinator.py`; Exclusive Session; house `apps/apps.yaml`.

## Tasks & Acceptance
**Execution:**
- [ ] `feedforward.py` + `pid.py` + imports — move `clamp` + `quantize_command`; no `pid` re-export; update `hvac_app` / `test_hvac_app` / `test_pid`.
- [ ] `hvac_app.py` — strip PID/RLS runtime/helpers/`_state_path`/init branding; drop `_clear_pid_ephemeral`; set weather-curve init log.
- [ ] `models.py` + `config.py` — strip water-law PID fields/parse/`_DEFAULT_BASE_WATER_TEMP`; delete `PidConfig`; legacy keys → top-level `ignored_keys` WARN.
- [ ] `apps.yaml.example` — strip pid/`base_water_temp`/adaptive commission + comments.
- [ ] `test_hvac_app.py` + `test_config.py` — slim fixtures; delete full removed-surface lock set; rewrite survivors + numeric-key lists; FF + no `rls_state.json` + import-locks; keep `test_pid` / `test_rls`.

**Acceptance Criteria:**
- Given Plant on + Heating Demand, when tick/event runs, then SWT follows FF quantize and tests prove no PID/RLS on that path (FF command + no `rls_state.json`; import-lock `hvac_app` ⊬ `rls` and ⊬ `quantize_command` from `pid`).
- Given `apps.yaml.example`, when parsed, then no live `pid` / `base_water_temp` water-law nest remains.
- Given leftover `pid` / `base_water_temp` / `boiler_water` with valid Outdoor+FF, when parsed, then config succeeds and those keys are top-level `ignored_keys`.
- Given `pid.py`/`rls.py` on disk, when `uv run pytest` / `uv run ruff check apps/ha_smart_hvac tests` run, then all pass/clean.

## Implementation Notes
Entry 1 restored FF and left PID/RLS zombies for this story. House HITL = entry 3; docs/module delete = epic 3. Vacuous clear until epic-2 trip state — epic R2/R3 prose unchanged here. AGENTS.md / CONTEXT.md still contradict FF demand until epic 3 — follow **this plan** (and entry 1), not those bullets, for water-path behavior.

## Plan Change Log
- 2026-11-11: OQ1-A (`quantize_command` → `feedforward`); OQ2-A (legacy ignored+WARN).
- 2026-11-11: F1-A vacuous clear; F2-A delete `PidConfig`; F3-A top-level `ignored_keys`; F4-A test DELETE/REWRITE; F5-A FF + no `rls_state.json`; F6-B no re-export; F7-A import-lock.
- 2026-11-11: Resume draft — Code Map refreshed vs post-tracer App/config/tests.
- 2026-11-11: Review apply-all — move `clamp` with `quantize`; strip `_state_path`/`Path`; init log string; broaden config DELETE + numeric-key surgery; explicit fixture slim; dual import-locks; AGENTS/CONTEXT override note; drop `_DEFAULT_BASE_WATER_TEMP` + stale `last_u` comment.

## Review Triage Log
- 2026-11-11 review: Critical `clamp` cycle → move `clamp`+`quantize` (applied). Important: `_state_path`, init log, config DELETE breadth, fixtures, import-lock pattern, AGENTS override (applied). Nits: `_DEFAULT_BASE_WATER_TEMP`, stale `last_u` comment (applied); optional `test_feedforward` quantize coverage declined (keep in `test_pid`).
- blind: pid public clamp/quantize bindings after feedforward import — verdict medium — evidence: `pid.py` `from feedforward import clamp, quantize_command` leaves names importable as `from pid import …`, violating F6-B no re-export.
- blind: docs/house-calibration.md still commissions pid/base — verdict false — evidence: Approach names apps.yaml.example as commission strip; house-calibration lag is pre-entry-1-style docs drift (FF already live), not a new live-App defect from this strip.
- blind: AGENTS/CONTEXT/ADR still describe PID SWT — verdict medium — evidence: real contradiction for agents/operators; intent Always forbids rewrite here (epic 3) → defer.
- blind: test_config `not hasattr` for pid/base/boiler/PidConfig — verdict medium — evidence: Design Notes F4-A ban hasattr zombies; new asserts added this diff (pre-existing ladrc hasattr left alone).
- blind: event demand lacks no-`rls_state.json` assert — verdict medium — evidence: AC wants tick/event; only `test_demand_tick_writes_ff_command_no_rls_state` checks file.
- blind: `test_event_idle_write_fail_still_logs` dropped Plant setpoint unavailable WARN — verdict medium — evidence: tick sibling still asserts it; event path can regress fail-closed WARN.
- blind: `test_write_setpoint_fail_closed` dropped `float("nan")` / `object()` — verdict medium — evidence: baseline parametrize included them; current list is strings/None only.
- blind: `test_plant_off_no_write` dropped `call_service.assert_not_called` — verdict low — evidence: `_set_value_writes == []` remains; restore is trivial belt-and-suspenders.
- blind: plan tasks unchecked / tickets.toml / memlog hygiene — verdict false — evidence: build workflow owns plan status; tickets mark forbidden; not a product defect.
- blind: no quantize coverage in test_feedforward — verdict false — evidence: prior Review Triage declined; coverage stays in test_pid until epic 3.
- blind: apps.yaml.example missing legacy-ignore WARN note — verdict low — rejected: everyday operators use house HITL entry 3; comment not required by intent.
- blind: pid.py docstring still reads as live SWT law — verdict low — rejected: module retained with evaluate_demand; epic 3 owns retirement banner.
- blind: AST import-lock misses alternate rls shapes / bare pid import / F6 re-export surface — verdict medium — evidence: current walk only checks `ha_smart_hvac.rls*` modules and named imports from pid.
- blind: feedforward docstring omits clamp/quantize — verdict low — rejected: cosmetic.
- edge: `from ha_smart_hvac import rls` / relative rls import evade lock — verdict medium — evidence: ImportFrom `ha_smart_hvac` with name `rls` not rejected.
- edge: `from ha_smart_hvac.pid import *` evades quantize/clamp name check — verdict medium — evidence: star not asserted before name set check.
- edge: claim "no pid re-export" falsified at pid.py:17 — verdict medium — evidence: same as blind re-export (carried).
- verification-gap: initialize never asserts no rls_state.json — verdict medium — evidence: pre-verified; only demand-tick tmp_path checks file; init tests never observe app_dir filesystem (gap: restore init persist would slip).
- verification-gap Other: pid re-export — verdict medium — carried with blind/edge re-export.
- intent-alignment: descriptive only — no separate defect rows beyond surfaces already triaged (proof proxies vs runtime strip).

## Design Notes
F4-A: delete app RLS/∫-only tests; strip ∫/RLS asserts from survivors; no `not hasattr` zombies; keep module unit tests until epic 3. F6: move `clamp` with `quantize_command` so `feedforward` does not import `pid`. Dropping keys from `_KNOWN_KEYS` yields top-level ignore+WARN; remove `_PID_KEYS` walker with the parse strip. Import-lock via source/AST scan, not runtime hasattr.

## Verification
**Commands:**
- `uv run pytest` — expected: all pass
- `uv run ruff check apps/ha_smart_hvac tests` — expected: clean
