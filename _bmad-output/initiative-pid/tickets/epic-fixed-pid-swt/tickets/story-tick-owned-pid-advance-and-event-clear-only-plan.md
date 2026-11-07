---
title: '1.2 Tick-owned PID advance and event clear-only'
type: 'feature'
ticket: '2'
created: '2026-11-07'
status: 'built'
baseline_revision: '7644c86e33316acc490e3af023091edebad563c8'
route: 'oneshot'
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

**Problem:** After 1.1, `control_event` under Heating Demand still writes rounded PID SWT (∫ unchanged), so demand plant writes are not tick-owned — short of R5/R6.

**Approach:** Keep `_gate_prelude` on both entrypoints for idle / plant-off / no-zones clears; on event demand (`zones` returned) do nothing — no `_run_demand`, no SWT write, no ∫ change. Only `control_tick` runs demand write + integral advance. Outdoor stays off listeners; FF/CAP-7 package files stay until entry 3.

## Boundaries & Constraints

**Always:**
- Idle / plant-off / no valid zones still clear via shared prelude on tick **and** event (idle write 0 + clear; plant-off no write + clear).
- Demand SWT write and PID ∫ advance only from `control_tick` → `_run_demand` (always advance).
- Listeners unchanged: Plant Management, zone air, thermostat `hvac_action` / setpoint; Outdoor not registered.
- Clear inventory unchanged: ephemeral ∫ + last commanded; plant equal-float + equal-rounded skip layers stay on the tick demand path.
- Decision: event demand branch is a pure no-op (do not call `evaluate_demand` / `_run_demand`); weight-unusable fail (write 0 + clear) stays tick-only.

**Never:**
- Demand-path SWT write or ∫ advance from `control_event`.
- Delete outdoor / weather FF / CAP-7 / `ff_auto_correct_state.json` (entry 3).
- ADR / CONTEXT / AGENTS edits (epic 2); RLS; change Exclusive Session or Heating Demand definition.
- Merge tick/event into one boolean-flagged entrypoint; do not add debounce.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Demand tick | Plant on, heating demand, valid zones | Write round(clamp(base+u_pid)); advance ∫ per 1.1 rules | — |
| Demand event | Same demand, `control_event` | No `number/set_value`; ∫ and last commanded unchanged | — |
| Event after tick demand | Last commanded set, ∫ advanced; event under demand | No write; ∫ and last unchanged | — |
| Event plant-off | Plant ≠ on | No write; clear ∫ + last | — |
| Event idle | Plant on, no heating | Write 0 (best-effort); clear ∫ + last | Clear even if write fails |
| Event no zones | Plant on, empty snapshots | Write 0 + clear (idle path) | — |
| Outdoor not listened | App initialized | Outdoor not among control listeners | — |

</frozen-after-approval>

## Implementation Notes

Oneshot (~40–90 LOC): flip `control_event` demand branch to return after prelude; drop `advance_integral` flag so `_run_demand` always advances; rewrite interim event-demand tests to lock no write / no ∫ change.

- `control_event` only calls `_gate_prelude()` (idle/plant-off/no-zones clears); demand returns with no write/∫.
- `_run_demand(zones)` always advances; still passes `advance_integral=True` into `evaluate_demand` (pid API kept for unit tests).
- Replaced interim event-demand tests with no-write / no-∫ / last-unchanged locks.

## Plan Change Log

## Review Triage Log

### 2026-11-07 (oneshot quick)
**Triage:** 0 high, 2 medium→patched, 0 low, 0 false, 0 maybe-false; 1 deferred group (docs).

| finding | verdict | evidence | route |
|---------|---------|----------|-------|
| Missing event no-zones clear test vs I/O matrix | medium | Shared `_gate_prelude` → `_go_idle`; only tick was locked | patch — `test_event_no_valid_zones_writes_zero_and_clears` |
| Missing event idle write-fail clear vs I/O matrix | medium | Idle clear not gated on write success; only tick fail locked | patch — `test_event_idle_write_fail_still_clears` |
| AGENTS / ADR 0004 / CONTEXT still CAP-8 demand event write | medium | Real docs/runtime mismatch; plan Never + epic 2 owns R4 docs | defer |

## Verification

**Commands:**
- `uv run pytest` -- expected: all tests green
- `uv run ruff check apps tests` -- expected: clean

## Code Review

### 2026-11-07

**Code review complete.** 0 `decision-needed`, 3 `patch`, 1 `defer`, 15 rejected. (Edge Case Hunter returned no findings.)

- [x] [Review][Patch] 1.2 deferred-work entry misfiled under the 1.1 heading and off-format [_bmad-output/initiative-pid/deferred-work.md:5]
- [x] [Review][Patch] Event idle write-fail test lacks the "Plant setpoint unavailable" warning assertion its tick twin has [tests/test_hvac_app.py:609]
- [x] [Review][Patch] `test_event_path_does_not_advance_integral` names an event path that no longer calls `evaluate_demand` [tests/test_pid.py:112]
- [x] [Review][Defer] AGENTS.md / ADR 0004 / CONTEXT.md still describe CAP-8 event demand writes of `clamp(u_ff)` and Outdoor as a listener [AGENTS.md] — deferred: pre-existing since 1.1; agent-context/ADR edits owned by epic 2 (R4 docs)

**Rejected**
- No ticket pointer in deferred entry — false: "epic 2" is `epic-pid-domain-docs` in initiative `tickets.toml`.
- Empty Plan Change Log — false: no post-approval plan changes occurred.
- Triage headline understates mediums — false: 2 patched + 1 deferred group matches the table.
- `review_loop_iteration: 0` — maybe-false, at most low.
- High risk with quick review — false: `review: quick` is pinned.
- Outdoor-not-listened not locked — false: `test_initialize_outdoor_not_among_listeners` covers it.
- Event under weight-unusable demand not locked — low: event demand branch is structurally a no-op, already locked by `test_demand_event_no_write_no_integral_change`.
- No explicit return/comment in `control_event` — false: docstring states demand is tick-owned.
- `control_tick` lacks docstring — low, pre-existing, cosmetic.
- 1.1 plan interim contract not marked superseded — false: 1.1 plan is that story's historical record.
- Verification lists only pytest/ruff — false: behavior is locked by tests.
- `control_interval` default 300 not in diff — false: shipped in 1.1 (`config.py:136`).
- Listener set preserved, not re-exercised — false: existing tests cover it.
