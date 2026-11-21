---
title: 'Docs: amend ADR/CONTEXT/AGENTS/knowledge for house-idle soft-close'
type: 'chore'
ticket: '3'
created: '2026-11-20'
status: 'built'
baseline_revision: 'a6e52d4084d977ba8bda42b655553b0a53cb3af1'
route: 'full'
route_source: 'auto'
risk: 'medium'
review: 'thorough'
review_source: 'auto'
lenses_ran:
  - blind-hunter
  - edge-case-hunter
  - verification-gap
  - intent-alignment
review_loop_iteration: 0
followup_review_recommended: true
context:
  - '{project-root}/_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-trv-house-idle-soft-close/tickets/story-tracer-trv-house-idle-soft-close.md'
  - '{project-root}/docs/decisions/adr-write-gated-supply-trip-latch.md'
warnings:
  - oversized
deferred: []
---

<intent-contract>

## Intent
**Problem:** Live ADR 0008, CONTEXT, AGENTS `bmad:context`, and knowledge still teach plant-on overshoot hysteresis and commissioned accuracy soft-close after entry 1 already ships house-idle floor + hold.

**Approach:** Amend those live surfaces to match entry 1 Requirements 1–7; banner the three overshoot/accuracy TRV decisions as historical; leave App/tests/yaml untouched beyond verify.

## Boundaries & Constraints
**Always:**
- Soft-close prose matches entry 1: first Plant-on all-idle observe writes `valve_closure_floor` (default 80) and arms one `trv_soft_close_hold_s` hold (default 300); no re-arm while hold active; hold expiry while idle writes 100 and stays at 100 without re-floor; orphan/token-mismatch expiry is a no-op; any Heating Demand (cold start, rising-edge, or sustained) writes 100 and cancels/never arms hold; return to all-idle floors and arms a new hold; plant-off writes 100 and cancels hold.
- Commissioned TRV = closure-only; leftover yaml `accuracy` is ConfigError; accuracy absent from Event-path / soft-close listener inventories.
- App never writes `valve_opening_degree`; Critical Zone does not drive soft-close; CAP-7 / `ff_auto_correct_state.json` stay out of live commissioning language.
- Historical banners on the three overshoot/accuracy decisions point live soft-close to ADR 0008 house-idle hold (reuse leading-line style of `docs/decisions/adr-write-gated-supply-trip-latch.md`).
- AGENTS edits only inside `<!-- bmad:context -->` … `<!-- /bmad:context -->`; Verified stamp line unchanged.
- Amend ADR 0008 in place (no new ADR number); keep `docs/decisions/adr-trv-before-water-prelude.md` live (no overshoot cite today — leave unless a one-line stale cross-cite appears).

**Never:**
- Edit App runtime, tests (beyond running them), `apps.yaml.example`, or house `apps/apps.yaml`.
- Copy epic R1 “rising-edge only” into live docs; invent hold/token law not in entry 1; author a new soft-close hold decision file.
- Restore temperature overshoot / `_trv_overshoot_latched` / accuracy-listen as live soft-close law.
- Touch weather-curve SWT, flame short-on, Exclusive Session, or Heating Demand definition.
- Prune deferred dead code/tests (entry 4); bump AGENTS Verified stamp.

## I/O & Edge-Case Matrix
| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| Happy path | Agent reads ADR 0008 / CONTEXT / AGENTS / `trv-soft-close.md` | House-idle floor→hold→100 law; closure-only; no accuracy listen | N/A |
| Plant-off docs | Plant Management off passage | Closure 100 + cancel soft-close hold (no overshoot-latch keep prose) | N/A |
| Historical open | Open any of the three TRV overshoot/accuracy decisions | Leading banner: not live soft-close; live → ADR 0008 | N/A |
| Hygiene | `rg` live soft-close paths for overshoot/accuracy | Hits only inside historical banners / clearly marked historical lines | Fail story if live teaching remains |
| Verify | `uv run pytest` + `uv run ruff check apps/ha_smart_hvac tests` | Both clean (docs-only diff) | Block done on failure |

</intent-contract>

## Code Map
Evidence HEAD `a6e52d4084d977ba8bda42b655553b0a53cb3af1`. Entry 1 App law already at `hvac_app.py` `_apply_trv_law` (~461+), hold arm/disarm/expiry (~172–220); `config.py` rejects `accuracy` (137–138) and parses `trv_soft_close_hold_s` / `valve_closure_floor`. **Docs only below — do not edit App.**

- `docs/adr/0008-weather-curve-trv-flame-swt.md` — Cite list L3: drop the three overshoot/accuracy decision paths as live cites (keep `adr-trv-before-water-prelude.md` + flame decisions). CAP-8 Event path L23–24: remove commissioned `accuracy` listener + accuracy-decision cite. § TRV soft-close L27–30: replace plant-off keep-latch + plant-on overshoot hysteresis with house-idle floor/hold/demand/plant-off cancel (defaults 80/300); leftover `accuracy` → ConfigError. Keep CAP-7 out-of-scope (L51–52).
- `CONTEXT.md` — Weather Feedforward listeners L58: drop commissioned `accuracy`. **TRV soft-close** L61–63: house-idle law; plant-off 100 + hold cancel; no `_trv_overshoot_latched`.
- `AGENTS.md` — Inside `bmad:context` only: Plant-off TRV line (~32), TRV soft-close bullet (~35), Event listeners (~38) — same house-idle / no-accuracy truth; leave Verified stamp untouched.
- `knowledge/concepts/trv-soft-close.md` — Frontmatter description + body + Related: house-idle; cite ADR 0008 + `adr-trv-before-water-prelude`; do not cite the three overshoot/accuracy decisions as live.
- `knowledge/concepts/index.md` L23 — TRV blurb: drop “plant-off max-close keeps overshoot latch”.
- `knowledge/concepts/outdoor-temperature.md` L11 — listener inventory: drop commissioned accuracy.
- `knowledge/log.md` — Append-only top Fact (date 2026-11-20): house-idle soft-close docs amend.
- `docs/decisions/adr-trv-write-gated-overshoot-latch.md`, `adr-trv-plant-off-no-latch-clear.md`, `adr-trv-accuracy-shared-control-event.md` — Leading historical banner → ADR 0008 house-idle hold; leave body as historical record.
- Do not change: App/`tests`/`apps.yaml*`; `adr-trv-before-water-prelude.md` (unless stale overshoot cross-cite appears — none at HEAD); SWT/flame sections except accuracy listener scrub on shared Event-path lists.

## Tasks & Acceptance
**Execution:**
- [x] `docs/adr/0008-weather-curve-trv-flame-swt.md` — Rewrite § TRV soft-close + Event-path listener list + live cite list for house-idle / closure-only; keep CAP-7 out of scope.
- [x] `CONTEXT.md` + `AGENTS.md` (`bmad:context` only) — Match ADR 0008 house-idle soft-close; strip accuracy from listener inventories; leave Verified stamp.
- [x] `knowledge/concepts/trv-soft-close.md` + `index.md` + `outdoor-temperature.md` + append `knowledge/log.md` Fact — Live knowledge teaches house-idle; no overshoot-latch / accuracy soft-close.
- [x] Three `docs/decisions/adr-trv-{write-gated-overshoot-latch,plant-off-no-latch-clear,accuracy-shared-control-event}.md` — Leading historical banners pointing to ADR 0008.
- [x] Verify — `rg` hygiene on live paths + `uv run pytest` + `uv run ruff check apps/ha_smart_hvac tests`.

**Acceptance Criteria:**
- Given ADR 0008 / CONTEXT / AGENTS / live knowledge soft-close prose, when an agent reads soft-close behavior, then it matches entry 1 Requirements 1–7 (floor+arm once; no re-arm while holding; idle expiry→100 stay; orphan no-op; any demand→100 cancel; return-to-idle re-floor+arm; plant-off→100 cancel) and does not copy epic “rising-edge only”.
- Given ADR 0008 after amend, when TRV soft-close and Event-path listeners are read, then plant-on soft-close is house-idle floor + `trv_soft_close_hold_s` (defaults 80/300) with demand/plant-off cancel; plant-off writes 100 and cancels hold (no `_trv_overshoot_latched` keep/clear); commissioned = closure-only and leftover `accuracy` is ConfigError; accuracy absent from Event-path list; never-opening + Critical Zone fences remain; live cite list no longer treats the three overshoot/accuracy decisions as live soft-close law.
- Given CONTEXT TRV/Weather Feedforward text and AGENTS `bmad:context` Conventions, when read, then they match ADR 0008 house-idle soft-close; AGENTS edits stay inside markers; Verified stamp unchanged.
- Given `knowledge/concepts/trv-soft-close.md`, concepts index TRV blurb, and `outdoor-temperature.md`, when amended, then they teach house-idle soft-close (cite ADR 0008 + live prelude), index no longer says plant-off keeps overshoot latch, outdoor listener list has no commissioned accuracy, and `knowledge/log.md` has an append-only Fact for this amend.
- Given the three overshoot/accuracy TRV decisions, when opened, then each has a leading historical banner pointing live soft-close to ADR 0008 house-idle hold; no new soft-close hold decision file exists.
- Given the amended live docs set, when CAP-7 language and hygiene `rg` / pytest / ruff run, then CAP-7 stays absent from live commissioning language; live soft-close paths show no `_trv_overshoot_latched` or commissioned accuracy listen except inside historical banners / clearly marked historical lines; pytest and ruff are clean.

## Implementation Notes

- Docs amend implemented 2026-11-20; review patches: ADR SWT plant-off parenthetical, CONTEXT/AGENTS orphan no-op, outdoor-temperature timestamp.
- Hygiene rg clean on live soft-close paths; pytest 370 passed; ruff clean; AGENTS Verified stamp unchanged.
- SoT is entry 1 Requirements 1–7 (continuity from ticket `1` plan Implementation Notes: idle-episode none→holding→closed_idle; soft-close hold expiry does not run Outdoor prelude).
- Banner pattern: one leading line like supply-trip historical decisions, plus live pointer to ADR 0008 (mirror `adr-idle-trip-clear-after-write.md` style when a live replacement exists).
- Parallel with entry 2 is fine — docs must not require house `apps.yaml`.

## Plan Change Log
## Review Triage Log

### 2026-11-20 — Review pass
- verdicts: 17 findings — high 0, medium 6, low 4, false 5, maybe-false 0
- findings:
  - `[medium]` `[patch]` ADR 0008 SWT gates plant-off still said soft-close “still runs” without 100+cancel — fixed parenthetical to closure 100 + cancel hold
  - `[medium]` `[patch]` CONTEXT/AGENTS omitted orphan/token-mismatch no-op — added to TRV soft-close passages (grouped with EC3–5 / IA reading C)
  - `[low]` `[reject]` CONTEXT/AGENTS omit cold-start/rising-edge/sustained enumeration — “any Heating Demand” already blocks rising-edge-only; everyday harm unlikely
  - `[low]` `[reject]` Historical banners lack markdown ADR links — bare ADR 0008 name is enough for agents; cosmetic
  - `[low]` `[reject]` CONTEXT TRV `_Avoid_` not updated for overshoot/accuracy — positive prose already demotes; extra Avoid complexity not worth it
  - `[low]` `[patch]` outdoor-temperature.md timestamp left at 2026-11-17 — bumped to 2026-11-20
  - `[false]` `[reject]` trv-soft-close Citations drop demoted decisions without historical pointer — intent required dropping live cites, not re-listing them as historical
  - `[false]` `[reject]` Story plan in-review with unchecked tasks mid-review — workflow process artifact, not a docs defect
  - `[reject]` `[reject]` Verification rg paths omit bannered decision files — would require editing this build's plan
  - `[false]` `[reject]` ADR omits floor-write-fail before arm — not in story SoT Requirements 1–7; ADR MUST-floor happy path is correct
  - `[false]` `[reject]` ADR omits hold-expiry write-fail re-floor — same; not required by intent
  - `[medium]` `[patch]` CONTEXT omit orphan on hold expiry — same fix as BH2
  - `[medium]` `[patch]` AGENTS omit orphan on hold expiry — same fix as BH2
  - `[medium]` `[patch]` Claim: CONTEXT/AGENTS omit orphan while ADR includes it — same fix as BH2
  - `[medium]` `[patch]` Intent-alignment reading C: CONTEXT/AGENTS incomplete vs Req 1–7 orphan clause — same fix as BH2
  - `[false]` `[reject]` Intent-alignment reading B: set-water-temperature plant-off soft-close pointer — does not teach overshoot/accuracy; outside Notes matrix
  - `[false]` `[reject]` Intent-alignment reading D: verify evidence not in diff — gates run and passed in this auto run; not a content gap
## Design Notes
Docs-only amend after App law landed; wrong overshoot/accuracy teaching is the residual agent hazard. Entry 4 owns deferred prune only.

## Verification
**Commands:**
- `rg -n '_trv_overshoot_latched|commissioned.*accuracy|accuracy.*control_event|overshoot-100|overshoot latch' docs/adr/0008-weather-curve-trv-flame-swt.md CONTEXT.md AGENTS.md knowledge/concepts/trv-soft-close.md knowledge/concepts/index.md knowledge/concepts/outdoor-temperature.md` — expected: no live-law hits (historical banners on the three decisions are out of this path set; if a hit remains it must be clearly historical wording only)
- `rg -n 'CAP-7|ff_auto_correct_state' docs/adr/0008-weather-curve-trv-flame-swt.md CONTEXT.md AGENTS.md knowledge/concepts/` — expected: only out-of-scope / avoid / historical framing, never commissioning instructions
- `uv run pytest` — expected: pass
- `uv run ruff check apps/ha_smart_hvac tests` — expected: clean

**Manual checks (if no CLI):**
- Open each of the three TRV decisions: leading banner visible before the historical title/body.
- Confirm AGENTS Verified stamp line byte-identical to baseline.

## Auto Run Result
- **Summary:** Live ADR 0008 / CONTEXT / AGENTS / knowledge now teach house-idle soft-close (floor + hold → 100); three overshoot/accuracy TRV decisions bannered historical; App/yaml untouched.
- **Files changed:**
  - `docs/adr/0008-weather-curve-trv-flame-swt.md` — house-idle TRV + Event-path accuracy scrub + plant-off parenthetical
  - `CONTEXT.md` — TRV / listeners / plant-off dialogue aligned; orphan no-op
  - `AGENTS.md` — bmad:context TRV/listeners/plant-off; orphan no-op; stamp unchanged
  - `knowledge/concepts/trv-soft-close.md` — house-idle primary page
  - `knowledge/concepts/index.md` — TRV blurb
  - `knowledge/concepts/outdoor-temperature.md` — accuracy listener scrub + timestamp
  - `knowledge/log.md` — append-only Fact
  - three `docs/decisions/adr-trv-*.md` — historical banners
  - this plan file
- **Review:** patches applied (2 medium groups + 1 low timestamp); deferred none; rejected lows/false as logged. Patched mediums: ADR plant-off parenthetical; CONTEXT/AGENTS orphan clause.
- **Follow-up review recommendation:** `true` — two medium patches on first pass. Unverified residual risk: compressed CONTEXT/AGENTS still omit cold-start/rising-edge/sustained demand enumeration (present on ADR/knowledge); agents could still under-specify demand flavors though “any Heating Demand” remains.
- **Verification:** hygiene `rg` no live overshoot/accuracy hits; CAP-7 only out-of-scope/avoid; `uv run pytest` 370 passed; `uv run ruff check apps/ha_smart_hvac tests` clean; AGENTS Verified stamp byte-identical to baseline.
- **Residual risks:** entry 4 still owns deferred dead-code/test prune; sibling `set-water-temperature.md` still says plant-off soft-close “still applies” without hold-cancel detail (not overshoot teaching).


## Code Review
### 2026-11-20
**Code review complete.** 0 `decision-needed`, 0 `patch`, 0 `defer`, 18 rejected.

#### Rejected
- R1 `false` — `set-water-temperature.md` plant-off “still applies”: outside Notes matrix / Req 4 overshoot-accuracy scope; companion link holds depth
- R2 `false` — banner markdown links: matches `adr-write-gated-supply-trip-latch` bare-ADR pattern
- R3 `false` — present-tense historical bodies: by design (banner + leave body)
- R4 `false` — ADR “no-op” vs CONTEXT parenthetical: synonymous, not different law
- R5 `low` — CONTEXT/AGENTS omit demand enum: “any Heating Demand” enough; ADR/knowledge carry flavors
- R6 `low` — CONTEXT TRV `_Avoid_` not expanded: positive prose already demotes; Avoid noise
- R7 `false` — CONTEXT omits flame-observe negative fence: positive schedule complete; not in Req 3 list
- R8 `false` — AGENTS “still applies (…)”: parenthetical states 100+cancel
- R9 `false` — Citations omit Historical subsection: intent dropped live cites, did not require re-index
- R10 `low` — log Fact unnamed paths: Fact is not a nav index
- R11 `false` — Verification rg skips banners/set-water: correct for overshoot/accuracy hygiene
- R12 `false` — followup_review_recommended / empty deferred: workflow signal, not docs defect
- R13 `false` — floor-write-fail before arm omitted: outside story SoT Req 1–7
- R14 `false` — hold-expiry write-fail re-floor omitted: same, outside SoT
- R15 `false` — claim vs write-gated arm: claims track story SoT, not App hardening
- R16 `low` — IA compressed demand (dup R5): rejected same reason
- R17 `false` — IA set-water sibling (dup R1): rejected same reason
- R18 `false` — Req 6 gates in plan not diff: expected for docs-only deliverable

### 2026-11-21 — walkthrough Intent Formal review
**Code review complete.** 0 `decision-needed`, 0 `patch`, 0 `defer`, 17 rejected.

#### Rejected
- R1 `false` — `set-water-temperature.md` plant-off “still applies”: outside Notes matrix / Req 4; companion holds depth
- R2 `false` — CONTEXT omits flame-observe negative fence: positive schedule complete; not in Req 3 (prior follow-up R7)
- R3 `low` — CONTEXT/AGENTS omit demand enum: “any Heating Demand” enough; ADR/knowledge carry flavors
- R4 `low` — CONTEXT TRV `_Avoid_` not expanded: positive prose already demotes
- R5 `low` — banner markdown links: bare-ADR pattern match
- R6 `false` — present-tense historical bodies: by design (banner + leave body)
- R7 `false` — empty Plan Change Log: scaffolding, not product defect
- R8 `false` — walkthrough Intent unchecked mid-session: correct process state
- R9 `false` — hygiene rg omits set-water: follows R1 / Notes matrix
- R10 `false` — Related drops demoted decisions: intent dropped live cites
- R11 `low` — index blurb drops plant-off cue: primary page holds detail
- R12 `false` — AGENTS “still applies (…)”: parenthetical states 100+cancel
- R13 `false` — ADR floor-write-fail before arm: outside docs SoT Req 1–7
- R14 `false` — ADR hold-expiry write-fail: outside SoT
- R15 `false` — ADR hold expiry while demand: outside SoT
- R16 `low` — IA demand-flavor split (dup R3): rejected same reason
- R17 `false` — Req 6 verify not in product diff: expected for docs-only

### 2026-11-21 — walkthrough Broad strokes Formal review
**Code review complete.** 0 `decision-needed`, 1 `patch`, 0 `defer`, 15 rejected.

- [x] [Review][Patch] Walkthrough Broad strokes relative links use four ../ (escape repo); need three [_bmad-output/initiative-weather-swt-supply-trip/walkthrough-story-7-3-docs-house-idle-soft-close/walkthrough-story-7-3-docs-house-idle-soft-close.md]

#### Rejected
- R2 `false` — set-water sibling: outside Notes matrix
- R3 `false` — house-calibration: outside story scope
- R4 `false` — ADR demotion map: banners + dropped cites suffice
- R5 `low` — banner markdown links: bare-ADR pattern
- R6 `false` — present-tense historical bodies: by design
- R7 `low` — CONTEXT `_Avoid_`: positive prose enough
- R8 `false` — Related drops demoted decisions: intent drop
- R9 `low` — log Fact unnamed paths: not a nav index
- R10 `low` — demand enum compression: any Heating Demand enough
- R11 `low` — index plant-off cue: primary page holds detail
- R12 `false` — walkthrough metadata lag: process/state nits
- R13–R15 `false` — ADR write-fail/expiry-while-heating: outside docs SoT
- R16 `false` — IA residuals: descriptive / already rejected

### 2026-11-21 — walkthrough Slice ADR Formal review
**Code review complete.** 0 `decision-needed`, 0 `patch`, 0 `defer`, 14 rejected.

#### Rejected
- R1 `false` — set-water sibling: outside Notes matrix
- R2 `low` — CONTEXT `_Avoid_`: positive prose enough
- R3 `false` — Related drops demoted decisions: intent drop
- R4 `low` — index plant-off cue: primary page holds detail
- R5 `false` — present-tense historical bodies: by design
- R6 `false` — ADR cite list no historical breadcrumb: banners are demotion surface
- R7 `false` — adr-trv-before-water-prelude overshoot provenance: prelude ordering still live; soft-close substance in ADR 0008
- R8 `low` — demand enum compression: any Heating Demand enough
- R9 `false` — later slice placeholders: correct mid-walkthrough state
- R10 `false` — empty Plan Change Log: scaffolding
- R11 `false` — Intent Problem present tense: frozen Intent paste from plan
- R12 `false` — demo CAP-7 L56: Out of scope H2 is L55; CAP-7 body is L56 (wc undercount without final newline)
- R13 `false` — Periphery open: not yet reached
- R14 `low` — banner bare ADR name: pattern match
