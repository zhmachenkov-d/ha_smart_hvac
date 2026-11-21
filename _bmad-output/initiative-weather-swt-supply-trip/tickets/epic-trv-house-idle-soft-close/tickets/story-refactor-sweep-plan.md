---
title: 'Refactor sweep'
type: 'chore'
ticket: '4'
created: '2026-11-21'
status: done
baseline_revision: 4881d04b2df87ea853ba2a1a1e8557bd63708827
route: 'full'
route_source: 'human'
risk: 'low'
review: 'thorough'
review_source: 'auto'
lenses_ran: ['blind-hunter', 'edge-case-hunter', 'verification-gap', 'intent-alignment']
followup_review_recommended: false
deferred: []
context:
  - '{project-root}/_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-trv-house-idle-soft-close/tickets/story-refactor-sweep.md'
  - '{project-root}/_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-trv-house-idle-soft-close/tickets/tickets.toml'
---

<intent-contract>

## Intent
**Problem:** Epic-7 entry 4 still reads as “prune deferred overshoot/accuracy soft-close leftovers,” but 7.1–7.3 left `deferred: []`, `_bmad-output/deferred-work.md` has no epic-7 bullets, and the live App already has no `_trv_overshoot*` helpers — so `bmad-build-auto` would invent scope.

**Approach:** Close the sweep from the frozen punch-list only: settle empty prune (P) with hygiene `rg` evidence; do not edit keep (K1–K4) or out-of-scope (O1–O5); update `tickets.toml` entry 4 if drifted; record Settled in Implementation Notes. No new product laws.

## Boundaries & Constraints
**Always:**
- Scope = story punch-list **P / K1–K4 / O1–O5** (see story Requirements 1–3). Prune set is **empty** at freeze (2026-11-21 inventory).
- Record **Settled — empty prune set** with the verify `rg` outputs (App `_trv_overshoot` empty; live soft-close path set clean of live overshoot/accuracy soft-close teaching).
- `uv run pytest` and `uv run ruff check apps/ha_smart_hvac tests` clean.
- Confirm `tickets.toml` `[[entry]] id = 4` description/verify/notes match this Intent (edit if drifted).

**Never:**
- Invent deletes, refactors, or docs “improvements” outside settle/record.
- Touch **K1–K4** (ConfigError + accuracy contract tests; Historical decision banners/bodies; live hold soft-close App path; 7.3 live docs teaching).
- Touch **O1–O5** (`set-water-temperature.md` residual; epic-6.3 CAP-8 / G–H; gitignored house yaml + `.pre-*`; Verified stamp / new laws / Exclusive Session; `_bmad-output/` walkthroughs).
- Restore overshoot/accuracy as live soft-close; bump AGENTS Verified stamp; edit house `apps/apps.yaml`.

## I/O & Edge-Case Matrix
| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| Empty prune | Inventory finds no dead helpers | Settled note + no App/test/docs product diff required | Do not invent prune targets |
| Keep guard | Tempted to delete `accuracy` ConfigError / contract tests | Leave K1 intact | Treat as live law, not dead code |
| Historical | Tempted to strip Historical ADR bodies | Leave K2 banners+bodies | Bodies are audit record |
| Residual doc | `set-water-temperature.md` “still applies” | Leave O1 untouched | Not deferred prune |
| CAP-8 | CAP-8 / G–H leftovers | Leave O2 for epic 6.3 | Fence explicit |
| Backup headers | `.pre-*` still say closure/accuracy | Leave O3 gitignored | No backup edits |
| Hygiene | Live path `rg` | Zero live overshoot/accuracy soft-close teaching | Fail story if live teaching returned |

</intent-contract>

## Code Map
- **No App/runtime edit expected** unless inventory regresses (then stop and re-freeze punch-list with human).
- `apps/ha_smart_hvac/config.py` — **K1 keep:** leftover `accuracy` → `ConfigError` (~L137–138).
- `apps/ha_smart_hvac/hvac_app.py` — **K3 keep:** house-idle hold soft-close only (no `_trv_overshoot*`).
- `tests/test_config.py` / `tests/test_hvac_app.py` — **K1 keep:** accuracy reject + no-accuracy-listen tests.
- `docs/decisions/adr-trv-{write-gated-overshoot-latch,plant-off-no-latch-clear,accuracy-shared-control-event}.md` — **K2 keep.**
- Live docs from 7.3 — **K4 keep.**
- `tickets.toml` entry `id = 4` — align description/verify/notes to punch-list if drifted.
- Out of scope paths: O1–O5 as named in story.

## Tasks & Acceptance
**Execution:**
- [x] Re-run start-of-work inventory `rg` (commands below); confirm prune set still empty.
- [x] Record **Settled — empty prune set** in Implementation Notes with command outputs (or cite clean).
- [x] Confirm keep K1–K4 and out O1–O5 untouched (no product file edits expected).
- [x] `tickets.toml` entry 4 — confirm description/verify/notes match frozen punch-list (edit only if drifted).
- [x] Verify — pytest + ruff + hygiene `rg` below.

**Acceptance Criteria:**
- Given the freeze inventory, when re-checked at build, then App `rg '_trv_overshoot'` under `apps/ha_smart_hvac` is empty and no dead overshoot soft-close helpers are proposed for delete.
- Given K1–K4, when the sweep finishes, then those paths are unchanged in intent (ConfigError + contract tests + Historical bodies + live hold path + 7.3 live docs still present as keep).
- Given O1–O5, when the sweep finishes, then none were edited.
- Given Implementation Notes, when read, then they contain **Settled — empty prune set** with hygiene evidence.
- Given `tickets.toml` entry 4, when compared to this Intent, then description/verify name empty-prune settle + keep/out guards (not a generic “prune dead helpers” without punch-list).
- Given the suite, when `uv run pytest` and `uv run ruff check apps/ha_smart_hvac tests` run, then both are clean.

**Verify (blocking):**
- `rg -n '_trv_overshoot' apps/ha_smart_hvac` → no matches
- `rg -n '_trv_overshoot_latched|commissioned.*accuracy|accuracy.*control_event|overshoot-100|overshoot latch' docs/adr/0008-weather-curve-trv-flame-swt.md CONTEXT.md AGENTS.md knowledge/concepts/trv-soft-close.md knowledge/concepts/index.md knowledge/concepts/outdoor-temperature.md` → no live-law hits
- Spot-check K1 still present: ConfigError accuracy reject in `config.py`; both named tests still exist
- Spot-check O1–O5 not in the diff
- `uv run pytest` — pass
- `uv run ruff check apps/ha_smart_hvac tests` — clean

## Implementation Notes
- **Settled — empty prune set** (2026-11-21 build): start-of-work / verify inventory confirms no deferred dead overshoot/accuracy soft-close helpers to delete.
  - `rg -n '_trv_overshoot' apps/ha_smart_hvac` → no matches (exit 1).
  - `rg -n '_trv_overshoot_latched|commissioned.*accuracy|accuracy.*control_event|overshoot-100|overshoot latch'` on live soft-close path set (`docs/adr/0008-weather-curve-trv-flame-swt.md`, `CONTEXT.md`, `AGENTS.md`, `knowledge/concepts/trv-soft-close.md`, `knowledge/concepts/index.md`, `knowledge/concepts/outdoor-temperature.md`) → no matches (exit 1).
  - `_bmad-output/deferred-work.md` has no epic-7 bullets.
- **K1–K4 spot-check (untouched):** `config.py` L137–138 leftover `accuracy` → `ConfigError`; tests `test_parse_rejects_trv_accuracy_in_mapping` / `test_initialize_trv_no_accuracy_listen` present; Historical banners on three `adr-trv-*` decisions; `_apply_trv_law` / `_arm_trv_soft_close_hold` live in `hvac_app.py`; 7.3 live docs left as-is.
- **O1–O5:** not edited (no product/docs/house-yaml/CAP-8/stamp/walkthrough changes).
- **tickets.toml** `[[entry]] id = 4`: description/verify/notes already match frozen punch-list (empty-prune settle + K/O guards) — **confirm-only, no edit**.
- **Suite:** `uv run pytest` → 370 passed; `uv run ruff check apps/ha_smart_hvac tests` → clean.
- **Files touched:** this plan only (`status: done`, execution checkboxes, Implementation Notes). No App/test/docs product diff.
- **Surprises:** none — inventory still empty as frozen 2026-11-21; no re-freeze needed.

## Plan Change Log
- 2026-11-21: Pre–bmad-build-auto review path 1 — freeze punch-list P empty / K1–K4 / O1–O5; story + plan authored; ready-for-dev pending human OK to run build-auto.
- 2026-11-21: Build settle — empty prune recorded with hygiene rg; tickets.toml confirm-only; pytest 370 + ruff clean; status done.

## Review Triage Log
### 2026-11-21 — Review pass
- verdicts: 16 findings — high 0, medium 0, low 0, false 16, maybe-false 0
- findings:
  - `[false]` `[reject]` Blind Hunter: frontmatter `in-review` vs notes/changelog `status done` — workflow set `in-review` for this review pass after build wrote `done`; finalize sets `built`. Fix would only edit this build's plan notes.
  - `[false]` `[reject]` Blind Hunter: missing cited `git status`/`diff` for O1–O5 — working tree since baseline is plan-only (`git diff --name-only` / `status --porcelain`); O paths untouched. Fix would only pad plan notes.
  - `[false]` `[reject]` Blind Hunter: O1–O5 not named individually in settle notes — out-of-scope fence already frozen in story/intent-contract; product paths absent from diff. Fix would only edit this build's plan.
  - `[false]` `[reject]` Blind Hunter: K2 spot-check mentions banners not bodies — three Historical `adr-trv-*` files still present with Historical banners and bodies on disk; not in diff. Fix would only edit plan notes.
  - `[false]` `[reject]` Blind Hunter: K3 notes omit disarm/expiry token — `_disarm_trv_soft_close_hold` and `_trv_soft_close_hold_token` / `_trv_soft_close_hold_expired` still live in `hvac_app.py`; untouched. Fix would only edit plan notes.
  - `[false]` `[reject]` Blind Hunter: deferred-work.md claim without quoted search — `_bmad-output/initiative-weather-swt-supply-trip/deferred-work.md` has no epic-7 hits on re-check. Fix would only edit plan notes.
  - `[false]` `[reject]` Blind Hunter: tickets.toml confirm-only without excerpt — entry `id = 4` description/verify/notes already match frozen punch-list; no edit required. Fix would only edit plan notes.
  - `[false]` `[reject]` Blind Hunter: hygiene `rg` paraphrased vs exact Verify line — re-ran exact Verify commands; both empty (exit 1). Fix would only edit plan notes.
  - `[false]` `[reject]` Blind Hunter: tests/ inventory missing from notes — `rg` overshoot/latch patterns under `tests/` empty; prune still empty. Fix would only edit plan notes.
  - `[false]` `[reject]` Blind Hunter: story file unchanged after settle — intent records Settled in plan Implementation Notes; ticket story files are not written by build-auto. Not a product gap.
  - `[false]` `[reject]` Edge Case Hunter: notes/changelog `status done` vs YAML `in-review` — same workflow intermediate as first finding; finalize → `built`. Fix would only edit this build's plan.
  - `[false]` `[reject]` Intent Alignment: evidence is narrative citation not committed transcripts — expected for empty-prune settle; Verify commands re-ran clean in this pass. Not a product defect.
  - `[false]` `[reject]` Intent Alignment: K1–K4 keep proven only by absence from diff — correct for no-touch keep; spot-check paths still present. Not a defect.
  - `[false]` `[reject]` Intent Alignment: tickets.toml match asserted in plan prose — confirm-only already aligned; no toml hunk required under R1.
  - `[false]` `[reject]` Intent Alignment: suite/hygiene reported in notes, no new tests — matches `covers = []` and Req 4 as verify gates, not new R*. Not a defect.
  - `[false]` `[reject]` Intent Alignment: notes `status done` vs frontmatter `in-review` — same as first finding; process surface only.

## Auto Run Result
- **Summary:** Settled epic-7 entry 4 empty prune set: hygiene `rg` clean, K1–K4/O1–O5 untouched, `tickets.toml` entry 4 confirm-only, plan Implementation Notes recorded Settled evidence. No App/test/docs product changes.
- **Files changed:**
  - `story-refactor-sweep-plan.md` — in-progress→built workflow fields, execution checkboxes, Settled Implementation Notes, review triage, auto-run result
- **Review findings:** patches applied 0; deferred 0; all 16 findings rejected (plan-note/process claims or expected empty-settle surfaces; no product defect).
- **Follow-up review recommendation:** false (no patched high/medium entries this pass; patched counts: high 0, medium 0, low 0).
- **Verification:**
  - `rg -n '_trv_overshoot' apps/ha_smart_hvac` → no matches
  - live soft-close path hygiene `rg` → no matches
  - `rg` overshoot/latch under `tests/` → no matches
  - K1 ConfigError + both named tests present; K3 hold helpers present; Historical ADR bodies present
  - `uv run pytest` → 370 passed
  - `uv run ruff check apps/ha_smart_hvac tests` → clean
  - diff since `4881d04b2df87ea853ba2a1a1e8557bd63708827` → plan file only
- **Residual risks:** invent-scope if someone reopens “prune leftovers” without the frozen P/K/O punch-list.
