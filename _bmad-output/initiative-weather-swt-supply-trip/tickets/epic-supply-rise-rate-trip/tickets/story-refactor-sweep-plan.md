---
title: 'Refactor sweep'
type: 'chore'
ticket: '4'
created: '2026-11-14'
status: 'built'
baseline_revision: '40e6a2a1806328aaded7ada74f3490ee1fdda257'
route: 'oneshot'
route_source: 'auto'
risk: 'low'
review: 'quick'
review_source: 'auto'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - _bmad-output/initiative-weather-swt-supply-trip/deferred-work.md
  - _bmad-output/initiative-weather-swt-supply-trip/tickets/epic-supply-rise-rate-trip/epic-supply-rise-rate-trip.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent
**Problem:** Epic 2 deferred notes still call out trip edge-case hardening, `run_in` None-after-latch, and CZ×trip leftovers; most hardening already landed in 2.1/2.2 code+tests, but deferred-work is stale and the CZ non-trip Always rule still has no latched-path test.

**Approach:** Add one CZ×trip verification test; settle `run_in` as AD 4.5.13 `-> str` (no production None guard); prune this epic’s settled deferred-work entries. No new trip behavior; leave epic-3 docs/`pid.py`/`rls.py` alone.

</frozen-after-approval>

## Tasks & Acceptance
**Execution:**
- [x] `tests/test_hvac_app.py` — add CZ×trip test: two zones under Plant∧Demand with CZ ≠ trip driver; force latched path (trip or `_run_demand` while latched); assert SWT `0`, latch stays as expected, and `select_max_error_demand_zone` is not consulted for the trip/latch write (mirror rising-edge CZ pattern at ~1595).
- [x] `_bmad-output/initiative-weather-swt-supply-trip/deferred-work.md` — remove epic-2 settled items (hardening bundle, `run_in` None deferral, CZ×trip deferral); keep the epic-3 AGENTS/CONTEXT/ADR PID contradiction entry untouched.
- [x] Confirm no unused trip/latch leftovers remain in epic-2 deferred notes; do not edit frozen Intent of 2.1/2.2 plans; do not change `hvac_app.py` latch/hold/`run_in` assignment unless a test proves a leftover bug.

**Acceptance Criteria:**
- Given Plant∧Demand, two heating zones, and a supply rise that trips (or demand while already latched), when the trip/latched write runs, then SWT is `0` and Critical Zone selection does not drive that write.
- Given AppDaemon 4.5.13 `ADAPI.run_in` annotated `-> str`, when this sweep completes, then production code keeps the existing `run_in` assignment (no None guard) and the deferred `run_in` None note is gone from epic deferred-work.
- Given epic-2 deferred notes after this sweep, when inspected, then they no longer call out unused trip/latch leftovers; the epic-3 AGENTS/CONTEXT/ADR entry remains.
- Given the suite, when `uv run pytest` and `uv run ruff check apps/ha_smart_hvac tests` run, then both are clean.

## Implementation Notes
Oneshot: ticket risk low; ~one test + deferred-work hygiene; no production behavior change expected after investigation (hardening already in tree; `run_in` never returns None in AD 4.5.13).
- Added `test_latched_trip_path_does_not_use_critical_zone`: two-zone latched `control_tick` asserts SWT `0`, latch held, and `select_max_error_demand_zone` not called.
- Pruned epic-2 deferred-work entries (hardening / `run_in` None / CZ×trip); left epic-3 AGENTS/CONTEXT/ADR entry.
- Hardening settlement evidence (already in tree from 2.1/2.2): `test_already_latched_does_not_restart_hold`, `test_orphan_hold_callback_after_clear_no_demand_write`, `test_orphan_hold_callback_after_retrip_does_not_clear_new_latch`, `test_outdoor_miss_leaves_zone_heating_prior_unchanged`, `test_supply_trip_under_demand_outdoor_unavailable`.
- `run_in` settlement provenance: installed AppDaemon 4.5.13 `appdaemon.adapi.ADAPI.run_in` annotated `-> str` (return is not Optional/None); no production None guard.
- No `hvac_app.py` production change.
- Verification: `uv run pytest` 343 passed; `uv run ruff check apps/ha_smart_hvac tests` clean.

## Plan Change Log
- 2026-11-14: Created oneshot plan; add CZ×trip latched-path test; prune epic-2 deferred-work; settle `run_in` as ADAPI `-> str`.
- 2026-11-14: Full code-review patches — settlement audit trail, Plan Change Log, tracer Defer markers marked settled by 2.4.
## Review Triage Log
- 2026-11-14 quick: 1 finding — false.
- [false] Missing blank line before new test would fail ruff E302 — disproof: project ruff select does not enable E302 without preview (`ruff check --select E302` warns preview); `uv run ruff check apps/ha_smart_hvac tests` already clean.

## Verification
**Commands:**
- `uv run pytest` — all pass.
- `uv run ruff check apps/ha_smart_hvac tests` — clean.

**Manual checks (if no CLI):**
- Epic deferred-work: only non-epic-2 leftovers (epic-3 docs) remain; no open trip/latch/CZ/`run_in` bullets for this epic.

## Code Review
### 2026-11-14
**Code review complete.** 0 `decision-needed`, 3 `patch`, 0 `defer`, 9 rejected.

- [x] [Review][Patch] Stale tracer [Review][Defer] markers after deferred-work prune [story-tracer-supply-rise-rate-trip-plan.md:~117,~128]
- [x] [Review][Patch] Thin settlement audit trail for pruned epic-2 deferrals [story-refactor-sweep-plan.md:Implementation Notes]
- [x] [Review][Patch] Empty Plan Change Log on built oneshot plan [story-refactor-sweep-plan.md:Plan Change Log]

#### Rejected
- R2 (false): AC trip-or-latched OR satisfied by latched `control_tick`; `supply_event` never reaches CZ selection.
- R5 (false): Missing plan `context` refs are not a defect in the shipped change.
- R6 (false): Inline `get_state` intentionally mirrors rising-edge CZ sibling pattern.
- R7 (low): Awkward "CZ ≠ trip driver" task wording — rarely visible after built; rewriting settled task prose adds noise.
- R8 (false): `critical_zone=` log assert matches latched early-return; C4 locked by `select_cz.assert_not_called`.
- R10 (low): Contrast with `test_latched_demand_writes_zero_no_ff` — optional plan prose; rarely visible.
- R11 (false): Same as R2 (intent surface vs already-latched test).
- R14 (false): "Orphans" as production dead-code was not the chosen Approach (reading 2).
