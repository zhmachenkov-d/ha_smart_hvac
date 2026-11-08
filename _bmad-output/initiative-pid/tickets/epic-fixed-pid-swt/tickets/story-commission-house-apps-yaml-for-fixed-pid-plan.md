---
title: '1.6 Commission house apps.yaml for fixed PID'
type: 'chore'
ticket: '6'
created: '2026-11-08'
status: done
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

Oneshot: `.gitignore` (committed) gains `apps/apps.yaml.*` (covers `apps/apps.yaml.pre-pid` and any later house-yaml backup); locally, `apps/apps.yaml.pre-pid` is created as a byte copy of the house yaml and `apps/apps.yaml` is rewritten (both gitignored). The commit carries `.gitignore`, this plan and a deferred-work "Resolved in 1.6" note; the house yaml never leaves the workstation.

Verified: `parse_config` on the house yaml → `ignored_keys == ()`, base 42 in [42, 60], `kp 2.0, ki 1.0, i_term [-15, 15]`, interval 300; plant and all 6 zone entity sets equal `apps.yaml.pre-pid`, and the `zones:` block is byte-identical; `git check-ignore` covers the backup.

`apps/apps.yaml.pre-pid` is an entity-ID reference, not a rollback: Weather Feedforward / Outdoor code is gone since 1.3, so restoring it on the current App only logs the legacy keys as `ignored_keys` and runs PID defaults at `control_interval: 60`. Rolling back to the weather curve needs a pre-1.3 App release plus this backup.

## Review Triage Log

### 2026-11-08 (quick)
**Triage:** 0 high, 1 medium, 3 low → 1 human-resolved, 2 patched, 1 rejected; 0 false.

- medium, HALT → human — `pid.ki: 0.02` reads as an old-unit value: with ki in 1/h and kp 2, Ti = 100 h, the I-term is out of reach and the loop runs P-only (retro SR1 again; `docs/house-calibration.md` upgrade note). Operator renegotiated to `ki: 1.0` (Ti = 2 h); house yaml re-verified.
- low, rejected — `i_term_min: -15` unreachable while `base_water_temp == setpoint_min` (negative e with ∫ ≤ 0 saturates low and freezes ∫, as `docs/house-calibration.md` §3 documents): harmless; the bound becomes live if base is later raised above 42.
- low, patch — Implementation Notes omitted the local `apps/apps.yaml.pre-pid` → notes rewritten.
- low, patch — `deferred-work.md` lacked a "Resolved in 1.6" line for the entry-5 base deferral → added.

## Verification

**Commands:**
- `PYTHONPATH=apps uv run python -c "import yaml; from ha_smart_hvac.config import parse_config; d = yaml.safe_load(open('apps/apps.yaml'))['hvac']; c = parse_config(d); assert not c.ignored_keys, c.ignored_keys; p = c.pid; assert (c.base_water_temp, p.kp, p.ki, p.i_term_min, p.i_term_max, c.control_interval) == (42, 2, 1.0, -15, 15, 300), c; assert all(set(z) <= {'name', 'temperature', 'thermostats', 'weight'} for z in d['zones']); print('ok')"` -- expected: `ok` (parse succeeds — base range is enforced by `parse_config`; Decisions values locked; zone sub-keys known, since `ignored_keys` does not cover them)
- `uv run python -c "import yaml; a, b = (yaml.safe_load(open(f))['hvac'] for f in ('apps/apps.yaml', 'apps/apps.yaml.pre-pid')); k = ('plant_management', 'plant_setpoint'); assert [a[x] for x in k] == [b[x] for x in k] and a['zones'] == b['zones']; print('entities ok')"` -- expected: `entities ok` (plant entity IDs and the whole parsed `zones:` block equal the backup; `outdoor_temperature` is left out on purpose — the ticket removes it)
- `git check-ignore apps/apps.yaml.pre-pid` -- expected: path printed (ignored); `git status --short` shows no `apps/` file

## Code Review

### 2026-11-08
**Code review complete.** 0 `decision-needed`, 5 `patch`, 0 `defer`, 9 rejected.

- [x] [Review][Patch] Verification command does not lock the commissioned values (kp / ki / i_term / interval / base) or zone sub-keys [story-commission-house-apps-yaml-for-fixed-pid-plan.md:## Verification]
- [x] [Review][Patch] Entity-equality check is not reproducible — no runnable command for the entity-set / `zones:` block comparison [story-commission-house-apps-yaml-for-fixed-pid-plan.md:## Verification]
- [x] [Review][Patch] `.gitignore` covers only the exact backup filename; use `apps/apps.yaml.*` [.gitignore:165]
- [x] [Review][Patch] Backup is not a rollback (WFF code is gone since 1.3); Implementation Notes do not say so [story-commission-house-apps-yaml-for-fixed-pid-plan.md:## Implementation Notes]
- [x] [Review][Patch] `deferred-work.md` 1.6 section sits before the earlier 1.7 code-review deferral block [_bmad-output/initiative-pid/deferred-work.md:42]

**Rejected**
- low — `outdoor_temperature` is an entity ID removed despite "only non-entity keys": the ticket mandates the removal; fix would edit the frozen intent.
- low — no rationale for `kp: 2` / `i_term_min: -15`: ticket allows house-chosen values; Decisions are frozen intent.
- low — no Boundaries & Constraints section: would edit the frozen intent; constraints are in Approach and AGENTS.md.
- false — `review_loop_iteration: 0` despite a loop: the counter increments only on an intent_gap / bad_plan loopback, which did not happen.
- false — `control_interval: 300` delays demand response: tick-only demand writes at 300 s are epic R5/R6 and SR3 (accepted).
- low — base 42 + `i_term_max: 15` caps e=0 SWT at 57: arithmetic correct, but values are the operator's frozen Decisions; watch at first Exclusive Session.
- false — ∫ cleared on every idle blip: epic R2/R3 and SR3 by design, not a 1.6 defect.
- low — strict reading of "entity IDs equal .pre-pid" fails: same intent tension as above; the ticket itself requires removing the outdoor sensor.
- false — backup byte-identity / copy order unprovable: backup holds the full pre-commission shape and an older mtime; nothing indicates divergence.
