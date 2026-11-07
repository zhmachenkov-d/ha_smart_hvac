---
title: 'Remove HACS support'
type: 'chore'
ticket: ''
created: '2026-11-07'
status: 'built'
baseline_revision: 'dcb1877e127bdac26acaf6dd3d884c3cb446057f'
route: 'oneshot'
route_source: 'auto'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['context-free']
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** HACS is no longer used for this Home Assistant install path, but the live repo still ships `hacs.json`, HACS Validate CI, and an install-first README/tests that assume a HACS AppDaemon custom repository.

**Approach:** Delete the live HACS knobs and rewrite install docs/tests for a public manual AppDaemon deploy (copy package + `apps.yaml.example`); keep dual-layout, semantic-release, CHANGELOG history, and `_bmad-output` HACS artifacts.

**Decisions locked:**
- Install path: public manual — place `apps/ha_smart_hvac/` under AppDaemon `app_dir`, wire from root `apps.yaml.example`.
- Cleanup: live surface only — do not rewrite CHANGELOG or delete `_bmad-output` HACS history.
- Keep: dual-layout (`apps/ha_smart_hvac/` only tracked under `apps/`, Exclusive Session `app_dir: ../apps`), GitHub Releases / semantic-release.
- Drop stranger-HACS `app_dir: /config/appdaemon/apps` and `hacs/integration#4442`; keep Exclusive Session + Production add-on `/config/apps` docs.

</frozen-after-approval>

## Implementation Notes

Oneshot: ~5 mechanical files (delete 2, edit README/example/tests); LOC ≤100. GitHub branch-protection requiring check `validate-hacs` is out of tree — note after delete; do not invent workflow stubs.

- Deleted `hacs.json` and `.github/workflows/validate.yaml`.
- README: Install (AppDaemon) manual path; dropped stranger-HACS `app_dir` section; no `hacs` string left in README.
- `apps.yaml.example` comment: Production only.
- `tests/test_dual_layout.py`: dropped HACS asserts; added `test_hacs_surface_removed`; retargeted README markers.
- `tests/test_release_workflow.py`: docstring only (release train, not HACS).
- Verify: 153 pytest passed; ruff clean.
- Out of tree: if GitHub ruleset still requires check `validate-hacs`, update ruleset after merge.

## Plan Change Log

## Review Triage Log

- context-free: (none) — no findings to triage.
- 2026-11-07 full: 3 patch applied (README tarball path, apps.yaml.example comment, workflow HACS-scan); 1 defer (initiative Done-when/R4); 9 rejected.

## Verification

**Commands:**
- `uv run pytest tests/test_dual_layout.py` -- expected: pass; no asserts on `hacs.json` / `hacs/action` / HACS install markers
- `uv run pytest` -- expected: full suite pass
- `uv run ruff check apps tests` -- expected: clean

## Code Review

### 2026-11-07T08:32:57+00:00

**Code review complete.** 0 `decision-needed`, 3 `patch`, 1 `defer`, 9 rejected.

- [x] [Review][Patch] Clarify Release tarball nest path in Install step 1 [README.md:9]
- [x] [Review][Patch] Widen apps.yaml.example app_dir comment beyond Production-only [apps.yaml.example:2]
- [x] [Review][Patch] Strengthen HACS-removal regression beyond two fixed paths [tests/test_dual_layout.py:93]
- [x] [Review][Defer] Initiative Done-when / R4 still assume live HACS publish surface [initiative-hacs.md:27] — deferred: intentional keep of `_bmad-output` HACS history; supersede/cancel/retarget is board hygiene outside this oneshot live-surface diff

Rejected:
- missing HACS→manual migration docs — false: locked intent drops live HACS path and README `hacs` string; migration prose conflicts with that
- undocumented `/config/appdaemon/apps` after stranger example removal — false: locked decision explicitly drops that example and keeps Exclusive Session + Production `/config/apps`
- no durable in-repo ruleset reminder for `validate-hacs` — false: active ruleset requires only `pr-title` and `pr-commits`; orphaned-check outcome does not occur
- README substring ban blocks honest former-HACS wording — false: matches plan Implementation Notes (“no `hacs` string left in README”) and reading C locked by tests
- no replacement CI packaging gate after deleting Validate — false: intent did not require a new gate; dual-layout/release tests remain
- Layout table omits post-HACS rationale for sole tracked `apps/` package — low: unlikely everyday harm; fix would add speculative maintainer prose
- install-order README markers can pass without procedure assertions — low: current README still has place/wire/app_dir steps; strengthening markers is speculative
- thin plan audit trail (`ticket: ''`, empty change log) — rejected: fix would edit the plan under review
- branch ruleset may still require deleted `validate-hacs` — false: ruleset `24390720` required checks are `pr-title`, `pr-commits` only
