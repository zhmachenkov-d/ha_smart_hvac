---
title: '1.6 Commission house apps.yaml for fixed PID'
type: 'chore'
ticket: '6'
created: '2026-11-08'
status: 'built'
baseline_revision: '8342bf221ca32094c7a5efc1a6c907cb66698ecb'
route: 'oneshot'
route_source: 'auto'
risk: 'medium'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The house `apps/apps.yaml` is still the Weather Feedforward commission: it carries `outdoor_temperature` and `weather_feedforward` (reported by `parse_config` as `ignored_keys` and logged as a WARNING since 1.7), has no explicit `base_water_temp` or `pid` nest (it runs on the clamped default 42 and C4 defaults by accident), and keeps `control_interval: 60` instead of the epic's 300 s tick (retro A5 / SR4).

**Approach:** Back up the house yaml to `apps/apps.yaml.pre-pid` (gitignored, never committed), then rewrite only non-entity keys: remove `outdoor_temperature` and `weather_feedforward`, add an explicit `base_water_temp` within [42, 60] and the `pid` nest (`kp` / `ki` / `i_term_min` / `i_term_max`), and set `control_interval`. Every entity ID and zone stays byte-identical. No live run — Exclusive Session commissioning waits for epic-pid-domain-docs.

**Decisions (operator, 2026-11-08):** `base_water_temp: 42` (= `setpoint_min`, today's effective base); `pid: {kp: 2, ki: 1.0, i_term_min: -15, i_term_max: 15}` (house-chosen kp / I-term bounds; `ki` renegotiated from 0.02 to the C4 1.0/h after review, 2026-11-08); `control_interval: 300`; no zone `weight` keys (all default 1.0).

</frozen-after-approval>

## Implementation Notes

Oneshot: `.gitignore` (committed) gains `apps/apps.yaml.pre-pid`; locally, `apps/apps.yaml.pre-pid` is created as a byte copy of the house yaml and `apps/apps.yaml` is rewritten (both gitignored). The commit carries `.gitignore`, this plan and a deferred-work "Resolved in 1.6" note; the house yaml never leaves the workstation.

Verified: `parse_config` on the house yaml → `ignored_keys == ()`, base 42 in [42, 60], `kp 2.0, ki 1.0, i_term [-15, 15]`, interval 300; plant and all 6 zone entity sets equal `apps.yaml.pre-pid`, and the `zones:` block is byte-identical; `git check-ignore` covers the backup.

## Review Triage Log

### 2026-11-08 (quick)
**Triage:** 0 high, 1 medium, 3 low → 1 human-resolved, 2 patched, 1 rejected; 0 false.

- medium, HALT → human — `pid.ki: 0.02` reads as an old-unit value: with ki in 1/h and kp 2, Ti = 100 h, the I-term is out of reach and the loop runs P-only (retro SR1 again; `docs/house-calibration.md` upgrade note). Operator renegotiated to `ki: 1.0` (Ti = 2 h); house yaml re-verified.
- low, rejected — `i_term_min: -15` unreachable while `base_water_temp == setpoint_min` (negative e with ∫ ≤ 0 saturates low and freezes ∫, as `docs/house-calibration.md` §3 documents): harmless; the bound becomes live if base is later raised above 42.
- low, patch — Implementation Notes omitted the local `apps/apps.yaml.pre-pid` → notes rewritten.
- low, patch — `deferred-work.md` lacked a "Resolved in 1.6" line for the entry-5 base deferral → added.

## Verification

**Commands:**
- `PYTHONPATH=apps uv run python -c "import yaml; from ha_smart_hvac.config import parse_config; c = parse_config(yaml.safe_load(open('apps/apps.yaml'))['hvac']); assert not c.ignored_keys, c.ignored_keys; assert c.setpoint_min <= c.base_water_temp <= c.setpoint_max; print(c)"` -- expected: succeeds, prints the commissioned values
- Entity check: every `plant_*`, zone `temperature` and `thermostats` value in `apps/apps.yaml` equals `apps/apps.yaml.pre-pid` (script compares the parsed entity sets) -- expected: equal
- `git check-ignore apps/apps.yaml.pre-pid` -- expected: path printed (ignored); `git status --short` shows no `apps/` file
