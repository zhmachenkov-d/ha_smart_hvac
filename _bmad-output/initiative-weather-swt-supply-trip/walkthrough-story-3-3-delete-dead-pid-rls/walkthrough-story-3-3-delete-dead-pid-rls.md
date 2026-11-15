# Walkthrough: Story 3.3 — delete dead pid/rls modules
Target: [PR #144](https://github.com/zhmachenkov-d/ha_smart_hvac/pull/144) · branch `chore/3-3-delete-dead-pid-rls-modules` · `357c76f`

**Current block:** Wrap-up (done — committed+pushed; merge deferred)

## Blocks
- [x] **Intent** — done
- [x] **Broad strokes** — done
- [x] **Slice: Relocate helpers + drop F6-B** — done (Test: 10 passed)
- [x] **Slice: Delete four modules** — done (Test 275; Second opinion align)
- [x] **Slice: Ticket graph + house-calibration** — done (Test + Second opinion align)
- [x] **Periphery** — done (Test: plan+deferred verified; local dirty noted)
- [x] **Wrap-up** — done (commit+push only; no merge)

---

### Intent
Source: frozen Intent from plan [story-delete-dead-pid-rls-modules-plan.md](../tickets/epic-supersede-pid-domain-docs/tickets/story-delete-dead-pid-rls-modules-plan.md) (Problem + Approach).

**Problem:** Live SWT no longer uses fixed-PID / RLS, but `pid.py`, `rls.py`, and their unit tests remain on disk; F6-B still assumes `pid.py` exists.

**Approach:** Delete the four dead modules/tests; relocate live `clamp`/`quantize_command` unit tests into `test_feedforward`; drop the F6-B on-disk lock; keep the `hvac_app` AST import-lock so the suite proves PID/RLS absence without retaining dead files.

---

### Broad strokes
Delete leftover PID/RLS modules/tests; keep live helper coverage and App import-lock; order ticket graph after knowledge demote.

1. [tests/test_feedforward.py](../../../tests/test_feedforward.py) — relocated `test_clamp_bounds` + `test_quantize_command_grid_snap` (Decision 1A)
2. [tests/test_hvac_app.py](../../../tests/test_hvac_app.py) — F6-B / `_PID_PATH` removed; AST import-lock kept
3. Deleted `apps/ha_smart_hvac/pid.py`, `rls.py`, `tests/test_pid.py`, `tests/test_rls.py` (commit `357c76f`) — four dead paths gone
4. [tickets.toml](../tickets/epic-supersede-pid-domain-docs/tickets/tickets.toml) — entry 3 `after = [1, 2]` (Decision A)
5. [docs/house-calibration.md](../../../docs/house-calibration.md) — drop “modules may remain / domain-docs lag until epic 3” wording

Review notes: Intent Test — 275 pytest; ruff clean; absences + locks verified. Broad strokes Test — 275; focused entry points green.

---

### Slice: Relocate helpers + drop F6-B
Order matters: relocate before deleting test_pid. Live SWT helpers stay covered under feedforward; F6-B cannot survive without pid.py on disk.

1. [test_feedforward.py](../../../tests/test_feedforward.py) — imports `clamp` / `quantize_command`; adds `test_clamp_bounds` + `test_quantize_command_grid_snap` with plan parametrize tuples
2. [test_hvac_app.py](../../../tests/test_hvac_app.py) — deletes `_PID_PATH` and `test_pid_does_not_reexport_clamp_or_quantize`; keeps `test_hvac_app_does_not_import_rls_or_pid_quantize`

---

### Slice: Delete four modules
Commit `357c76f` removes the dead modules and their unit suites. No App callers remained after epic-1 detach.

Deleted on HEAD (absent):
- `apps/ha_smart_hvac/pid.py` (−118)
- `apps/ha_smart_hvac/rls.py` (−285)
- `tests/test_pid.py` (−294) — after relocate
- `tests/test_rls.py` (−399)

---

### Slice: Ticket graph + house-calibration
Decision A locks knowledge demote before module delete. Operator prose no longer claims modules may remain until epic 3.

1. [tickets.toml](../tickets/epic-supersede-pid-domain-docs/tickets/tickets.toml) — entry 3 `after = [1, 2]`
2. [house-calibration.md](../../../docs/house-calibration.md) — drop domain-docs lag banner; «modules removed»

---

### Periphery
PR #144 leftovers outside the three slices:
1. [story-delete-dead-pid-rls-modules-plan.md](../tickets/epic-supersede-pid-domain-docs/tickets/story-delete-dead-pid-rls-modules-plan.md) — build plan + prior triage / Code Review notes
2. [deferred-work.md](../deferred-work.md) — meta-defer of stale epic-1 bullet + CAP-8/AGENTS lag → entry 4

Not in PR (local dirty only): walkthrough folder; uncommitted formal-review append to plan/deferred-work; party memlog.

---

### Wrap-up
Review complete for [PR #144](https://github.com/zhmachenkov-d/ha_smart_hvac/pull/144) (story 3.3).

Follow-through chosen: **commit + push only** (no merge). Included walkthrough + formal-review appends to plan/`deferred-work`; excluded party memlog.