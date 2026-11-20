---
title: 'Tracer: TRV house-idle soft-close'
type: 'feature'
ticket: '1'
created: '2026-11-20'
status: done
baseline_revision: '468ac9fe5aeafedd64cad5fd0c40c849cd796f1a'
route: 'full'
route_source: 'auto'
risk: 'high'
review: 'thorough'
review_source: 'auto'
lenses_ran:
  - blind-hunter
  - edge-case-hunter
  - verification-gap
  - intent-alignment
review_loop_iteration: 0
followup_review_recommended: true
context:
  - '{project-root}/_bmad-output/initiative-weather-swt-supply-trip/research-trv-soft-close-and-hold-timers/research-trv-soft-close-and-hold-timers.md'
warnings:
  - oversized
deferred: []
---

<intent-contract>

## Intent
**Problem:** Live soft-close still uses plant-on floor + temperature-overshoot hysteresis with required `accuracy`, so idle max-close does not follow house Heating Demand and epic R1/R2 stay false in the App.

**Approach:** Replace that law with house-idle soft-close (floor → hold-or-demand → 100), retire accuracy/overshoot from config and runtime, commission `trv_soft_close_hold_s` + closure-only keys in `apps.yaml.example`, and lock behavior with automated tests (including hold cancel/orphan).

## Boundaries & Constraints
**Always:**
- Soft-close runs before Outdoor water prelude on `control_tick`, eligible `control_event`, and flame-hold expiry; Outdoor unreadability and flame latch must not block or freeze soft-close.
- Plant on + house all-idle (`not has_heating_demand(_read_zones)`): on first idle observe for an episode (cold start already idle, or return to idle after demand/plant-off cleared the episode) write `valve_closure_degree` = yaml `valve_closure_floor` (default 80) on every commissioned TRV and arm one soft-close hold of yaml `trv_soft_close_hold_s` (default 300); while hold is armed, later idle passes do not restart the timer; after hold expiry wrote 100 while still idle, stay at 100 until demand or plant-off (do not re-floor/re-arm).
- Hold expiry with matching token + still Plant on + all-idle → write closure 100; token mismatch (cancel/orphan) → no soft-close write.
- Plant on + any Heating Demand (cold-start already heating, rising-edge off hold, or sustained) → write closure 100 on all commissioned TRVs; cancel hold (token bump); never arm hold while demand present.
- Plant off → write closure 100; cancel hold; clear idle-episode state.
- Soft-close hold mirrors flame hold: `_trv_soft_close_hold_handle` / `_trv_soft_close_hold_token`, `run_in` with `token=`, `_disarm_trv_soft_close_hold` bumps token + `cancel_timer`.
- Commissioned = `valve_closure` only; leftover yaml `accuracy` → `ConfigError`; omitted `trv_soft_close_hold_s` defaults 300 (same positive int-after-truncate rules as `flame_trip_hold_s`); no accuracy listeners; remove `_trv_overshoot_latched`.
- Write only via `_write_number` (equal-float skip; unreadable/non-finite skip); never `valve_opening_degree`; Critical Zone never drives soft-close.
- Example yaml commissions hold + floor + closure-only TRV mappings; house `apps.yaml` / ADR / CONTEXT / AGENTS / `knowledge/` are out of scope (7.2 / 7.3).

**Never:**
- Change weather-curve SWT, flame observe/latch/clear, Exclusive Session, or Heating Demand = `hvac_action=heating`.
- Edit house `apps/apps.yaml`; amend ADR/CONTEXT/AGENTS/`knowledge/`; restore temperature overshoot as live soft-close; infer TRV entities by name; write `valve_opening_degree`.

## I/O & Edge-Case Matrix
| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| First all-idle | Plant on; no zone heating; cold start or new idle episode | Write floor on all commissioned; arm hold once | Unreadable closure → skip that write |
| Idle while holding | Same idle; hold armed | No timer restart; floor already commanded | Equal-float skip OK |
| Hold expiry idle | Matching token; still all-idle | Write 100; episode closed (no re-arm while still idle) | — |
| Orphan expiry | Token mismatch after cancel | No soft-close write | — |
| Any demand | Plant on; any zone `hvac_action=heating` | Write 100; cancel hold; never arm | Cold-start demand must not floor/arm |
| Return to idle | Demand cleared after 100 | Floor + arm new hold | — |
| Plant off | Plant not on | Write 100; cancel hold | — |
| Closure-only yaml | Mapping has `valve_closure`, no `accuracy` | Parse OK; commissioned; no accuracy listen | Leftover `accuracy` → ConfigError |
| Hold key | Omitted / valid / invalid `trv_soft_close_hold_s` | Default 300 / accept truncate≥1 / ConfigError | Same rules as flame hold |
| Opening / CZ | Any soft-close path | Never write opening; CZ unused for TRV | — |

</intent-contract>

## Code Map
Evidence HEAD; research `2ec1908088a50a2a88fb157b9652532cbb46e704` still matches listed paths (`git diff --stat` empty).

- `apps/ha_smart_hvac/hvac_app.py` — Replace `_apply_trv_law` (398–467): drop overshoot latch (45, 421–457); house-idle/demand/plant-off law via `has_heating_demand` + `_read_zones`; add soft-close hold fields/arm/disarm/expiry (mirror flame 42–43, 152–158, 160–163, 198–206); remove accuracy `listen_state` (74–75). Keep call sites tick 239 / event 256 / flame expiry 165 before prelude. Soft-close hold expiry writes 100 only (no Outdoor prelude/SWT).
- `apps/ha_smart_hvac/models.py` — `ThermostatConfig.commissioned` closure-only (16–18); drop/ignore accuracy field per parse reject; `HvacConfig.trv_soft_close_hold_s`.
- `apps/ha_smart_hvac/config.py` — Closure-only `_parse_thermostat` (128–145); reject `accuracy` key; parse `trv_soft_close_hold_s` like `flame_trip_hold_s` (234–239) default 300; `_KNOWN_KEYS`.
- `apps.yaml.example` — `trv_soft_close_hold_s: 300`; floor; Sonoff mapping without `accuracy`.
- `tests/test_config.py` — Rewrite commission/partial/accuracy/example asserts (~70–123, 536–604, 629+); add hold parse/truncate/reject.
- `tests/test_hvac_app.py` — Replace overshoot/`test_trv_*` (~2083–2640) with house-idle/hold/demand/plant-off/orphan/cold-start goldens; drop accuracy listen asserts; keep Outdoor-prelude isolation + never-opening + plain-string skip; mirror flame orphan/cancel patterns (1581, 1595, 1516).
- Do not change: `coordinator.py` / `feedforward.py` / flame SWT path / house `apps/apps.yaml` / ADR/CONTEXT/AGENTS/`knowledge/`.

## Tasks & Acceptance
**Execution:**
- [x] `apps/ha_smart_hvac/models.py` + `config.py` — Closure-only commission; reject `accuracy`; add `trv_soft_close_hold_s` (default 300, flame-hold parse rules).
- [x] `apps/ha_smart_hvac/hvac_app.py` — House-idle soft-close + hold arm/cancel/orphan expiry; remove overshoot latch and accuracy listeners; keep TRV-before-prelude call sites.
- [x] `apps.yaml.example` — Commission hold + floor + closure-only TRV; drop accuracy.
- [x] `tests/test_config.py` + `tests/test_hvac_app.py` — Rewrite TRV/config tests for new law; add hold cancel/orphan + cold-start demand/idle coverage.
- [x] Verify — full pytest + ruff on `apps/ha_smart_hvac` and `tests`.

**Acceptance Criteria:**
- Given Plant on and no zone Heating Demand on first idle observe (including initialize already idle), when soft-close runs, then every commissioned TRV gets `valve_closure_floor` and exactly one soft-close hold is armed; later idle passes do not restart that hold.
- Given an armed soft-close hold, when it expires with a matching token while still all-idle, then commissioned TRVs get closure 100 and a cancelled/orphan callback writes nothing.
- Given Plant on and any zone Heating Demand (including cold start already heating), when soft-close runs, then commissioned TRVs get 100 and no soft-close hold remains armed.
- Given Plant on after demand cleared, when the house returns to all-idle, then floor is written again and a new hold is armed.
- Given Plant Management off, when soft-close runs, then commissioned TRVs get 100 and any soft-close hold is cancelled.
- Given thermostat yaml with closure-only mapping and optional/omitted `trv_soft_close_hold_s`, when parsed, then commission succeeds (hold default 300); leftover `accuracy` or invalid hold → ConfigError; App registers no accuracy soft-close listeners.
- Given any soft-close path, when writes run, then `valve_opening_degree` is never written, Critical Zone does not drive TRV, and `apps.yaml.example` shows hold + floor + closure-only keys.
- Given `uv run pytest` and `uv run ruff check apps/ha_smart_hvac tests`, when run, then both succeed.

## Implementation Notes
- House-idle law implemented 2026-11-20; `uv run pytest` + ruff clean.
- Idle-episode state: none → (all-idle) holding → (expiry while idle) closed_idle; demand or plant-off → none. Prevents re-floor after expiry while still idle.
- Soft-close hold expiry does not run Outdoor prelude or SWT; flame-hold expiry still calls `_apply_trv_law` then prelude.
- High-risk orphan AC: after heating-edge cancel, stale soft-close hold callback performs no soft-close write.

## Plan Change Log
## Review Triage Log

### 2026-11-20 — Review pass
- verdicts: 33 findings — high 5, medium 8, low 6, false 8, maybe-false 0
- findings:
  - `[false]` `[reject]` AGENTS/CONTEXT still describe overshoot/accuracy — intent story 7.1 Boundaries exclude AGENTS/CONTEXT/knowledge amend (7.3)
  - `[false]` `[reject]` ADR 0008 / adr-trv-* contradict new law — same intent exclusion (docs amend is 7.3)
  - `[high]` `[patch]` Hold expiry early-return on demand leaves `_trv_idle_episode` at holding with handle None — verified at hvac_app.py:196-197; next idle ticks early-return forever — clear episode on abort — fix applied: episode None on plant-off/demand abort
  - `[medium]` `[patch]` No tests for hold-expiry no-ops under plant-off / demand with matching token — real gap (VG pre-verified) — fix applied: matching-token demand/plant-off expiry tests
  - `[medium]` `[patch]` `run_in` soft-close schedule not pinned (callback/delay/token) — only assert_called_once — strengthen like flame — fix applied: pin callback/delay/token/handle
  - `[low]` `[reject]` initialize listen inventory weakened — climate attrs still registered; restoring asserts adds noise without user-facing harm
  - `[low]` `[reject]` outdoor-unavailable warning / floor 80.0 pin / log-reason tests narrowed — unlikely everyday defect; log reasons cosmetic
  - `[low]` `[reject]` No operator migration note for accuracy ConfigError — intent owns example+App schema only; house yaml is 7.2
  - `[false]` `[reject]` Plan review fields empty / status in-progress — mid-run snapshot; frontmatter already set in-review/thorough during this pass
  - `[low]` `[reject]` Bare string episode states without constants — cosmetic; no named caller divergence today
  - `[false]` `[reject]` No new ADR for house-idle law — intent forbids ADR amend in 7.1
  - `[high]` `[patch]` Hold expiry demand early-return leaves holding — same root as BH3 (edge-case)
  - `[high]` `[patch]` Hold expiry plant-off early-return leaves holding — same root; clear episode
  - `[high]` `[patch]` holding episode with no active handle permanently skips law — consequence of BH3/EC1/EC2
  - `[medium]` `[patch]` Expiry sets closed_idle even when all closure writes skip/fail — verified: unconditional assign at :208; write-gate closed_idle — fix applied: closed_idle only if any write True else None
  - `[high]` `[patch]` Return-to-idle after demand abort at expiry never refloors — claim of same stuck holding state
  - `[medium]` `[patch]` closed_idle without successful 100 write — same write-gate root as EC4
  - `[medium]` `[patch]` Soft-close run_in schedule not pinned like flame hold — VG pre-verified — fix applied in test suite
  - `[medium]` `[patch]` Hold expiry demand re-guard not exercised with matching token — VG pre-verified — fix applied in test suite
  - `[medium]` `[patch]` Hold expiry plant-off re-guard not exercised with matching token — VG pre-verified — fix applied in test suite
  - `[medium]` `[patch]` Hold expiry SWT/prelude isolation not asserted — VG pre-verified — fix applied in test suite
  - `[medium]` `[patch]` Multi-zone partial demand does not assert all TRVs get 100 — VG pre-verified — fix applied in test suite
  - `[false]` `[reject]` Req7 pytest/ruff only claimed in plan — parent ran both green this session
  - `[medium]` `[patch]` Hold-expiry-under-demand undertested — same as VG demand re-guard
  - `[low]` `[reject]` Call-site matrix lightly tested via flame-hold expiry idle progression — existing flame-hold TRV tests remain; not everyday user harm
  - `[low]` `[reject]` Rising-edge demand via hvac_action control_event not dedicated — tick path covers demand law; listener already registered
  - `[false]` `[reject]` Empty _read_zones treated as idle — intentional plan/Design Notes reading; test updated
  - `[low]` `[reject]` Hold arms with zero commissioned TRVs — no user-facing valve harm; Given clause is about writes when commissioned
  - `[false]` `[reject]` CZ/never-opening coverage thin in diff delta — code never uses CZ; opening scan test remains
  - `[low]` `[reject]` Accuracy listen retirement assert narrow — removal verified; inventory assert optional
  - `[false]` `[reject]` Retired overshoot tests — intentional per intent
  - `[false]` `[reject]` Plan markdown artifact in diff — workflow deliverable, mirrors intent
  - `[false]` `[reject]` Stale AGENTS vs app until 7.3 — intent excludes
## Design Notes
House all-idle soft-close demand probes each climate `hvac_action` directly (Heating Demand = `hvac_action=heating`); it does not require readable zone air/setpoint via `_read_zones` (water path keeps `_read_zones`). Floor/hold arm and expiry `closed_idle` require every commissioned closure write to succeed. Soft-close hold copies flame token/`run_in`/`cancel_timer` without coupling to flame latch. Accuracy retirement is hard ConfigError so house yaml cannot silently keep overshoot inputs.

## Verification
**Commands:**
- `uv run pytest` -- expected: all tests pass
- `uv run ruff check apps/ha_smart_hvac tests` -- expected: clean

## Auto Run Result
- **Summary:** Replaced plant-on floor+overshoot TRV soft-close with house-idle soft-close (floor → tokenized hold → 100), retired accuracy/overshoot from config and runtime, commissioned `trv_soft_close_hold_s` in `apps.yaml.example`, and locked behavior with tests. Review patches cleared stuck `holding` after aborting expiry and write-gated `closed_idle`.
- **Files changed:**
  - `apps/ha_smart_hvac/hvac_app.py` — house-idle law, soft-close hold arm/disarm/expiry, episode state
  - `apps/ha_smart_hvac/config.py` — closure-only TRV parse; reject accuracy; `trv_soft_close_hold_s`
  - `apps/ha_smart_hvac/models.py` — closure-only `commissioned`; hold field
  - `apps.yaml.example` — hold + closure-only Sonoff mapping
  - `tests/test_config.py` / `tests/test_hvac_app.py` — rewritten + review-patch coverage
  - plan `story-tracer-trv-house-idle-soft-close-plan.md` — planning/review artifact
- **Review:** Patched high stuck-holding on expiry abort + medium write-gated closed_idle + medium test pins (run_in, expiry demand/plant-off, SWT isolation, multi-zone demand). Deferred: none. Rejected: docs/ADR/AGENTS (7.3), migration blurb (7.2), cosmetic/low noise, mid-run plan snapshot, intentional empty-zones idle reading.
- **Follow-up review recommendation:** true — patched high-severity expiry episode abort; residual unverified risk: on multi-TRV hold expiry, any single successful 100 write marks `closed_idle`, so a sibling TRV whose write skipped/failed can remain at floor until demand/plant-off.
- **Patched counts:** high 5 findings (1 root), medium 8 findings (write-gate + verification pins).
- **Verification:** `uv run pytest` — 365 passed; `uv run ruff check apps/ha_smart_hvac tests` — clean (post-patch).
- **Residual risks:** House `apps/apps.yaml` still may carry `accuracy` until 7.2 (parse will fail); AGENTS/CONTEXT/ADR lag until 7.3; partial multi-TRV expiry write success as above.

## Code Review
### 2026-11-20 (follow-up after bmad-build-auto)
**Code review complete.** 0 `decision-needed`, 5 `patch`, 0 `defer`, 16 rejected. Decision F1 → A (hvac_action demand probe).

- [x] [Review][Patch] Soft-close Heating Demand via climate `hvac_action` without requiring readable zone temp/setpoint [apps/ha_smart_hvac/hvac_app.py:461-464] — decision A: probe `hvac_action` per climate so unreadable air/setpoint cannot drop a heating zone into house-idle floor
- [x] [Review][Patch] Hold expiry any-success `closed_idle` leaves sibling TRVs stuck off 100; multi-TRV expiry untested [apps/ha_smart_hvac/hvac_app.py:201-213]
- [x] [Review][Patch] First all-idle arms hold and sets `holding` even when all floor writes fail/skip [apps/ha_smart_hvac/hvac_app.py:469-475]
- [x] [Review][Patch] Flame-latched + house-idle soft-close floor/arm path untested [tests/test_hvac_app.py:2218-2235]
- [x] [Review][Patch] equal-float already-at-floor path does not assert hold arm / holding episode [tests/test_hvac_app.py:2254-2257]

#### Rejected
- R7 low — floor value already pinned by first-observe / floor-override tests
- R9 false — accuracy listeners cannot exist under current schema
- R10 low — tick-path demand covers law; dedicated hvac_action control_event pin optional
- R11 low — cosmetic log-string asserts
- R12 low — other SWT isolation pins remain
- R13 false — accuracy migration guidance is 7.2 scope
- R14 false — residual tracked as F2; not a standalone defect
- R17 low — zero-commissioned hold churn has no valve harm
- R20 false — story episode law (Reading A), not epic continuous floor
- R21 false — story requires sustained demand → 100
- R22 false — docs/house yaml deferred to 7.2/7.3
- R23 false — matching-token plant-off/demand no-op aligns with still-idle AC
- R25 false — empty `_read_zones` → idle is intentional Design Notes reading
- R26 false — BMAD plan artifact is workflow deliverable
- R27 low — accuracy/CZ inventory asserts optional
- R28 false — pytest/ruff claim is Auto Run Result, not a code defect

- Patches applied 2026-11-20 follow-up: F1 hvac_action demand probe; F2/F3 all-commissioned write gates; F4/F5 tests. `uv run pytest` + ruff clean.
