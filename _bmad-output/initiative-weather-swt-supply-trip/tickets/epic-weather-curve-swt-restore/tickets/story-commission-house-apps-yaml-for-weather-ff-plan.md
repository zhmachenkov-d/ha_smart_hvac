---
title: 'Commission house apps.yaml for weather FF'
type: 'chore'
ticket: '3'
created: '2026-11-12'
status: 'built'
baseline_revision: '63c38441661e4ec94a93e5dc040705f58f94cddc'
route: oneshot
route_source: auto
risk: medium
context: []
review: 'quick'
review_source: 'auto'
lenses_ran: ['quick']
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent
**Problem:** Live house `apps/apps.yaml` is still PID-era (no `outdoor_temperature` / `weather_feedforward`; still has `pid` / `base_water_temp` / `boiler_water`). After stories 1.1–1.2 the App requires Outdoor+FF to parse, so Production AppDaemon fails `ConfigError` until this HITL commission.

**Approach:** Update gitignored house `apps/apps.yaml` only: restore Outdoor entity from `apps.yaml.pre-pid`; commission `weather_feedforward` with house-chosen **base=30, slope=1.0, comfort_ref=20** (S2); delete `pid` and `base_water_temp`; keep `boiler_water` for epic 2. Keep existing plant/zone/rails entity IDs. Prove parse via `parse_config` — no Exclusive Session / live AppDaemon.

**HITL decisions (2026-11-12):**
- FF coeffs: S2 — `base=30`, `slope=1.0`, `comfort_ref=20` (owner: slope ~1.0; rails 50–60 → u_ff at 0 °C = 50).
- Outdoor entity: restore from `apps.yaml.pre-pid` (2A).
- Legacy keys: delete `pid` + `base_water_temp`; keep `boiler_water` (3A).

## Boundaries & Constraints
**Always:**
- Edit only house `apps/apps.yaml` (gitignored). Pre-change backup `apps/apps.yaml.pre-1.3` before editing.
- Commission non-empty `outdoor_temperature` and `weather_feedforward` with only `base` / `slope` / `comfort_ref` (whitelist; finite) — values as above.
- Keep existing house plant_management, plant_setpoint, setpoint_min/max, control_interval, and zone entity IDs / weights (no owner-confirmed ID changes).
- Remove `pid` and `base_water_temp`; keep `boiler_water` (ignored today; epic 2 supply).
- Verify with offline parse (`parse_config` on loaded house yaml args) — no `./scripts/run-appdaemon`, no Exclusive Session.
- Do not commit `apps/apps.yaml` or other `apps/apps.yaml.*` backups.

**Never:**
- Change house entity IDs without owner confirmation.
- Restore CAP-7 / `ff_auto_correct` / `ff_auto_correct_state.json`.
- Re-introduce live `pid` / `base_water_temp` as water-law drivers.
- Rewrite AGENTS.md / CONTEXT.md / ADRs / `knowledge/` (epic 3).
- Edit `apps.yaml.example` or App Python (already FF-only after 1.1–1.2).
- Run live Exclusive Session / Production AppDaemon for this story’s verify.

## I/O & Edge-Case Matrix
| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| Happy parse | House yaml with Outdoor + FF S2; plant/zones intact | `parse_config` succeeds; FF 30/1.0/20; no live pid water law | — |
| boiler_water kept | Present after edit | Top-level `ignored_keys` includes `boiler_water`; init WARN | No ConfigError |
| Entity IDs | Pre-1.3 backup vs post-edit | Plant/zone/boiler entities unchanged | — |
| Outdoor | From pre-pid | Same Outdoor entity id as `apps.yaml.pre-pid` | — |

</frozen-after-approval>

## Code Map
Continuity (entries 1–2): App already FF-only; leftover house `boiler_water` → top-level `ignored_keys` WARN. Entry 1 accepted config break until this HITL.

- `apps/apps.yaml` — **edited (gitignored)**: Outdoor + FF S2; removed pid/base_water_temp; kept boiler_water + plant/zones/rails.
- `apps/apps.yaml.pre-1.3` — pre-change PID-era backup (gitignored).
- `apps/apps.yaml.pre-pid` — Outdoor entity source (read-only).
- `apps/ha_smart_hvac/config.py` — `parse_config` for verify only.
- Do not change: App Python, `apps.yaml.example`, tests.

## Tasks & Acceptance
**Execution:**
- [x] Backup current `apps/apps.yaml` → `apps/apps.yaml.pre-1.3`.
- [x] Add `outdoor_temperature` from pre-pid and `weather_feedforward` 30/1.0/20.
- [x] Delete `pid` / `base_water_temp`; keep `boiler_water`.
- [x] Confirm plant/zone/setpoint/boiler entity IDs match pre-1.3 backup.
- [x] Offline verify: `parse_config` succeeds; Outdoor+FF present; pid not live water law.

**Acceptance Criteria:**
- Given the pre-change backup, when house yaml is updated, then plant/zone/plant entity IDs match the backup unless the owner confirmed a change.
- Given the updated house `apps/apps.yaml`, when `parse_config` runs on its `hvac` args, then it succeeds with `outdoor_temperature` and `weather_feedforward` commissioned.
- Given the updated house yaml, when inspected, then `pid` / `base_water_temp` are not the live water-law commission (absent, or only ignored legacy).

## Implementation Notes
- HITL: 1C→S2 (30/1.0/20), 2A, 3A applied 2026-11-12.
- Backup: `apps/apps.yaml.pre-1.3`. Outdoor copied from `apps.yaml.pre-pid`.
- `parse_config` OK; `ignored_keys=('boiler_water',)`; added Outdoor+FF; removed pid/base_water_temp; entity IDs match pre-1.3.
- House yaml remains gitignored — do not commit.

## Plan Change Log
- 2026-11-12: Initial oneshot plan for ticket 1.3 / entry 3.
- 2026-11-12: HITL answers folded — S2 FF, Outdoor from pre-pid, strip pid/base keep boiler.

## Review Triage Log
- 2026-11-12 quick review: no findings.

## Design Notes
- S2 chosen so at T_out=0 °C, u_ff=50 (=setpoint_min); cold −10 °C → 60 (=max); mild 10 °C pins at min.
- Epic-2 keeps `boiler_water` present for later supply commission.

## Verification
**Commands:**
- `uv run python` + `parse_config` on `apps/apps.yaml` — expected: success; FF 30/1.0/20; ignored_keys includes boiler_water only among legacy; no pid/base
- Entity compare `apps.yaml.pre-1.3` vs `apps/apps.yaml` — expected: plant/zone/boiler ids unchanged; Outdoor+FF added; pid/base removed

**Manual checks (if no CLI):**
- Open house yaml: Outdoor + weather_feedforward 30/1.0/20; no pid nest; boiler_water present.
