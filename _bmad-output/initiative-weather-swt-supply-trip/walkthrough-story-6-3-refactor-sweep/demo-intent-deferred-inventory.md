# Demo: Story 6.3 Intent — deferred-work inventory → in/out
Generated: 2026-11-17T13:32:00+02:00
Branch checked: `docs/6-2-knowledge-live-curve-trv-flame-demote-supply-trip` @ `67ebb44`

Offline spot-read of [deferred-work.md](../deferred-work.md) against current AGENTS / CONTEXT / CAP-8 / house-calibration. Maps each **open** bullet to ticket 6.3 scope (docs supersede hygiene; no new product law). Epic boundary: code remediation (e.g. `control_event` docstring) stays out.

## Legend
- **IN** — settle or prune in 6.3 plan
- **OUT** — leave (code/test debt outside epic 6)
- **DECIDE** — deferred by this epic; plan must choose expand vs prune-with-cite

## Open bullets

| # | Deferred claim | Spot-check now | Map |
| --- | --- | --- | --- |
| A | AGENTS / CONTEXT / ADR 0005–0006 still describe live PID/∫/RLS after FF detach | False — epic 3 + ADR 0008 rewrite those surfaces | **IN** prune (claim obsolete) |
| B | Epic-1 deferred bullet still frames PID supersede as outstanding after 3.1 | Meta-stale; same root as A | **IN** prune with A |
| C | `adr-cap8-…` still warns about AGENTS sticky-latch prose until epic 3 | True — [adr-cap8-shared-ff-demand-writer.md](../../../../docs/decisions/adr-cap8-shared-ff-demand-writer.md) L3 still says “until epic 3” | **IN** reword historical note (cosmetic) then prune |
| D | AGENTS still says knowledge/ may lag until story 3.2 | False — AGENTS Where-things-are cites live law = ADR 0008 + CONTEXT + `knowledge/` (no 3.2 lag) | **IN** prune only (already fixed) |
| E | Code-review repeat of B (2026-11-14) | Duplicate of B | **IN** prune with A/B |
| F | AGENTS / CONTEXT omit commissioned TRV `accuracy` as `control_event` listen | False — AGENTS TRV + initialize bullets and CONTEXT Weather FF / Dev Q&A name accuracy | **IN** prune (settled by 6.1) |
| G | No accuracy `control_event` + Outdoor-fail isolation test | Still a test gap (runtime already listens) | **OUT** — code/test; epic Does-not-own |
| H | Empty-zone isolation pins law-ran only via spy | Still a test-shape gap | **OUT** — same as G |
| I | house-calibration §1 table lacks flame / `ch_active` / TRV rows; plant-off “leaves SWT untouched” without flame-clear | True — [house-calibration.md](../../../../docs/house-calibration.md) §1 table is Outdoor/plant/zones only; intro already names flame/`ch_active`/TRV | **DECIDE** — expand §1 rows vs Settled cite of intro (6.1 Never forbade full table) |

## Structure note
Bullet **I** is currently nested under `## Settled: epic-5 …` without its own open header — formatting orphan. 6.3 prune should refile or remove it when settled.

## Already Settled (not 6.3 work)
- epic-4 TRV soft-close leftovers (4.3)
- epic-5 flame short-on leftovers (5.3)

## Explicit OUT (epic / ticket)
- `control_event` docstring remediation (epic Boundaries) — docstring still says “shared prelude + FF…” while body runs `_apply_trv_law` first; leave alone
- New product laws / runtime / house `apps.yaml`
- Separate closing e2e suite

## Ticket Intent fit
Ticket description (“stale deferred-work.md epic-3 / entry-4 bullets; no new scope”) matches **A–F + C** as prune/edit hygiene. **I** is this epic’s own deferred finding → must be named in plan Intent Always/Never. **G–H** must stay Never.
