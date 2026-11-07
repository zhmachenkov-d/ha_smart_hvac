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

## Verification

**Commands:**
- `uv run pytest tests/test_dual_layout.py` -- expected: pass; no asserts on `hacs.json` / `hacs/action` / HACS install markers
- `uv run pytest` -- expected: full suite pass
- `uv run ruff check apps tests` -- expected: clean
