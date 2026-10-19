---
title: 'Live Exclusive Session windup check'
type: 'chore'
ticket: '7'
created: '2026-10-19'
status: done
baseline_revision: 'e8a8437a9b0150b073e01c367febccd8c4eeb41c'
route: 'full'
route_source: 'auto'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 1
context:
  - '{project-root}/CONTEXT.md'
  - '{project-root}/docs/adr/0001-exclusive-session-against-production-ha.md'
  - '{project-root}/docs/adr/0004-weather-curve-swt.md'
  - '{project-root}/_bmad-output/initiative-weather-curve-zone-actuators/spec-weather-curve-swt-only/spec-weather-curve-swt-only.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** CAP-5 locks weather-curve-only SWT in pytest, but the epic success signal still needs a live Exclusive Session against the house: the old near-setpoint flat-air windup shape must not climb Set Water Temperature to `setpoint_max` via tracking.

**Approach:** Under Exclusive Session, reproduce that shape (near-zero Zone Error, flat air, moderate FF clamp with headroom; outdoor documented, ~+10°C ideal), capture operator notes / AppDaemon log evidence that `command` stays at the feedforward clamp, and record the run in a walkthrough artifact — no control-law changes. Human runs the session and HA spots; agent seeds and fills the walkthrough narrative + log.

## Boundaries & Constraints

**Always:**
- Exclusive Session only (ADR 0001): confirm Production AppDaemon add-on is **stopped** before `./scripts/run-appdaemon`; abort if dual-run risk; **always** restore the add-on on pass, fail, or blocked; never dual-run.
- Pass criterion (**4A**): over ≈5 × house `control_interval` ticks, AppDaemon INFO shows `command=` steady at the FF clamp (`clamp(soft u_ff)`), not climbing toward house `setpoint_max` via tracking. INFO logs soft `u_ff=` (`hvac_app.py`); at floor/ceiling soft may differ from `command=` — that is **not** failure. Score by clamp stability / expected clamp, not by `command ==` logged `u_ff`. `setpoint_min` stays 40.
- Preflight shape before claiming pass: at least one demand zone with near-setpoint air (error ≈ 0.2°C class) and flat `y`; moderate FF clamp below `setpoint_max` with headroom (soft curve may floor at 40 — still the FF clamp, not windup); outdoor as available (document actual value — +10°C is ideal, not a hard gate).
- Distinguish CAP-7: when params adapt, soft `u_ff` and `command` may step together with `command` still equal to the new clamp — feedforward adapt, not tracking windup. Fail only if `command` climbs above the FF clamp toward `setpoint_max`. CAP-7 stays live (decision 1A).
- HITL split: human operator runs Exclusive Session + HA spots; agent seeds/fills walkthrough narrative + log only. Log format matches pr-63/66/70 HITL shape; content is live plant evidence, not PR review.
- Evidence under `_bmad-output/initiative-weather-curve-zone-actuators/walkthrough-story-1-7/` (narrative + HITL log).
- Ask before changing house entity IDs in `apps/apps.yaml`; never commit `.env` or `appdaemon/secrets.yaml`.
- Decisions (2026-10-19): **1A** CAP-7 live; **2B** outdoor ideal-not-gate (document actual + expected clamp); **3A** window = 5 × house `control_interval` from `apps/apps.yaml` (document both); **4A** score by FF clamp / `command` series, not logged soft-`u_ff` equality (soft≠command at floor/ceiling OK).

**Never:**
- Change SWT law, CAP-7 formula, `setpoint_min`/`max`, FF commission defaults, or production code to “make the check pass”.
- Treat pytest CAP-5 alone as closing this ticket.
- Claim pass when flat-air / near-setpoint demand / moderate-clamp-with-headroom shape was not met — reschedule or mark blocked with reason. Do not block solely on outdoor ≠ +10°C.
- Dual-run local AD with Production add-on; invent `u_track` logging that the weather-curve path does not emit.
- Fail a soft-floor run solely because logged soft `u_ff` ≠ `command` (forbidden by 4A).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Happy windup shape | Exclusive Session; demand; CZ-class error ≈ 0.2; flat air; moderate clamp < max (outdoor documented) | ≈5× house `control_interval`: `command` steady at FF clamp; no climb to `setpoint_max` | Capture log excerpts + HA spot checks in walkthrough log |
| CAP-7 nudge mid-window | Params adapt; soft `u_ff` / clamp step | `command` follows new clamp; not climb independent of clamp | Note param nudge in evidence; do not fail solely for matching step |
| Soft floor at min | Soft `u_ff` < 40 → clamp 40 | Steady `command=40` while outdoor/FF imply floor — pass under 4A even if log shows soft ≠ 40 | Document floor vs windup in notes |
| Shape unavailable | No flat near-setpoint demand, or clamp already pegged at max (no headroom) | Do not claim pass | Reschedule or `blocked` with reason; always restore Production add-on |
| Write / session failure | `_write_setpoint` fails or AD dies mid-run | Incomplete — not a pass | Always restore Production add-on; retry later |

</frozen-after-approval>

## Code Map

- `apps/ha_smart_hvac/hvac_app.py` L79–82 — INFO soft `u_ff=` from `weather_feedforward` + clamped `command=` (primary evidence). Do not change.
- `ff_auto_correct.py` / `feedforward.py` — `clamp_uff` + CAP-7; SWT stays `clamp(u_ff)`.
- `tests/test_hvac_app.py` — `test_cap5_flat_air_multi_tick_stays_at_ff_clamp` (unit only).
- ADR 0001 + `README.md` + `scripts/run-appdaemon` — stop Production → local AD → restore.
- Spec success signal; ADR 0004 / `CONTEXT.md` — law/gates.
- House `apps/apps.yaml` — read `control_interval` + entities; no ID edits unless asked.
- `walkthrough-pr-{63,66,70}/` — HITL log shape; live plant deferred here.

## Tasks & Acceptance

**Execution:**
- [ ] `apps/apps.yaml` + HA — Preflight: (1) Production AD **stopped** (not merely stoppable), (2) read `control_interval` → window = 5× that (document both), (3) windup shape (near-setpoint flat air, Heating Demand, moderate clamp with headroom; document outdoor), (4) abort if dual-run risk — gate *(agent: yaml timing documented in walkthrough; live (1)(3)(4) still human)*
- [x] `_bmad-output/initiative-weather-curve-zone-actuators/walkthrough-story-1-7/walkthrough-story-1-7.md` -- Agent seeds narrative (Intent, procedure with **4A** pass rule, evidence checklist, outcome) linked to ticket verify + spec success signal -- artifact
- [ ] `_bmad-output/initiative-weather-curve-zone-actuators/walkthrough-story-1-7/walkthrough-story-1-7-log.md` -- Human runs Exclusive Session + HA spots; agent fills Action/Result/Evidence/Open with AppDaemon lines over the 5× window -- evidence *(agent: HITL log seeded blocked; live INFO series pending)*
- [ ] `_bmad-output/.../walkthrough-story-1-7/walkthrough-story-1-7-log.md` -- Close-out: always restore Production AppDaemon add-on; record pass/fail/blocked; leave control code untouched -- hygiene

**Acceptance Criteria:**
- Given Exclusive Session against the house with the windup shape met, when demand ticks run for ≈5 × house `control_interval`, then AppDaemon logs show `command` steady at the FF clamp and not climbing to `setpoint_max` via tracking (soft logged `u_ff` may differ at floor/ceiling — 4A).
- Given CAP-7 may nudge FF params, when the clamp steps during the window, then evidence still shows `command` following that clamp — not an independent climb toward max.
- Given the walkthrough folder, when the run completes, then narrative + log contain outdoor, flat near-setpoint context, house `control_interval` + window length, and the `command`/`u_ff` series (with 4A scoring notes).
- Given the session ends (pass, fail, or blocked), when teardown runs, then Production AppDaemon add-on is restored and no dual-run occurred.
- Given this story’s diff, when inspected, then no SWT/CAP-7/law/code changes were introduced to force a green result.

## Implementation Notes

- 2026-10-19: Prior seed reverted after quick-review intent_gap; human chose **4A** — re-seed walkthrough with clamp-based pass rule.

## Plan Change Log

- 2026-10-19 plan review patch-all: Never outdoor gate vs 2B; bind window to house `control_interval`; HITL human vs agent split; Exclusive Session stopped+always-restore; Approach soft outdoor; path-prefixed preflight/close-out; trim Code Map / Design Notes for scope. KEEP: 1A CAP-7 live; 2B outdoor ideal-not-gate; 3A ≈5 ticks; artifact `walkthrough-story-1-7/`; no control-law changes.
- 2026-10-19 intent_gap loop 1: human **4A** — pass by FF clamp / `command` stability; soft≠command at floor/ceiling OK. Amended frozen Always/Never/matrix + Design Notes/ACs; avoided known-bad `command ==` logged soft `u_ff`. KEEP: prior KEEP + Exclusive Session hygiene + HITL split.

## Review Triage Log

- 2026-10-19: patched high Never/2B; medium window/HITL/ES hygiene; low Approach/paths/scope trim. Rejected: CAP-7 confound, artifact path, soft floor (already coherent).
- 2026-10-19 quick loop 1 · `high` · intent_gap · walkthrough/plan pass rule `command == u_ff` (both clamped) vs `hvac_app.py` L79–82 logging soft `weather_feedforward` as `u_ff=` and clamped `result.command` as `command=` — at outdoor +10 soft 37 / command 40 would false-fail a correct soft-floor run. Implementation reverted; frozen Always/Design Notes need human renegotiation.
- 2026-10-19 quick loop 1 · `false` · rejected · unmet live Exclusive Session ACs (INFO series / CAP-7 co-step / outdoor+shape / Production restore) — HITL Intent requires human run; seeded artifacts correctly left disposition blocked/pending (now reverted with gap loopback). Not a defect in unfinished plant evidence.
- 2026-10-19: human resolved intent_gap → **4A**; plan regenerated for re-approval before re-implement.
- 2026-10-19 quick loop 2 · `false` · carried · unmet live Exclusive Session ACs (INFO/`command` series, CAP-7 co-step, outdoor+shape, Production restore) — HITL Intent; seed correctly leaves disposition blocked/pending until human run.
- 2026-10-19 quick loop 2 · `medium` · patch · walkthrough Expected-clamp section / Outcome yaml-only numbers vs live CAP-7 overlay (`_load_ff_overlay`) — operator can mis-score if yaml table used alone; require recording loaded overlay / current base·slope before 4A scoring.
- 2026-10-19 quick loop 2 · `low` · patch · log §2 Open renumbers human preflight (1)(2)(3) vs plan (1)(3)(4) — align indices.

## Design Notes

Pass vs confound (log shape, **4A**): score `command` vs expected FF clamp each tick — soft logged `u_ff` may differ at floor/ceiling. CAP-7 nudge OK if `command` follows the new clamp. Fail if `command` climbs above the FF clamp toward `setpoint_max`. Unit CAP-5(d) = outdoor=10, y=21.8/Tr=22, 5 ticks (soft 37 → clamp 40) — live mirrors that shape on the house, not pytest.

## Verification

**Commands:**
- `uv run pytest tests/test_hvac_app.py -k cap5_flat_air` -- expected: pass (regression lock; not a live substitute)

**Manual checks:**
- Production AD stopped → `./scripts/run-appdaemon` → capture INFO over 5× house `control_interval` → Ctrl+C → **always** restart Production add-on
- Document outdoor + expected clamp; flat near-setpoint; `plant_setpoint` matches `command`; not ramping to max; soft≠command at floor OK (4A)
- Walkthrough log proves pass/fail/blocked; no production code diff for this story
