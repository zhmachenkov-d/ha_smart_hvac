---
title: 'Tracer: ADR 0007 + AGENTS/CONTEXT'
type: 'feature'
ticket: '1'
created: '2026-11-14'
status: built
baseline_revision: '5416a81e2afdf15dd586534cf86c5fa92f092080'
route: 'full'
route_source: 'auto'
risk: 'high'
review: 'thorough'
review_source: 'auto'
context:
  - _bmad-output/initiative-weather-swt-supply-trip/tickets/epic-supersede-pid-domain-docs/epic-supersede-pid-domain-docs.md
  - docs/decisions/adr-supply-event-no-outdoor-prelude.md
  - docs/decisions/adr-idle-trip-clear-after-write.md
lenses_ran: ['blind-hunter', 'edge-case-hunter', 'verification-gap', 'intent-alignment']
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent
**Problem:** Live App already runs weather-curve SWT + supply rise-rate trip, but ADR 0005/0006 and AGENTS/CONTEXT still teach fixed PID / RLS as the water law.

**Approach:** Add ADR 0007 as the **agent-law** live water law (curve + trip; CAP-7 hard out), mark 0005/0006 superseded with live-pointers, leave 0004 historical (`superseded by ADR-0005`) plus one live-pointer to 0007, rewrite AGENTS.md + CONTEXT.md to match the shipped App — no knowledge demotion, no dead-module deletes (3.2 / 3.3).

## Boundaries & Constraints
**Always:**
- ADR 0007 is **law for agents** (not a boiler-operator handbook): MUST-floor = `clamp(u_ff)` / Outdoor on `control_event` / dual-gate / trip latch-after-successful-write `0` / Decision C / CZ not on SWT / CAP-7 hard out — no integrator recipe, no test-matrix dump.
- ADR 0007 states live law: Plant∧Demand → `round-to-0.1(clamp(u_ff))` with `u_ff = base + slope × (comfort_ref − T_out)`; Outdoor is a `control_event` listener; CAP-8 shared writer on tick + events.
- Supply trip: `r_obs` °C/min vs `r_max`; latch only after successful trip write `0`; latched demand keeps `0`; clear on hold expiry, zone rising-edge under `_gate_prelude`, and on `_go_idle` after successful idle `0` (Decision C); plant-off via `_clear_trip_state` (no write).
- **Decision C / `_go_idle`:** covers every Plant-on non-demand exit — no Heating Demand, unavailable Outdoor, no valid zones, non-finite `u_ff`. Always disarm hold + wipe samples; clear latch only after successful idle write `0` (write-fail keeps latch). Empty zone reads leave `_zone_heating_prior` unchanged.
- In ADR 0007, document trip latch and Decision C as **two explicit sections** (do not merge into one paragraph).
- Dual-gate: Outdoor/`control_*` use `_gate_prelude` (Plant + readable Outdoor + zones + demand); `supply_event` uses `_plant_and_heating_demand` only (never Outdoor prelude).
- Critical Zone diagnostics/logging only — not SWT or trip.
- CAP-7 / adapting base/slope / `ff_auto_correct_state.json`: **not on water path; do not commission; out of ADR 0007 scope** — no deferred/later/optional-later soft language.
- No live PID/∫/RLS / `rls_state.json` / sticky gated-demand prose in AGENTS or CONTEXT.
- Mark `docs/adr/0005-*.md` and `0006-*.md` frontmatter `status: superseded by ADR-0007` **and** one live-pointer line each («live water law: ADR-0007»); bodies otherwise unchanged.
- Leave `docs/adr/0004-*.md` status `superseded by ADR-0005` (historical; frontmatter already present) **and** add one live-pointer line to ADR-0007; do not rewrite the 0004 body beyond that pointer.
- Edit AGENTS only inside `<!-- bmad:context -->` … `<!-- /bmad:context -->`; set Verified comment to evidence `baseline_revision` `5416a81e2afdf15dd586534cf86c5fa92f092080` and date `2026-11-14` — **not** post-edit / post-commit HEAD (self-referential SHA).
- Cite shipped behavior from `hvac_app.py` / `feedforward.py` and decision notes `docs/decisions/adr-supply-event-no-outdoor-prelude.md`, `docs/decisions/adr-idle-trip-clear-after-write.md` — do not invent new runtime.

**Never:**
- Change App runtime, tests, `apps.yaml.example`, house yaml, or Exclusive Session / Heating Demand definition.
- Demote or rewrite `knowledge/` (story 3.2); delete `pid.py`/`rls.py` (story 3.3).
- Restore CAP-7; reintroduce `base_water_temp + u_pid` as live law; hardcode house entity ids.
- Rewrite ADR 0001–0003 bodies; rewrite ADR 0004 beyond the single live-pointer line; rewrite 0005/0006 beyond status + one live-pointer; do not change `docs/decisions/*` contents (0007 may reference them).

## I/O & Edge-Case Matrix
| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| Happy docs | Reader opens ADR 0007 / AGENTS / CONTEXT | One water law: clamp(u_ff) + supply trip; dual-gate; CZ diagnostics | — |
| Supersede chain | Open 0005 / 0006 | Frontmatter `superseded by ADR-0007` + one live-pointer line each | — |
| Historical 0004 | Open 0004 | Status still `superseded by ADR-0005`; one live-pointer to 0007; body not rewritten as live | — |
| CAP-7 language | Grep / read live docs | Hard out: not on water path; do not commission; out of scope — never deferred/later soft | — |
| PID/RLS live | Grep AGENTS/CONTEXT | No live PID/∫/RLS/`rls_state.json` / sticky / «Outdoor not a control listener» claims | — |
| Latch sections | Open ADR 0007 | Separate trip-latch vs Decision C idle sections | — |
| `_go_idle` exits | ADR / AGENTS / CONTEXT | Decision C applies to all Plant-on non-demand exits (not demand-idle alone) | — |
| Out of scope | knowledge/, pid.py | Untouched | — |

</frozen-after-approval>

## Code Map
Evidence commit `5416a81e2afdf15dd586534cf86c5fa92f092080` (clean `main`).

- `apps/ha_smart_hvac/feedforward.py` — `weather_feedforward`, `quantize_command` (clamp + round-to-0.1).
- `apps/ha_smart_hvac/hvac_app.py` — Outdoor `listen_state`→`control_event`; `_gate_prelude` vs `_plant_and_heating_demand`; `_run_demand` (latched→0 else FF); `supply_event` trip latch/hold; `_go_idle` Decision C on all Plant-on non-demand exits; `_hands_off` plant-off; empty `_read_zones` leaves prior unchanged; CZ log-only after FF write.
- `apps/ha_smart_hvac/config.py` / `apps.yaml.example` — Outdoor, FF nest, `boiler_water`/`r_max`/`hold`; legacy `pid` ignored (do not edit this story).
- `docs/adr/0004-weather-curve-swt.md` — already `status: superseded by ADR-0005`; **add one live-pointer line to ADR-0007**.
- `docs/adr/0005-fixed-pid-swt.md`, `docs/adr/0006-optional-rls-adaptive-pid.md` — already have YAML `status:` frontmatter; set `superseded by ADR-0007` + one live-pointer line each; bodies otherwise prior-art record.
- **New** `docs/adr/0007-weather-curve-supply-trip-swt.md` — YAML frontmatter like 0006 (`---` / `status: accepted` / `---`); agent-law live ADR (gates, FF, CAP-8 listeners, **Trip latch** section, **Idle clear (Decision C)** section covering all `_go_idle` exits, dual-gate, CZ, CAP-7 hard out, no PID/RLS).
- `docs/decisions/adr-supply-event-no-outdoor-prelude.md`, `docs/decisions/adr-idle-trip-clear-after-write.md` — cite; do not edit.
- `AGENTS.md` (`bmad:context`) — replace 0005/0006 pointers and PID/Outdoor/CAP-7 / sticky demand-edge conventions with 0007 + curve/trip/dual-gate/Decision C; CAP-7 hard out; **preserve** still-valid clauses: `initialize` first `control_tick`, equal-float plant readback skip as write throttle, unreadable/non-finite plant readback skips write, Heating Demand listener updates in same change, initiative `done` only when every epic in `tickets.toml` is done.
- `CONTEXT.md` — Outdoor on path; replace **PID** live term with Weather Feedforward + Supply rise-rate trip; invert avoid-lists; rewrite Plant Management; **rewrite stale dialogues 4, 6, 7** (zones→boiler write; Plant Management off; event reactivity / Outdoor listener / supply trip) — dialogues 1–3 and 5 stay Exclusive Session / AppDaemon / SWT≠air unless they still name PID; keep Critical Zone diagnostics sense.

Do not change: `knowledge/**`, `apps/ha_smart_hvac/pid.py`, `rls.py`, runtime tests (run only).

## Tasks & Acceptance
**Execution:**
- [ ] `docs/adr/0007-weather-curve-supply-trip-swt.md` — create with 0006-style YAML frontmatter `status: accepted`; agent-law live SWT = weather curve + supply trip; supersedes 0005/0006; CAP-7 hard out; dual-gate; **Trip latch** and **Idle clear (Decision C)** as separate sections (Decision C = all Plant-on non-demand `_go_idle` exits); CZ diagnostics-only.
- [ ] `docs/adr/0004-weather-curve-swt.md` — add one live-pointer line to ADR-0007; leave status `superseded by ADR-0005`; no other body rewrite.
- [ ] `docs/adr/0005-fixed-pid-swt.md` + `docs/adr/0006-optional-rls-adaptive-pid.md` — set frontmatter `status: superseded by ADR-0007` **and** one live-pointer line each; bodies otherwise unchanged.
- [ ] `AGENTS.md` — rewrite `bmad:context` ADR pointer + Conventions to match App (u_ff, Outdoor listener, trip latch/clear, dual-gate, Decision C `_go_idle` exits, no PID/RLS/sticky, CAP-7 hard out); **keep** initialize tick / equal-float throttle / unreadable skip / Heating Demand listener coupling / initiative done rule; set Verified to `5416a81e2afdf15dd586534cf86c5fa92f092080` @ `2026-11-14`.
- [ ] `CONTEXT.md` — rewrite Outdoor / Plant Management / PID→FF+trip terms, avoid-lists; rewrite dialogues **4, 6, 7** to the same law (hard CAP-7 out).
- [ ] Verify — `uv run pytest`; `uv run ruff check apps/ha_smart_hvac tests`; grep guards below; spot-read AC below.

**Acceptance Criteria:**
- Given the repo after this story, when an agent reads ADR 0007, then it is the accepted **agent-law** live water law: Plant∧Demand → round-to-0.1(clamp(u_ff)); supply trip with **separate** trip-latch (only after successful trip write `0`) and Decision C sections covering all Plant-on non-demand `_go_idle` exits; dual-gate; CAP-7 hard out (not on water path; do not commission; out of scope); no live PID/RLS.
- Given ADR 0007 vs `hvac_app.py`, when spot-read for `_gate_prelude` / `_plant_and_heating_demand` / trip latch-on-successful-write / Decision C keep-latch, then ADR prose matches App (fail story if merged or drifted).
- Given ADR 0005 and 0006, when opened, then each has frontmatter `superseded by ADR-0007` **and** one live-pointer line to ADR-0007; ADR 0004 remains `superseded by ADR-0005` **and** has one live-pointer to ADR-0007 without a body rewrite as live law.
- Given AGENTS.md and CONTEXT.md, when read as domain SoT, then they describe Outdoor as control listener, clamp(u_ff), supply trip (hold + zone rising-edge; `_go_idle` write-fail keeps latch), dual-gate Outdoor vs supply, Critical Zone diagnostics-only, and do not teach live PID/∫/RLS/`rls_state.json`, sticky demand-edge, or CAP-7 commissioning (no deferred/later soft for CAP-7).
- Given CONTEXT example dialogue, when turns 4, 6, and 7 are read, then none claim `base_water_temp + u_pid`, ∫/RLS advance, sticky demand-edge, or «Outdoor is not a control listener».
- Given this story’s scope, when diff is inspected, then `knowledge/`, `pid.py`, `rls.py`, and App runtime behavior are unchanged.
- Given CI-local verify, when `uv run pytest` and `uv run ruff check apps/ha_smart_hvac tests` run, then both succeed.

## Implementation Notes
- Filename: `0007-weather-curve-supply-trip-swt.md` (matches ticket “weather curve + supply trip”).
- ADR 0007 frontmatter: copy 0006 shape (`---` / `status: accepted` / `---`).
- ADR 0007 audience: **agents** — MUST-floor only; match 0005 density; sections: gates, FF law, CAP-8 listeners, **Trip latch**, **Idle clear (Decision C)** (all `_go_idle` exits), dual-gate, out-of-scope — not a dump of test matrices.
- Trip latch-on-trip: only after successful `_write_setpoint(0)`; **separate section** from Decision C idle keep-latch.
- Live-pointer wording (0004/0005/0006): hard «live water law: ADR-0007» (or equivalent), not soft «also see».
- CAP-7 / `ff_auto_correct_state.json`: hard out in 0007 + AGENTS + CONTEXT — not on water path; do not commission; out of scope.
- AGENTS Verified line: `Verified 2026-11-14 against 5416a81e2afdf15dd586534cf86c5fa92f092080` — never the commit that contains this edit.
- CONTEXT: prefer **Weather Feedforward** and **Supply rise-rate trip**; demote **PID** to avoid/historical only if a short pointer helps — do not keep PID as a live glossary entry. Dialogues 4/6/7 must be rewritten; 1–3/5 only if they still name PID.
- Leave `docs/house-calibration.md` / README alone (already Outdoor+FF from epic 1).

## Plan Change Log
- 2026-11-14 party (installed): ADR 0007 = agent law; **F1-B** one live-pointer on 0004 (status stays superseded by 0005); **F2-A** AC spot-read dual-gate + latch-on-success + Decision C and two ADR sections; **F3-H** CAP-7 hard out; **F4-L** 0005/0006 frontmatter + one live-pointer each.
- 2026-11-14 review-plan apply: Verified = baseline SHA (not post-commit); `_go_idle` = all Plant-on non-demand exits + empty-read prior; CONTEXT dialogues 4/6/7 named; AGENTS preserve still-valid conventions; expand negative grep; 0007 frontmatter like 0006; per-file positive `rg`; restore plan YAML frontmatter.

## Review Triage Log
| lens | finding | verdict | route | evidence |
| --- | --- | --- | --- | --- |
| blind-hunter | ADR 0007 cite list omits Decision A / write-gated latch / CAP-8 decision docs | false | — | Intent Requires citing dual-gate + Decision C notes only; body already states rising-edge clear and CAP-8 shared writer. Extra cites are density, not a defect. |
| blind-hunter | Trip yaml (`boiler_water`/`r_max`/`hold`) underspecified vs FF nest | false | — | Intent: ADR 0007 is agent-law MUST-floor, not an integrator handbook / commissioning recipe. |
| blind-hunter | AGENTS short line overstates Decision C as unconditional trip clear | medium | patch | AGENTS.md L33 «follows Decision C trip clear» can be read as always clearing latch; L35 correctly says write-fail keeps latch. Same looseness in ADR 0007 SWT gates. |
| blind-hunter | AGENTS/CONTEXT omit `setpoint_min`/`setpoint_max` on clamp | low | — | Rejected: clamp(u_ff) matches frozen MUST-floor wording; rails live in ADR 0007 Feedforward law. Everyday agents hit ADR for rails. |
| blind-hunter | ADR 0004 body still present-tense / looks live | false | — | Intent forbids rewriting 0004 beyond the single live-pointer; status stays superseded by ADR-0005. |
| blind-hunter | ADR 0005/0006 bodies still assert PID / Outdoor-off | false | — | Intent: bodies otherwise unchanged; status + one live-pointer each is the required cutover. |
| blind-hunter | ADR 0007 never states relation to 0004 | false | — | Out-of-scope already: «ADR 0004–0006 are historical prior art with live-pointers». |
| blind-hunter | Trip latch omits Decision A empty-prior / missing-zone semantics | false | — | Intent: no test-matrix dump; frozen clear law is «zone rising-edge under `_gate_prelude`». |
| blind-hunter | Hold-expiry omits prelude-failure resume path | false | — | Intent MUST-floor density; hold expiry → clear + re-run prelude is stated; failure then follows existing `_go_idle` law. |
| blind-hunter | CONTEXT Outdoor `_Avoid_: Weather` collides with Weather Feedforward | medium | patch | CONTEXT.md Outdoor Avoid still says «Weather», while Weather Feedforward is now first-class live term — agents can avoid legitimate FF language. |
| blind-hunter | CAP-8 section never lists `supply_event` | false | — | CAP-8 is the shared FF demand writer; supply_event is the dual-gate trip path, documented separately — not a CAP-8 listener. |
| blind-hunter | Dialogues omit trip-clear FAQ | low | — | Rejected: dialogues 4/6/7 already cover latch, dual-gate, Decision C; another FAQ turn is optional polish. |
| blind-hunter | Unreadable `boiler_water` branch absent from ADR | false | — | Intent: no test-matrix dump on ADR 0007. |
| blind-hunter | AGENTS uses Decision C jargon without link | low | — | Rejected as standalone; folded into the medium Decision C wording patch (L33/L35 already name Decision C keep-latch). |
| edge-case-hunter | Unreadable/non-finite boiler_water on supply_event | false | — | Intent excludes test-matrix dump; latch-only-after-successful-write already implies no latch without write. |
| edge-case-hunter | First supply sample / no prior | false | — | Same MUST-floor exclusion. |
| edge-case-hunter | Non-positive dt_s | false | — | Same. |
| edge-case-hunter | r_obs ≤ r_max sample-only path | false | — | Same. |
| edge-case-hunter | supply_event when Plant∧Demand false clears sample | false | — | Same. |
| edge-case-hunter | Already latched while still over-rate (no hold restart) | false | — | Same. |
| verification-gap | (none) | — | — | Lens reported no verification gaps for docs-only diff. |
| intent-alignment | Docs↔runtime fidelity asserted without tests in diff | false | — | Descriptive audit under R1: story is docs cutover; plan Verification (pytest + rg + spot-read) is outside the diff and was run by the build. Not a defect in the change surface. |


## Verification
**Commands:**
- `uv run pytest` — expected: all pass (docs-only; no runtime drift).
- `uv run ruff check apps/ha_smart_hvac tests` — expected: clean.
- `test -f docs/adr/0007-weather-curve-supply-trip-swt.md` — expected: exists.
- `rg -n "status: superseded by ADR-0007" docs/adr/0005-fixed-pid-swt.md docs/adr/0006-optional-rls-adaptive-pid.md` — expected: both files match.
- `rg -n "ADR-0007|ADR 0007" docs/adr/0004-weather-curve-swt.md docs/adr/0005-fixed-pid-swt.md docs/adr/0006-optional-rls-adaptive-pid.md` — expected: live-pointer present in all three.
- `rg -n "base_water_temp \\+ u_pid|rls_state\\.json|pid\\.adaptive|advance PID|u_pid|∫|sticky|not a control listener|weighted demand-zone" AGENTS.md CONTEXT.md` — expected: no live-path matches (historical avoid-list mentions of PID ok only if clearly non-live).
- `rg -l "clamp\\(u_ff\\)" AGENTS.md CONTEXT.md docs/adr/0007-weather-curve-supply-trip-swt.md` — expected: all three files.
- `rg -l "Outdoor" AGENTS.md CONTEXT.md docs/adr/0007-weather-curve-supply-trip-swt.md` — expected: all three files.
- `rg -l "supply|r_max|rise-rate" AGENTS.md CONTEXT.md docs/adr/0007-weather-curve-supply-trip-swt.md` — expected: all three files.
- `rg -n "ff_auto_correct_state\\.json" AGENTS.md CONTEXT.md docs/adr/0007-weather-curve-supply-trip-swt.md` — expected: only as absent/out-of-scope / hard-out, never as live commission or deferred/later.

**Manual checks (supports AC spot-read):**
- Spot-read ADR 0007 vs `hvac_app.py`: `_gate_prelude` vs `_plant_and_heating_demand`; trip latch only after successful write `0`; Decision C on all `_go_idle` exits (disarm vs keep-latch on write fail) — two ADR sections.
- AGENTS Conventions vs CONTEXT glossary + dialogues 4/6/7 for the same law.
