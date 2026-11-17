---
title: 'Tracer: ADR + AGENTS/CONTEXT for TRV+flame water law'
type: 'story'
ticket: '1'
created: '2026-11-17'
status: built
baseline_revision: '928b2b624929029016b4eee5e0d2ab072ea1f286'
route: 'full'
route_source: 'auto'
risk: 'high'
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
**Problem:** Live App already runs weather-curve SWT + TRV soft-close + flame short-on, but ADR 0007 / AGENTS / CONTEXT still teach supply rise-rate trip as live anti-cycle and omit TRV/flame.

**Approach:** Add ADR 0008 as agent-law live water law (curve + TRV soft-close + flame short-on; CAP-7 hard out), mark 0007 historical (supply-trip era), retarget live-pointers on 0004–0006 and `docs/house-calibration.md`, rewrite AGENTS.md + CONTEXT.md to match the shipped App, and mark zombie supply-trip `docs/decisions/*` historical — no `knowledge/` demotion (6.2), no runtime changes.

## Boundaries & Constraints
**Always:**
- ADR 0008 is **law for agents** (MUST-floor): weather-curve `round-to-0.1(clamp(u_ff))` with Outdoor-gated CAP-8 writer; TRV soft-close before water prelude; flame observe/latch/clear; Critical Zone diagnostics-only for SWT / TRV / flame; CAP-7 hard out — no integrator recipe, no test-matrix dump.
- Live SWT demand: Plant∧Demand∧¬`_flame_trip_latched` → `u_ff = base + slope × (comfort_ref − T_out)` then round/clamp; latched demand keeps SWT `0` (no curve / no CZ select-log). Plant-on non-demand exits → `_go_idle` write `0` + Decision C. Plant-off → `_hands_off` (no SWT write; `_clear_flame_trip_state`).
- TRV: `_apply_trv_law` before `_gate_prelude` on tick/event/hold-expiry; write only `valve_closure_degree`; never `valve_opening_degree`; plant-off → closure 100 **without** clearing `_trv_overshoot_latched`; plant-on floor / overshoot-100 hysteresis (write-gated); accuracy as `control_event` listen when commissioned; CZ never drives TRV.
- Flame MUST-floor (cite `adr-flame-*` / write-gated flame latch): short-on = `flame_on` True duration `< flame_on_min_s` on True→False fall; `_flame_observe_gate` = Plant∧Demand∧`ch_active` on∧¬latch — **never Outdoor**; latch only after successful trip write `0` **and** hold `run_in` scheduled; RAM-only latch — while latched, flame/`ch_active` observers wipe `since` only (no SWT re-assert); token orphan on hold callback (`_flame_trip_hold_token`); clear on hold expiry (`_apply_trv_law` then Outdoor prelude + demand), zone Heating Demand rising-edge under `_gate_prelude`, plant-off (`_clear_flame_trip_state`), and Decision C idle write-0 success (write-fail keeps `_flame_trip_latched`; disarm via `_disarm_flame_trip_hold` — **no** supply-sample wipe).
- Dual-gate today: Outdoor/`control_*` use `_gate_prelude`; flame observe uses flame gate (not Outdoor). No live `supply_event` / `r_obs` / `r_max` / `boiler_water` trip.
- New file `docs/adr/0008-weather-curve-trv-flame-swt.md` with 0007-style YAML `status: accepted`; supersedes 0007 for live water law.
- Mark `docs/adr/0007-*.md` `status: superseded by ADR-0008` + historical supply-trip framing + one live-pointer to 0008; keep supply-era body (no rewrite into TRV/flame) **except framing carve-out**: replace L8 live «agent law for the live App» claim with historical/superseded wording, and fix L42 so it no longer claims 0004–0006 live-pointers target this ADR (live = ADR 0008).
- Retarget live-pointer lines on `docs/adr/0004` / `0005` / `0006` and `docs/house-calibration.md` to ADR-0008; set 0005/0006 frontmatter `status: superseded by ADR-0008`; leave 0004 status `superseded by ADR-0005` (optional one-line live ADR-0008 note on 0004).
- `docs/house-calibration.md`: retarget Live water law → ADR 0008; kill «Commission Outdoor + Weather Feedforward only»; add 1–2 sentences that flame/`ch_active`/TRV yaml are required anti-cycle wiring (details in ADR 0008 / `apps.yaml.example`) and plant-off = no SWT write + clear flame latch (TRV soft-close still applies). No full commissioning recipe tables.
- Mark zombie supply decisions historical (first-paragraph banner; no body rewrite as live): `adr-supply-event-no-outdoor-prelude.md`, `adr-write-gated-supply-trip-latch.md`, `adr-trip-hold-token-orphan-guard.md`, and **`adr-idle-trip-clear-after-write.md`** (supply-era Decision C freeze — 0007 keeps citing it).
- **New** live Decision C note `docs/decisions/adr-idle-flame-clear-after-write.md` (symbols: `_flame_trip_latched`, `_disarm_flame_trip_hold`, `_clear_flame_trip_state`; cite from ADR 0008). One-line fix on `adr-trv-before-water-prelude.md` (drop stale `supply_event` clause / note flame handlers do not run `_apply_trv_law`).
- Edit AGENTS only inside `<!-- bmad:context -->` … `<!-- /bmad:context -->`; Verified = evidence `baseline_revision` `928b2b624929029016b4eee5e0d2ab072ea1f286` and date `2026-11-17` — **not** post-edit HEAD.
- Cite shipped behavior from `hvac_app.py` / `feedforward.py` / `coordinator.py` and live flame/TRV `docs/decisions/*` — do not invent runtime.
- AGENTS Conventions: **rewrite all water-law / anti-cycle / dual-gate bullets** for 0008 (curve + TRV + flame + Decision C + dual-gate Outdoor vs flame). Carry init first `control_tick`, equal-float plant readback skip, unreadable/non-finite plant skip, and Heating Demand listener coupling into those new bullets — do not preserve old paragraphs that embed `supply_event` / `_clear_trip_state`. Preserve only named non-water clauses: Exclusive Session; initiative `done` rule; never push `main`; no `.env`/`secrets.yaml` commits; ask before house entity ids.
- AGENTS knowledge line: live water law = ADR 0008 (+ CONTEXT); **`knowledge/` SWT/anti-cycle pages are not live until story 6.2 — do not follow for water law** (hard warning, not soft «may lag»).

**Never:**
- Change App runtime, tests, `apps.yaml.example`, house `apps.yaml`, or Exclusive Session / Heating Demand definition.
- Demote or rewrite `knowledge/` (story 6.2); restore CAP-7 or supply rise-rate as live law; hardcode house entity ids.
- Rewrite ADR 0001–0003 bodies; rewrite 0004 beyond live-pointer (+ optional live note); rewrite 0007 into TRV/flame (framing carve-out L8/L42 only); add full TRV/flame commissioning tables to house-calibration.
- Mark live flame/TRV decision notes historical (except token-orphan banner, TRV prelude one-liner, and the frozen supply-era idle Decision C banner).
- Author ADR via toolsmith skill — write in-story.

**Decisions:**
- ADR slug/title: `0008-weather-curve-trv-flame-swt.md` (curve + TRV + flame).
- Historical decision banner pattern: leading paragraph «Historical — supply rise-rate trip (epic 2); live anti-cycle is flame short-on + TRV soft-close (epics 4–5 / ADR 0008).» before existing prose.
- Deferred-work hygiene for stale epic-3 AGENTS/knowledge lag bullets is optional in this tracer; not required to close 6.1 ACs. Accuracy-listen AGENTS/CONTEXT inventory is in-scope (must appear in rewrite).
- Keep full plan — accept context-rot risk; no scope split.
- Idle Decision C (party hole 1 **A**): **new** `adr-idle-flame-clear-after-write.md` as live cite; freeze `adr-idle-trip-clear-after-write.md` with historical banner; 0007 continues to cite the frozen supply-era file.
- `adr-trip-hold-token-orphan-guard.md`: historical banner only; live orphan rule via flame latch/hold decisions + ADR 0008 MUST (2B).
- `adr-trv-before-water-prelude.md`: one-line update — remove stale `supply_event` clause; note flame handlers do not run `_apply_trv_law` (3A).
- Party hole fixes 2026-11-17: verify greps **A**; ADR 0008 MUST outline **A**; 0007 framing carve-out **A**; 0005/0006 status → 0008 **A**; knowledge hard-warn **A**; house-calibration +2 sentences **A**; CONTEXT term checklist **A**; AGENTS rewrite water bullets **A**.

</frozen-after-approval>

## Code Map
Evidence commit `928b2b624929029016b4eee5e0d2ab072ea1f286` (clean `main`).

- `apps/ha_smart_hvac/feedforward.py` — `weather_feedforward`, `quantize_command` (cite only).
- `apps/ha_smart_hvac/hvac_app.py` — `_gate_prelude`, `_run_demand` (flame-latched→0), `_apply_trv_law` before prelude, `_flame_observe_gate` / `flame_event`, hold expiry TRV→prelude, `_go_idle` Decision C, `_hands_off` / `_clear_flame_trip_state` (cite only).
- `apps/ha_smart_hvac/coordinator.py` — `has_heating_demand`, `select_max_error_demand_zone` diagnostics-only (cite only).
- **New** `docs/adr/0008-weather-curve-trv-flame-swt.md` — accepted agent-law ADR (gates, FF, CAP-8, TRV soft-close, flame trip latch, Idle clear Decision C, dual-gate Outdoor vs flame, CZ, CAP-7 hard out).
- `docs/adr/0007-weather-curve-supply-trip-swt.md` — `superseded by ADR-0008`; historical framing + live-pointer; supply-era body; framing carve-out L8/L42 only.
- `docs/adr/0004-weather-curve-swt.md` — live-pointer → ADR-0008; status stays `superseded by ADR-0005` (optional live note).
- `docs/adr/0005-fixed-pid-swt.md`, `0006-optional-rls-adaptive-pid.md` — live-pointer → ADR-0008; **status → `superseded by ADR-0008`**.
- `docs/house-calibration.md` — Live water law → ADR 0008; drop Outdoor+FF-only; +1–2 sentences flame/TRV required wiring + plant-off flame clear.
- `docs/decisions/adr-supply-event-no-outdoor-prelude.md`, `adr-write-gated-supply-trip-latch.md`, `adr-trip-hold-token-orphan-guard.md`, `adr-idle-trip-clear-after-write.md` — historical banner; leave body.
- **New** `docs/decisions/adr-idle-flame-clear-after-write.md` — live flame Decision C (symbols as Always).
- `docs/decisions/adr-trv-before-water-prelude.md` — one-line drop of stale `supply_event` clause.
- Live cite targets (do not mark historical): `adr-flame-observe-gate-no-outdoor.md`, `adr-flame-latch-ram-only-no-reassert.md`, `adr-flame-hold-expiry-trv-then-prelude.md`, `adr-write-gated-flame-latch.md`, `adr-trv-before-water-prelude.md`, `adr-trv-write-gated-overshoot-latch.md`, `adr-trv-plant-off-no-latch-clear.md`, `adr-trv-accuracy-shared-control-event.md`, **new** `adr-idle-flame-clear-after-write.md`, `adr-outdoor-unavailable-idle-zero.md`, `adr-cap8-shared-ff-demand-writer.md`, `adr-zone-rising-edge-decision-a.md`.
- `AGENTS.md` (`bmad:context`) — full water-law Conventions rewrite to 0008; hard `knowledge/` not-live-until-6.2 warning; CAP-7 hard out; CZ not on SWT/TRV/flame.
- `CONTEXT.md` — checklist: terms Plant Management / Critical Zone / Weather Feedforward / Multi-Zone Coordinator; demote/replace **Supply rise-rate trip**; add **TRV soft-close** + **Flame short-on trip**; accuracy listen in FF/CAP-8 inventory; rewrite dialogues that teach supply trip (incl. ~4, 6, 7).

Do not change: `knowledge/**`, `apps/ha_smart_hvac/**` runtime, tests (run only), `apps.yaml.example`, house yaml.

## Tasks & Acceptance
**Execution:**
- [ ] `docs/adr/0008-weather-curve-trv-flame-swt.md` — create accepted agent-law ADR (curve + TRV + flame; CAP-7 hard out; separate flame latch vs Decision C; MUST bullets per Always).
- [ ] `docs/adr/0007-*.md` — superseded by 0008 + historical framing + live-pointer; framing carve-out L8/L42; supply-era body otherwise.
- [ ] `docs/adr/0004-weather-curve-swt.md` / `0005-fixed-pid-swt.md` / `0006-optional-rls-adaptive-pid.md` — live-pointer → ADR-0008; 0005/0006 status → superseded by ADR-0008; 0004 status stays →0005.
- [ ] `docs/house-calibration.md` — pointer → 0008; drop Outdoor+FF-only; +1–2 anti-cycle wiring / plant-off sentences.
- [ ] Decisions — historical banner on supply-event / write-gated-supply / trip-hold-token-orphan / supply-era idle; **new** `adr-idle-flame-clear-after-write.md`; one-line TRV-prelude fix.
- [ ] `AGENTS.md` — rewrite water-law `bmad:context` bullets to 0008; hard knowledge-until-6.2 warning; Verified `928b2b624929029016b4eee5e0d2ab072ea1f286` @ `2026-11-17`.
- [ ] `CONTEXT.md` — term checklist + TRV/Flame terms + dialogues (no leftover live supply anti-cycle teaching).
- [ ] Verify — pytest + ruff; grep/spot-read guards below.

**Acceptance Criteria:**
- Given the repo after this story, when an agent reads ADR 0008, then it is the accepted agent-law live water law: Outdoor-gated clamp(u_ff); TRV soft-close before prelude; flame short-on with write∧hold latch, RAM-only/no re-assert, token orphan, separate Decision C section; CAP-7 hard out; no live supply rise-rate trip.
- Given ADR 0008 vs `hvac_app.py`, when spot-read for `_gate_prelude` / `_flame_observe_gate` / TRV-before-prelude / latch-on-successful-write∧hold / Decision C keep-latch / `_clear_flame_trip_state`, then ADR prose matches App.
- Given ADR 0007, when opened, then frontmatter `superseded by ADR-0008`, historical supply-trip framing, live-pointer to 0008; body not rewritten as TRV/flame; L8/L42 no longer claim live agent law / live-pointer target.
- Given ADR 0004–0006 and `docs/house-calibration.md`, when opened, then each live-pointer cites ADR-0008; 0005/0006 status `superseded by ADR-0008`; 0004 status still superseded by 0005; calibration does not say Outdoor+FF only and names flame/TRV as required anti-cycle wiring.
- Given AGENTS.md and CONTEXT.md, when read as domain SoT, then they describe curve + TRV soft-close (incl. accuracy listen) + flame trip clears, Critical Zone diagnostics-only for SWT/TRV/flame, CAP-7 absent, hard knowledge-not-live-until-6.2 warning, and do not teach live supply rise-rate / `supply_event` / `r_obs` as anti-cycle.
- Given zombie supply decisions in scope (incl. frozen supply-era idle), when opened, then they no longer read as live law; live Decision C is `adr-idle-flame-clear-after-write.md`.
- Given this story’s scope, when diff is inspected, then `knowledge/` and App runtime behavior are unchanged.
- Given CI-local verify, when `uv run pytest` and `uv run ruff check apps/ha_smart_hvac tests` run, then both succeed.

## Implementation Notes
- Mirror story 3.1 density: agent MUST-floor ADR, not commissioning handbook.
- ADR 0008 sections: SWT gates (incl. plant-off / idle / flame-latched demand), Feedforward law, CAP-8 listeners (+ TRV accuracy listen), TRV soft-close (never-opening; plant-off keep overshoot latch), Flame trip latch (short-on trigger; write∧hold; RAM-only; token orphan; hold expiry TRV→prelude), Idle clear (Decision C + new decision cite), dual-gate Outdoor vs flame, Out of scope (CAP-7; supply-trip historical via 0007).
- Cite live decisions: write-gated flame latch + flame observe/RAM-only/hold-expiry; TRV before-prelude / overshoot / plant-off latch / accuracy; new idle flame Decision C; do not cite supply-event, token-orphan (historical), or frozen supply-era idle as live.
- CONTEXT checklist: Plant Management, Critical Zone, Weather Feedforward (accuracy listen), Multi-Zone; demote **Supply rise-rate trip** into that glossary heading only (term + `_Avoid_` — the Verification allowlist); add **TRV soft-close**, **Flame short-on trip**; dialogues ~4/6/7 must not use supply anti-cycle terms outside that block.
- AGENTS: rewrite water-law Conventions bullets; hard knowledge warning until 6.2.

## Plan Change Log
- 2026-11-17 human: Keep full plan; OQ 1A (rewrite idle Decision C for flame), 2B (historical token-orphan), 3A (TRV prelude one-liner).
- 2026-11-17 party hole-hunt (code-review-crew): (1) idle Decision C → new live flame file + freeze supply-era idle; (2) broadened anti-cycle verify + allowlist; pointer `ADR-0008|ADR 0008`; (3) expand 0008 MUST outline; (4) 0007 L8/L42 framing carve-out; (5) 0005/0006 status → 0008; (6) AGENTS hard knowledge-until-6.2; (7) house-calibration +2 sentences; (8) CONTEXT term checklist; (9) AGENTS full water-law bullet rewrite.
- 2026-11-17 review-plan: CONTEXT supply-term allowlist defined; enumerate flame/TRV live cites + write-gated flame latch; ADR 0008 token-orphan rg; task paths use full 0004/0005/0006 filenames. Rejected false L8/L42 drift; declined optional I/O matrix.

## Review Triage Log
| lens | finding | verdict | route | evidence |
| --- | --- | --- | --- | --- |
| blind-hunter | ADR 0008 missing YAML `status: accepted` | high | patch | File starts with `#` heading; Intent Always requires 0007-style `status: accepted`; peers 0004–0007 have YAML status. |
| edge-case-hunter | ADR 0008 missing `status: accepted` (claim) | high | patch | Same defect as blind-hunter status finding. |
| intent-alignment | R3 peer-ADR accepted corpus unmet | high | patch | Diff implements R1+R2 but omits YAML status on 0008; Intent Always names it. |
| blind-hunter | ADR 0008 no trailing newline | low | reject | EOF lacks `
`; unlikely everyday harm for markdown ADR. |
| blind-hunter | Live docs omit `flame_trip_hold_s` name | low | reject | Intent MUST-floor requires hold `run_in` scheduled, not the yaml key; `flame_on_min_s` is the named threshold. |
| blind-hunter | house-calibration points entity/nest details at ADR 0008 | medium | patch | Intro says details in ADR 0008 / apps.yaml.example, but ADR is MUST-floor with no nests — overclaim vs shipped ADR body. |
| edge-case-hunter | Reader seeks entity nests in ADR 0008 | medium | patch | Same root as calibration overclaim. |
| blind-hunter | ADR 0008 omits flame_on/ch_active listen_state inventory | false | reject | CAP-8 inventories Outdoor shared writer; flame handlers are named (`flame_event` / `ch_active_event`); Intent forbids integrator recipe dump. |
| blind-hunter | Rising-edge clear lacks cite to adr-zone-rising-edge-decision-a | medium | patch | Clear bullet names rising-edge only; Code Map lists that decision as live cite; runtime uses `_clear_flame_trip_state`. |
| edge-case-hunter | Rising-edge clear may leave hold/token if only latch cleared | medium | patch | ADR rising-edge bullet omits `_clear_flame_trip_state`; code at `_gate_prelude` calls that helper (disarm+clear). |
| blind-hunter | CONTEXT Plant Management omits overshoot-latch retention | low | reject | Retention rule already lives under CONTEXT **TRV soft-close**; unlikely miss in everyday agent use. |
| blind-hunter | CONTEXT Weather Feedforward omits TRV-before-prelude | false | reject | Ordering is stated under **TRV soft-close** and dialogues; FF term is not wrong. |
| blind-hunter | Plan Execution tasks still `- [ ]` | false | reject | Fix would edit this build's plan; frozen/process artifact, not agent-law SoT. |
| blind-hunter | house-calibration §1 table still Outdoor/plant/zones only; plant-off wording | medium | defer | §1 table pre-existed; Intent Never forbids full TRV/flame commissioning tables; intro sentences were the in-scope fix. |
| edge-case-hunter | Non-binary flame edges undocumented | low | reject | Runtime wipes since; Intent MUST-floor + no test-matrix dump — not everyday agent-law miss. |
| edge-case-hunter | True→False with since None undocumented | low | reject | Same MUST-floor brevity; code returns without latch. |
| edge-case-hunter | adr-trv-before-water-prelude omits hold-expiry TRV caller | medium | patch | After 3A edit, note lists tick/event only; ADR/AGENTS say hold expiry also runs `_apply_trv_law` — decision note now understates callers. |
| verification-gap | (none) | false | reject | Docs-only screen; no gaps filed. |

## Code Review

### 2026-11-17 (walkthrough Formal review)
0 decision-needed, 6 patch, 0 defer, 12 rejected.

- [x] [Review][Patch] AGENTS/CONTEXT rising-edge clear omits `_clear_flame_trip_state` (hold disarm) [AGENTS.md:36; CONTEXT.md:66]
- [x] [Review][Patch] AGENTS/CONTEXT hold expiry omits prelude-None / zones guard before demand [AGENTS.md:36; CONTEXT.md:66]
- [x] [Review][Patch] house-calibration L1 still defines Outdoor+FF+plant-only calibration [docs/house-calibration.md:1]
- [x] [Review][Patch] ADR 0008 opening cite inventory omits zone-rising-edge decision [docs/adr/0008-weather-curve-trv-flame-swt.md:3]
- [x] [Review][Patch] Historical idle-trip note lacks forward link to live Decision C [docs/decisions/adr-idle-trip-clear-after-write.md:1]
- [x] [Review][Patch] adr-trv-before-water-prelude title understates hold-expiry caller [docs/decisions/adr-trv-before-water-prelude.md:1]

Rejected:
- R3 ADR 0008 trailing newline — low; rarely visible, prior triage same class
- R5/R18 house-calibration §1 flame/TRV table — Intent Never forbids full TRV/flame commissioning tables; prior defer
- R7 present-tense zombie bodies — false; intentional historical-banner pattern
- R8 ADR 0007 cites hvac_app for era — false; historical framing + live-pointer present
- R9 plan tasks unchecked — false; process artifact
- R10 walkthrough incomplete — false; review-process untracked artifact
- R11 CONTEXT omits RAM-only — low; ADR/AGENTS are MUST-floor
- R17 Verify pytest not in diff — false; docs-only by design
