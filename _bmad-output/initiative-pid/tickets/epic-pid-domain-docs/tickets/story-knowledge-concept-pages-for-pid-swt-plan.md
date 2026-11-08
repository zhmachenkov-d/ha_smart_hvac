---
title: 'knowledge concept pages for PID SWT'
type: 'chore'
ticket: '4'
created: '2026-11-08'
status: 'built'
baseline_revision: '023d931abddfcb5f3ee53ed75918c97bdb101cfc'
route: 'oneshot'
route_source: 'auto'
risk: 'medium'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The six `knowledge/concepts` pages named in epic Done when still commission weather-curve / CAP-7 SWT (ADR 0004 language), so algorithm depth contradicts ADR 0005 and the shipped fixed-PID App.

**Approach:** Rewrite those pages (and matching `index.md` table cells) against ADR 0005: demand `round-to-0.1(clamp(base + u_pid))`, tick-owned demand / event clear-only at concept altitude, Critical Zone diagnostics-only, Outdoor/ADRC reframed as not water-path commissioning. Do not edit AGENTS, CONTEXT, ADR bodies, App code, or other `knowledge/` files.

</frozen-after-approval>

## Implementation Notes

Oneshot: six short concept docs (~55–75 substantive lines). Match ADR 0005 / CONTEXT altitude — law + roles, not R7/throttle dump (those stay AGENTS/ADR). Cite 0005; drop live CAP-7 / `clamp(u_ff)` / Outdoor-as-SWT-input. Leave `ladrc`/`madrc`/`knowledge/index.md`/AGENTS “pending 2.4” for story 2.5.
- Rewrote `set-water-temperature`, `outdoor-temperature`, `adrc` “In this project”, `critical-zone`, `multi-zone-coordinator`; updated `index.md` CZ/MZC/Outdoor description cells.
- CAP-7 / weather-curve / ADR 0004 appear only as removed/superseded history, not live commissioning.
- Outdoor Related: dropped MZC link; kept SWT + total-disturbance.
- Manual verify: no live commissioning language on the six paths; AGENTS/CONTEXT/ADR/App untouched.
- Quick review patch: MZC `description` / index cell no longer scope “for diagnostics” over ZE/HD — Critical Zone selection only.
- Quick review defer: `adrc.md` Related still links `ladrc.md`/`madrc.md` whose Project notes commission ADR 0004 — owned by story 2.5.
- Full review patches: SWT gate law (weight-unusable tick-only + no-valid-zones shared); `base_water_temp` gloss; SWT description/index PID signal; ADRC Related caveat for ladrc/madrc (siblings still 2.5).

## Plan Change Log

## Review Triage Log

### 2026-11-08 quick
**Code review complete.** 0 `decision-needed`, 1 `patch`, 1 `defer`, 0 rejected.

- [x] [Review][Patch] MZC blurb scoped “for diagnostics” over ZE/HD [multi-zone-coordinator.md:description, index.md:MZC row] — Critical Zone selection only is diagnostics-only
- [x] [Review][Defer] ADRC Related → ladrc/madrc still commission weather-curve under ADR 0004 [adrc.md:Related] — deferred to story 2.5 (plan left those pages untouched)

## Verification

**Manual checks (if no CLI):**
- `knowledge/concepts/{set-water-temperature,outdoor-temperature,adrc,critical-zone,multi-zone-coordinator,index}.md` cite ADR 0005 / PID demand law where they describe live SWT; no live CAP-7 / Weather Feedforward / `clamp(u_ff)` / Outdoor-as-control commissioning.
- Critical Zone is diagnostics/logging only and must not drive SWT; Multi-Zone Coordinator still computes ZE/HD/CZ selection without owning the SWT write.
- Outdoor and ADRC “In this project” (or equivalent) state they are not on the live water path.
- No edits outside those six paths (AGENTS/CONTEXT/ADR/App/`ladrc`/`madrc`/`knowledge/index.md` untouched).

## Code Review

### 2026-11-08
**Code review complete.** 0 `decision-needed`, 4 `patch`, 0 `defer`, 9 rejected. Decision F4 → patch (A).

- [x] [Review][Patch] ADRC Related caveat for ladrc/madrc still on ADR 0004 [adrc.md:Related] — decided A: one-line Related caveat; siblings stay 2.5
- [x] [Review][Patch] SWT concept gate enumeration incomplete vs ADR 0005 [set-water-temperature.md:15]
- [x] [Review][Patch] `base_water_temp` unexplained on SWT concept page [set-water-temperature.md:15]
- [x] [Review][Patch] SWT index/description lack PID / ADR 0005 signal [set-water-temperature.md:description; index.md:SWT row]

#### Rejected
- R1 false — “air error” matches ADR 0005/CONTEXT; formula already has `u_pid`
- R2 low — ZE/HD already listed as computed; CZ-only diagnostics tag is enough; affirming PID wiring is altitude creep
- R4 false — ADR 0005 is under Citations; git hunk context was misleading
- R5 low — Outdoor body already says not on SWT path; Related framing rarely needed
- R7 low — plan Verification meta vs deferred-work/plan artifacts; product six-path scope still holds
- R9 low — empty Plan Change Log scaffold; unused on oneshot
- R10 false — `control_tick`/`control_event`/∫ match ADR/CONTEXT altitude
- R11 low — Outdoor negation is the intentional reframe payload
- R14/R15 false — CONTEXT/AGENTS/App out of frozen plan; docs-only verify is manual
