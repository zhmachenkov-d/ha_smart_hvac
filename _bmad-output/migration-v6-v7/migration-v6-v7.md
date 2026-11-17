---
type: migration
title: Fold remaining 6.13 pre-release spec folders into v7 tickets
status: done
created: 2026-11-17
completed: 2026-11-17
---

# Fold remaining 6.13 pre-release spec folders

This project was already on the v7 initiative + `tickets/` layout (`active_initiative` = `initiative-weather-swt-supply-trip`). Migration 1 ran in the **pre-release-spec-only** path.

## Backup

`.v6-v7-migration-backup-20261117-0630/` — `_bmad/` (pre-clean) + `_bmad-output/` (pre-fold, 230 files). `.gitignore` = `*`. Do not commit. Delete when satisfied.

## v6 leftover clean (same session)

Removed before the fold:

- keys: `core.document_output_language` (`_bmad/custom/config.toml`), `core.communication_language` (`_bmad/custom/config.user.toml`)
- unused customizations: `bmad-correct-course.user.toml`, `bmad-spec.user.toml`

## Folds executed

Command:

```bash
uv run .agents/skills/bmad/scripts/migrate_v6.py \
  --project-root /workspaces/ha-smart-hvac \
  --skill .agents/skills/bmad \
  --fold-specs /workspaces/ha-smart-hvac/_bmad-output
```

### 1. `spec-gate-omega-c-on-saturation` → initiative

| | |
|---|---|
| Ticket | `initiative-gate-omega-c-on-saturation/initiative-gate-omega-c-on-saturation.md` |
| Ids | CAP-1…6 → R1…R6 |
| Companions moved | `architecture-diagrams.md`, `control-tick-behaviors.md` |
| Memlog | `initiative-gate-omega-c-on-saturation/.memlog.md` |
| Unresolved companions (outside store; files exist at project paths) | `docs/adr/0003-…`, `docs/house-calibration.md` |

### 2. `spec-weather-curve-swt-only` → initiative

| | |
|---|---|
| Ticket | `initiative-weather-curve-zone-actuators/initiative-weather-curve-zone-actuators.md` |
| Ids | CAP-1…8 → R1…R8 |
| Companions moved | `architecture-diagrams.md`, `brownfield.md` |
| Memlog | `initiative-weather-curve-zone-actuators/.memlog.md` |
| Unresolved companions (outside store; file exists) | `CONTEXT.md` |

### 3. `spec-fix-ladrc-blow-up` → epic

| | |
|---|---|
| Ticket | `…/epic-fix-ladrc-blow-up/epic-fix-ladrc-blow-up.md` |
| Ids | CAP-1…5 → R1…R5 |
| Companions moved | `architecture-diagrams.md` |
| Memlog | `…/epic-fix-ladrc-blow-up/.memlog.md` |
| Unresolved companions (outside store; files exist) | `docs/adr/0002-…`, `docs/adr/0003-…` |
| Note | Epic kept prior summary lines as R1–R5 **and** appended full `R n (CAP-n)` lines — duplicate wording left for optional manual consolidate |

## Manual path fixes after fold

Fold rewriter missed some prose folder paths; fixed:

- `initiative-fix-ladrc-blow-up.md` Description → points at epic ticket
- `epic-fix-ladrc-blow-up.md` Description → “Spec folded into this epic”
- `initiative-gate-omega-c-on-saturation.md` Description → points at initiative ticket
- `forge-weather-curve-zone-actuators.md` closed note → `../initiative-weather-curve-zone-actuators.md`

## Checklist results

| # | Item | Result |
|---|---|---|
| 1 | No `spec-<slug>/` with `spec-<slug>.md` under `_bmad-output/` | **pass** |
| 2 | Folded tickets have Requirements (`Rn (CAP-n)`), Constraints, companions beside ticket + References, memlog records fold | **pass** |
| 3 | No bare `CAP-` in the three folded homes outside R-parentheses / `.memlog.md` | **pass** (product CAP-7/CAP-8 prose elsewhere, e.g. `initiative-pid`, is pre-existing domain language — not fold scope) |
| 4 | Live paths the fold/manual fixes own resolve; historical leftovers listed | **pass with leftovers** (below) |
| config | `active_initiative` + `output_folder` unchanged and valid | **pass** |

### Historical / non-resolving leftovers (do not fail; user may ignore or tidy)

- Retrospectives still name old `spec-…/` folders in evidence tables
- Plans with ellipsis paths `_bmad-output/.../spec-weather-curve-swt-only/…` (never literal paths)
- Walkthrough link **text** still says `spec-….md` while href already targets the initiative ticket
- `walkthrough-pr-24-log.md` evidence line names `spec-fix-ladrc-blow-up.md`

### Outside store

No project-owned source files (excluding `.tokenade` cache and the migration backup) required edits for old spec-folder paths.

## Approval

Approved by user 2026-11-17; fold completed same day.
