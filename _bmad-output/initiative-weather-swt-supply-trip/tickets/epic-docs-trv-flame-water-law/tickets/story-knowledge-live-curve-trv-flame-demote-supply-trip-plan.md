---
title: 'knowledge/: live curve+TRV+flame; demote supply-trip'
type: 'feature'
ticket: '2'
created: '2026-11-17'
status: built
baseline_revision: 'c85eeee243caff6cf21d66c20a7653a1332b40f9'
route: 'full'
route_source: 'auto'
risk: 'medium'
review: 'thorough'
review_source: 'auto'
lenses_ran: ['blind-hunter', 'edge-case-hunter', 'verification-gap', 'intent-alignment']
review_loop_iteration: 0
context:
  - '{project-root}/CONTEXT.md'
  - '{project-root}/AGENTS.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent
**Problem:** ADR 0008 + AGENTS/CONTEXT already teach weather-curve SWT + TRV soft-close + flame short-on, but `knowledge/` still teaches ADR 0007 + supply rise-rate trip as live anti-cycle and has no TRV/flame concept depth.

**Approach:** Rewrite live SWT-facing knowledge to ADR 0008 (`clamp(u_ff)` + dual-gate); add companion concept pages for TRV soft-close and flame short-on; demote supply-trip to a one-line ADR 0007 historical fence; retarget ADRC/LADRC/MADRC/RLS live-pointers and indexes; append `knowledge/log`; clear the AGENTS knowledge-until-6.2 warning. Docs-only — no CAP-7 restore, no runtime.

## Boundaries & Constraints
**Always:**
- Live knowledge matches ADR 0008 / App: Outdoor-gated `round-to-0.1(clamp(u_ff))` with `u_ff = base + slope × (comfort_ref − T_out)`; dual-gate Outdoor/`control_*` vs `_flame_observe_gate` (never Outdoor); TRV soft-close before water prelude (write only `valve_closure_degree`; plant-off closure 100 without clearing `_trv_overshoot_latched`; accuracy as `control_event` when commissioned); flame short-on trip (latch after successful SWT `0` ∧ hold scheduled; RAM-only / no re-assert; clear on hold expiry TRV→prelude, zone rising-edge, plant-off `_clear_flame_trip_state`, Decision C idle write-0 success); Critical Zone diagnostics-only for SWT / TRV / flame; CAP-7 / `ff_auto_correct_state.json` hard out.
- Demote supply rise-rate trip as live anti-cycle (do **not** reintroduce `supply_event` / `r_obs` / `r_max` / `_clear_trip_state` into live knowledge prose). Cite ADR 0008 as live; ADR 0007 as historical supply-trip era; ADR 0004–0006 remain historical prior art.
- Reuse story 3.2 demotion pattern: `## Project note` / **removed — superseded by ADR 0008**; `tags: […, historical]` only when demoting a whole page; append-only `knowledge/log.md`; bump concept timestamps on edit; cite ADR 0008 + live flame/TRV decisions — do not invent runtime.
- **Decision (1A):** New companion pages `knowledge/concepts/trv-soft-close.md` + `flame-short-on-trip.md` (must-floor depth; cite live decisions). **Required links:** SWT + both indexes point to both companions. CZ / multi-zone: diagnostics fence naming TRV + flame (companion path links optional).
- **Decision (2A):** In `AGENTS.md` `bmad:context` only — rewrite the knowledge line so live water law = ADR 0008 + CONTEXT + `knowledge/` (drop «not live until story 6.2»). Do not rewrite other AGENTS water-law Conventions; do not bump the Verified stamp.
- **Decision (3A):** On SWT, replace the live supply section with pointers to TRV/flame companions; one historical sentence pointing at ADR 0007 supply rise-rate trip (no extracted supply page; no multi-paragraph supply mechanics; no supply-era symbols).
- Verify includes `uv run pytest` and `uv run ruff check apps/ha_smart_hvac tests` (hygiene) plus greps/spot-reads below.

**Never:**
- Change App runtime, tests, `apps.yaml` / example / house yaml, Exclusive Session, Heating Demand definition.
- Rewrite ADR bodies, CONTEXT.md dialogues, or AGENTS water-law Conventions beyond the single knowledge-line clear (2A).
- Restore CAP-7 or teach supply rise-rate as live anti-cycle; write `valve_opening_degree`; Outdoor-gate flame observe; paste full ADR/test-matrix into knowledge.
- Edit `knowledge/playbooks/**`, `knowledge/raw/**`, or literature-only bodies without live-law claims (`zone.md`, `zone-error.md`, `extended-state-observer.md`, `total-disturbance.md`, `plant.md` body).
- Create a hybrid anti-cycle umbrella page or fold TRV/flame must-floor solely into SWT (1A chosen).

## I/O & Edge-Case Matrix
| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| Happy SWT | Open `set-water-temperature.md` | Live = clamp(u_ff) + dual-gate under ADR 0008; short pointers to TRV + flame pages; one-line ADR 0007 historical fence; no live supply trip / PID; no supply-era symbols | — |
| TRV companion (1A) | Open `trv-soft-close.md` | Must-floor soft-close (before prelude; closure-only; plant-off keep overshoot latch; accuracy listen); cite live TRV decisions + ADR 0008 | — |
| Flame companion (1A) | Open `flame-short-on-trip.md` | Must-floor short-on latch/clear (observe gate; write∧hold; RAM-only; Decision C); cite live flame decisions + ADR 0008 | — |
| Outdoor | Open `outdoor-temperature.md` | Outdoor on demand / `control_event`; cite 0008; explicit not-flame-observe fence | — |
| CZ / multi-zone | Open those pages | Diagnostics-only for SWT/TRV/flame; supersede → 0008; companion links optional | — |
| Supply demotion (3A) | Grep live pages | No supply-era symbols; no live supply teaching; SWT ≤1 historical ADR 0007 sentence | — |
| ADRC family / RLS | Open project notes | Live pointer → ADR 0008 curve+TRV+flame; literature kept | — |
| Indexes + log | Open indexes / `log.md` | Live = 0008; TRV/flame rows + paths; new append Fact; old Facts untouched | — |
| AGENTS (2A) | Read knowledge line | Live = ADR 0008 + CONTEXT + knowledge; no «until story 6.2»; Verified stamp unchanged | — |
| CAP-7 | Grep touched live pages | Hard-out on SWT (and any other touched live page that mentions it) | — |
| Out of scope | Diff apps/, tests/, adr/ | Untouched; AGENTS only knowledge line | — |

</frozen-after-approval>

## Code Map
Evidence commit `c85eeee243caff6cf21d66c20a7653a1332b40f9` (`main` after 6.1 / PR #157). Continuity from ticket `after: [1]` plan `story-tracer-adr-agents-context-for-trv-flame-water-law-plan.md` (knowledge deferred; AGENTS hard-warn until 6.2). Pattern from story 3.2 plan `story-knowledge-live-curve-trip-demote-pid-rls-plan.md`.

- `docs/adr/0008-weather-curve-trv-flame-swt.md` — SoT live water law (cite only; do not edit).
- Live decision cites (do not edit): `docs/decisions/adr-flame-observe-gate-no-outdoor.md`, `adr-write-gated-flame-latch.md`, `adr-flame-latch-ram-only-no-reassert.md`, `adr-flame-hold-expiry-trv-then-prelude.md`, `adr-zone-rising-edge-decision-a.md`, `adr-idle-flame-clear-after-write.md`, `adr-trv-before-water-prelude.md`, `adr-trv-write-gated-overshoot-latch.md`, `adr-trv-plant-off-no-latch-clear.md`, `adr-trv-accuracy-shared-control-event.md`, `adr-cap8-shared-ff-demand-writer.md`, `adr-outdoor-unavailable-idle-zero.md`.
- `AGENTS.md` — **2A:** clear knowledge-until-6.2 warning inside `bmad:context` only (knowledge bullet); leave Verified stamp as-is.
- `CONTEXT.md` — glossary already has TRV soft-close / Flame short-on / Supply rise-rate Avoid (cite; do not rewrite dialogues).
- `knowledge/concepts/set-water-temperature.md` — **rewrite** frontmatter+body+citations: ADR 0008 curve + dual-gate; **required** short pointers to TRV/flame companions; **3A** one-line ADR 0007 historical fence (no supply-era symbols); CAP-7 hard out.
- **New** `knowledge/concepts/trv-soft-close.md` — **1A** must-floor TRV soft-close; cite ≥1 `docs/decisions/adr-trv-*` + ADR 0008; link SWT.
- **New** `knowledge/concepts/flame-short-on-trip.md` — **1A** must-floor flame short-on; cite ≥1 `docs/decisions/adr-flame-*` (and idle-flame Decision C as needed) + ADR 0008; link SWT.
- `knowledge/concepts/outdoor-temperature.md` — retarget cite/desc 0007→0008; Outdoor on demand path; explicit fence that Outdoor is not an input to `_flame_observe_gate`.
- `knowledge/concepts/critical-zone.md`, `multi-zone-coordinator.md` — diagnostics-only for SWT/TRV/flame; supersede/cite → 0008; companion path links optional.
- `knowledge/concepts/rls-adaptive-pid.md`, `adrc.md`, `ladrc.md`, `madrc.md` — retarget Project-note / live-pointers **0007 → 0008** (curve+TRV+flame); keep literature/historical bodies; RLS stays `historical`.
- `knowledge/references/huang-2018-ladrc-hvac.md`, `wang-2026-madrc-sst.md` — one-line project-fit live-law → ADR 0008.
- `knowledge/concepts/index.md`, `knowledge/index.md` — live blurb ADR 0008; SWT/Outdoor/CZ/coordinator cells; **required rows + paths** for TRV soft-close + flame short-on; no live supply teaching.
- `knowledge/log.md` — **append** dated align entry; do not edit old Facts.
- Do not change: `playbooks/**`, `raw/**`, `decisions/index.md` (empty), `references/index.md`, literature-only concept bodies without live claims.

## Tasks & Acceptance
**Execution:**
- [ ] `knowledge/concepts/trv-soft-close.md` — **create** must-floor TRV soft-close page (1A); cite live TRV decisions + ADR 0008.
- [ ] `knowledge/concepts/flame-short-on-trip.md` — **create** must-floor flame short-on page (1A); cite live flame decisions + ADR 0008.
- [ ] `knowledge/concepts/set-water-temperature.md` — rewrite to ADR 0008 curve + dual-gate; **required** pointers to companions; **3A** one-line ADR 0007 fence; CAP-7 hard out; no supply-era symbols.
- [ ] `knowledge/concepts/outdoor-temperature.md` — Outdoor on path; cite ADR 0008; not-flame-observe fence.
- [ ] `knowledge/concepts/critical-zone.md` + `multi-zone-coordinator.md` — CZ fence includes TRV/flame; live cite 0008 (companion links optional).
- [ ] `rls-adaptive-pid.md` + `adrc.md` + `ladrc.md` + `madrc.md` — live-pointers → ADR 0008.
- [ ] Huang/Wang project-fit one-liners → ADR 0008.
- [ ] `knowledge/concepts/index.md` + `knowledge/index.md` — live = 0008; **required** TRV/flame rows/paths; no live supply blurbs.
- [ ] `knowledge/log.md` — append align entry (include new companions + AGENTS clear).
- [ ] `AGENTS.md` — **2A** clear knowledge-until-6.2 warning in `bmad:context` (Verified stamp unchanged).
- [ ] Verify — pytest + ruff + greps + spot-reads.

**Acceptance Criteria:**
- Given `set-water-temperature.md`, when opened, then it cites ADR 0008, states `clamp(u_ff)` and dual-gate, links both TRV and flame companions, and has at most one ADR 0007 historical supply sentence (no supply-era symbols; no live supply anti-cycle).
- Given `trv-soft-close.md` and `flame-short-on-trip.md`, when read, then each carries the must-floor clauses listed in Implementation Notes and cites ADR 0008 plus matching live `docs/decisions/` paths.
- Given `outdoor-temperature.md`, when read, then Outdoor is on the demand path / `control_event` under ADR 0008 and an explicit fence states it is not required for flame observe.
- Given `critical-zone.md` and `multi-zone-coordinator.md`, when read, then CZ is diagnostics-only for SWT, TRV soft-close, and flame trip; live cite ADR 0008.
- Given ADRC/LADRC/MADRC/RLS project notes and Huang/Wang fit lines, when read, then live pointers name ADR 0008 (not live under ADR 0007).
- Given indexes + `log.md`, when read, then live water path is ADR 0008; TRV/flame concept rows/paths exist; a new append entry records this align; prior Facts unchanged; indexes do not teach live supply rise-rate trip.
- Given CAP-7 / `ff_auto_correct_state.json`, when grepped in touched live pages, then only hard-out / absent language appears.
- Given `AGENTS.md` `bmad:context`, when the knowledge line is read, then it names ADR 0008 + CONTEXT + knowledge as live and does not say «not live until story 6.2»; Verified stamp unchanged.
- Given this story’s scope, when diff is inspected, then apps/, tests/, and ADR bodies are unchanged; AGENTS changes are confined to the knowledge line.
- Given CI-local verify, when `uv run pytest` and `uv run ruff check apps/ha_smart_hvac tests` run, then both succeed.

## Implementation Notes
- Knowledge density = ADR/CONTEXT must-floor, not commissioning handbook / test matrix.
- **TRV companion MUST outline:** before `_gate_prelude` / water prelude; write only `valve_closure_degree` (never opening); plant-off closure 100 without clearing `_trv_overshoot_latched`; plant-on floor / overshoot-100 write-gated; accuracy as `control_event` when commissioned; flame handlers do not run `_apply_trv_law`; CZ never drives TRV. Cite ≥1 of `adr-trv-before-water-prelude`, `adr-trv-write-gated-overshoot-latch`, `adr-trv-plant-off-no-latch-clear`, `adr-trv-accuracy-shared-control-event`.
- **Flame companion MUST outline:** short-on = `flame_on` True duration `< flame_on_min_s` on True→False; `_flame_observe_gate` = Plant∧Demand∧`ch_active`∧¬latch — never Outdoor; latch only after successful SWT `0` ∧ hold `run_in`; RAM-only / no SWT re-assert while latched; clear on hold expiry (TRV→prelude), zone rising-edge, plant-off `_clear_flame_trip_state`, Decision C idle write-0 success (fail keeps latch). Cite ≥1 of `adr-flame-observe-gate-no-outdoor`, `adr-write-gated-flame-latch`, `adr-flame-latch-ram-only-no-reassert`, `adr-flame-hold-expiry-trv-then-prelude`, plus `adr-idle-flame-clear-after-write` for Decision C.
- SWT stays the curve/dual-gate hub; anti-cycle depth lives on the two companions (1A); supply is one historical sentence (3A) without supply-era symbols.
- Retarget every live «ADR 0007» / «supply rise-rate trip» claim under `knowledge/` that still reads as current law; leave append-only historical log Facts alone.
- Timestamps: bump edited concept frontmatter to build date; set new companions’ timestamps to build date.
- Companions (Huang/Wang): only project-fit / live-pointer sentences.
- pytest/ruff are hygiene only; story completion blocked on Verification greps + spot-reads.
- Stale deferred-work «AGENTS may lag until 3.2» remains 6.3 hygiene; clearing the 6.2 warning is in-scope via 2A. Ticket 6.2 text is knowledge-scoped; 2A is plan-owned (6.1 deferred the clear) — do not edit ticket files.

## Plan Change Log
- 2026-11-17: Initial draft from ticket 6.2 + knowledge audit + 3.2 pattern + ADR 0008 MUST-floor; route full (medium risk; 10+ prose files; OQ page structure). Open Questions: TRV/flame structure, AGENTS warning, supply demotion depth.
- 2026-11-17: Human Keep full plan (~2300+ tokens); decisions 1A companions, 2A clear AGENTS warning, 3A one-line supply fence; Open Questions cleared.
- 2026-11-17: Plan review apply — companion MUST outlines + proveable greps; SWT content greps; ADRC positive 0008 / drop bare supply-phrase negative; index supply negatives; Outdoor flame-fence grep; AGENTS positive tighten; Always demote without supply symbols; companion links required only on SWT+indexes; reject ticket-file amend for 2A.

## Review Triage Log
| lens | finding | verdict | route | evidence |
| --- | --- | --- | --- | --- |
| intent-alignment | Companion must-floor ACs not proveable | high | fixed | MUST outlines + clause/decision greps |
| intent-alignment | SWT clamp/dual-gate only spot-read | high | fixed | Positive SWT content greps |
| intent-alignment | Ticket omits AGENTS 2A | medium | reject | Never write ticket files; 2A plan-owned from 6.1 deferral |
| intent-alignment | Companion link scope inconsistent | medium | fixed | Required SWT+indexes; CZ optional |
| intent-alignment | Always listed supply-era symbols | medium | fixed | Demote law; forbid reintroducing symbols |
| intent-alignment | Indexes can keep live supply prose | medium | fixed | Negative greps on both indexes |
| verification-gap | ADRC bare `supply rise-rate trip` over-blocks | high | fixed | Drop bare phrase; + positive ADR 0008 |
| verification-gap | Outdoor ≠ flame gate untested | medium | fixed | Fence grep on outdoor page |
| verification-gap | AGENTS `rg knowledge/` too broad | medium | fixed | Tighten positive assert |
| verification-gap | Index/log/diff mechanical checks weak | medium | fixed | Path greps + log/diff commands |
| edge-case | Missed knowledge files outside Code Map | false | — | Audit: none |
| edge-case | 2A requires Verified bump | false | — | Explicitly leave stamp |

| blind-hunter | New-file hunks not proper git apply format | false | — | Diff_file staging artifact for lenses; product files exist on disk |
| blind-hunter | Flame page omits `_flame_trip_hold_token` orphan guard | false | — | Frozen Always / flame MUST outline intentionally omit ADR paste; density rule |
| blind-hunter | Zone rising-edge clear lacks Decision A semantics / cite | false | — | Plan MUST is rising-edge clear one-liner; Decision A depth stays in decision doc |
| blind-hunter | Decision C omits `_disarm_flame_trip_hold` + every Plant-on exit | false | — | Page states disarm + write-gated clear; ADR paste of exit list out of must-floor |
| blind-hunter | Companions lack Avoid guidance | low | reject | Unlikely everyday harm; peers vary; not required by plan |
| blind-hunter | Multi-zone ownership sentence omits TRV (index includes it) | low | patch | Body L11 owns SWT+flame only; diagnostics already fences TRV — align ownership clause |
| blind-hunter | SWT hub missing ## Related | false | — | Companion paths already in body prose; Citations list ADRs |
| blind-hunter | Outdoor Related adds flame but not TRV | low | reject | Navigation nicety; accuracy/TRV already on SWT/TRV pages |
| blind-hunter | Huang/Wang timestamps not bumped | false | — | Plan bumps concept timestamps; refs are one-line project-fit only |
| blind-hunter | Flame latched-demand omits CZ select-log | medium | patch | Always/SWT teach no curve / no CZ select-log; flame L19 says no curve only |
| edge-case-hunter | Orphan hold token not documented | false | — | Same as token-orphan MUST omission; App guard exists, knowledge density excludes |
| edge-case-hunter | True→False with since unset not documented | false | — | App edge; not in companion MUST outline / no test-matrix dump |
| edge-case-hunter | Non-binary flame edges not documented | false | — | App edge; not in companion MUST outline |
| verification-gap | (none — docs-only static skip) | — | — | Lens reported no gaps |
| intent-alignment | Fence form vs dedicated one-line artifact | false | — | Decision 3A = embedded SWT historical sentence; matches chosen reading |

## Design Notes
- Mirror story 3.2 slices: Live SWT + new companions → Historical demotions (0007→0008 pointers) → Indexes + log → AGENTS knowledge line.
- Do not re-demote PID/RLS as if still live; only retarget their live-pointer from 0007 supply-trip wording to 0008.
- After 2A, knowledge becomes a follow surface for agents — prefer must-floor accuracy over encyclopedic depth.

## Verification
**Commands:**
- `uv run pytest` — expected: pass
- `uv run ruff check apps/ha_smart_hvac tests` — expected: pass
- `test -f knowledge/concepts/trv-soft-close.md && test -f knowledge/concepts/flame-short-on-trip.md` — expected: both exist
- `rg -n 'ADR 0008|ADR-0008' knowledge/concepts/set-water-temperature.md knowledge/concepts/outdoor-temperature.md knowledge/concepts/critical-zone.md knowledge/concepts/multi-zone-coordinator.md knowledge/concepts/trv-soft-close.md knowledge/concepts/flame-short-on-trip.md knowledge/index.md knowledge/concepts/index.md` — expected: hits on each
- `rg -n 'clamp\(u_ff\)' knowledge/concepts/set-water-temperature.md` — expected: hit
- `rg -n 'dual-gate|_gate_prelude|_flame_observe_gate' knowledge/concepts/set-water-temperature.md` — expected: dual-gate named (both gates or equivalent)
- `rg -n 'trv-soft-close|flame-short-on-trip' knowledge/concepts/set-water-temperature.md knowledge/index.md knowledge/concepts/index.md` — expected: both companion paths on each of these three files
- `rg -n 'valve_closure_degree|_apply_trv_law|before.*prelude|_trv_overshoot_latched|accuracy' knowledge/concepts/trv-soft-close.md` — expected: must-floor TRV clauses present
- `rg -n 'docs/decisions/adr-trv-' knowledge/concepts/trv-soft-close.md` — expected: ≥1 cite
- `rg -n '_flame_observe_gate|flame_on_min_s|_flame_trip_latched|RAM-only|Decision C|idle' knowledge/concepts/flame-short-on-trip.md` — expected: must-floor flame clauses present
- `rg -n 'docs/decisions/adr-flame-|adr-idle-flame-clear-after-write|adr-write-gated-flame-latch' knowledge/concepts/flame-short-on-trip.md` — expected: ≥1 live flame/Decision-C cite
- `rg -n '_flame_observe_gate|not.*flame observe|never Outdoor' knowledge/concepts/outdoor-temperature.md` — expected: non-empty not-flame-observe fence
- `rg -n 'diagnostics-only|must not drive' knowledge/concepts/critical-zone.md knowledge/concepts/multi-zone-coordinator.md` — expected: hits; pages also name TRV and flame
- `rg -n 'TRV|flame' knowledge/concepts/critical-zone.md knowledge/concepts/multi-zone-coordinator.md` — expected: both concepts fenced on each page
- `rg -n 'ADR 0008|ADR-0008' knowledge/concepts/adrc.md knowledge/concepts/ladrc.md knowledge/concepts/madrc.md knowledge/concepts/rls-adaptive-pid.md knowledge/references/huang-2018-ladrc-hvac.md knowledge/references/wang-2026-madrc-sst.md` — expected: hits on each
- `rg -n 'superseded by ADR 0007|live.*ADR 0007' knowledge/concepts/adrc.md knowledge/concepts/ladrc.md knowledge/concepts/madrc.md knowledge/concepts/rls-adaptive-pid.md knowledge/references/huang-2018-ladrc-hvac.md knowledge/references/wang-2026-madrc-sst.md` — expected: no leftover live-under-0007 pointers
- `rg -n 'supply_event|r_obs|r_max|_clear_trip_state' knowledge/concepts/set-water-temperature.md knowledge/concepts/outdoor-temperature.md knowledge/concepts/critical-zone.md knowledge/concepts/multi-zone-coordinator.md knowledge/concepts/trv-soft-close.md knowledge/concepts/flame-short-on-trip.md knowledge/index.md knowledge/concepts/index.md` — expected: absent
- `rg -n 'live.*supply rise-rate|supply rise-rate trip' knowledge/index.md knowledge/concepts/index.md` — expected: absent (historical one-liner allowed only on SWT)
- `rg -n 'CAP-7|ff_auto_correct_state' knowledge/concepts/set-water-temperature.md knowledge/concepts/critical-zone.md knowledge/concepts/multi-zone-coordinator.md` — expected: hard-out / absent / historical-removed only
- `rg -n 'not live until story 6\.2' AGENTS.md` — expected: absent
- `rg -n 'ADR 0008.*CONTEXT|CONTEXT.*knowledge' AGENTS.md` — expected: knowledge line names ADR 0008 + CONTEXT + knowledge as live
- `rg -n '^## 2026-11-17' knowledge/log.md` — expected: new append section present
- `git diff --name-only` — expected: no `apps/` / `tests/` / `docs/adr/` paths; AGENTS only if knowledge-line change
- `git diff AGENTS.md` — expected: knowledge bullet only; Verified stamp line unchanged

**Manual checks:**
- Spot-read SWT + both companions against Implementation Notes MUST outlines (judgment only for prose quality beyond greps).
- Spot-read `knowledge/log.md` top entry: Updated path list (incl. new companions) + Fact naming 0008 + demoted supply-trip; older Facts unchanged (`git diff knowledge/log.md` shows append-only).
