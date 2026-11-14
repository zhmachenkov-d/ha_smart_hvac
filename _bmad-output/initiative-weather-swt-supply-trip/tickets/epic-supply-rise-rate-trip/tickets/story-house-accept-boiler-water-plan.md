---
title: 'House: accept boiler_water'
ticket: '3'
created: '2026-11-14'
status: 'built'
baseline_revision: 'bade2292d5f530f6157d666e2671a76684b4c108'
route: 'oneshot'
route_source: 'auto'
risk: 'medium'
review: 'quick'
review_source: 'auto'
lenses_ran: ['quick']
context:
  - _bmad-output/initiative-weather-swt-supply-trip/tickets/epic-supply-rise-rate-trip/epic-supply-rise-rate-trip.md
  - _bmad-output/initiative-weather-swt-supply-trip/tickets/epic-supply-rise-rate-trip/tickets/story-tracer-supply-rise-rate-trip-plan.md
  - _bmad-output/initiative-weather-swt-supply-trip/tickets/epic-weather-curve-swt-restore/tickets/story-commission-house-apps-yaml-for-weather-ff-plan.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent
**Problem:** R7 house accept-check: after 2.1, `boiler_water` is required in parse/example, but Production house `apps/apps.yaml` must be confirmed accepted (not `ignored_keys` WARN) at the Q2 entity id.

**Approach:** HITL verify-only on gitignored house `apps/apps.yaml`: keep existing `boiler_water: sensor.opentherm_bridge_boiler_water_temperature_degc` (no id change); offline `parse_config` must succeed with `boiler_water` commissioned and absent from `ignored_keys`. No App Python / example / live Exclusive Session. Leave optional `r_max`/`hold` unset so defaults 2/900 apply (same as today).

## Boundaries & Constraints
**Always:**
- Touch only house `apps/apps.yaml` if an edit is required; prefer no edit when already accepted.
- Entity id stays `sensor.opentherm_bridge_boiler_water_temperature_degc` unless the owner confirms a change (AGENTS.md HITL).
- Prove with offline `parse_config` on loaded house yaml args — no `./scripts/run-appdaemon`, no Exclusive Session.
- Do not commit `apps/apps.yaml` or `apps/apps.yaml.*` backups.

**Never:**
- Change house entity IDs without owner confirmation.
- Edit App Python, `apps.yaml.example`, or automated tests for this story.
- Add CAP-7 / trip JSON / live AppDaemon verify.
- Rewrite AGENTS.md / CONTEXT.md / ADRs (epic 3).

## I/O & Edge-Case Matrix
| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| Happy accept | House yaml with Q2 `boiler_water` + Outdoor/FF | `parse_config` OK; `cfg.boiler_water` = Q2 id; `"boiler_water" not in ignored_keys` | — |
| Defaults | `r_max`/`hold` omitted | `r_max=2.0`, `hold=900` | — |
| Entity IDs | Pre-check vs post | Plant/zone/Outdoor/boiler ids unchanged | — |
| No edit needed | Already accepted (post-2.1) | Record verify only; no yaml write | — |

</frozen-after-approval>

## Code Map
Continuity: 2.1 put `boiler_water` in `_KNOWN_KEYS` + `_require`; 1.3 kept house `boiler_water` while it was still ignored. Investigation (HEAD `bade229…`): house already has Q2 id; offline parse → `ignored_keys=()`, defaults 2/900.

- `apps/apps.yaml` — **gitignored house commission**; verify (edit only if accept fails).
- `apps/ha_smart_hvac/config.py` — `parse_config` / `_KNOWN_KEYS` / `_require(…, "boiler_water")` — **verify only, do not change**.
- `apps/ha_smart_hvac/models.py` — `HvacConfig.boiler_water` — do not change.
- Do not change: App Python trip path, `apps.yaml.example`, `tests/`.

## Tasks & Acceptance
**Execution:**
- [x] Confirm house `boiler_water` entity id equals `sensor.opentherm_bridge_boiler_water_temperature_degc` (no change unless owner confirms).
- [x] Offline verify: `parse_config` on house `hvac` args succeeds; `boiler_water` commissioned; not in `ignored_keys`.
- [x] If verify fails: minimal house yaml fix (add/fix `boiler_water` only after owner confirm), re-run verify; backup to `apps/apps.yaml.pre-2.3` before any edit.
- [x] Record outcome in plan Implementation Notes (ids unchanged; parse result).

**Acceptance Criteria:**
- Given current house `apps/apps.yaml`, when `parse_config` runs on its `hvac` args, then it succeeds and `"boiler_water" not in cfg.ignored_keys`.
- Given the same yaml, when inspected, then `boiler_water` is `sensor.opentherm_bridge_boiler_water_temperature_degc` unless the owner confirmed a different id.
- Given plant/zone/Outdoor entity ids before this story, when verify completes, then those ids are unchanged.

## Implementation Notes
- 2026-11-14: No house yaml edit — already accepted post-2.1. `boiler_water=sensor.opentherm_bridge_boiler_water_temperature_degc`; offline `parse_config` → `ignored_keys=()`, `r_max=2.0`, `hold=900`. Plant/Outdoor/zones unchanged; no backup created.
## Plan Change Log
- 2026-11-14: Initial oneshot plan for ticket 2.3 / entry 3 (verify-only HITL; house already accepts post-2.1).
## Review Triage Log
- 2026-11-14 quick (context-free): no findings — verify-only plan; house yaml already accepts Q2 boiler_water; ignored_keys empty by inspection.
## Design Notes
- Shared R7: entry 1 = example + parse accept; this entry = house accept-check only.
- Mirror 1.3 verify pattern (offline parse, no Exclusive Session); no new unit tests for gitignored house yaml.
- Explicit house `r_max`/`hold` out of scope — defaults already commissioned by 2.1 parser.

## Verification
**Commands:**
- Offline `parse_config` (expected: success; Q2 `boiler_water`; not in `ignored_keys`; defaults OK if rates omitted):

```sh
PYTHONPATH=apps uv run python - <<'PY'
from pathlib import Path
import yaml
from ha_smart_hvac.config import parse_config
args = yaml.safe_load(Path("apps/apps.yaml").read_text())["hvac"]
args = {k: v for k, v in args.items() if k not in ("module", "class")}
cfg = parse_config(args)
assert cfg.boiler_water == "sensor.opentherm_bridge_boiler_water_temperature_degc"
assert "boiler_water" not in cfg.ignored_keys
assert cfg.r_max == 2.0 and cfg.hold == 900
print("ok", cfg.boiler_water, cfg.ignored_keys, cfg.r_max, cfg.hold)
PY
```
**Manual checks (if no CLI):**
- Open house yaml: top-level `boiler_water` present at Q2 id; no need for `r_max`/`hold` unless desired.