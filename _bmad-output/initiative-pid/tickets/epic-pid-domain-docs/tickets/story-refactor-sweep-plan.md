---
title: '2.5 Refactor sweep'
type: 'chore'
ticket: '5'
created: '2026-11-08'
status: 'built'
baseline_revision: 'ae26c32300fe69ee1759b714d0801f2977c14ccb'
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

**Problem:** After stories 2.1–2.4, leftover knowledge pages and AGENTS “pending” lines still present ADR 0004 / weather-curve / CAP-7 as the live SWT path, so a reader can contradict ADR 0005 and the shipped App.

**Approach:** Cleanup-only: reframe those leftovers and obvious cross-links to ADR 0005 fixed-PID (literature stays literature); drop stale AGENTS pending 2.3+/2.4; no new scope, no App/ADR body rewrite.

</frozen-after-approval>

## Implementation Notes

Oneshot (~25–35 lines across ~7 docs files; mechanical reframe). Mirror `adrc.md` “In this project” altitude for LADRC/MADRC Project notes; point live water path at ADR 0005 everywhere that still says weather-curve-only / CAP-7 commissioning.

- `knowledge/concepts/ladrc.md` + `madrc.md` — Project note → removed from water path, superseded by ADR 0005; Huang/MADRC gains remain literature.
- `knowledge/concepts/adrc.md` — drop Related “siblings still 2.5” caveat once those notes match.
- `knowledge/index.md` — frontmatter description + intro live-path line → ADR 0005 / fixed-PID (keep ADRC literature disclaimer).
- `knowledge/references/huang-2018-ladrc-hvac.md` + `wang-2026-madrc-sst.md` — “This repo” / mapping rows: PID SWT, Critical Zone diagnostics-only, no CAP-7 / weather-curve FF.
- `knowledge/log.md` — append a 2026-11-08 entry (append-only; do not rewrite the 2026-10-19 Fact).
- `AGENTS.md` — drop “pending stories 2.3+” / “pending story 2.4”; Verified stamp → `ae26c32` (baseline).
- Out of scope: App runtime, ADR 0004/0005 bodies, CONTEXT.md (already aligned), house-calibration (already migration text), epic-3 RLS.
- Closed 2.4 deferral target: ladrc/madrc Project notes + adrc Related caveat.
- Quick review patches: ladrc/madrc Project notes mirrored to adrc altitude; wang Critical Zone “diagnostics and logging only” + full demand clamp formula; Verification rg excludes append-only `knowledge/log.md`.

## Plan Change Log

## Review Triage Log

### 2026-11-08 quick
**Code review complete.** 0 `decision-needed`, 4 `patch`, 0 `defer`, 2 rejected.

- [x] [Review][Patch] ladrc Project note thinner than adrc In-this-project [ladrc.md:Project note]
- [x] [Review][Patch] madrc Project note thinner than adrc In-this-project [madrc.md:Project note]
- [x] [Review][Patch] wang mapping drops “logging” from diagnostics-only [wang-2026-madrc-sst.md:Cascade row]
- [x] [Review][Patch] wang live-path shorthand omits round-to-0.1(clamp) [wang-2026-madrc-sst.md:Schedule row]
- [x] [Review][Patch] Verification rg still hits append-only 2026-10-19 log Fact [plan:Verification] — narrowed paths away from `knowledge/log.md`

#### Rejected
- false — knowledge/log Updated omits AGENTS.md: OKF log covers knowledge/ only; AGENTS is separate agent-context (same pattern as 2026-10-19 entry)
- false (covered by Verification patch) — historical weather-curve-only Fact in log is intentional append-only history

## Verification

**Commands:**
- `rg -n "weather-curve-only|live water path: \*\*ADR 0004\*\*|feeds CAP-7|pending stor(y|ies) 2\.[34]" AGENTS.md knowledge/concepts knowledge/index.md knowledge/references` -- expected: no matches (dated `knowledge/log.md` history stays append-only)
- `rg -n "Weather Feedforward|CAP-7|clamp\\(u_ff\\)|ff_auto_correct" AGENTS.md CONTEXT.md docs/adr/0005-fixed-pid-swt.md knowledge/concepts/{set-water-temperature,outdoor-temperature,adrc,critical-zone,multi-zone-coordinator,ladrc,madrc,index}.md knowledge/index.md` -- expected: only removed/not-on-path / superseded framing, no live commissioning

**Manual checks (if no CLI):**
- `ladrc.md` / `madrc.md` Project notes and the two reference “This repo” rows cite ADR 0005 / fixed-PID, not weather-curve as live.
- `knowledge/index.md` live water path is ADR 0005.
- `AGENTS.md` Where-things-are no longer says PID/concept pages pending 2.3+/2.4.
- No App or ADR body edits.
