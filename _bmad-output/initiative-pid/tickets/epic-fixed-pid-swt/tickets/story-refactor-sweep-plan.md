---
title: '1.4 Refactor sweep'
type: 'refactor'
ticket: '4'
created: '2026-11-07'
status: done
baseline_revision: '21ec33046f7c8eeed843bdba3e2f7a3033978dd4'
route: 'oneshot'
route_source: 'auto'
risk: 'low'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The fixed-PID SWT change left two orphans in the package: the CAP-7 sticky tie-break `previous_name` in `select_max_error_demand_zone` (only caller passes `None`; deferred to 1.4 by user decision in 1.3 review), and the `evaluate_demand(advance_integral=...)` switch, an interim from 1.1 when demand events wrote without advancing ∫ — since 1.2 the only caller passes `True`.

**Approach:** Drop `previous_name` (ties break by lexicographic name only) and `advance_integral` (∫ always steps, subject to the saturation freeze); update the caller and the tests that exercised the removed branches. No behavior change on the live path.

</frozen-after-approval>

## Implementation Notes

Oneshot: two signature removals, one caller, two test files touched; well under 100 lines.

- `apps/ha_smart_hvac/coordinator.py` — remove `previous_name` param, T-hold docstring sentence, and the tie-set lookup; keep finite/non-finite pool and lex tie-break (Critical Zone diagnostics, R9).
- `apps/ha_smart_hvac/pid.py` — remove `advance_integral` param and the `if`; docstring says ∫ steps per call (tick-owned).
- `apps/ha_smart_hvac/hvac_app.py` — update both calls.
- `tests/test_coordinator.py` — drop `None` / name args; delete `test_select_max_error_t_hold_keeps_previous_in_tie_set`.
- `tests/test_pid.py` — drop `advance` from `_eval` and callers; delete `test_no_advance_keeps_integral`.
- `story-tracer-fixed-gain-pid-swt-law-plan.md` — ticked the Execution checkboxes (1.1 deferral: tasks open while status done).
- Out of scope: AGENTS.md / ADR 0004 / CONTEXT.md / `knowledge/` (epic 2 per deferred-work); absence tests for Outdoor/FF in `test_config.py` / `test_hvac_app.py` are intentional and stay.

## Plan Change Log

## Review Triage Log

### 2026-11-07 (oneshot quick)
**Triage:** 0 high, 0 medium, 3 low → patched, 0 false, 0 maybe-false.

- low — 1.1 deferral (plan Tasks `[ ]` while status done) unowned → patched: ticked the five Execution boxes in the 1.1 plan.
- low — `deferred-work.md` still lists `previous_name` as deferred to 1.4 → closed here instead (workflow forbids editing old deferred entries): `previous_name` removed in this change; docs deferrals stay with epic 2.
- low — Implementation Notes said three test files; diff touches two → patched wording.

## Verification

**Commands:**
- `uv run pytest` -- expected: all green
- `uv run ruff check apps tests && uv run ruff format --check apps tests` -- expected: clean
- `rg -n "previous_name|advance_integral|T-hold" apps tests` -- expected: no matches
- `rg -ni "cap-7|u_ff|ff_auto|feedforward|outdoor|weather" apps/ha_smart_hvac` -- expected: no matches (story verify: no FF/CAP-7 leftovers)

## Code Review

### 2026-11-07
**Code review complete.** 0 `decision-needed`, 5 `patch`, 1 `defer`, 13 rejected.

- [x] [Review][Patch] deferred-work.md not updated for items 1.4 resolved (`previous_name`, 1.1 checkboxes still read as open) [_bmad-output/initiative-pid/deferred-work.md:12]
- [x] [Review][Patch] Plan Verification grep narrower than story verify clause — add FF/CAP-7 sweep rg [story-refactor-sweep-plan.md:56]
- [x] [Review][Patch] `test_select_max_error_ignores_non_demand_pool` no longer isolates the demand-pool filter [tests/test_coordinator.py:137]
- [x] [Review][Patch] Lexicographic tie test passes for input-order selection [tests/test_coordinator.py:127]
- [x] [Review][Patch] `evaluate_demand` docstring omits pre-step ∫ ordering / tick-only caller rule [apps/ha_smart_hvac/pid.py:70]
- [x] [Review][Defer] AGENTS.md / ADR 0004 / CONTEXT.md / knowledge describe the removed FF/CAP-7/CAP-8 design [AGENTS.md] — deferred: pre-existing from 1.2/1.3; agent-context/ADR edits owned by epic 2 (`epic-pid-domain-docs`)

**Rejected:**
- false — NaN `e` pins ∫/command (pid.py:84): `_read_float` drops non-finite values and `_read_zones` skips the zone; never reaches `evaluate_demand`.
- false — "no behavior change" rests on untouched hvac_app tests: live caller used exactly the retained paths; existing hvac_app tests pin tick-only ∫ and Critical Zone logging; suite green.
- false — `advance_integral` outside deferred notes: in scope as an orphan per the ticket description.
- false — 1.1 checkbox edit on another plan: closes deferred-work.md 1.1 entry.
- false — gates not confirmed: review ran them (130 passed, ruff clean).
- false — non-finite fallback pool dead on live path: deliberate guard against `min()` on an empty tie set in a pure function.
- low — unreachable `tset is None` / double `weight_sum` (pid.py): type-narrowing check and reshaping return; predates 1.4, not worth the restructure.
- false — deleted `test_no_advance_keeps_integral` lost pre-step ∫ check: `test_no_freeze_when_sat_opposite_sign` fails (raw 35) if post-step ∫ were used.
- false — Verification lists no results: plan template format; commands pass.
- false — no Tasks & Acceptance section: oneshot plan template (1.2 identical).
- low — 1.1 verify in tickets.toml mentions event-demand writes: closed ticket's historical acceptance; 1.2 verify states the current rule.
- false — tie-break rule not recorded for epic 2: existing CONTEXT/knowledge deferral covers the Critical Zone rewrite.
- low — `list` vs `Sequence` hints: cosmetic, not introduced by this change.
