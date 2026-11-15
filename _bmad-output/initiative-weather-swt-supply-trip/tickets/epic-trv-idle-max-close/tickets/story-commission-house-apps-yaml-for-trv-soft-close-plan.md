---
title: 'Commission house apps.yaml for TRV soft-close'
type: 'feature'
ticket: '2'
created: '2026-11-15'
status: built
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
- `apps/apps.yaml` (gitignored) — sole edit target; currently plain-string Sonoff climates; no `valve_closure_floor`.
- `apps/apps.yaml.pre-4.2` — create as pre-edit backup (gitignored via `apps/apps.yaml.*`).
- `apps.yaml.example` — shape reference only (`valve_closure_floor` + `{climate, valve_closure, accuracy}`); do not edit.
- `apps/ha_smart_hvac/config.py` — `parse_config` offline verify; do not change.
- Initiative Notes 2026-11-15 — confirmed closure/accuracy entity IDs (already closed).
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
- `PYTHONPATH=apps uv run python -c '...'` — `yaml.safe_load(apps/apps.yaml)["hvac"]`, drop `module`/`class`, `parse_config`; assert floor 80 + four commissioned TRV ids + three plain generics -- expected: exit 0
- `git check-ignore -v apps/apps.yaml apps/apps.yaml.pre-4.2` -- expected: both ignored
- `git status --short` -- expected: no staged/untracked house yaml (ignored)

**Manual checks (if no CLI):**
- Diff house yaml vs `apps.yaml.pre-4.2`: only floor + Sonoff mapping structure added.
