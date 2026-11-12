---
title: 'Tracer: supply rise-rate trip'
ticket: '1'
created: '2026-11-12'
status: 'built'
risk: 'high'
route: 'full'
route_source: 'auto'
review_source: 'auto'
review: 'thorough'
context: []
baseline_revision: '93157eee2504bc820fd872bf41d4109dfb4aef9e'
lenses_ran: [blind-hunter, edge-case-hunter, verification-gap, intent-alignment]
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent
**Problem:** CAP-8 weather-curve SWT has no supply rise-rate trip; `boiler_water` is ignored leftover.

**Approach:** Top-level `boiler_water` / `r_max`(2) / `hold`(900); `supply_event` under Plant∧Demand → `r_obs` °C/min; `r_obs > r_max` latches SWT `0` + `run_in(hold)` from first latch; latched `_run_demand` writes `0` (no FF); clear on hold expiry / idle-`0` / plant-off; hold cb re-reads gates then may re-run curve. Entry 2 rising-edge; entry 3 house accept; epic Done when = 1–3. Deferred: re-trip/orphan/outdoor-miss/CZ AC/tests.

## Boundaries & Constraints
**Always:**
- Non-empty `boiler_water` (mirror Outdoor). `r_max`/`hold` → 2/900; finite `>0` else `ConfigError`. Top-level; keep yaml names; local `r_obs` ok. Config break until entry 3; no house ids. Drop `boiler_water` from `ignored_keys`; keep `pid`/`base_water_temp` ignored.
- `supply_event` ≠ `control_event`: **never call `_gate_prelude`** (Outdoor). Gate = Plant on ∧ Heating Demand (`plant` + `_read_zones`/`has_heating_demand`). Bad supply → WARN, no trip/clear/advance; `(T,t)` → `r_obs=(T2−T1)/(dt_s/60)`; `dt_s≤0` → WARN, keep latest; trip → latch + `run_in(hold)` + write `0`; already latched → no `run_in` restart. Logs °C/min.
- Latched `_run_demand` skips FF → `0`. Else CAP-8 unchanged.
- `_clear_trip_state` from `_go_idle` / extended `_hands_off` (not log-only) / hold cb (idempotent). Hold cb like `control_tick(kwargs)`: clear, then **re-call `_gate_prelude()`**; if demand → `_run_demand`. Latch RAM-only. CZ not trip driver.
- Example: keys + °C/min and latch-seconds comments.

**Never:** Rising-edge clear; house yaml; CAP-7/trip JSON; change Exclusive Session / Heating Demand / FF / CAP-8 writer; CZ→SWT; docs; rename keys; sliding hold; Outdoor-gated `supply_event`.

## I/O & Edge-Case Matrix
| Scenario | In | Out | Err |
| --- | --- | --- | --- |
| Happy trip | Plant∧Demand; `r_obs>r_max` | Latch; SWT `0`; `run_in` | — |
| Latched demand | Latch + demand | Write `0`; no FF | — |
| Hold expiry gated | Cb; prelude demand | Clear; curve | — |
| Hold expiry closed | Cb; prelude None | Clear only | — |
| Idle / plant-off | Latched/sampled | Clear; idle `0`; plant-off no write | — |
| Bad supply | Non-finite | WARN; latch stays | WARN |
| `dt_s≤0` | Bad dt | WARN; keep latest | WARN |
| Parse OK/omit | Valid supply | Defaults 2/900 | — |
| Parse reject | Missing/bad | `ConfigError` | ConfigError |
| Example | Parse example | Keys + comments | — |

</frozen-after-approval>

## Code Map
Vacuous clear → trip clear (`adr-vacuous-clear-after-pid-detach`). No CAP-7 (`a305049`).

1. `models.py` — `boiler_water`, `r_max`, `hold`.
2. `config.py` — `_KNOWN_KEYS`; require `boiler_water`; `_number` + `>0`.
3. `hvac_app.py` — latch/sample/timer; `listen_state(supply_event)`; plant∧demand gate (**not** `_gate_prelude`); latched `_run_demand`→`0`; clear on `_go_idle`/extended `_hands_off`/hold cb; hold cb re-prelude; injectable clock; reuse `_write_setpoint`/`_read_float`/`has_heating_demand`/`_read_zones`; `run_in`/`cancel_timer`.
4. `apps.yaml.example` — trip keys + unit comments.
5. Tests — `_minimal_args`/`_tick_args`/`_init_app` + `boiler_water`; mock `run_in`/`cancel_timer`; flip ignore/example-absent; matrix below.

## Tasks & Acceptance
**Execution:**
- [ ] `models.py`+`config.py` — fields; require `boiler_water`; rate rules.
- [ ] `hvac_app.py` — `supply_event` (no prelude); injectable clock; latch/hold; latched→`0`; clear hooks; hold cb re-prelude; unit logs.
- [ ] `apps.yaml.example` — commission + comments.
- [ ] `tests/test_config.py` — `_minimal_args`+example accept; defaults; reject; flip ignore/absent.
- [ ] `tests/test_hvac_app.py` — fixtures + `run_in`/`cancel_timer` mocks; listener; trip; latched; hold gated/closed; idle/plant-off; bad supply; `dt_s≤0`.

**Acceptance Criteria:**
- Given Plant∧Demand and `r_obs > r_max`, when second sample arrives, then latch + SWT `0`.
- Given latch under demand, when `_run_demand` runs, then SWT `0` and no FF.
- Given latch, when hold cb fires and `_gate_prelude` returns demand, then clear + curve demand.
- Given latch, when hold cb fires and gates closed, then clear only.
- Given latch/samples, when idle-`0` or plant-off, then clear (+ cancel hold).
- Given bad supply under demand, when `supply_event` fires, then WARN only.
- Given `dt_s≤0` under demand, when second sample arrives, then WARN, keep latest, no trip.
- Given missing/empty `boiler_water` or bad `r_max`/`hold`, when parsed, then `ConfigError`.
- Given example/parse with valid trip keys (rates optional), when parsed, then defaults 2/900 + unit comments.

## Implementation Notes
## Plan Change Log
- 2026-11-12: party A1/B1/C1; hardening → deferred-work; review B patched (supply≠prelude, AC parity, fixtures/clock/hold re-prelude, `_hands_off`).
## Review Triage Log
| Lens | Finding | Verdict | Evidence / route |
| --- | --- | --- | --- |
| blind-hunter | `dt_s<=0` keeps previous sample despite "keep latest" | high | Code returns without updating `_supply_sample`; Always/matrix want keep/replace latest. → patch |
| blind-hunter | Orphan `_trip_hold_expired` can `_run_demand` after clear | high | No armed-handle/latch guard; stale cb after idle clear may rewrite curve. → patch |
| blind-hunter | Frozen Intent rewritten without renegotiation note | false | Draft→approve process rewrite; not a product defect; reject plan-edit fix |
| blind-hunter | `hold` must be whole seconds vs Always finite `>0` | medium | Extra parser constraint vs frozen Always. → patch (drop integer rule) |
| blind-hunter | deferred-work vs `test_already_latched_*` | false | Extra coverage of Always first-latch hold is fine; deferral was AC/matrix only |
| blind-hunter | Example test omits latch-seconds comment assert | medium | Only `°C/min` checked. → patch |
| blind-hunter | Re-trip WARNING log spam while latched | medium | Every over-threshold sample WARNs. → patch (log on first latch) |
| blind-hunter | Re-trip test thin vs pre-deferral matrix | false | Hardening deferred; no-restart assert enough for Always |
| blind-hunter | Plan file missing trailing newline | low | Rejected: cosmetic |
| blind-hunter | Unused `monotonic_times` in helper | low | Rejected: unlikely everyday harm |
| edge-case-hunter | Trip latches/`run_in` even when `_write_setpoint(0)` fails | high | Latch+hold before/without successful write; SWT may stay hot. → patch (latch/hold only after write True) |
| edge-case-hunter | Claim latch+SWT0 vs write-fail | high | Same root as write-fail latch. → patch (group) |
| verification-gap | No Outdoor-down supply trip test | high | Pre-verified; Outdoor-gating regress silent. → patch |
| verification-gap | No plant-off/no-demand `supply_event` negative | high | Pre-verified. → patch |
| verification-gap | `run_in` callback identity untested | high | Pre-verified; expiry tests call method directly. → patch |
| verification-gap | `listen_state` callback identity untested | high | Pre-verified; entity-only assert. → patch |
| intent-alignment | Descriptive readings R1–R5 | false | Audit only; no product defect |
## Design Notes
- `run_in`+`cancel_timer` from first latch; injectable monotonic clock; supply ≠ Outdoor prelude; `_go_idle` clears trip (outdoor-miss AC deferred).

## Verification
**Commands:**
- `uv run pytest` — all pass.
- `uv run ruff check apps/ha_smart_hvac tests` — clean.

**Manual checks:**
- Exclusive Session: fast rise → SWT `0` for `hold`; idle/plant-off clears; curve after hold if gated.