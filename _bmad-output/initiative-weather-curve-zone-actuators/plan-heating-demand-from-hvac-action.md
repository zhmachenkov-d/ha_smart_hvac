---
title: 'Heating Demand from hvac_action'
type: 'feature'
ticket: ''
created: '2026-10-19'
status: done
baseline_revision: 'd42bfab20f1d5abb53a7a14c8a581d84dfd4d0fa'
route: 'full'
route_source: 'auto'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - '{project-root}/CONTEXT.md'
  - '{project-root}/docs/adr/0004-weather-curve-swt.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Heating Demand for the SWT gate is true only when some zone has `zone_error > 0`. A thermostat with `hvac_action == "heating"` but air already at/above setpoint (error ≤ 0) is treated as idle, so the plant writes `0` while climate still calls for heat.

**Approach:** Redefine Heating Demand as presence of any thermostat with `hvac_action == "heating"` (same eligibility already used for Zone Error contributors). Update coordinator gate, tests that currently manufacture idle via heating+zero-error, and domain docs that equate demand with positive Zone Error.

## Boundaries & Constraints

**Always:**
- Heating Demand predicate is thermostat `hvac_action == "heating"` (idle / off / cooling / unavailable / None do not demand).
- Shared API: `ZoneSnapshot.has_heating_eligible` (property wrapping `_eligible_thermostats`); both `has_heating_demand` and `select_max_error_demand_zone` must use it — not `zone_error > 0` and not `isfinite(zone_error)`.
- Plant Management off / outdoor missing / no valid zones behavior unchanged.
- CAP-7 demand pool uses the same Heating Demand predicate; then pick max `zone_error` among that pool (error may be ≤ 0). Zone Error formula and rise-rate math otherwise unchanged — including existing `near_setpoint_eps_k` hold when `|error| < eps`.
- Domain language stays Heating Demand / Zone Error / Critical Zone per CONTEXT.

**Never:**
- Restore air→SWT tracking or Critical Zone as SWT driver.
- Change weather-curve `clamp(u_ff)` formula or CAP-8 listener set.
- Use setpoint−temp sign as the SWT Heating Demand gate.
- Keep a separate `zone_error > 0` filter inside `select_max_error_demand_zone`.
- Define Heating Demand as `zone_error > -inf` / `isfinite(zone_error)` alone.

**Decisions:**
- CAP-7 demand pool aligns with Heating Demand (`hvac_action == "heating"`), then max Zone Error among that pool.
- Public eligibility API is `ZoneSnapshot.has_heating_eligible`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Heating, error ≤ 0 | Any zone has thermostat `hvac_action=heating`, zone_error ≤ 0 | `has_heating_demand` True → demand path (`clamp(u_ff)` when plant on); CAP-7 may select that zone | No error expected |
| Heating, deep overshoot | `hvac_action=heating`, zone_error ≤ −`near_setpoint_eps_k` | Demand True; CAP-7 may select; near_setpoint hold only if `|error| < eps`; otherwise rise-rate adaptation allowed (unchanged) | No error expected |
| Idle, large delta | All thermostats non-heating; air far below setpoint | `has_heating_demand` False → plant-on idle writes `0`; CAP-7 returns None | No error expected |
| Mixed zones | One heating (any error), peers idle | Demand True; CAP-7 picks max error among heating zones only | No error expected |
| Empty / no eligible | No zones or no heating actions | Demand False | No error expected |
| Unavailable action | `hvac_action=None` only | Not demand | No error expected |

</frozen-after-approval>

## Code Map

- `apps/ha_smart_hvac/models.py` — add `ZoneSnapshot.has_heating_eligible` wrapping `_eligible_thermostats`; do not change Zone Error math.
- `apps/ha_smart_hvac/coordinator.py` — `has_heating_demand` and `select_max_error_demand_zone` both filter via `z.has_heating_eligible`; drop `zone_error > 0` demand wording in docstrings.
- `apps/ha_smart_hvac/hvac_app.py` — only consumer of `has_heating_demand` (idle vs demand); no API change expected.
- `apps/ha_smart_hvac/ff_auto_correct.py` — only consumer of `select_max_error_demand_zone`; near_setpoint hold stays as-is.
- `tests/test_coordinator.py` — rewrite demand tests; heating+non-positive error → demand True; CAP-7 no-demand: `test_select_max_error_empty_or_no_demand` and `test_select_max_error_ignores_non_demand_pool` must use non-heating actions (not merely non-positive error).
- `tests/test_hvac_app.py` — pass `hvac_action="idle"` on `test_cap5_plant_on_idle_writes_zero`, `test_cap7_no_demand_clears_ephemeral_json_untouched`, `test_cap8_idle_writes_zero_json_untouched` (helpers default to heating).
- `CONTEXT.md` — Heating Demand definition (L47–48) and Zone Error sentence that “Eligible Zone Errors feed Heating Demand” (L44); dialogue L76 if it implies error-driven demand.
- `knowledge/concepts/zone-error.md` — “needs heat (zone error > 0)” line; Critical Zone “largest positive” → largest among Heating Demand zones (error may be ≤ 0).
- Do **not** edit superseded ADR 0002; ADR 0004 names Heating Demand without restating `> 0` — touch only if a sentence becomes false.

## Tasks & Acceptance

**Execution:**
- [x] `apps/ha_smart_hvac/models.py` — add `has_heating_eligible` property.
- [x] `apps/ha_smart_hvac/coordinator.py` — both demand functions use `has_heating_eligible`; update docstrings.
- [x] `tests/test_coordinator.py` — lock new gate matrix; rewrite `test_select_max_error_empty_or_no_demand` and `test_select_max_error_ignores_non_demand_pool` to non-heating for no-demand.
- [x] `tests/test_hvac_app.py` — idle: `test_cap5_plant_on_idle_writes_zero`, `test_cap7_no_demand_clears_ephemeral_json_untouched`, `test_cap8_idle_writes_zero_json_untouched` get `hvac_action="idle"`; demand fixtures stay heating; golden `test_cap5_heating_at_setpoint_still_writes_clamp_uff`.
- [x] `CONTEXT.md` + `knowledge/concepts/zone-error.md` — Heating Demand = `hvac_action`; Zone Error still ranks Critical Zone among demand zones.

**Acceptance Criteria:**
- Given plant on and a zone with `hvac_action=heating` and zone_error ≤ 0, when the gate runs, then Heating Demand is true and SWT follows the demand path.
- Given plant on and heating with `|zone_error| ≥ near_setpoint_eps_k` (including overshoot), when CAP-7 runs, then near_setpoint does not hold solely because error is non-positive.
- Given plant on and all thermostats non-heating (even with large setpoint−temp), when the gate runs, then idle writes `0`.
- Given CAP-7 selection among heating zones (any error sign), when multiple demand, then Critical Zone is max Zone Error (T-hold / lex unchanged); no demand only when no heating actions.
- Given docs, when read Heating Demand in CONTEXT, then it refers to `hvac_action`, not positive Zone Error.

## Implementation Notes

## Plan Change Log

- 2026-10-19 pre-approve review: named `ZoneSnapshot.has_heating_eligible`; forbade `isfinite(zone_error)` demand; added deep-overshoot I/O + AC for near_setpoint; listed exact idle/no-demand tests. Avoids implementer API drift and silent fixture flips.

## Review Triage Log

| finding | verdict | route | evidence |
|---------|---------|-------|----------|
| `select_max_error_demand_zone` ValueError on heating+NaN zone_error (empty tie_set; M2 flush broken) | high | patch | Confirmed: `test_m2_non_finite_zone_temp_flushes` failed with `min() iterable argument is empty`. Patched: finite-only max/tie; all-non-finite demand pool still returns a zone for M2. |

## Design Notes

Today eligibility for Zone Error already requires `hvac_action == "heating"`, but demand additionally requires error > 0. That second gate is what drops SWT while climate still reports heating (hysteresis / overshoot). Golden flip:

```text
# Before: heating, temp=22, setpoint=22 → zone_error=0 → no demand → write 0
# After:  heating, temp=22, setpoint=22 → demand True → clamp(u_ff)
# Idle:   idle,    temp=10, setpoint=22 → demand False → write 0
```

## Verification

**Commands:**
- `uv run pytest tests/test_coordinator.py tests/test_hvac_app.py -q` -- expected: all pass
- `uv run ruff check apps/ha_smart_hvac/coordinator.py apps/ha_smart_hvac/models.py` -- expected: clean
