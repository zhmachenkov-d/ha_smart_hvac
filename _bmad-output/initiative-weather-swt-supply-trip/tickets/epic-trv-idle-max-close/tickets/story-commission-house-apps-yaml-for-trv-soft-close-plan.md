---
title: 'Commission house apps.yaml for TRV soft-close'
type: 'feature'
ticket: '2'
created: '2026-11-15'
status: done
baseline_revision: '3539f091467cbb4e976994d32493f1d3f2ab93d1'
route: 'oneshot'
route_source: 'auto'
risk: 'medium'
review: 'quick'
review_source: 'auto'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - '{project-root}/CONTEXT.md'
  - '{project-root}/AGENTS.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent
**Problem:** House `apps/apps.yaml` still lists Sonoff TRVs as plain climate strings, so the 4.1 idle max-close law never commissions on the live house.

**Approach:** HITL-update local gitignored `apps/apps.yaml`: add `valve_closure_floor: 80` and map livingroom×2, bedroom, and childroom climates to the confirmed closure+accuracy number entities; leave generic climates as strings; do not change existing entity IDs; no Exclusive Session.

## Boundaries & Constraints
**Always:**
- Backup `apps/apps.yaml` to `apps/apps.yaml.pre-4.2` before editing (gitignored like the house file).
- Add top-level `valve_closure_floor: 80`.
- Convert only these climates to mappings with confirmed IDs (initiative Notes 2026-11-15):
  - `climate.livingroom_sonoff_trvzb_thermostat` → `number.livingroom_sonoff_trvzb_valve_closure_degree` + `number.livingroom_sonoff_trvzb_temperature_control_accuracy`
  - `climate.livingroom_sonoff_trvzb_thermostat_2` → `number.livingroom_sonoff_trvzb_valve_closure_degree_2` + `number.livingroom_sonoff_trvzb_temperature_control_accuracy_2`
  - `climate.bedroom_sonoff_trvzb_thermostat` → `number.bedroom_sonoff_trvzb_valve_closure_degree` + `number.bedroom_sonoff_trvzb_temperature_control_accuracy`
  - `climate.childroom_sonoff_trvzb_thermostat` → `number.childroom_sonoff_trvzb_valve_closure_degree` + `number.childroom_sonoff_trvzb_temperature_control_accuracy`
- Keep bathroom / kitchen / wc as plain-string climates.
- Ask before changing any pre-existing house entity ID value (AGENTS.md).
- Verify offline with `yaml.safe_load` → drop `module`/`class` → `parse_config`.

**Never:**
- Commit `apps/apps.yaml` or `apps/apps.yaml.*` backups.
- Edit `apps/ha_smart_hvac/*`, `apps.yaml.example`, tests, ADR/`knowledge/`.
- Add `flame_on` / `ch_active` (epic 5) or run `./scripts/run-appdaemon`.
- Infer TRV entities by guessing; change Outdoor / plant / zone / climate / FF IDs without owner confirm.

**Decisions:**
- Floor value: `80` (yaml default / example).
- Climate→TRV pairing follows existing climate entity suffixes (`_2` for livingroom second TRV).
- Existing entity ID strings stay byte-identical to pre-4.2 backup except for added keys/structure around Sonoff TRVs + floor.

## I/O & Edge-Case Matrix
| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| Commission Sonoff | Livingroom×2, bedroom, childroom climates | Each is a mapping with both `valve_closure` and `accuracy` confirmed IDs | `parse_config` ConfigError if partial |
| Generics untouched | bathroom / kitchen / wc | Remain plain climate strings | No TRV keys |
| Floor present | After edit | `valve_closure_floor == 80` on parsed config | Missing key → default 80 still OK; story wants explicit 80 |
| ID stability | Diff vs `apps.yaml.pre-4.2` | No changed values for Outdoor, plant, zones, climates, FF, boiler_water | Stop and ask owner if any ID change is needed |
| Offline parse | `parse_config` on house args | Returns `HvacConfig`; four commissioned TRVs | Fail → fix yaml before done |

</frozen-after-approval>

## Code Map
- `apps/apps.yaml` (gitignored) — sole edit target; post-edit: `valve_closure_floor: 80`; livingroom×2 / bedroom / childroom commissioned; bathroom / kitchen / wc plain strings.
- `apps/apps.yaml.pre-4.2` — pre-edit backup (gitignored via `apps/apps.yaml.*`).
- `apps.yaml.example` — shape reference only (`valve_closure_floor` + `{climate, valve_closure, accuracy}`); do not edit.
- `apps/ha_smart_hvac/config.py` — `parse_config` offline verify; do not change.
- Initiative Notes 2026-11-15 — confirmed closure/accuracy entity IDs (already closed); see `_bmad-output/initiative-weather-swt-supply-trip/initiative-weather-swt-supply-trip.md` Notes (“House entities closed”).
- Continuity from story 4.1 plan: mapping needs both TRV fields; plain string = climate-only; house ids deferred to this story.

## Tasks & Acceptance
**Execution:**
- [x] Backup `apps/apps.yaml` → `apps/apps.yaml.pre-4.2`.
- [x] Add `valve_closure_floor: 80`; convert the four Sonoff climates to mappings with confirmed closure/accuracy IDs; leave generics as strings; keep all other entity ID values unchanged.
- [x] Offline `parse_config` verify: floor 80; four commissioned TRVs with expected entity ids; bathroom/kitchen/wc still plain.

**Acceptance Criteria:**
- Given the pre-4.2 backup, when comparing entity ID values after the edit, then Outdoor, plant, boiler_water, FF, zone temperatures, weights, names, and climate entity ids are unchanged unless the owner confirmed a change.
- Given the edited house yaml, when args are passed through `parse_config`, then `valve_closure_floor` is 80 and livingroom×2, bedroom, and childroom thermostats are commissioned with the confirmed closure/accuracy entity ids.
- Given bathroom, kitchen, and wc thermostats, when parsed, then each remains climate-only (no TRV keys).
- Given git status, when checked, then `apps/apps.yaml` and `apps/apps.yaml.pre-4.2` are not staged for commit.

## Implementation Notes
- 2026-11-15: Backed up to `apps/apps.yaml.pre-4.2`; added `valve_closure_floor: 80`; mapped livingroom×2, bedroom, childroom to confirmed closure/accuracy IDs; bathroom/kitchen/wc left plain.
- Offline verify used `PYTHONPATH=apps` (package not on default `uv run` path). All pre-edit entity IDs preserved; eight new number entities only.
- House yaml remains gitignored; tracked artifact for this story is this plan file.

## Plan Change Log
- 2026-11-15: House commission completed (backup + floor + four Sonoff mappings); Execution tasks checked; Implementation Notes filled.
- 2026-11-15: Quick-review patches — Verification command documents `yaml.safe_load` → drop AD keys → `parse_config` sequence; PYTHONPATH=apps kept.
- 2026-11-15: Walkthrough Formal review patches — runnable Verification script; Code Map post-edit; Initiative Notes path; Manual backup path `apps/apps.yaml.pre-4.2`.
## Review Triage Log
| lens | finding | verdict | route | evidence |
| --- | --- | --- | --- | --- |
| quick | Verification missing PYTHONPATH=apps | false | reject | Current Verification command already prefixes `PYTHONPATH=apps`; stale diff predates that edit. |
| quick | Execution tasks unchecked / Implementation Notes empty in tracked diff | medium | patch | Notes were already filled; checked off all three Execution items to match completed house commission. |
| quick | Verification placeholder omits yaml.safe_load → drop AD keys → parse_config | low | patch | Expanded Verification command line to name that sequence; Always already required it. |

## Design Notes
House file only; law already shipped in 4.1. Naming aligns climate suffixes with confirmed number entities. No live AppDaemon session.

## Verification
**Commands:**
- `PYTHONPATH=apps uv run python -c "import yaml; from pathlib import Path; from ha_smart_hvac.config import parse_config; raw=yaml.safe_load(Path('apps/apps.yaml').read_text())['hvac']; raw={k:v for k,v in raw.items() if k not in ('module','class')}; cfg=parse_config(raw); assert cfg.valve_closure_floor==80; want={'climate.livingroom_sonoff_trvzb_thermostat':('number.livingroom_sonoff_trvzb_valve_closure_degree','number.livingroom_sonoff_trvzb_temperature_control_accuracy'),'climate.livingroom_sonoff_trvzb_thermostat_2':('number.livingroom_sonoff_trvzb_valve_closure_degree_2','number.livingroom_sonoff_trvzb_temperature_control_accuracy_2'),'climate.bedroom_sonoff_trvzb_thermostat':('number.bedroom_sonoff_trvzb_valve_closure_degree','number.bedroom_sonoff_trvzb_temperature_control_accuracy'),'climate.childroom_sonoff_trvzb_thermostat':('number.childroom_sonoff_trvzb_valve_closure_degree','number.childroom_sonoff_trvzb_temperature_control_accuracy')}; got={}; [got.update({t.climate:(t.valve_closure,t.accuracy)}) for z in cfg.zones for t in z.thermostats if t.valve_closure]; assert got==want; plain={t.climate for z in cfg.zones for t in z.thermostats if not t.valve_closure}; assert plain=={'climate.bathroom_generic_thermostat','climate.kitchen_generic_thermostat','climate.wc_generic_thermostat'}"` — expected: exit 0
- `git check-ignore -v apps/apps.yaml apps/apps.yaml.pre-4.2` -- expected: both ignored
- `git status --short` -- expected: no staged/untracked house yaml (ignored)

**Manual checks (if no CLI):**
- Diff house yaml vs `apps/apps.yaml.pre-4.2`: only floor + Sonoff mapping structure added.

## Code Review

### 2026-11-15
**Code review complete.** 0 `decision-needed`, 5 `patch`, 0 `defer`, 4 rejected.

- [x] [Review][Patch] Verification command is a non-runnable python -c stub [story-commission-house-apps-yaml-for-trv-soft-close-plan.md:100]
- [x] [Review][Patch] Code Map still describes pre-edit house state after built [story-commission-house-apps-yaml-for-trv-soft-close-plan.md:63]
- [x] [Review][Patch] Plan Change Log is empty [story-commission-house-apps-yaml-for-trv-soft-close-plan.md:87]
- [x] [Review][Patch] Initiative Notes citation lacks navigable path [story-commission-house-apps-yaml-for-trv-soft-close-plan.md:67]
- [x] [Review][Patch] Manual verification backup path missing apps/ prefix [story-commission-house-apps-yaml-for-trv-soft-close-plan.md:105]

Rejected:
- R4 bathroom/kitchen AC not in hunk — false: full apps/apps.yaml still has bathroom/kitchen/wc as plain climate strings; hunk omission is adjacency only.
- R5 no HA entity existence check — false: Approach/Never forbid Exclusive Session; offline AC by design.
- R6 offline built does not close live problem — false: yaml commission is the story scope; live soft-close binds on next AD load.
- R9 review_loop_iteration 0 — low, rarely visible process metadata; not worth a fix pass.

### 2026-11-16 (house slice)
**Code review complete.** 0 `decision-needed`, 2 `patch`, 0 `defer`, 4 rejected.

- [x] [Review][Patch] Purpose header still SWT-only after TRV commission [apps/apps.yaml:2]
- [x] [Review][Patch] valve_closure_floor lacks idle max-close comment [apps/apps.yaml:15]

Rejected:
- R3 Sonoff mapping shape comments — low; multi-site comment noise beyond one-line fix.
- R4 climate-only notes on generics — low; plan/AC already document intentional plain strings.
- R5 bathroom omitted from hunk — false: full apps/apps.yaml keeps bathroom/kitchen/wc as plain climate strings.
- R6 SWT/TRV section grouping — low; duplicate of floor-comment patch.
