---
title: 'Zone rising-edge latch clear'
type: 'feature'
ticket: '2'
created: '2026-11-13'
status: 'built'
baseline_revision: 'd19294cf1009afd8d5175f015db526d931ce8968'
route: 'full'
route_source: 'auto'
risk: 'high'
review: 'thorough'
review_source: 'auto'
lenses_ran: ['blind-hunter', 'edge-case-hunter', 'verification-gap', 'intent-alignment']
review_loop_iteration: 0
context:
  - _bmad-output/initiative-weather-swt-supply-trip/tickets/epic-supply-rise-rate-trip/epic-supply-rise-rate-trip.md
  - _bmad-output/initiative-weather-swt-supply-trip/tickets/epic-supply-rise-rate-trip/tickets/story-tracer-supply-rise-rate-trip-plan.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent
**Problem:** R6 rising-edge clear is missing: latch clears on hold/idle/plant-off only; per-zone prior Heating Demand is not tracked (aggregate `has_heating_demand` alone).

**Approach:** RAM map `zone.name → had Heating Demand`. After `_read_zones` in `_gate_prelude`, detect per-zone False→True; if latched and ≥1 real edge, `_clear_trip_state` then weather-curve SWT via `_run_demand`. No new zone edge keeps the latch. Critical Zone is unused for clear.

## Boundaries & Constraints
**Always:**
- **Decision A:** If a configured zone is missing from this read's snapshots (unreadable), treat its current `has_heating_eligible` as `False`.
- Prior keyed by config `zone.name`; current = `has_heating_eligible` when the zone is in this read's snapshots, else Decision A.
- **Detect then update:** `had_edge = any(current[name] and prior.get(name) is False for name in config zones)` — only keys already present in prior with value `False` count (missing key ≠ edge). Then replace prior for all config zone names from this read's currents. If prior was empty (or this is the first non-empty zone read after empty snapshots while latched): seed prior from currents and do **not** clear.
- Call that helper after every `_read_zones` in `_gate_prelude` that yields snapshots — including the no-demand branch **before** `_go_idle`. When `_read_zones` is empty, leave prior unchanged (no seed, no edge).
- When latched and `had_edge` under successful Plant∧Outdoor∧Demand prelude: `_clear_trip_state()` (latch + cancel hold + wipe samples, same as hold expiry) before `_run_demand` so weather-curve SWT runs.
- Aggregate-only continuity (same zones still heating, no False→True on keyed prior) must not clear the latch.
- Detect/update only on `_gate_prelude` zone reads (`control_tick` / `control_event`). `supply_event` / `_plant_and_heating_demand` do not touch prior (may leave prior stale until next control prelude — by design).
- Latch is RAM-only. Rising-edge clear must not call `select_max_error_demand_zone`.

**Never:**
- Do not change trip latch / hold / `r_obs` behavior from 2.1; house yaml; CAP-7 / trip JSON; Exclusive Session; Heating Demand definition; CAP-8 FF formula; docs/ADR.
- Do not clear on aggregate `has_heating_demand` False→True; clear only on per-zone keyed `has_heating_eligible` False→True.
- Do not drive clear or SWT from Critical Zone.

## I/O & Edge-Case Matrix
| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| Rising-edge clear | Latched; Plant∧Demand∧Outdoor; prior A=True B=False; B idle→heating | Clear latch/hold/samples; weather-curve SWT | — |
| No new edge | Latched; same zones still heating; tick/event | Latch stays; SWT `0` | — |
| Edge, not latched | Demand; zone rises; latch false | Update prior only; weather-curve SWT | — |
| First seed / empty prior | Prior empty; zones heating; latch false or true | Seed prior; no clear | — |
| Empty→valid while latched | Prior empty or unchanged after empty `_read_zones`; zones return heating | Seed prior; no clear | — |
| Skip→return | Latched; B skipped (prior Forced False); later B heating | Rising-edge clear + weather-curve SWT | — |
| Idle no-demand | Zones read; none heating | Update prior (all false); then idle `0` path | — |
| Plant-off | No zone read | Prior unchanged; `_hands_off` clear unchanged | — |
| Outdoor miss | Outdoor unavailable (before zone read) | Prior unchanged; idle clear path unchanged | — |

</frozen-after-approval>

## Code Map
Reuse 2.1 `_clear_trip_state` / latched `_run_demand`→`0` / hold re-prelude (hold clears latch first — no double edge clear).

1. `hvac_app.py` — `_zone_heating_prior`; helper after `_read_zones` in `_gate_prelude` (demand + no-demand-with-snapshots): detect→update→clear-if-latched∧edge; seed-only when prior empty / empty→valid. No `supply_event` / CZ for clear.
2. Reuse `has_heating_eligible` / `has_heating_demand`.
3. `tests/test_hvac_app.py` — see Execution.

## Tasks & Acceptance
**Execution:**
- [ ] `hvac_app.py` — prior map + detect→update helper in `_gate_prelude`; seed-without-clear; `_clear_trip_state` on latched∧edge.
- [ ] `tests/test_hvac_app.py` — multi-zone rising-edge clear; no-edge; not-latched prior; latched+empty-prior seed; idle prior all-false; skip→return (Decision A).

**Acceptance Criteria:**
- Given latched under Plant∧Demand∧Outdoor with prior A=True B=False, when B starts heating, then clear latch/hold/samples and set demand SWT from the weather curve.
- Given latched with unchanged per-zone demand, when tick/event re-evaluates, then latch stays and demand path still commands `0`.
- Given prior empty while latched and zones already heating, when prelude runs, then prior is seeded and latch is not cleared.
- Given not latched, when a zone rises into heating, then prior updates and weather-curve path is unchanged.
- Given rising-edge clear, when CZ would differ from the rising zone, then clear uses only `_clear_trip_state` (no `select_max_error_demand_zone`).

## Plan Change Log
- 2026-11-13: Draft 2.2; Decision A; review patch (seed-without-clear; detect→update; idle prior; Never aggregate).

## Design Notes
- Clear via `_clear_trip_state` then `_run_demand`. Plant-off prior unchanged; Decision A skip→return kept.

## Verification
**Commands:**
- `uv run pytest` — all pass.
- `uv run ruff check apps/ha_smart_hvac tests` — clean.

**Manual checks:**
- Exclusive Session (optional): latched trip; second zone `hvac_action=heating` → latch clears; weather-curve SWT resumes.

## Review Triage Log
| Finding | Verdict | Evidence / route |
| --- | --- | --- |
| Plan Execution checkboxes still unchecked | false | Rejected: fix would only edit this build's plan. |
| No `control_event` rising-edge/no-edge test | low | Same `_gate_prelude` as tick; AC names event. Route: patch — add one `control_event` rising-edge clear test. |
| Missing prior key ≠ edge untested | medium | Code uses `prior.get(name) is False`; empty-prior early-return hides regressions. Route: patch — add latched partial-prior test. |
| `test_empty_zone_read` double `get_state` assign | low | First MagicMock overwritten. Route: patch — delete dead setup. |
| No dedicated rising-edge clear log | false | Intent does not require a distinct log; clear is `_clear_trip_state` then demand path. |
| `_two_zone_app` drops `plant_setpoint` from `get_state` | medium | `kwargs.pop` then `_two_zone_get_state(**kwargs)` without forwarding; override ignored. Route: patch. |
| Empty→valid two-tick while latched missing | false | Empty `_read_zones` calls `_go_idle`, which clears latch; latched empty-prior seed already covers reachable seed-without-clear. |
| Plan markdown missing EOF newline | false | Rejected: fix would only edit this build's plan. |
| `test_latched_no_new_edge` omits hold/sample asserts | low | Test never arms hold/sample; incomplete pin. Route: patch — arm and assert intact. |
| CZ test does not mock `select_max_error_demand_zone` | false | Clear path never calls CZ; demand path still logs CZ after clear — non-consultation of CZ for clear is already true. |
| Edge: `_two_zone_app` plant_setpoint not forwarded | medium | Same defect as blind-hunter plant_setpoint finding. Route: patch (grouped). |
| Verification-gap: latched partial zone fall untested | medium | Pre-verified: True→False under continued demand would not fail existing tests if edge became any-change. Route: patch. |
