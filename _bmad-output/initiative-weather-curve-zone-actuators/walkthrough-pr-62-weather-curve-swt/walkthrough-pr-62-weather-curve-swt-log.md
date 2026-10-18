# Review log: PR #62 weather-curve SWT

Target: https://github.com/zhmachenkov-d/ha_smart_hvac/pull/62 (`feat/1-1-weather-curve-swt-law` @ a10c00d)

<!--
Append-only record of outcomes/decisions.
Main purpose: persisted context for resuming or analyzing
the review process. You're writing this log for consumption
by another LLM session.

Record decisions and their reasons, user constraints, unresolved
findings, and references needed to recover evidence. Link to large
results rather than copying them here.
This is NOT a transcript or internal deliberation.
The review narrative (the human-facing file) owns review blocks
and their statuses.

Log entry:
Use format below. Omit empty fields. In Result, give each finding's
disposition: fixed, accepted as-is, deferred, or open. When a
disposition changes, append a new entry; do not edit earlier ones.
Record the actual session ID supplied by the environment and an ISO
8601 timestamp with local timezone for each entry. If the session ID
is unavailable, write "unavailable" rather than inventing one.

Token budget: up to 150 tokens per entry.
The smaller the better, but do not sacrifice precision.
-->

## 1 — orientation — started

Session: unavailable · Timestamp: 2026-10-18T18:07:47+03:00

- Action: Assumed target PR #62 @ a10c00d; created walkthrough folder + narrative from frozen plan Intent and Block shapes.
- Result: Narrative created; current block Intent (in progress); no findings yet.
- Evidence: walkthrough-pr-62-weather-curve-swt.md; story-tracer-weather-curve-swt-law-plan.md Intent; PR #62
- Open: Walk Intent block with user

## 2 — Intent — Thoughts

Session: 64b7f198-3a88-470b-b888-e1bdb444d1a5 · Timestamp: 2026-10-18T18:08:00+03:00

- Action: User selected Thoughts on Intent block; main session reviewed Intent vs live control_tick / CAP-5 scope.
- Result: Intent still accurate for PR #62; no Intent rewrite requested. Open: user has not marked Intent done.
- Evidence: plan frozen Intent; hvac_app.py demand branch clamp(u_ff); CAP-5 in test_hvac_app.py
- Open: awaiting user accept Intent or further move

## 3 — Intent — accepted

Session: 64b7f198-3a88-470b-b888-e1bdb444d1a5 · Timestamp: 2026-10-18T18:11:00+03:00

- Action: User said Intent done
- Result: Intent accepted; advancing to Broad strokes
- Evidence: user message "done"

## 4 — Broad strokes — Thoughts

Session: 64b7f198-3a88-470b-b888-e1bdb444d1a5 · Timestamp: 2026-10-18T18:11:40+03:00

- Action: User selected Thoughts on Broad strokes; session reviewed five entry points vs live wiring
- Result: Brokes strokes accurate; noted CZ still in coordinator unused on SWT path; dormant helpers still in hvac_app; no rewrite
- Evidence: hvac_app.py:11,184–215,24–43; coordinator.py:8,17; feedforward.py:8; test_hvac_app.py:792
- Open: Broad strokes not accepted; dirty-tree commit question unanswered

## 5 — Broad strokes — accepted

Session: 64b7f198-3a88-470b-b888-e1bdb444d1a5 · Timestamp: 2026-10-18T18:20:00+03:00

- Action: User said Broad strokes done
- Result: Accepted; advancing to Demand-path clamp law
- Evidence: user "done"

## 6 — Demand-path clamp law — Thoughts

Session: 64b7f198-3a88-470b-b888-e1bdb444d1a5 · Timestamp: 2026-10-18T18:22:00+03:00

- Action: User selected Thoughts on Demand-path clamp law
- Result: Session reviewed demand write/abort and gate clears; no block rewrite requested
- Evidence: hvac_app.py:202–230, _write_setpoint
- Open: block not accepted; dirty-tree commit still open

## 7 — Demand-path clamp law — Test started

Session: 64b7f198-3a88-470b-b888-e1bdb444d1a5 · Timestamp: 2026-10-18T18:22:30+03:00

- Action: User selected Test on Demand-path clamp law
- Result: pytest subset launched in main session
- Open: awaiting pass/fail and gap check for demand fail-write

## 7 — Demand-path clamp law — Test

Session: 64b7f198-3a88-470b-b888-e1bdb444d1a5 · Timestamp: 2026-10-18T18:22:30+03:00

- Action: User selected Test; ran pytest CAP-5/matrix/write_setpoint subset + manual demand fail-write abort
- Result: 16 passed. Manual abort OK (no set_value, WARN unavailable, no command= INFO). Gap: no automated tick test for demand fail-write abort — open/optional
- Evidence: uv run pytest … -k 'cap5 or matrix_outdoor or matrix_no_valid or write_setpoint' → 16 passed; PYTHONPATH=apps one-off PASS abort True
- Open: user may add test, accept gap, or mark block done

## 8 — Demand-path clamp law — add fail-write tick test

Session: 64b7f198-3a88-470b-b888-e1bdb444d1a5 · Timestamp: 2026-10-18T18:24:30+03:00

- Action: User asked to add test for demand fail-write INFO gap
- Result: fixed — added test_demand_fail_write_aborts_without_success_info; 1 passed; ruff clean. Gap closed.
- Evidence: tests/test_hvac_app.py test_demand_fail_write_aborts_without_success_info
- Open: uncommitted test change; Demand-path block not marked done; dirty tree incl. walkthrough + memlog

## 9 — Demand-path clamp law — commit fail-write test

Session: 64b7f198-3a88-470b-b888-e1bdb444d1a5 · Timestamp: 2026-10-18T18:25:00+03:00

- Action: User asked to commit the new fail-write tick test
- Result: committed `c328048` (tests/test_hvac_app.py only); walkthrough/memlog left dirty
- Evidence: git log -1 → c328048 test(hvac): lock demand abort when plant setpoint unread
- Open: Demand-path block not done; push not requested

## 10 — Demand-path clamp law — accepted

Session: 64b7f198-3a88-470b-b888-e1bdb444d1a5 · Timestamp: 2026-10-18T18:25:30+03:00

- Action: User said Demand-path done
- Result: Accepted; advancing to Heating-demand gate
- Evidence: user "done"

## 11 — Heating-demand gate — Thoughts

Session: 64b7f198-3a88-470b-b888-e1bdb444d1a5 · Timestamp: 2026-10-18T18:27:00+03:00

- Action: User selected Thoughts on Heating-demand gate
- Result: Session reviewed eligibility + SWT wiring; no rewrite
- Evidence: coordinator.py has_heating_demand; hvac_app.py:202; models zone_error; test_coordinator
- Open: block not accepted

## 12 — Heating-demand gate — Test

Session: 64b7f198-3a88-470b-b888-e1bdb444d1a5 · Timestamp: 2026-10-18T18:27:30+03:00

- Action: User selected Test; ran test_coordinator + idle CAP-5/clear tick tests
- Result: 13 passed (coordinator) + 2 passed (idle tick paths). Eligibility/idle cases green. No HA live test.
- Evidence: uv run pytest tests/test_coordinator.py; test_cap5_plant_on_idle_writes_zero_and_clears; test_idle_paths_clear_blow_up_warned
- Open: Heating-demand block not accepted

## 13 — Heating-demand gate — accepted

Session: 64b7f198-3a88-470b-b888-e1bdb444d1a5 · Timestamp: 2026-10-18T18:29:00+03:00

- Action: User said Heating-demand done
- Result: Accepted; advancing to CAP-5 tests / kill-list
- Evidence: user "done"

## 14 — CAP-5 tests / kill-list — Thoughts

Session: 64b7f198-3a88-470b-b888-e1bdb444d1a5 · Timestamp: 2026-10-18T18:30:00+03:00

- Action: User selected Thoughts; verified kill-list absent, leave-list/CAP-5 present
- Result: Block accurate; no rewrite
- Evidence: tests/test_hvac_app.py; plan Code Map kill/leave lists
- Open: block not accepted

## 15 — CAP-5 tests / kill-list — Test

Session: 64b7f198-3a88-470b-b888-e1bdb444d1a5 · Timestamp: 2026-10-18T18:31:00+03:00

- Action: User selected Test; ran CAP-5/matrix/fail-write; control_tick filter; leave-list sample
- Result: pending main — expect CAP-5 green, control_tick empty/deselected, leave helpers green
- Evidence: pytest -k filters on test_hvac_app.py
- Open: block not accepted

## 16 — CAP-5 tests / kill-list — Test results

Session: 64b7f198-3a88-470b-b888-e1bdb444d1a5 · Timestamp: 2026-10-18T18:31:30+03:00

- Action: Confirmed pytest outcomes from Test move
- Result: CAP-5/matrix/fail-write 8 passed; control_tick filter 0 collected (exit 5 expected); leave-list sample 34 passed. Disposition: verified.
- Evidence: uv run pytest tests/test_hvac_app.py -k filters
- Open: CAP-5 block not accepted

## 17 — CAP-5 tests / kill-list — accepted

Session: 64b7f198-3a88-470b-b888-e1bdb444d1a5 · Timestamp: 2026-10-18T18:32:30+03:00

- Action: User said CAP-5 tests / kill-list done
- Result: Accepted; advancing to Dormancy of LADRC
- Evidence: user "done"

## 18 — Dormancy of LADRC — Thoughts

Session: 64b7f198-3a88-470b-b888-e1bdb444d1a5 · Timestamp: 2026-10-18T18:32:45+03:00

- Action: User selected Thoughts on Dormancy of LADRC
- Result: Session reviewed construct/clear/unwired demand; no rewrite
- Evidence: hvac_app.py initialize + control_tick; ladrc_tuner._load; module helpers
- Open: block not accepted

## 19 — Dormancy of LADRC — Test

Session: 64b7f198-3a88-470b-b888-e1bdb444d1a5 · Timestamp: 2026-10-18T18:33:15+03:00

- Action: User selected Test; CAP-5 demand/idle/off + initialize/idle clear; static control_tick banned-name scan
- Result: pending exact counts in chat — expect green + no banned names in control_tick
- Evidence: pytest named tests; inspect.getsource(HvacApp.control_tick)
- Open: block not accepted

## 20 — Dormancy of LADRC — Test results

Session: 64b7f198-3a88-470b-b888-e1bdb444d1a5 · Timestamp: 2026-10-18T18:33:30+03:00

- Action: Confirmed dormancy Test outcomes
- Result: 5 passed. control_tick banned-name hits: none. initialize still constructs _ladrc/_tuner; idle/off clear present. Disposition: verified.
- Evidence: named pytest; PYTHONPATH=apps inspect sources
- Open: Dormancy block not accepted

## 21 — Dormancy of LADRC — accepted

Session: 64b7f198-3a88-470b-b888-e1bdb444d1a5 · Timestamp: 2026-10-18T18:33:45+03:00

- Action: User said Dormancy done
- Result: Accepted; advancing to Periphery
- Evidence: user "done"

## 22 — Periphery — Thoughts

Session: 64b7f198-3a88-470b-b888-e1bdb444d1a5 · Timestamp: 2026-10-18T18:44:00+03:00

- Action: User selected Thoughts on Periphery
- Result: Session reviewed plan/spec/CONTEXT gap; no rewrite of periphery block
- Evidence: plan status built; CONTEXT still LADRC wording; PR must not claim ADR 0002 governs live SWT
- Open: Periphery not accepted; wrap-up pending

## 23 — Periphery — accepted

Session: 64b7f198-3a88-470b-b888-e1bdb444d1a5 · Timestamp: 2026-10-18T18:44:30+03:00

- Action: User said Periphery done
- Result: All narrative blocks accepted; suggest Wrap-up
- Evidence: user "done"
- Open: Wrap-up not started; dirty walkthrough + memlog; unpushed c328048

## 24 — Wrap-up — commit and push

Session: 64b7f198-3a88-470b-b888-e1bdb444d1a5 · Timestamp: 2026-10-18T18:45:00+03:00

- Action: User asked commit all and push
- Result: committing walkthrough + memlog; pushing branch incl. c328048
- Evidence: user "commit all and push"
