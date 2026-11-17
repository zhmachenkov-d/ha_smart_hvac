---
title: 'Refactor sweep'
type: 'chore'
ticket: '3'
created: '2026-11-17'
status: 'built'
baseline_revision: 'e8798fff5909d165d7ce7e64f489c363538ef5a1'
route: 'oneshot'
route_source: 'auto'
risk: 'low'
review: 'quick'
review_source: 'auto'
lenses_ran: ['context-free']
review_loop_iteration: 0
context:
  - '{project-root}/CONTEXT.md'
  - '{project-root}/AGENTS.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent
**Problem:** Epic 5 deferred notes still call out open flame short-on leftovers from 5.1’s token split, and a few supply-era test names remain after the trip removal.

**Approach:** Close only this epic’s deferred leftovers — add the still-missing arm/truncate goldens, rename supply-era test helpers, then prune settled deferred-work bullets with cites. No new product laws; docs stay in epic 6.

## Boundaries & Constraints
**Always:**
- Scope = epic-replace-supply-trip-with-flame deferred bullets from `deferred-work.md` (2026-11-16 token split) plus supply-era naming orphans in tests.
- Still deliver: restart-mid-flame arm golden (cold construct / wiped `since` while `flame_on` still on under open gate → no arm; True→False without `since` does not latch); dedicated `flame_trip_hold_s` 900.9→900 truncate golden.
- Prune-as-covered (cite existing tests/comments, no new product AC): E1 combined example comment (`apps.yaml.example` L14); named orphan_hold / plant_off / idle ports; None/unavailable→on + CH-already-on arm edges; latched flame/ch_active no-SWT; meta house-yaml-not-in-verify (settled by 5.2 + `tests/test_dual_layout.py`).
- Rename `_two_zone_trip_args` → `_two_zone_args` and `test_latched_trip_path_does_not_use_critical_zone` → `test_latched_demand_does_not_use_critical_zone` (call sites only).
- After settlement, prune only this epic’s flame deferred bullets; leave epic-3 / epic-4 / docs-hygiene bullets alone.
- `uv run pytest` and `uv run ruff check apps/ha_smart_hvac tests` clean.

**Never:**
- New product laws (no flame gate/latch/clear changes; no CAP-7; no house `apps/apps.yaml` edits).
- Restore supply rise-rate trip; edit AGENTS/CONTEXT/ADR/`knowledge/` (epic 6).
- Expand into optional DRY of triplicate flame RAM init blocks, or a separate closing e2e suite.
- Touch epic-3 / epic-4 deferred bullets or frozen 5.1/5.2 Intent.

**Decisions:**
- Restart-mid-flame = RAM `since` absent while flame already on under open gate (cold construct or wiped mid-burn); not a rising off→on arm.
- V1 default golden is additive beside existing 90.9→90; do not remove the 90.9 case.
- E1 / named ports / most U1·S1 / latched no-SWT / house-meta = prune with cites only.

## I/O & Edge-Case Matrix
| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| Restart mid-flame | Open gate; `flame_on` already on; `_flame_on_since is None` | No arm; True→False does not latch | Same as open-gate fall without since |
| Hold truncate default | yaml `flame_trip_hold_s: 900.9` | Parsed hold == 900 | Existing `<1` / open-unit rejects unchanged |
| Rename helpers | Callers of old trip names | Compile/import under new names; behavior unchanged | N/A |
| Deferred prune | Epic-5 token-split bullets after ACs green | Those bullets removed; epic-3/4/docs remain | N/A |

</frozen-after-approval>

## Code Map
- `tests/test_hvac_app.py` — add restart-mid-flame golden near other flame arm tests (~L1306+); rename `_two_zone_trip_args` (L1629, call ~L1689) → `_two_zone_args`; rename `test_latched_trip_path_does_not_use_critical_zone` (L2014) → `test_latched_demand_does_not_use_critical_zone`. Reuse `_flame_trip_app` / `_fire_flame`; do not change production flame handlers.
- `tests/test_config.py` — add `900.9→900` beside `test_parse_flame_trip_hold_truncates_fractional_seconds` (~L330, today 90.9→90); keep 90.9 case.
- `apps.yaml.example` — L14 combined flame comment already covers E1; **do not edit** unless a prune cite needs the exact line.
- `_bmad-output/.../deferred-work.md` — prune only the five 5.1 token-split bullets (L31–45); add a short Settled note citing the covering tests/comments + new goldens; leave epic-3/4/docs bullets.
- `apps/ha_smart_hvac/*` — **no change** (no supply-trip orphans left; flame path stays).
- Out of scope: house yaml, AGENTS/CONTEXT/ADR, epic-6 docs, triplicate `_flame_*` RAM DRY in CZ helpers.

## Tasks & Acceptance
**Execution:**
- [ ] `tests/test_config.py` — add dedicated `flame_trip_hold_s` 900.9→900 truncate assert; keep 90.9→90.
- [ ] `tests/test_hvac_app.py` — restart-mid-flame arm golden; rename `_two_zone_trip_args` + `test_latched_trip_path_does_not_use_critical_zone` and their call sites.
- [ ] `deferred-work.md` — after green, prune epic-5 token-split bullets; Settled note with cites; leave other epics’ bullets.
- [ ] Verify — pytest + ruff below.

**Acceptance Criteria:**
- Given open observe gate and `flame_on` already on with `_flame_on_since is None`, when True→False fires, then no latch and SWT is not written for the trip.
- Given yaml `flame_trip_hold_s: 900.9`, when parsed, then hold seconds == 900; 90.9→90 still passes.
- Given the suite, when searched, then `_two_zone_trip_args` and `test_latched_trip_path_does_not_use_critical_zone` are gone (renamed).
- Given epic-5 deferred notes after this sweep, when inspected, then the five 5.1 token-split bullets are gone (pruned with cites); epic-3 / epic-4 / docs-hygiene bullets remain.
- Given the suite, when `uv run pytest` and `uv run ruff check apps/ha_smart_hvac tests` run, then both are clean.

## Implementation Notes
- Parametrized truncate golden `(90.9, 90)` + `(900.9, 900)` in `test_parse_flame_trip_hold_truncates_fractional_seconds`.
- Added `test_restart_mid_flame_does_not_arm_or_latch_on_fall` via `_flame_trip_app(flame_on="on")` then on→off.
- Renamed `_two_zone_trip_args` → `_two_zone_args`; `test_latched_trip_path_does_not_use_critical_zone` → `test_latched_demand_does_not_use_critical_zone`.
- Pruned epic-5 token-split deferred bullets into Settled note with cites; left epic-3/4/docs bullets.
- Verification: 362 pytest passed; ruff clean. No production App edits.
- Review patch: restart golden now covers mid-burn since wipe + on→on no-rearm before fall (was duplicate of fall-without-since).
## Plan Change Log
- 2026-11-17: Oneshot scope from epic-5 deferred audit — open goldens + rename orphans; prune covered bullets with cites; docs → epic 6.
## Review Triage Log
| Finding | Verdict | Route | Evidence |
| --- | --- | --- | --- |
| Restart golden unused flame_on="on"; duplicates fall-without-since | medium | patch | Strengthened: mid-burn wipe + on→on no-rearm + fall; unique vs `test_open_gate_fall_without_since_does_not_latch` |
| Deferred Settled over-claims restart coverage | medium | patch | Same root cause; Settled bullet now cites wipe+on→on+fall |

## Design Notes
No production flame/SWT edits: live supply-trip path is already gone; leftover work is test goldens, naming, and deferred prune. Restart-mid-flame locks RAM-only `since` (no rising edge after cold/wipe). House meta AC is documentation of ownership, not a new pytest — settled by 5.2 commission + dual_layout ignore pin.

## Verification
**Commands:**
- `uv run pytest` -- expected: pass
- `uv run ruff check apps/ha_smart_hvac tests` -- expected: clean

**Manual checks (if no CLI):**
- `deferred-work.md`: epic-5 token-split section pruned; epic-3/4/docs bullets still present.
- `rg '_two_zone_trip_args|test_latched_trip_path_does_not_use_critical_zone'` → no matches.
