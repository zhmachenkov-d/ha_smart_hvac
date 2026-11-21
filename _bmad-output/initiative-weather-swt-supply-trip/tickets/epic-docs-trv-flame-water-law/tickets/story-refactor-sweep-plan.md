---
title: 'Refactor sweep'
type: 'chore'
ticket: '3'
status: ready-for-dev
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent
**Problem:** Deferred-work still lists settled documentation debt — PID-supersede-as-outstanding, AGENTS «until 3.2» lag, missing accuracy listener note, CAP-8 «until epic 3», and house-calibration §1 table expand — although 6.1/6.2 already aligned live agent law.

**Approach:** Documentation-only hygiene: (1) reword CAP-8 so it no longer claims AGENTS still has sticky-latch prose until epic 3; (2) on the implementing branch, re-spot-read inventory A–I then prune A–F (+ E) and settle I by removing the bullet and citing house-calibration intro + `apps.yaml.example` (do not expand §1); (3) leave G–H and the `control_event` docstring unchanged. No new product behavior; no runtime or test edits; no edits to house `apps/apps.yaml`.

## Boundaries & Constraints
**Scope (IN):**
- Inventory A–I in `_bmad-output/initiative-weather-swt-supply-trip/deferred-work.md` + CAP-8 lag clause in `docs/decisions/adr-cap8-shared-ff-demand-writer.md` (body paragraph, currently line 3).
- **Order:** CAP-8 reword lands before prune of deferred bullet C.
- **A–F (+ E):** prune only the deferred-work claims (AGENTS/CONTEXT/accuracy/CAP-8 lag / meta-PID-outstanding). A does **not** require rewriting ADR 0005/0006 historical bodies (they already point live law to ADR-0008; body demotion is OUT).
- **I:** Settled prune-with-cite — remove misplaced bullet under Settled epic-5 **before** adding Settled epic-6 cite; cite by heading/keys (`## 1. House wiring`, intro anti-cycle sentences, `flame_on` / `ch_active` / TRV nest in `apps.yaml.example`), not brittle L2–7. §1 table unchanged. Settled note must state known checklist gap: §1 `plant_management` row is SWT-only vs intro plant-off clears flame latch.
- **Settled epic-6 note:** one bullet per pruned row A–F/I/C with path + covering story (6.1 / 6.2 / this CAP-8 edit).
- **Empty headers:** after pruning E, remove empty `## Deferred from: code review of story-delete-dead-pid-rls-modules-plan (2026-11-14)` (or any other header left with zero children).
- **tickets.toml:** path `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-docs-trv-flame-water-law/tickets/tickets.toml` `[[entry]] id = 3` — **edit** description/verify to match this scope (stale = A–F/I/CAP-8 only; G–H exempt).
- Hygiene verify: `uv run pytest` and `uv run ruff check apps/ha_smart_hvac tests` clean **plus** blocking manual checks below (pytest alone does not prove docs ACs).

**Never / OUT:**
- New product behavior; restore supply rise-rate as live law; CAP-7; house entity ids; expand house-calibration §1 (Decision B).
- G–H under header exactly: `## Deferred from: code review of story-refactor-sweep-plan (2026-11-16, walkthrough slice Prelude-isolation + expanded goldens)`.
- `hvac_app.py` `control_event` docstring (epic Boundaries: code remediation out; leave tracked only if already outside deferred-work — do not add new product scope).
- ADR 0005/0006 body rewrite; AGENTS/CONTEXT/ADR 0008 / `knowledge/` beyond CAP-8 + deferred prune; frozen 6.1/6.2 Intent edits.

**Decisions:**
- I = prune-with-cite — remove the bullet and cite house-calibration intro + `apps.yaml.example` as source of truth for anti-cycle wiring (walkthrough 2026-11-17; second-opinion option B).
- CAP-8 keeps historical trade-off; drop only the AGENTS sticky-latch / «until epic 3» lag claim; remaining prose must not imply AGENTS still documents sticky latch.

</frozen-after-approval>

## Tasks & Acceptance
**Execution (order):**
1. [x] Re-spot-read inventory A–I on the implementing branch (not only demo commit `67ebb44`).
2. [x] `docs/decisions/adr-cap8-shared-ff-demand-writer.md` — reword body lag clause (line 3 today); spot-read: no claim that AGENTS still has sticky-latch prose / until epic 3.
3. [x] `_bmad-output/initiative-weather-swt-supply-trip/deferred-work.md` — **after** step 2: prune A–F (+ E) and C; remove empty deferred headers; fix I nesting then Settled epic-6 note with per-row cites; leave G–H under the exact Prelude-isolation header above.
4. [x] `…/epic-docs-trv-flame-water-law/tickets/tickets.toml` entry `id=3` — description/verify/notes already updated in Formal review patch-all (G–H exempt; CAP-8 + F + I); confirm no drift at build time.
5. [x] Verify — commands + blocking manual checks.

**Acceptance Criteria:**
- Given CAP-8 after edit, when opened, then it no longer says AGENTS sticky-latch prose until epic 3, and a spot-read does not imply AGENTS still documents sticky latch.
- Given deferred-work after prune, when inspected, then bullets A–F (+ E) are removed, item I is settled with heading/key cites (not line-number-only), G–H remain under the exact Prelude-isolation header, epic-4/5 Settled sections remain, and no empty `## Deferred from…` headers remain.
- Given house-calibration §1, when inspected, then the table is unchanged (still Outdoor / plant_management / plant_setpoint / zones only).
- Given tickets.toml at the epic-docs path entry `id=3`, when compared to this Intent, then description/verify name CAP-8 + deferred A–F/I hygiene and exempt G–H (edited in this story).
- Given the suite, when `uv run pytest` and `uv run ruff check apps/ha_smart_hvac tests` run, then both are clean.
- Given docs verify, when the blocking manual checks run, then all pass.

**Verify (blocking):**
- `uv run pytest` — pass
- `uv run ruff check apps/ha_smart_hvac tests` — clean
- `rg -n 'until epic 3|sticky-latch prose' docs/decisions/adr-cap8-shared-ff-demand-writer.md` → no AGENTS-lag claim
- Spot-read CAP-8: remaining text does not imply AGENTS still documents sticky latch
- `rg -n 'may lag until story 3\.2|still describe live PID|omit commissioned TRV .accuracy|until epic 3' _bmad-output/initiative-weather-swt-supply-trip/deferred-work.md` → no matches for pruned A–F/C/D claims
- `rg -n 'No accuracy .control_event. \+ Outdoor-fail|Empty-zone isolation pins law-ran' _bmad-output/initiative-weather-swt-supply-trip/deferred-work.md` → G–H still present
- house-calibration §1 table still four rows
- Optional hygiene: `rg -n 'may lag until story 3\.2|AGENTS sticky-latch prose until epic 3' _bmad-output AGENTS.md CONTEXT.md docs/decisions` — report leftovers outside deferred-work; do not expand scope unless identical CAP-8/AGENTS lag strings remain in live docs

## Implementation Notes
- Re-spot-read on `chore/6-3-refactor-sweep-plan` after main@ba3e820 (6.2 merged): inventory A–I still open as claimed; AGENTS/CONTEXT already have accuracy; CAP-8 lag still present.
- CAP-8: dropped AGENTS sticky-latch / epic-3 lag clause; kept shared FF writer + equal-float history.
- deferred-work: pruned A–F/E/C; removed empty 2026-11-14 header; Settled epic-6 with per-row cites; G–H retained under Prelude-isolation header; I nest fixed via Settled epic-6 (removed from under epic-5).
- Verify: 362 pytest; ruff clean; blocking rg/spot-read pass (Settled C wording avoids false-positive on pruned-pattern rg).

## Plan Change Log
- 2026-11-17: Walkthrough Intent+Broad strokes lock — A–F+C IN, G–H OUT, I=B prune-with-cite; CAP-8 documentation-only hygiene.
- 2026-11-17: Formal review patch-all — CAP-8-before-C order; tickets.toml path+verify edit (G–H exempt); empty-header AC; heading/key cites; CAP-8 line 3; narrow A (no ADR body demotion); blocking rg; Settled template; re-spot-read on implement branch; structure condense Tasks-after-Boundaries.

## Review Triage Log
| Finding | Verdict | Route | Evidence |
| --- | --- | --- | --- |
| CAP-8 before prune C / unordered tasks | high | patch | Ordered Execution 1→2→3; Always Order |
| tickets.toml path ambiguous + verify vs G–H | high | patch | Pin epic-docs path; edit verify/description |
| Empty header after E prune | high | patch | AC + Always empty-headers |
| I cites L2–7 brittle; nesting order | high | patch | Heading/key cites; nest-fix before Settled |
| Code Map said CAP-8 L2 (actually L3) | high | patch | Body paragraph / line 3 today |
| Prune A vs ADR 0005/0006 bodies | medium | patch | Narrow A; body demotion OUT |
| pytest alone ≠ docs AC | high | patch | Blocking Verify rg/spot-read |
| Settled epic-6 needs per-row cites | medium | patch | Always Settled template |
| Demo evidence pinned to 67ebb44 | medium | patch | Re-spot-read step 1 |
| control_event docstring OUT underexplained | low | patch | Never/OUT + epic Boundaries |
| Exact G–H header text | low | patch | Quoted in Never |
| CAP-8 may still imply AGENTS sticky after edit | medium | patch | Spot-read AC + Decisions |
| Duplicate stale strings outside deferred-work | low | patch | Optional hygiene rg |
| Structure: condense Scope/Tasks; cut empty Notes | medium | patch | This rewrite |
| Prose: AC grammar; spell option B; full paths | low | patch | Intent/AC wording |
| tickets description understates F/I/CAP-8 | high | patch | tickets.toml edit task |