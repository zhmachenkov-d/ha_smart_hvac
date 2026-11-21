---
title: 'Commission house apps.yaml for house-idle soft-close'
type: 'feature'
ticket: '2'
created: '2026-11-20'
status: done
---

<intent-contract>

## Intent
**Problem:** House `apps/apps.yaml` still commissions Sonoff TRVs with `accuracy` and lacks `trv_soft_close_hold_s`, so Production cannot load under the 7.1 closure-only + hold schema and epic R1/R2 soft-close cannot run on the next AppDaemon start.

**Approach:** Offline HITL-shaped edit of gitignored house yaml only: backup to `.pre-7.2`, add explicit `trv_soft_close_hold_s: 300`, keep `valve_closure_floor: 80`, drop every `accuracy` key (closure-only Sonoffs), leave all entity IDs unchanged, prove with parse_config + gitignore — no Exclusive Session.

</intent-contract>

## Code Map
- `apps/apps.yaml` (gitignored) — sole edit target; today: floor 80, four Sonoffs with accuracy (livingroom×2, childroom, bedroom), no `trv_soft_close_hold_s`; generics bathroom/kitchen/wc are plain climate strings.
- `apps/apps.yaml.pre-7.2` — create as byte-identical pre-edit backup (gitignore `apps/apps.yaml.*`).
- `apps.yaml.example` — shape reference only (`trv_soft_close_hold_s: 300`, floor 80, closure-only); do not edit.
- `apps/ha_smart_hvac/config.py` — read-only offline verify via `parse_config`; leftover `accuracy` → ConfigError (L137–138); hold default/parse like flame hold.
- Continuity: law + example shipped in entry 1; sibling pattern story 5.2 plan (backup → edit → offline parse → gitignore).

## Tasks & Acceptance
**Execution:**
- [x] `apps/apps.yaml` → `apps/apps.yaml.pre-7.2` — copy before any edit (entity-ID baseline).
- [x] `apps/apps.yaml` — add `trv_soft_close_hold_s: 300`; keep `valve_closure_floor: 80`; remove all four `accuracy` keys; keep every other entity-ID / weight / name / climate / closure value byte-identical; update header for hold + closure-only + `.pre-7.2` note (no accuracy as required commission).
- [x] Offline verify — `yaml.safe_load` → drop `module`/`class` → `parse_config`; assert hold 300, floor 80, four closure-only commissioned TRVs, zero `accuracy:` under zones; ID stability vs backup; re-insert accuracy fails load; `git check-ignore` on house + backup.

**Acceptance Criteria:**
- Given the current house yaml, when the story begins, then `apps/apps.yaml.pre-7.2` exists before any edit.
- Given the edited house yaml, when top-level `hvac` keys are inspected and args load via `parse_config`, then raw yaml has `trv_soft_close_hold_s: 300` and `valve_closure_floor: 80`, and load yields hold 300 and floor 80.
- Given the four Sonoff mappings (livingroom×2, bedroom, childroom), when edited and loaded, then each keeps its `valve_closure` entity with no `accuracy` key, raw yaml under `zones` has zero `accuracy:` keys, and a copy that re-inserts `accuracy` on any of those mappings fails load.
- Given bathroom, kitchen, and wc thermostat entries, when the house yaml is edited, then those entries remain climate-only strings (no TRV-law keys).
- Given `apps/apps.yaml.pre-7.2` and the edited house yaml, when entity-ID string values are compared (Outdoor, plant, flame, ch_active, zone temperatures, weights, names, climates, valve_closure), then every value matches the backup (no owner-confirmed ID or floor change in this run).
- Given the house yaml header comments, when the edit is complete, then the header names `trv_soft_close_hold_s`, says commissioned Sonoff TRVs use closure only, does not pair closure with `accuracy` as required keys, and notes the `.pre-7.2` backup.
- Given `apps/apps.yaml` and `apps/apps.yaml.pre-7.2`, when `git check-ignore` and `git status` are checked, then both paths are ignored and neither is staged or force-added.

## Implementation Notes
- 2026-11-20: Backed up to `apps/apps.yaml.pre-7.2`; added `trv_soft_close_hold_s: 300`; kept floor 80; removed four Sonoff `accuracy` keys; header names hold + closure only + `.pre-7.2`; all entity IDs unchanged.
- Offline verify: `parse_config` hold 300 / floor 80 / four commissioned; re-insert accuracy → ConfigError; both house + backup gitignored.
- Header verify assert: forbid "closure/accuracy" pairing as required commission keys (header may say "no accuracy").
- Tracked artifact is this plan file; house yaml remains gitignored (same as 5.2).

## Plan Change Log
- 2026-11-20: House commission completed (backup + hold + drop accuracy); Implementation Notes filled; verify header assert adjusted.
- 2026-11-20: Review patch — removed stray `)` at plan EOF.

## Review Triage Log

### 2026-11-20 — Review pass
- verdicts: 1 findings — high 0, medium 0, low 1, false 0, maybe-false 0
- findings:
  - `[low]` `[patch]` Plan file EOF stray `)` and missing trailing newline — verified at plan EOF; removed stray `)` and ensured final newline
## Design Notes
Config-only house slice after 7.1. Keep floor 80 and all entity IDs unchanged — no owner confirmation needed when values do not change. Match example key shape; do not edit App code, example, tests, or docs (7.3). Route oneshot: ticket risk medium, yaml-only edit well under 100 LOC.

## Verification
**Commands:**
- `test -f apps/apps.yaml.pre-7.2 || cp apps/apps.yaml apps/apps.yaml.pre-7.2` (before edit) — expected: `.pre-7.2` exists before mutation
- `PYTHONPATH=apps uv run python <<'PY'
import copy, yaml
from pathlib import Path
from ha_smart_hvac.config import parse_config, ConfigError
text = Path("apps/apps.yaml").read_text()
raw = yaml.safe_load(text)["hvac"]
pre = yaml.safe_load(Path("apps/apps.yaml.pre-7.2").read_text())["hvac"]
assert raw.get("trv_soft_close_hold_s") == 300 and raw.get("valve_closure_floor") == 80
assert sum(1 for z in raw["zones"] for t in z["thermostats"] if isinstance(t, dict) and "accuracy" in t) == 0
gens = {"bathroom", "kitchen", "wc"}
assert all(isinstance(t, str) for z in raw["zones"] if z["name"] in gens for t in z["thermostats"])
args = {k: v for k, v in raw.items() if k not in ("module", "class")}
cfg = parse_config(args)
assert cfg.trv_soft_close_hold_s == 300 and cfg.valve_closure_floor == 80.0
c = [t for z in cfg.zones for t in z.thermostats if t.commissioned]
assert len(c) == 4 and all(t.valve_closure for t in c)
assert set(raw) - set(pre) <= {"trv_soft_close_hold_s"}
assert all(pre[k] == raw[k] for k in ("outdoor_temperature", "plant_management", "plant_setpoint", "flame_on", "ch_active"))
assert [(z["name"], z["temperature"], z["weight"]) for z in pre["zones"]] == [(z["name"], z["temperature"], z["weight"]) for z in raw["zones"]]
clim = lambda h: [t if isinstance(t, str) else t["climate"] for z in h["zones"] for t in z["thermostats"]]
clos = lambda h: [t["valve_closure"] for z in h["zones"] for t in z["thermostats"] if isinstance(t, dict)]
assert clim(pre) == clim(raw) and clos(pre) == clos(raw)
hdr = text.split("hvac:", 1)[0]
assert "trv_soft_close_hold_s" in hdr and "closure only" in hdr.lower() and "pre-7.2" in hdr
assert "closure/accuracy" not in hdr.lower() and "closure and accuracy" not in hdr.lower()
bad = copy.deepcopy(args)
bad["zones"][1]["thermostats"][0]["accuracy"] = "number.x"
try:
    parse_config(bad)
    raise SystemExit("expected ConfigError")
except ConfigError:
    pass
print("ok")
PY` — expected: prints `ok`, exit 0
- `git check-ignore -v apps/apps.yaml apps/apps.yaml.pre-7.2` — expected: both ignored
- `git status --short` — expected: no staged/untracked house yaml (ignored)

**Manual checks (if no CLI):**
- Diff house yaml vs `apps/apps.yaml.pre-7.2`: only `trv_soft_close_hold_s` added, all `accuracy` lines removed, header comments updated; entity IDs unchanged.

## Auto Run Result
- **Summary:** Commissioned gitignored house `apps/apps.yaml` for 7.1 closure-only + hold schema: backup `.pre-7.2`, explicit `trv_soft_close_hold_s: 300`, floor 80 kept, four Sonoff `accuracy` keys removed, entity IDs unchanged; offline parse + gitignore verified.
- **Files changed:**
  - `apps/apps.yaml` (gitignored) — hold key, drop accuracy, header update
  - `apps/apps.yaml.pre-7.2` (gitignored) — pre-edit backup
  - plan `story-commission-house-apps-yaml-for-house-idle-soft-close-plan.md` — planning/review artifact
- **Review:** Patched low plan EOF stray `)`. Deferred: none. Rejected: none.
- **Follow-up review recommendation:** false — only one low patch; no high/medium patches this pass.
- **Patched counts:** low 1.
- **Verification:** offline `parse_config` script — ok; `git check-ignore` — both house + backup ignored; house yaml not staged.
- **Residual risks:** Live AppDaemon still needs a Production/local restart outside this story to load the new yaml; docs/AGENTS lag until 7.3.
