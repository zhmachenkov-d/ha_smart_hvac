---
id: 2
type: story
title: "Commission house apps.yaml for house-idle soft-close"
parent: epic-trv-house-idle-soft-close
covers: [R1, R2]
after: [1]
hitl: true
risk: medium
refined: true
---

# Commission house apps.yaml for house-idle soft-close
## Description
HITL: operator updates gitignored house `apps/apps.yaml` to the schema from entry 1 — add explicit `trv_soft_close_hold_s: 300`, keep `valve_closure_floor: 80`, drop `accuracy` from commissioned Sonoff TRVs (closure-only); house entity IDs unchanged unless the owner confirms. No Exclusive Session.

1. Makes the live house yaml load under the 7.1 closure-only + hold schema so epic R1/R2 soft-close can run on the next AppDaemon start.
2. Retires leftover `accuracy` keys that now ConfigError after 7.1.
3. Keeps house entity IDs stable unless the owner confirms a change (AGENTS.md / epic C5).
4. Proves the edit offline (backup + parse + gitignore) without Exclusive Session.

## Requirements
1. **Pre-edit backup** (R1, R2)
   **Given** the current house `apps/apps.yaml`
   **When** the operator begins this story
   **Then** a copy exists at `apps/apps.yaml.pre-7.2` before any edit
   **Failure:** edit proceeds with no `.pre-7.2` baseline for entity-ID compare

2. **Explicit hold and kept floor** (R1)
   **Given** the house yaml after edit
   **When** the top-level `hvac` keys are inspected and the house commission is loaded the same way Production loads AppDaemon args
   **Then** raw yaml includes `trv_soft_close_hold_s: 300` and `valve_closure_floor: 80`
   **And** load succeeds with hold **300** and floor **80**
   **Failure:** hold omitted or not 300, floor changed without owner confirmation, or load rejects the keys

3. **Closure-only Sonoff TRVs** (R1, epic C5)
   **Given** the four commissioned Sonoff mappings (livingroom×2, bedroom, childroom)
   **When** the house yaml is edited and the house commission is loaded the same way Production loads AppDaemon args
   **Then** each keeps its `valve_closure` entity and has no `accuracy` key
   **And** raw yaml under `zones` has zero `accuracy:` keys
   **And** a copy that re-inserts `accuracy` on any of those mappings fails load
   **Failure:** any accuracy key remains, a Sonoff loses closure, or leftover accuracy still loads

4. **Generic climates stay plain** (R1)
   **Given** bathroom, kitchen, and wc thermostat entries
   **When** the house yaml is edited
   **Then** those entries remain climate-only strings (no TRV-law keys added)
   **Failure:** a generic becomes a mapping or gains closure/accuracy keys

5. **Entity-ID stability** (epic C5)
   **Given** `apps/apps.yaml.pre-7.2` and the edited house yaml
   **When** entity-ID string values are compared (Outdoor, plant, flame, ch_active, zone temperatures, weights, names, climates, valve_closure)
   **Then** every value matches the backup unless the owner confirmed a specific change and that change is recorded
   **Failure:** an entity ID changes without a recorded owner confirmation

6. **Header matches closure-only law** (R1)
   **Given** the house yaml header comments
   **When** the edit is complete
   **Then** the header names `trv_soft_close_hold_s` and says commissioned Sonoff TRVs use closure only
   **And** the header has no line that pairs closure with `accuracy` as required commission keys
   **And** it notes the `.pre-7.2` backup
   **Failure:** header still requires or lists `accuracy` beside closure for soft-close commission

7. **Gitignored; no force-add** (epic C5)
   **Given** `apps/apps.yaml` and `apps/apps.yaml.pre-7.2`
   **When** `git check-ignore` and `git status` are checked
   **Then** both paths are ignored and neither is staged or force-added
   **Failure:** house yaml or backup appears tracked or staged

## Boundaries
- Must not change: weather-curve Set Water Temperature law; flame short-on observe/latch/clear; Exclusive Session; Heating Demand = thermostat `hvac_action=heating`
- Must not: edit App code or tests; edit `apps.yaml.example`; amend ADR/CONTEXT/AGENTS/`knowledge/` (story 7.3); run `./scripts/run-appdaemon` or require Exclusive Session unless the user asks; infer or invent entity IDs; change `valve_closure_floor` without owner confirmation; leave any `accuracy` key on a commissioned TRV
- Allowed diffs vs `.pre-7.2`: add `trv_soft_close_hold_s`, remove every `accuracy` key, header/comment updates, and only owner-confirmed entity-ID or floor changes
- Soft-close law and example schema already shipped in entry 1; this story only commissions the house file
- If the user asks for Exclusive Session during this story: defer live bind — Done remains offline backup + parse + ID stability + gitignore; hand off restart outside this story

## References
- parent — `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-trv-house-idle-soft-close/epic-trv-house-idle-soft-close.md`, Requirements R1–R2; Constraints C5, C7; Notes Decision house yaml HITL / config-only
- prerequisite — `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-trv-house-idle-soft-close/tickets/story-tracer-trv-house-idle-soft-close.md`, Requirements (closure-only + hold schema; house yaml owned by 7.2)
- sibling pattern — `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-replace-supply-trip-with-flame/tickets/story-commission-house-apps-yaml-for-flame-short-on-plan.md`, Always/Never backup + offline parse + gitignore

## Notes
- Decision: keep `valve_closure_floor: 80` (no adjust unless owner supplies another value) (2026-11-20).
- Decision: write explicit `trv_soft_close_hold_s: 300` in house yaml (match example; do not omit-and-rely-on-default) (2026-11-20).
- Decision: house entity IDs unchanged vs `.pre-7.2` (2026-11-20).
- Decision: strip `accuracy` only from livingroom×2, bedroom, childroom; leave bathroom/kitchen/wc climate-only (2026-11-20).
- Decision: config-only — offline parse verify; no Exclusive Session / `./scripts/run-appdaemon` unless the user asks (2026-11-20).
- Risk reason: wrong house yaml leaves Production unable to load after 7.1 (accuracy ConfigError) or soft-closes the wrong entities.
- HITL step: ask before changing any house entity ID (AGENTS.md); owner confirmation required for floor retune.
- Shared R1/R2: house commission here; law + example in entry 1; docs amend in entry 3.
- Waits on entry 1 because: schema + example must exist before house applies them.
- Offline verify shape (builder Notes): `yaml.safe_load` → drop `module`/`class` → `parse_config`; assert hold 300, floor 80, four closure-only TRVs, zero accuracy keys; compare entity IDs to `.pre-7.2`; `git check-ignore` on house + backup.
