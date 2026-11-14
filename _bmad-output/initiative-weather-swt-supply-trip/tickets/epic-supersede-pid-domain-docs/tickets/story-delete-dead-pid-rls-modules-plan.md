---
title: 'Delete dead pid/rls modules'
type: 'feature'
ticket: '3'
created: '2026-11-14'
status: built
review: 'thorough'
review_source: 'auto'
baseline_revision: '5bdf49ee81aeb5ff27de65e52b83757784195aa4'
route: 'full'
route_source: 'auto'
risk: 'medium'
context:
  - _bmad-output/initiative-weather-swt-supply-trip/tickets/epic-supersede-pid-domain-docs/epic-supersede-pid-domain-docs.md
  - _bmad-output/initiative-weather-swt-supply-trip/tickets/epic-weather-curve-swt-restore/tickets/story-detach-pid-rls-from-live-swt-and-example-commissioning-plan.md
lenses_ran:
  - blind-hunter
  - edge-case-hunter
  - verification-gap
  - intent-alignment
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent
**Problem:** Live SWT no longer uses fixed-PID / RLS, but `pid.py`, `rls.py`, and their unit tests remain on disk; F6-B still assumes `pid.py` exists.

**Approach:** Delete the four dead modules/tests; relocate live `clamp`/`quantize_command` unit tests into `test_feedforward`; drop the F6-B on-disk lock; keep the `hvac_app` AST import-lock so the suite proves PID/RLS absence without retaining dead files.

## Boundaries & Constraints
**Always:**
- Delete `apps/ha_smart_hvac/pid.py`, `apps/ha_smart_hvac/rls.py`, `tests/test_pid.py`, `tests/test_rls.py`.
- **Decision (1A):** Move `test_clamp_bounds` and `test_quantize_command_grid_snap` (parametrize + `pytest` / `clamp` / `quantize_command` imports) into `tests/test_feedforward.py` before deleting `test_pid.py`; do not keep PID/∫/`weighted_error` tests.
- **Decision (A):** Epic `tickets.toml` entry 3 `after = [1, 2]` (knowledge demote before module delete; was `[1]`).
- Keep `test_hvac_app_does_not_import_rls_or_pid_quantize` (AST lock on `hvac_app.py` only).
- Remove `test_pid_does_not_reexport_clamp_or_quantize` and `_PID_PATH` (they require `pid.py` on disk).
- Confirm `apps.yaml.example` has no `pid` / RLS / `base_water_temp` nest (already true after epic 1 — verify only; no house `apps.yaml` HITL).
- `uv run pytest` and `uv run ruff check apps/ha_smart_hvac tests` clean after the delete.

**Never:**
- Change live SWT runtime (`hvac_app.py`, `feedforward.py` law), Exclusive Session, Heating Demand definition, or Critical Zone role.
- Restore CAP-7 / `ff_auto_correct_state.json` / adapting `base`/`slope`.
- Edit house `apps/apps.yaml` entity IDs; rewrite ADR / AGENTS / CONTEXT / `knowledge/` (owned by 3.1 / 3.2).
- Keep dead modules solely to satisfy F6-B.

## I/O & Edge-Case Matrix
| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| Happy delete | Four target files present | Files gone; suite green | — |
| Import-lock | `hvac_app.py` source | Still forbids any pid/rls import | Fail if lock weakened |
| F6-B after delete | No `pid.py` | F6-B test and `_PID_PATH` removed | — |
| Example yaml | `apps.yaml.example` | No `pid` / RLS / `base_water_temp` nest; FF + `boiler_water` remain | — |
| Live helpers | `clamp` / `quantize_command` | Unit tests live in `test_feedforward` (1A) | — |
| Ticket graph | entry 3 `after` | `[1, 2]` (Decision A; after knowledge demote) | — |

</frozen-after-approval>

## Code Map
Evidence commit `5bdf49ee81aeb5ff27de65e52b83757784195aa4` (clean `main`). Continuity: epic-1 detach left modules on disk; F6-B / import-locks from that plan.

- `apps/ha_smart_hvac/pid.py` (~118) — **DELETE**; no App callers.
- `apps/ha_smart_hvac/rls.py` (~285) — **DELETE**; no App callers.
- `tests/test_pid.py` — **DELETE** after 1A relocate; source of `test_clamp_bounds` (L72–77) and `test_quantize_command_grid_snap` (L142–154); rest is dead PID/∫/`weighted_error`.
- `tests/test_rls.py` (~399) — **DELETE**.
- `tests/test_hvac_app.py` — keep `test_hvac_app_does_not_import_rls_or_pid_quantize` (~226–267); **remove** `_PID_PATH` (~38) and `test_pid_does_not_reexport_clamp_or_quantize` (~269–289).
- `tests/test_feedforward.py` — **add** relocated clamp/quantize tests + `pytest` import; keep existing `weather_feedforward` tests; do not change `feedforward.py` behavior.
- `apps/ha_smart_hvac/feedforward.py` / `hvac_app.py` — **do not change**.
- `apps.yaml.example` — verify only (no pid / `base_water_temp` / RLS nest).
- `tests/test_config.py` — leave ignored-legacy `"pid"` / `"base_water_temp"` fixture keys unless collection breaks (intentional ignored_keys coverage, not commissioning).
- `_bmad-output/.../epic-supersede-pid-domain-docs/tickets/tickets.toml` — entry 3 `after`: `[1]` → `[1, 2]` (**Decision A** — human «по порядку»; knowledge demote before module delete).

Do not change: trip/curve runtime, ADR/AGENTS/CONTEXT/`knowledge/`, house yaml, CAP-7 surfaces.

## Tasks & Acceptance
**Execution:**
1. [x] `tests/test_feedforward.py` — relocate `test_clamp_bounds` + `test_quantize_command_grid_snap` from `test_pid`; import `clamp`, `quantize_command`, `pytest`. Clamp cases: `(39.9, 40.0), (40.0, 40.0), (47.5, 47.5), (55.0, 55.0), (55.1, 55.0)` with `lo=40.0, hi=55.0`. Quantize cases: `(60.0, 40.0, 55.06, 55.0), (30.0, 42.04, 55.0, 42.1), (41.96, 40.0, 55.0, 42.0), (55.03, 55.01, 55.06, 55.03)`.
2. [x] `tests/test_hvac_app.py` — delete `_PID_PATH` and `test_pid_does_not_reexport_clamp_or_quantize`; leave import-lock intact.
3. [x] Delete `apps/ha_smart_hvac/pid.py`, `apps/ha_smart_hvac/rls.py`, `tests/test_pid.py`, `tests/test_rls.py`.
4. [x] `tickets.toml` entry 3 — set `after = [1, 2]` (Decision A); leave entry 2/`after` and other fields unchanged.
5. [x] Verify — pytest + ruff; four paths gone; example has no pid/`base_water_temp`/RLS nest; import-lock present; clamp/quantize under `test_feedforward`; entry 3 `after` includes `2`.

**Acceptance Criteria:**
- Given the repo after this story, when the four paths are listed, then `pid.py`, `rls.py`, `test_pid.py`, and `test_rls.py` are absent.
- Given `tests/test_feedforward.py`, when `test_clamp_bounds` and `test_quantize_command_grid_snap` run, then they pass for clamp `(39.9→40.0), (40.0→40.0), (47.5→47.5), (55.0→55.0), (55.1→55.0)` at `[40,55]` and quantize `(60,40,55.06→55.0), (30,42.04,55→42.1), (41.96,40,55→42.0), (55.03,55.01,55.06→55.03)`.
- Given `tests/test_hvac_app.py`, when collected, then `test_hvac_app_does_not_import_rls_or_pid_quantize` remains and no test reads `pid.py` from disk.
- Given `apps.yaml.example`, when grepped for commissioning nests, then there is no `pid` / RLS / `base_water_temp` nest (`weather_feedforward` and `boiler_water` may remain).
- Given epic `tickets.toml` entry 3, when read, then `after` is `[1, 2]` (knowledge demote before module delete).
- Given CI-local verify, when `uv run pytest` and `uv run ruff check apps/ha_smart_hvac tests` run, then both succeed.
- Given the diff, when inspected, then live SWT runtime, CAP-7 absence, house entity ids, and ADR/AGENTS/CONTEXT/`knowledge/` are unchanged.

## Implementation Notes
- Order: relocate clamp/quantize → drop F6-B/`_PID_PATH` → delete the four files (never leave a half-applied tree that still reads missing `pid.py`).
- Do not replace F6-B with a “pid.py must not exist” assert — absence is filesystem state; import-lock is the App guard.
- `rls_state.json` string asserts in `test_hvac_app` stay (demand-path filename absence), unrelated to deleting `rls.py`.
- Decision A: epic `tickets.toml` entry 3 `after = [1, 2]` so the leaf graph matches human «по порядку» (3.2 knowledge before 3.3 delete). Do not encode PR numbers in pytest AC — graph edge only.
- No App callers of `pid`/`rls` today; only `test_pid` / `test_rls` import those modules. Half-applied delete-before-relocate is the real suite risk; Notes order above is mandatory.

## Plan Change Log
- 2026-11-14: Initial draft from ticket 3.3 + detach continuity + codebase investigation.
- 2026-11-14: Resolved OQ1 → 1A relocate clamp/quantize into `test_feedforward`; removed Open Questions.
- 2026-11-14: Review apply — explicit clamp/quantize parametrize in tasks+AC; numbered Execution 1–5; Decision A in Always.
- 2026-11-14: Party dig — Decision A: entry 3 `after = [1, 2]`; Amelia edges (no App callers; F6-B sole on-disk reader; example already clean; knowledge has no `pid.py`/`rls.py` links post-#143) closed without new runtime scope; fixture `"pid"` in `test_config` stays as ignored_keys coverage.

## Review Triage Log
| Finding | Verdict | Evidence / route |
| --- | --- | --- |
| BH: plan `in-progress` + unchecked Execution while deletes land | false | Status already `in-review` at triage; unchecked boxes are plan bookkeeping — fix would edit this build's plan (rejected). |
| BH: empty Review Triage Log while implementation lands | false | Log is filled in this triage pass; prior emptiness is workflow timing, not a code defect. |
| BH: `docs/house-calibration.md` still says modules may remain / domain docs lag until epic 3 | low | Line 85 parenthetical is false after this delete; top Domain-docs lag is also stale post-3.1 AGENTS/CONTEXT. Intent Never omits house-calibration. → **patch** |
| BH: Plan Verification never greps house-calibration | false | Rejected: fix edits this build's plan; covered by house-calibration patch above. |
| BH: entry 3 `tickets.toml` verify omits clamp relocate / F6-B gone | false | Execution 4 left other fields unchanged by design; ticket verify still covers files/import-lock/example/pytest; relocate proven by suite. |
| BH: entry 3 description still says suite adjusts on-disk pid readers | false | Description is the story work statement, not a post-merge status bulletin. |
| BH: `deferred-work.md` still frames epic-3 supersede as outstanding | medium (unverified→defer) | Pre-existing epic-1 defer about AGENTS/CONTEXT/ADR; 3.1 already rewrote those — not caused by module delete. → **defer** |
| BH: `test_feedforward` docstring still only says weather feedforward | false | File still tests weather FF; helpers belong on that path — no named everyday harm. |
| BH: Plan Change Log has no build/apply entry | false | Rejected: fix edits this build's plan. |
| BH: Code Map baseline vs Design Notes PR #143 | false | HEAD/`baseline_revision` `5bdf49ee` *is* the #143 merge; citations match the delete tree. |
| BH: `docs/decisions/adr-cap8-…` still says AGENTS sticky-latch until epic 3 | low | Historical decision note; AGENTS already updated in 3.1 — not caused by this delete. → **defer** |
| BH: `AGENTS.md` still says knowledge may lag until 3.2 | low | 3.2 done; fix edits agent-context (Intent Never + triage rule). → **defer** |
| Edge-case hunter: (none) | — | Empty findings array. |
| Verification-gap: (none) | — | No gaps filed. |
| Intent-alignment: R2 suite-proves-absence vs AST lock | false | Descriptive divergence only; plan Notes intentionally keep import-lock (not filesystem absence assert). |

## Design Notes
- Ticket verify requires import-lock survival without dead modules; 1A keeps live helper coverage after `test_pid` deletion (detach left that coverage “until epic 3”); AC lists explicit parametrize tuples (no git required).
- Risk medium: wrong delete could weaken the App import-lock or drop live helper tests; runtime path itself is already detached.
- Sequencing: 3.2 knowledge demote (PR #143 merged) before 3.3 module delete — reflected as `after = [1, 2]` on entry 3 (Decision A). Prior `after = [1]` allowed parallel with 3.2; human locked order.

## Verification
**Commands:**
- `uv run pytest` — expected: all pass; no collection of deleted modules; clamp/quantize under `test_feedforward`.
- `uv run ruff check apps/ha_smart_hvac tests` — expected: clean.
- `test ! -e apps/ha_smart_hvac/pid.py && test ! -e apps/ha_smart_hvac/rls.py && test ! -e tests/test_pid.py && test ! -e tests/test_rls.py` — expected: success.
- `rg -n '^(pid:|base_water_temp:)|rls_state|adaptive' apps.yaml.example` — expected: no pid / base_water_temp / RLS commissioning matches.
- `rg -n 'test_pid_does_not_reexport|_PID_PATH' tests/test_hvac_app.py` — expected: no matches.
- `rg -n 'does_not_import_rls_or_pid|test_clamp_bounds|test_quantize_command_grid_snap' tests/` — expected: import-lock + relocated tests present.
- `rg -n 'after\s*=\s*\[1,\s*2\]' _bmad-output/initiative-weather-swt-supply-trip/tickets/epic-supersede-pid-domain-docs/tickets/tickets.toml` — expected: match on entry 3 (after Decision A task).

**Manual checks (if no CLI):**
- Spot-diff: no edits under `docs/adr/`, `AGENTS.md`, `CONTEXT.md`, `knowledge/`, or house `apps/apps.yaml`.
