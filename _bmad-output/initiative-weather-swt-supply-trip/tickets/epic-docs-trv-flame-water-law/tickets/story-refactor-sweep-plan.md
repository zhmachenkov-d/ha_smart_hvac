---
title: 'Refactor sweep'
type: 'chore'
ticket: '3'
status: ready-for-dev
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent
**Problem:** After epic 7 closed, story 6.3 is still `ready-for-dev` with a Nov-17 CAP-8 / deferred A–F Intent already merged in [PR #159](https://github.com/zhmachenkov-d/ha_smart_hvac/pull/159), while `deferred-work.md` still carries accuracy-framed G (+ Settled F accuracy-listen as covering truth), Settled epic-4 overshoot framing, and epic 7 left named leftovers for this story: O1 `set-water-temperature.md` hold/cancel depth, O2 G–H disposition, P4 `house-calibration.md` hold/floor/`accuracy` keys, and P1 `control_event` docstring («no sticky latch»).

**Approach:** Post–epic-7 hygiene only. Treat PR #159 CAP-8 + Settled epic-6 A–F/I as baseline (re-spot-read; no CAP-8 re-edit unless lag regresses). (1) Deferred-work: prune G as obsolete; keep H under the Prelude-isolation header; caveat Settled F for epic-7 ConfigError / closure-only; fence Settled epic-4 overshoot as historical. (2) Docs: plant-off soft-close hold/cancel on `set-water-temperature.md`; name hold/floor + leftover `accuracy`→ConfigError on `house-calibration.md` without expanding §1. (3) App comment only: fix `control_event` docstring for flame latched-zero and TRV soft-close hold/episode. (4) Meta: clear epic-7 block note; align `tickets.toml` + walkthrough. No new product laws; no new tests; no house yaml.

## Boundaries & Constraints
**Scope (IN):**
- **Baseline (confirm-only):** `docs/decisions/adr-cap8-shared-ff-demand-writer.md` still has no AGENTS sticky-latch / «until epic 3» lag; Settled epic-6 A–F/I rows remain. Re-edit CAP-8 **only** if that lag claim regressed.
- **`deferred-work.md`:**
  - **G:** prune as obsolete (accuracy×Outdoor-fail isolation — accuracy retired; leftover yaml `accuracy` is ConfigError).
  - **H:** keep under exact header `## Deferred from: code review of story-refactor-sweep-plan (2026-11-16, walkthrough slice Prelude-isolation + expanded goldens)`.
  - **Settled F:** add post–epic-7 caveat — 6.1 accuracy-listen covering is superseded for live soft-close by epic 7 (closure-only; no accuracy listeners; leftover key → ConfigError).
  - **Settled epic-4:** fence the overshoot / expanded-goldens Settled bullet as historical (live soft-close = house-idle floor/hold, not overshoot).
  - Record a short **Settled: epic-6 post–7 hygiene** note for G prune + F caveat (path + this story).
  - Remove empty `## Deferred from…` headers if any appear after G prune (Prelude header stays because H remains).
- **`knowledge/concepts/set-water-temperature.md`:** plant-off sentence — TRV soft-close still applies **with** house-idle hold/cancel (point at companion `trv-soft-close.md`); do not dump full soft-close law here.
- **`docs/house-calibration.md`:** intro (or adjacent anti-cycle commissioning prose) names `trv_soft_close_hold_s`, `valve_closure_floor`, and leftover TRV `accuracy` → ConfigError; cite `apps.yaml.example`. **§1 table stays four rows** (Outdoor / plant_management / plant_setpoint / zones) — Decision B unchanged.
- **`apps/ha_smart_hvac/hvac_app.py`:** `control_event` docstring only — remove «no sticky latch»; name flame latched-zero **and** TRV soft-close hold/episode (epic-7 retro action #1 / P1). No other App/runtime edits.
- **`tickets.toml`** `[[entry]] id = 3` — description/verify/notes match this Intent; clear «Blocked until epic 7» note.
- **Walkthrough** `_bmad-output/initiative-weather-swt-supply-trip/walkthrough-story-6-3-refactor-sweep/walkthrough-story-6-3-refactor-sweep.md` — Wrap-up: PR #159 merged; this renegotiation is the open work.
- Hygiene verify: `uv run pytest` + `uv run ruff check apps/ha_smart_hvac tests` clean **plus** blocking manual checks below.

**Never / OUT:**
- New product behavior; restore overshoot or accuracy as live soft-close; CAP-7; house `apps/apps.yaml` / entity ids; expand house-calibration §1 table; bump AGENTS Verified stamp.
- New tests for G/H, ADV2, V1, Exclusive Session soft-close spot-check, or other epic-7 deferred runtime items.
- ADR 0005/0006 body rewrite; AGENTS/CONTEXT/ADR 0008 / live `knowledge/` soft-close law rewrite beyond the two named doc edits; frozen 6.1/6.2 Intent edits.
- Re-prune Settled epic-6 A–E/I/C rows; invent-scope deletes outside this Intent.
- CAP-8 historical trade-off rewrite (shared FF writer / equal-float) — only lag-clause regress repair is in scope.

**Decisions:**
- Package C (2026-11-21): baseline PR #159 + deferred G prune/F caveat/epic-4 fence + O1/P4 docs + P1 docstring + meta; H remains deferred.
- §1 table expand stays OUT (Decision B from 2026-11-17 walkthrough).
- Docstring fix is App **comment** only — not new runtime law.

</frozen-after-approval>

## Tasks & Acceptance
**Execution (order):**
1. [ ] Baseline spot-read: CAP-8 has no AGENTS sticky-latch / «until epic 3» lag; Settled epic-6 A–F/I present. If CAP-8 lag regressed → repair lag clause only before deferred edits.
2. [ ] `deferred-work.md` — prune G; keep H under Prelude-isolation header; caveat Settled F; fence Settled epic-4 overshoot as historical; add Settled epic-6 post–7 hygiene note; drop empty deferred headers if any.
3. [ ] `knowledge/concepts/set-water-temperature.md` — plant-off soft-close hold/cancel one-liner (+ companion cite).
4. [ ] `docs/house-calibration.md` — hold/floor + leftover `accuracy`→ConfigError; §1 table unchanged (four rows).
5. [ ] `apps/ha_smart_hvac/hvac_app.py` — `control_event` docstring only (flame latched-zero + TRV soft-close hold/episode; no «no sticky latch»).
6. [ ] `tickets.toml` entry `id=3` — description/verify/notes match this Intent; clear epic-7 block note.
7. [ ] Walkthrough 6.3 — Wrap-up reflects PR #159 merged + this renegotiation as remaining work (or done when build closes).
8. [ ] Verify — commands + blocking manual checks.

**Acceptance Criteria:**
- Given CAP-8 on the build tip, when opened, then it still has no AGENTS sticky-latch / «until epic 3» lag claim (or that claim was repaired only if it had regressed).
- Given `deferred-work.md` after edit, when inspected, then G is gone, H remains under the exact Prelude-isolation header, Settled F carries a post–epic-7 accuracy/ConfigError caveat, Settled epic-4 overshoot is marked historical, Settled epic-6 A–F/I rows remain, and a post–7 hygiene Settled note cites this story.
- Given `set-water-temperature.md` plant-off prose, when read, then soft-close still applies with hold/cancel (companion cite), not a bare «still applies» with no hold.
- Given `house-calibration.md`, when read, then hold/floor and leftover `accuracy`→ConfigError are named; §1 table still has exactly four rows.
- Given `control_event` docstring, when read, then it does not say «no sticky latch» and names flame latched-zero and TRV soft-close hold/episode.
- Given `tickets.toml` entry `id=3`, when compared to this Intent, then description/verify name post–7 hygiene (deferred G/F/epic-4 fence + set-water + house-cal + docstring) and notes no longer say blocked on epic 7.
- Given the suite, when `uv run pytest` and `uv run ruff check apps/ha_smart_hvac tests` run, then both are clean.
- Given docs/App comment verify, when the blocking manual checks run, then all pass.

**Verify (blocking):**
- `uv run pytest` — pass
- `uv run ruff check apps/ha_smart_hvac tests` — clean
- `rg -n 'until epic 3|sticky-latch prose' docs/decisions/adr-cap8-shared-ff-demand-writer.md` → no AGENTS-lag claim
- `rg -n 'No accuracy .control_event. \+ Outdoor-fail' _bmad-output/initiative-weather-swt-supply-trip/deferred-work.md` → no G
- `rg -n 'Empty-zone isolation pins law-ran' _bmad-output/initiative-weather-swt-supply-trip/deferred-work.md` → H still present
- Spot-read Settled F: post–epic-7 ConfigError / closure-only caveat present
- Spot-read Settled epic-4: overshoot framing marked historical
- `rg -n 'trv_soft_close_hold_s|valve_closure_floor|ConfigError' docs/house-calibration.md` → hold/floor/accuracy-ConfigError present
- house-calibration §1 table still four rows
- `rg -n 'still applies' knowledge/concepts/set-water-temperature.md` → plant-off soft-close line names hold/cancel (or equivalent)
- `rg -n 'no sticky latch' apps/ha_smart_hvac/hvac_app.py` → no matches in `control_event` docstring
- Spot-read `control_event` docstring: flame latched-zero + TRV soft-close hold/episode named
- `rg -n 'Blocked until epic 7' _bmad-output/initiative-weather-swt-supply-trip/tickets/epic-docs-trv-flame-water-law/tickets/tickets.toml` → no matches

## Implementation Notes
_(fill at build)_

## Plan Change Log
- 2026-11-17: Walkthrough Intent+Broad strokes lock — A–F+C IN, G–H OUT, I=B prune-with-cite; CAP-8 documentation-only hygiene.
- 2026-11-17: Formal review patch-all — CAP-8-before-C order; tickets.toml path+verify edit (G–H exempt); empty-header AC; heading/key cites; CAP-8 line 3; narrow A; blocking rg; Settled template; re-spot-read; structure condense.
- 2026-11-17: Built and merged as PR #159 (CAP-8 lag + deferred A–F/E/I Settled); later marked `done`, then `blocked` pending epic 7 (2026-11-20), then `ready-for-dev` after epic 7 close.
- 2026-11-21: Human renegotiate Intent → **package C** post–epic-7 hygiene (baseline PR #159; G prune; F caveat; epic-4 historical fence; set-water hold/cancel; house-cal hold/floor/accuracy; `control_event` docstring; meta). Tasks reset for build-auto.

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
| Pre-build 2026-11-21: Intent stale vs PR #159 + epic 7 | — | renegotiate | Package C chosen |
