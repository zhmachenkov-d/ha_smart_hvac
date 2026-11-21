---
title: 'Refactor sweep'
type: 'chore'
ticket: '4'
created: '2026-11-21'
status: ready-for-dev
route: 'full'
route_source: 'human'
risk: 'low'
review: 'thorough'
review_source: 'human'
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
- [ ] Re-run start-of-work inventory `rg` (commands below); confirm prune set still empty.
- [ ] Record **Settled — empty prune set** in Implementation Notes with command outputs (or cite clean).
- [ ] Confirm keep K1–K4 and out O1–O5 untouched (no product file edits expected).
- [ ] `tickets.toml` entry 4 — confirm description/verify/notes match frozen punch-list (edit only if drifted).
- [ ] Verify — pytest + ruff + hygiene `rg` below.

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
_(fill at build: Settled — empty prune set + rg evidence; tickets.toml confirm/edit; suite results)_

## Plan Change Log
- 2026-11-21: Pre–bmad-build-auto review path 1 — freeze punch-list P empty / K1–K4 / O1–O5; story + plan authored; ready-for-dev pending human OK to run build-auto.
