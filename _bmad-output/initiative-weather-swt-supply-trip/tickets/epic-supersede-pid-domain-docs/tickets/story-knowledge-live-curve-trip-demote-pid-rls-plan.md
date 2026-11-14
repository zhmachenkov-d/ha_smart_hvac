---
title: 'knowledge/: live curve+trip; demote PID/RLS'
type: 'feature'
ticket: '2'
created: '2026-11-14'
status: built
baseline_revision: 'f433d43886f4b80452db77c071b9a55fa7ba4a6f'
route: 'full'
route_source: 'auto'
risk: 'medium'
review: 'thorough'
review_source: 'auto'
lenses_ran: ['blind-hunter', 'edge-case-hunter', 'verification-gap', 'intent-alignment']
context:
  - _bmad-output/initiative-weather-swt-supply-trip/tickets/epic-supersede-pid-domain-docs/epic-supersede-pid-domain-docs.md
  - docs/adr/0007-weather-curve-supply-trip-swt.md
  - _bmad-output/initiative-weather-swt-supply-trip/tickets/epic-supersede-pid-domain-docs/tickets/story-tracer-adr-0007-agents-context-plan.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent
**Problem:** ADR 0007 + AGENTS/CONTEXT already teach weather-curve SWT + supply rise-rate trip, but `knowledge/` still presents fixed-PID / RLS (ADR 0005/0006) as the live water law.

**Approach:** Rewrite live SWT-facing knowledge pages to `clamp(u_ff)` + supply trip under ADR 0007; demote PID/RLS pages and ADRC/LADRC/MADRC live-pointers to historical prior art (LADRC pattern); update indexes and append `knowledge/log`. Docs-only — no CAP-7 restore, no module deletes.

## Boundaries & Constraints
**Always:**
- Live SWT law in knowledge matches ADR 0007 / App: Plant∧Demand → `round-to-0.1(clamp(u_ff))` with `u_ff = base + slope × (comfort_ref − T_out)`; Outdoor on `control_event` / Outdoor-gated demand writer (tick + eligible events); dual-gate (`_gate_prelude` vs `supply_event` Plant∧Demand only); supply trip latch only after successful trip write `0`; Decision C idle clear latch only after successful idle write `0`; plant-off = no SWT write + clear trip state; Critical Zone diagnostics/logging only (not SWT or trip).
- CAP-7 / adapting `base`/`slope` / `ff_auto_correct_state.json`: hard out — not on water path; do not commission; out of scope (never deferred/later soft).
- Demote fixed-PID / RLS / `rls_state.json` as live law; cite ADR 0007 as live; ADR 0005/0006 as historical prior art with live-pointers.
- Reuse LADRC/ADRC demotion structure for project notes: **removed / not on live path** — **superseded by ADR 0007**; literature fence; live pointer sentence to Set Water Temperature / Coordinator / Critical Zone diagnostics.
- Append-only `knowledge/log.md` (do not rewrite historical Fact entries).
- Cite ADR 0007 and shipped App; do not invent new runtime.
- **Decision (1A):** Also retarget companion live-pointers in `multi-zone-coordinator.md` and Huang/Wang «fit to this project» lines to ADR 0007 (one-line each) so no knowledge page still asserts live fixed-PID under 0005.
- **Decision (2A):** Demote `rls-adaptive-pid.md` LADRC-like — keep technical body as historical record; add Project note / frontmatter that RLS is **not** on the live path (**superseded by ADR 0007**; ADR 0005/0006 historical); live pointer to Set Water Temperature under ADR 0007.

**Never:**
- Change App runtime, tests, `apps.yaml` / example yaml, house yaml, Exclusive Session, or Heating Demand definition.
- Delete `pid.py` / `rls.py` (story 3.3); rewrite ADR 0007 / AGENTS / CONTEXT (story 3.1 done).
- Restore CAP-7; reintroduce `base_water_temp + u_pid` / sticky demand-edge / «Outdoor not a control listener» as live law.
- Edit `knowledge/playbooks/**`, `knowledge/raw/**`, or literature cores that do not assert live SWT law (`zone.md`, `zone-error.md`, `extended-state-observer.md`, `total-disturbance.md`, `plant.md` body).

## I/O & Edge-Case Matrix
| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| Happy SWT page | Open `set-water-temperature.md` | Live = clamp(u_ff) + Outdoor-gated demand + supply trip; cites ADR 0007; no live PID/RLS | — |
| Outdoor page | Open `outdoor-temperature.md` | Outdoor required on demand path / control listener; Weather Feedforward input; not «off path» | — |
| CZ page | Open `critical-zone.md` | Diagnostics-only; superseded pointer → ADR 0007; supply trip not CZ-driven | — |
| RLS demotion | Open `rls-adaptive-pid.md` | LADRC-like: technical body kept; Project note = not on live path; live → ADR 0007 SWT | — |
| ADRC family | Open adrc/ladrc/madrc | Project notes retarget live pointer to 0007 formula; literature fence kept | — |
| Companions (1A) | Open multi-zone + Huang/Wang fit | One-line live pointers → ADR 0007; no «live fixed-PID under 0005» | — |
| Indexes | Open knowledge + concepts index | Live = ADR 0007; RLS/PID framed historical; Outdoor/SWT blurbs match pages | — |
| Log | Open `log.md` | New append entry for 0007 align; old Facts untouched | — |
| CAP-7 | Grep knowledge live pages | Only hard-out / absent language | — |
| Out of scope | Diff apps/, tests/, adr/, AGENTS, CONTEXT | Untouched | — |

</frozen-after-approval>

## Code Map
Evidence commit `f433d43886f4b80452db77c071b9a55fa7ba4a6f` (`main` tip after ADR 0007 merge). Continuity from ticket `after: [1]` plan `story-tracer-adr-0007-agents-context-plan.md` (knowledge deferred to 3.2; AGENTS caveat that knowledge may lag).

- `docs/adr/0007-weather-curve-supply-trip-swt.md` — SoT live water law for pointers (do not edit).
- `AGENTS.md` / `CONTEXT.md` — already 0007; knowledge must agree (do not edit this story).
- `knowledge/concepts/set-water-temperature.md` — **rewrite** frontmatter + body + citations from PID/`u_pid`/sticky/Outdoor-off to FF + trip under 0007; hard-out CAP-7; link Outdoor + optional historical RLS page as prior art only.
- `knowledge/concepts/outdoor-temperature.md` — **rewrite** to Outdoor on path (`T_out` in `u_ff`, `control_event`); align Avoid with CONTEXT (do not ban Weather Feedforward); cite ADR 0007.
- `knowledge/concepts/critical-zone.md` — keep diagnostics-only body; retarget supersede/citation **0005 → 0007**; clarify supply rise-rate trip is not CZ-driven.
- `knowledge/concepts/rls-adaptive-pid.md` — **2A LADRC-like demote:** keep technical body; add Project note + frontmatter «not on live path / superseded by ADR 0007»; live pointer to SWT; ADR 0005/0006 historical cites.
- `knowledge/concepts/adrc.md`, `ladrc.md`, `madrc.md` — retarget `## In this project` / `## Project note` + citation live-pointers from ADR 0005 PID formula → ADR 0007 `clamp(u_ff)` (+ CZ diagnostics); keep literature bodies.
- `knowledge/concepts/multi-zone-coordinator.md` — **1A:** retarget supersede/citation live-pointers 0005 → 0007 (Coordinator still does not own SWT/trip).
- `knowledge/references/huang-2018-ladrc-hvac.md`, `wang-2026-madrc-sst.md` — **1A:** one-line project-fit live-law swap to ADR 0007; leave paper bodies alone.
- `knowledge/concepts/index.md`, `knowledge/index.md` — update root live-path blurb and Outdoor/SWT/RLS description cells.
- `knowledge/log.md` — **append** dated entry (align knowledge with ADR 0007; demote PID/RLS).
- Do not change: `playbooks/**`, `raw/**`, `decisions/index.md`, `references/index.md`, literature-only concept bodies without live-law claims.

## Tasks & Acceptance
**Execution:**
- [ ] `knowledge/concepts/set-water-temperature.md` — rewrite live law to weather FF + supply trip (ADR 0007); remove live PID/∫/RLS/sticky/Outdoor-off; CAP-7 hard out; update citations.
- [ ] `knowledge/concepts/outdoor-temperature.md` — Outdoor on demand path / control listener; cite ADR 0007; Avoid does not forbid Weather Feedforward.
- [ ] `knowledge/concepts/critical-zone.md` — retarget supersede + citation to ADR 0007; keep diagnostics-only.
- [ ] `knowledge/concepts/rls-adaptive-pid.md` — LADRC-like demote (2A): keep body; Project note + frontmatter not-on-live-path; live → ADR 0007 SWT.
- [ ] `knowledge/concepts/adrc.md` + `ladrc.md` + `madrc.md` — retarget project-note live pointers + ADR citations to 0007.
- [ ] `knowledge/concepts/multi-zone-coordinator.md` + `references/huang-2018-ladrc-hvac.md` + `wang-2026-madrc-sst.md` — 1A one-line live-pointer retarget to ADR 0007.
- [ ] `knowledge/concepts/index.md` + `knowledge/index.md` — live = ADR 0007; Outdoor/SWT/RLS blurbs match pages; ADRC family remains literature.
- [ ] `knowledge/log.md` — append 2026-11-14 (or build date) align entry; do not edit old Facts.
- [ ] Verify — pytest + ruff + grep guards + spot-read ACs.

**Acceptance Criteria:**
- Given live SWT-facing knowledge pages, when opened, then they cite ADR 0007 / `clamp(u_ff)` + supply trip and do not present fixed-PID or RLS as live law.
- Given `outdoor-temperature.md`, when read, then Outdoor is on the demand path (control listener / `T_out` in FF), not «not a control listener».
- Given `critical-zone.md`, when read, then CZ remains diagnostics-only and supersede/live cite points at ADR 0007 (trip not CZ-driven).
- Given `rls-adaptive-pid.md`, when read, then technical body remains as historical record and a Project note fences it off the live path with live pointer to ADR 0007 SWT (not a commissioning guide).
- Given ADRC/LADRC/MADRC project notes and 1A companions (`multi-zone-coordinator`, Huang/Wang fit), when read, then live pointers name ADR 0007 weather-curve SWT (not fixed-gain PID under 0005).
- Given `knowledge/index.md` and `concepts/index.md`, when read, then live water path is ADR 0007 and Outdoor/SWT(/RLS) blurbs match the concept pages.
- Given `knowledge/log.md`, when read, then a new append entry records this align; prior Fact entries are unchanged.
- Given CAP-7 / `ff_auto_correct_state.json`, when grepped in touched live pages, then only hard-out / absent language appears.
- Given this story’s scope, when diff is inspected, then apps/, tests/, ADR bodies, AGENTS.md, and CONTEXT.md are unchanged.
- Given CI-local verify, when `uv run pytest` and `uv run ruff check apps/ha_smart_hvac tests` run, then both succeed.

## Implementation Notes
- Match App via ADR 0007 + `hvac_app.py` / `feedforward.py` — knowledge depth may briefly name dual-gate / latch-after-successful-write / Decision C, but do not dump test matrices. Manual SWT spot-read must confirm trip latch/clear + dual-gate appear without pasting the full ADR.
- Outdoor Avoid: prefer CONTEXT’s Weather Feedforward language; ban forecast-as-control only if needed.
- Timestamps on concept frontmatter: bump when editing that page.
- RLS: add `## Project note` (or equivalent) above Related; do not strip Kp/Ki / `rls_state.json` historical mechanics. Opening sentences after demotion must not read as live commissioning (`pid.adaptive` only inside historical fence).
- Companions: only the live-pointer / supersede / fit sentences — do not rewrite Huang/Wang paper tables beyond the project-fit row/bullet.
- Done criteria: `pytest` / `ruff` are hygiene only (necessary, not sufficient). Story completion is blocked on Verification greps + manual spot-reads.
- Epic debt (out of this diff): after knowledge aligns, remove or reword AGENTS «knowledge/ may lag until 3.2» (epic Done-when / follow-on, not a 3.2 task).

## Plan Change Log
- 2026-11-14: Initial draft from ticket 3.2 + investigation; route full (medium risk; 12+ prose files); Open Questions on companion breadth and RLS demotion depth.
- 2026-11-14: User Keep full plan (~2100+ tokens); decisions 1A companions include, 2A RLS LADRC-like; Open Questions cleared.
- 2026-11-14: Party review — add five Verification guards before Approve: `concepts/index` in positive ADR 0007/`clamp(u_ff)`; 1A companions positive 0007 + negative live PID/`u_pid`; negative leftover `superseded by ADR 0005` on CZ/multi-zone/ADRC family/SWT; positive RLS live-path fence + 0007; negative SWT sticky/rising-edge demand ghosts.

- 2026-11-14: Chat plan-review apply — CZ/trip positives; index frontmatter + RLS blurb negatives; pytest/ruff hygiene-only; epic debt AGENTS lag caveat; RLS commissioning spot-read.

## Review Triage Log
- 2026-11-14 (party): Verification under-covered existing ACs (indexes, 1A companions, supersede retarget, RLS fence, sticky SWT). Guards added; no scope reopen.
- 2026-11-14 (chat review): Verification still weak on CZ/trip/index frontmatter/RLS index blurb; pytest/ruff insufficient; RLS commissioning read risk; AGENTS lag caveat → epic debt. Patched Verification + Implementation Notes; no frozen reopen.

| lens | finding | verdict | route | evidence |
| --- | --- | --- | --- | --- |
| blind-hunter | Missing trailing newlines on CZ/Outdoor/RLS/SWT | low | fixed | Applied in knowledge hunks; no `No newline at end of file` on those paths in current tree |
| blind-hunter | log Fact omits round-to-0.1 | medium | fixed | knowledge/log.md Fact now uses round-to-0.1(clamp(u_ff)) |
| blind-hunter | concepts/index CZ blurb omits supply trip | medium | fixed | CZ index cell includes supply trip |
| blind-hunter | multi-zone CZ fence omits trip; timestamp stale | medium | fixed | multi-zone-coordinator.md fences trip; timestamp bumped in knowledge hunk |
| blind-hunter | adrc/ladrc/madrc timestamps not bumped | low | fixed | timestamps 2026-11-14T14:58:00Z |
| blind-hunter | SWT omits clamp rails / hold / boiler_water / decision docs | false | — | Plan/Impl Notes: knowledge depth without full ADR paste / commissioning recipe |
| blind-hunter | SWT omits debounce / control_interval / _hands_off detail | false | — | Same intentional density; AGENTS/ADR remain SoT for those clauses |
| blind-hunter | RLS historical body present-tense pid.adaptive defaults | medium | fixed | body uses defaulted / was; latch started false (walkthrough formal review patch) |
| blind-hunter | Plan Execution checkboxes still unchecked | false | — | Reject: fix would edit this build's plan workflow artifact |
| blind-hunter | Append-only log Facts contradict without cross-ref | false | — | Intent: append-only; prior Facts must stay; latest dated entry is current |
| blind-hunter | No Weather Feedforward concept page | false | — | Intent approach does not require a new OKF concept |
| edge-case-hunter | CZ index blurb omits supply trip | medium | fixed | Same root as blind-hunter index CZ — fixed |
| edge-case-hunter | log Fact omits round-to-0.1 | medium | fixed | Same root as blind-hunter log Fact — fixed |
| edge-case-hunter | RLS present-tense pid.adaptive | medium | fixed | Same root as blind-hunter RLS tense — fixed |
| edge-case-hunter | ladrc/madrc parenthetical omits ADR 0006 | false | — | Live pointer already ADR 0007 weather FF + trip; 0006 not implied live |
| edge-case-hunter | trailing newlines CZ/Outdoor/RLS/SWT | low | fixed | Same root as blind-hunter newlines — fixed |
| edge-case-hunter | RLS spot-read historical claim | medium | fixed | Same root as RLS tense — fixed |
| verification-gap | (none) | — | — | Lens: docs-only; no behavioral verification gaps |
| intent-alignment | Diff implements R3/R4 prose; verification not in diff | false | — | Descriptive; pytest/rg ran outside diff; not a knowledge defect |

## Design Notes
Reuse ADRC/LADRC project-note demotion shape; SWT page is the primary live rewrite (same role PID page held under 0005). Indexes and log follow the 2026-11-08 ADR 0005 align entry pattern (append log; update index blurbs).

## Verification
**Commands:**
- `uv run pytest` — expected: all pass (hygiene only; docs-only; not sufficient for ACs).
- `uv run ruff check apps/ha_smart_hvac tests` — expected: clean (hygiene only).
- `rg -n "ADR 0007|ADR-0007|clamp\\(u_ff\\)" knowledge/concepts/set-water-temperature.md knowledge/concepts/outdoor-temperature.md knowledge/concepts/critical-zone.md knowledge/index.md knowledge/concepts/index.md` — expected: matches in each.
- `rg -n "supply|r_max|rise-rate|trip" knowledge/concepts/set-water-temperature.md` — expected: supply trip / rate language present.
- `rg -n "base_water_temp \\+ u_pid|not a control listener|Outdoor Temperature, Weather Feedforward.*not on this path" knowledge/concepts/set-water-temperature.md knowledge/concepts/outdoor-temperature.md` — expected: no live-path matches.
- `rg -n "Rising-edge into gated demand|stay no-op until clear" knowledge/concepts/set-water-temperature.md` — expected: no matches (no sticky demand-edge ghost).
- `rg -n "fixed-PID SWT|live water path: \\*\\*ADR 0005\\*\\*|optional RLS adaptive: \\*\\*ADR 0006\\*\\*" knowledge/index.md` — expected: no matches (frontmatter + body).
- `rg -n "Optional online retune of PID" knowledge/concepts/index.md` — expected: no match (RLS blurb demoted / historical).
- `rg -n "Does not own.*supply trip|supply trip" knowledge/concepts/index.md` — expected: Multi-Zone Coordinator cell mentions supply trip non-ownership.
- `rg -n "fixed-gain PID|ADR 0005\\)\\s*— live SWT" knowledge/concepts/adrc.md knowledge/concepts/ladrc.md knowledge/concepts/madrc.md` — expected: no live-pointer matches (historical mentions only if clearly non-live).
- `rg -n "ADR 0007|ADR-0007" knowledge/concepts/multi-zone-coordinator.md knowledge/references/huang-2018-ladrc-hvac.md knowledge/references/wang-2026-madrc-sst.md` — expected: matches in each (1A live-pointer).
- `rg -n "base_water_temp \\+ u_pid|fixed-gain PID \\(.*ADR 0005|Live water path is fixed-gain PID" knowledge/concepts/multi-zone-coordinator.md knowledge/references/huang-2018-ladrc-hvac.md knowledge/references/wang-2026-madrc-sst.md` — expected: no live-PID claims.
- `rg -n "superseded by ADR 0005" knowledge/concepts/critical-zone.md knowledge/concepts/multi-zone-coordinator.md knowledge/concepts/adrc.md knowledge/concepts/ladrc.md knowledge/concepts/madrc.md knowledge/concepts/set-water-temperature.md` — expected: no matches (supersede retarget → 0007).
- `rg -n "not on the live path|superseded by ADR 0007" knowledge/concepts/rls-adaptive-pid.md` — expected: matches (2A fence).
- `rg -n "ADR 0007|ADR-0007" knowledge/concepts/rls-adaptive-pid.md` — expected: matches (live pointer).
- `rg -n "ff_auto_correct_state\\.json" knowledge/concepts/set-water-temperature.md knowledge/concepts/outdoor-temperature.md knowledge/concepts/rls-adaptive-pid.md` — expected: only hard-out / absent / historical, never commission or deferred.
- `rg -n "^## 2026-11-14" knowledge/log.md` — expected: new append section present (adjust date if build day differs).

**Manual checks (blocking with greps):**
- Spot-read SWT + Outdoor + CZ vs ADR 0007 MUST-floor (gates, FF, trip latch/clear + dual-gate on SWT without full ADR paste, CZ diagnostics).
- Spot-read RLS Project note: opening does not read as live commissioning; technical body clearly historical.
- Spot-read ADRC family + 1A companions for historical fence + live 0007 pointer.
- Diff excludes apps/, tests/, `docs/adr/**` bodies, AGENTS.md, CONTEXT.md; prior `log.md` Facts unchanged.

## Code Review

### 2026-11-14
**Code review complete.** 0 `decision-needed`, 9 `patch`, 0 `defer`, 6 rejected. Decision ADRC→(b) resolved to patch.

- [x] [Review][Patch] ADRC family: drop prior-ADR parentheticals; cite only ADR 0007 + literature [knowledge/concepts/{adrc,ladrc,madrc}.md] — decided 2026-11-14: option (b)
- [x] [Review][Patch] concepts/index Multi-Zone blurb omits supply-trip non-ownership [knowledge/concepts/index.md:16]
- [x] [Review][Patch] SWT page drops live control_interval non-reset clause [knowledge/concepts/set-water-temperature.md:15]
- [x] [Review][Patch] RLS historical latch clause still present tense [knowledge/concepts/rls-adaptive-pid.md:19]
- [x] [Review][Patch] Plan Review Triage Log stale vs already-applied knowledge patches [story-knowledge-live-curve-trip-demote-pid-rls-plan.md Review Triage Log]
- [x] [Review][Patch] Plan Verification greps miss Multi-Zone index trip fence [plan Verification]
- [x] [Review][Patch] RLS CAP-7 hard-out sentence awkward in historical paragraph [knowledge/concepts/rls-adaptive-pid.md:19]
- [x] [Review][Patch] Outdoor CONTEXT citation omits Weather Feedforward [knowledge/concepts/outdoor-temperature.md:24]
- [x] [Review][Patch] Huang fit omits CZ must not drive supply trip [knowledge/references/huang-2018-ladrc-hvac.md:39]

Rejected:
- R7 SWT hold/Decision C density — intentional knowledge depth per plan Impl Notes; ADR 0007 remains SoT
- R9 Intent Approach clamp vs round-to-0.1 — would edit frozen Intent
- R10 Plan status built vs unchecked Execution — workflow artifact
- R15 Full epic R4 code/commissioning — out of story 3.2 scope by design
- R16 pytest/ruff in Verify — hygiene outside docs diff by design
- R17 multi-zone/Huang/Wang beyond Title list — plan Decision 1A

Applied 2026-11-14 (walkthrough Formal review option 1): Multi-Zone index trip fence; SWT `control_interval`; RLS latch past tense + drop CAP-7 clause; ADRC family drop prior-ADR parentheticals (b); Outdoor CONTEXT+WF cite; Huang CZ trip fence; Verification Multi-Zone index grep; Review Triage Log rows marked fixed.
