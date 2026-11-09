---
title: 'Refactor sweep (RLS retune)'
type: 'chore'
ticket: '5'
created: '2026-11-09'
status: 'built'
baseline_revision: 'f4e47b614a0af440f80ccd92f3325a2afbd41358'
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

**Problem:** After stories 1–4, one formal deferral remains unowned (entry-1 `tickets.toml` description still says clears keep “last-good adapted gains” without the entry-2 unhealthy/rails latch → YAML override), companion Persistence still says “last-good gains”, and three intentional wontfix items from entry 2 are not yet bookkept as owned.

**Approach:** Cleanup-only: align entry-1 ticket + companion wording with parked adapted / latch→YAML, and close deferred-work ownership for the tickets.toml fix plus the three entry-2 wontfix items; no App runtime change.

## Boundaries & Constraints

**Always:** Keep entry-1/2/3/4 shipped runtime and docs semantics; mark deferred items Resolved or explicit wontfix/owned so none from entries 1–4 stay unowned.

**Never:** New RLS/PID features; App/test code edits; ADR/CONTEXT/AGENTS/`knowledge/` rewrites; reopen hysteresis, fixed-outside-rails INFO, or plan mega-MERGE as new work.

</frozen-after-approval>

## Implementation Notes

Oneshot: ~15–40 LOC of ticket/docs/deferred-work only (≤100, ≤5 files, mechanical).

Touch:
1. `tickets.toml` entry 1 `description` — parked adapted across clears; IMC-invalid/unhealthy/rails → entry-2 latch YAML (match verify/notes).
2. `rls-adaptive-algorithm.md` Persistence — last-good → parked adapted; while latched, demand uses YAML fixed.
3. `deferred-work.md` — Resolved for tickets.toml defer; record hysteresis / fixed-outside-rails INFO / structure mega-MERGE as owned wontfix under this sweep.

Done: applied all three touches on branch `chore/rls-refactor-sweep-3-5`. No App/runtime edits.

## Plan Change Log

## Review Triage Log

- 2026-11-09 quick: 1 finding → `low` / **patch** — `deferred-work.md` Companion orphan bullet lacked Resolved/Owned prefix vs siblings; evidence: section bullets used `Resolved:`/`Owned wontfix:` except that line. Patched to `Resolved: companion orphan…`.

## Verification

**Commands:**
- `uv run pytest` -- expected: all green
- `uv run ruff check .` -- expected: clean
- Grep/audit -- expected: no entry 1–4 deferral left without Resolved or owned-wontfix ownership in `deferred-work.md`; entry-1 description no longer claims last-good without latch override
