<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent
**Problem:** House `apps/apps.yaml` still commissions legacy `boiler_water` and lacks `flame_on` / `ch_active`, so the 5.1 flame short-on law cannot load on the live house.

**Approach:** HITL-update local gitignored `apps/apps.yaml`: remove supply-trip keys (`boiler_water`; `r_max` / supply hold if present); add confirmed `flame_on` / `ch_active` plus explicit `flame_on_min_s: 300` / `flame_trip_hold_s: 900`; leave all other entity IDs unchanged; no Exclusive Session.

## Boundaries & Constraints
**Always:**
- Backup `apps/apps.yaml` → `apps/apps.yaml.pre-5.2` before editing (gitignored like the house file).
- Remove `boiler_water` (and any `r_max` / supply-trip `hold` if present).
- Add confirmed entities (initiative Notes 2026-11-15):
  - `flame_on: binary_sensor.opentherm_bridge_flame_on`
  - `ch_active: binary_sensor.opentherm_bridge_ch_active`
- Set `flame_on_min_s: 300` and `flame_trip_hold_s: 900` (match example / code defaults).
- Ask before changing any pre-existing house entity ID value (AGENTS.md).
- Verify offline with `yaml.safe_load` → drop `module`/`class` → `parse_config`.

**Never:**
- Commit `apps/apps.yaml` or `apps/apps.yaml.*` backups.
- Edit `apps/ha_smart_hvac/*`, `apps.yaml.example`, tests, ADR/`knowledge`/AGENTS/CONTEXT.
- Run `./scripts/run-appdaemon` or require Exclusive Session for this story.
- Infer flame entity IDs by guessing; change Outdoor / plant / zone / climate / FF / TRV IDs without owner confirm.

**Decisions:**
- Flame IDs from initiative Notes 2026-11-15 (already closed).
- Explicit min/hold at defaults (same shape as `apps.yaml.example`), not omit-and-rely-on-code-defaults.
- Existing non-trip entity ID strings stay byte-identical to `apps.yaml.pre-5.2` except removed trip keys and added flame keys.

## I/O & Edge-Case Matrix
| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| Add flame | Confirmed flame entities + min/hold | Parsed `flame_on` / `ch_active` / 300 / 900 | Missing flame → ConfigError |
| Drop trip | Pre-edit has `boiler_water` | Trip keys absent after edit | Leftover trip keys would only land in `ignored_keys`; story still removes them |
| ID stability | Diff vs `apps.yaml.pre-5.2` | No changed values for Outdoor, plant, FF, zones, TRVs, climates | Stop and ask owner if any ID change is needed |
| Offline parse | `parse_config` on house args | Returns `HvacConfig` with flame fields | Fail → fix yaml before done |
| Gitignore | House file + backup | Both ignored; not staged | Do not force-add |

</frozen-after-approval>

## Code Map
- `apps/apps.yaml` (gitignored) — sole edit target; pre-edit has `boiler_water` (L12) and no flame keys; post-edit: no trip keys; `flame_on` / `ch_active` / `flame_on_min_s: 300` / `flame_trip_hold_s: 900`.
- `apps/apps.yaml.pre-5.2` — pre-edit backup (gitignored via `apps/apps.yaml.*`).
- `apps.yaml.example` — shape reference only (L14–18 flame block); do not edit.
- `apps/ha_smart_hvac/config.py` — `parse_config` offline verify; required `flame_on`/`ch_active`; optional min/hold defaults 300/900; unknown trip keys → `ignored_keys`; do not change.
- Initiative Notes 2026-11-15 — confirmed flame IDs in `_bmad-output/initiative-weather-swt-supply-trip/initiative-weather-swt-supply-trip.md` Notes (“House entities closed”).
- Continuity from story 5.1 plan: law + example already shipped; house yaml is entry id=2 only.

## Tasks & Acceptance
**Execution:**
- [x] Backup `apps/apps.yaml` → `apps/apps.yaml.pre-5.2`.
- [x] Remove `boiler_water` (and any `r_max` / supply hold); add confirmed `flame_on` / `ch_active` plus `flame_on_min_s: 300` / `flame_trip_hold_s: 900`; keep all other entity ID values unchanged; note flame purpose in header comments.
- [x] Offline `parse_config` verify: flame fields match confirmed IDs + 300/900; trip keys absent from raw yaml; other IDs unchanged vs backup.

**Acceptance Criteria:**
- Given the pre-5.2 backup, when comparing entity ID values after the edit, then Outdoor, plant, FF, zone temperatures, weights, names, climates, and TRV closure/accuracy IDs are unchanged unless the owner confirmed a change.
- Given the edited house yaml, when args are passed through `parse_config`, then `flame_on` and `ch_active` are the confirmed entities and `flame_on_min_s` / `flame_trip_hold_s` are 300 / 900.
- Given the edited house yaml top-level `hvac` keys, when inspected, then `boiler_water`, `r_max`, and supply-trip `hold` are absent as keys (not a substring search — `flame_trip_hold_s` may remain).
- Given `git check-ignore`, when checked, then `apps/apps.yaml` and `apps/apps.yaml.pre-5.2` are ignored (and thus not staged or listed as untracked).

## Implementation Notes
- 2026-11-16: Backed up to `apps/apps.yaml.pre-5.2`; removed `boiler_water`; added confirmed `flame_on` / `ch_active` plus `flame_on_min_s: 300` / `flame_trip_hold_s: 900`; header comments note flame + backup.
- Pre-5.2 backup had no `r_max` or supply-trip `hold` top-level keys; post-edit confirms those keys remain absent (only `boiler_water` was removed).
- Offline verify used `PYTHONPATH=apps`; pre→post ID stability holds for all non-trip/non-flame keys (zones/TRV/FF/plant/outdoor unchanged).
- House yaml remains gitignored; tracked artifact for this story is this plan file.

## Plan Change Log
- 2026-11-16: House commission completed (backup + remove trip + add flame); Implementation Notes filled.
- 2026-11-16: Formal review patches — hold key AC/verify, ID-stability command, Notes r_max/hold, gitignore AC, markdown blanks, trailing newline.

## Review Triage Log
| lens | finding | verdict | route | evidence |
| --- | --- | --- | --- | --- |
| quick | (none) | — | — | No unmet ACs, rule breaks, or bugs on inspection |
| formal | hold AC/verify + ID-stability cmd + notes/gitignore/hygiene | medium/low → patch | patch×6 | Code Review 2026-11-16; 6 rejected |

## Design Notes
House file only; flame law already shipped in 5.1. Match example key shape with confirmed house IDs. No live AppDaemon session.

## Verification
**Commands:**
- `PYTHONPATH=apps uv run python -c "import yaml; from pathlib import Path; from ha_smart_hvac.config import parse_config; text=Path('apps/apps.yaml').read_text(); raw=yaml.safe_load(text)['hvac']; assert 'boiler_water' not in raw and 'r_max' not in raw and 'hold' not in raw; args={k:v for k,v in raw.items() if k not in ('module','class')}; cfg=parse_config(args); assert cfg.flame_on=='binary_sensor.opentherm_bridge_flame_on'; assert cfg.ch_active=='binary_sensor.opentherm_bridge_ch_active'; assert cfg.flame_on_min_s==300.0; assert cfg.flame_trip_hold_s==900.0; pre=yaml.safe_load(Path('apps/apps.yaml.pre-5.2').read_text())['hvac']; trip={'boiler_water','r_max','hold'}; flame={'flame_on','ch_active','flame_on_min_s','flame_trip_hold_s'}; assert set(pre)-set(raw)<=trip; assert set(raw)-set(pre)<=flame; assert all(pre[k]==raw[k] for k in set(pre)&set(raw) if k not in ('module','class'))"` — expected: exit 0
- `git check-ignore -v apps/apps.yaml apps/apps.yaml.pre-5.2` -- expected: both ignored
- `git status --short` -- expected: no staged/untracked house yaml (ignored)

**Manual checks (if no CLI):**
- Diff house yaml vs `apps/apps.yaml.pre-5.2`: only trip keys removed and flame block added (header comments may also change).

## Code Review

### 2026-11-16
**Code review complete.** 0 `decision-needed`, 6 `patch`, 0 `defer`, 5 rejected.

- [x] [Review][Patch] Verification/AC under-specify supply-trip hold absence [plan:Verification + AC]
- [x] [Review][Patch] Verification Commands omit automated ID-stability check [plan:Verification]
- [x] [Review][Patch] Implementation Notes omit r_max/hold absence [plan:Implementation Notes]
- [x] [Review][Patch] Plan missing trailing newline [plan:EOF]
- [x] [Review][Patch] Git AC vs check-ignore strength mismatch [plan:AC + Verification]
- [x] [Review][Patch] Markdown blank lines before later ## sections [plan:Plan Change Log / Review Triage Log]

Rejected:
- R4 live activation undefined — false: Design Notes already say no live AppDaemon session
- R6 flame_trip_hold_s ==900 type — false: float compares equal to 900 and 900.0
- R7 rollback path — low rejected: rarely needed; cp-from-backup noise for HITL
- R8 byte-identical Decision vs comments — low rejected: AC already scopes entity IDs
- R11 Approach omits header comments — rejected: fix would edit frozen intent
- R13 diff hunk omits zones — false: truncated review hunk, not a product defect
