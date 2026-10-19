# Review log: Story 1.7 Live Exclusive Session windup check

Target: plan story-live-exclusive-session-windup-check-plan.md (ticket 7). Live plant evidence — not PR review.

Disposition: **pass (4A)** — Production restored; plant_setpoint operator-confirmed; command series at soft-floor clamp 40.

## 1 — seed — narrative + 4A pass rule

Session: agent · Timestamp: 2026-10-19T15:58:00+03:00

- Action: Re-seed walkthrough after intent_gap loop 1 → human **4A** (score `command` vs FF clamp; soft≠command at floor/ceiling OK). Wrote narrative Intent, procedure, evidence checklist, outcome.
- Result: Narrative ready; disposition blocked until live run. No control-law / apps code changes.
- Evidence: walkthrough-story-1-7/walkthrough-story-1-7.md; plan Design Notes / Always 4A; hvac_app.py L79–82 soft `u_ff=` + clamped `command=`
- Open: Human Exclusive Session + HA spots

## 2 — preflight — house apps.yaml timing + expected clamp

Session: agent · Timestamp: 2026-10-19T15:58:30+03:00

- Action: Read gitignored house `apps/apps.yaml` for window binding (**3A**) and FF commission (no entity ID edits).
- Result: `control_interval=60` → observation window **5 × 60 = 300 s**. `setpoint_min=40`, `setpoint_max=55`. FF yaml `base=25`, `slope=1.2`, `comfort_ref=20`. At outdoor +10°C: soft `u_ff=37` → expected clamp `command=40` (soft floor; 4A: soft≠40 OK). Moderate clamp with headroom vs max 55.
- Evidence: apps/apps.yaml L7–13 (`control_interval`, setpoints, `weather_feedforward`); feedforward law ADR 0004
- Open: Live gates still human — (1) Production AD **stopped**, (3) windup shape (near-setpoint flat air + Heating Demand + clamp headroom), (4) abort if dual-run risk. Agent owns (2) window. Outdoor ideal +10 not a hard gate (**2B**).

## 3 — verify — CAP-5 flat-air unit lock (not live substitute)

Session: agent · Timestamp: 2026-10-19T15:59:00+03:00

- Action: Ran plan Verification command `uv run pytest tests/test_hvac_app.py -k cap5_flat_air`.
- Result: *see following entry if this races; otherwise filled in ## 4*.
- Evidence: tests/test_hvac_app.py::test_cap5_flat_air_multi_tick_stays_at_ff_clamp (outdoor=10, y=21.8/Tr=22, 5 ticks → clamp 40)
- Open: Does not close ticket 7; live Exclusive Session still required

## 4 — verify — CAP-5 pytest result

Session: agent · Timestamp: 2026-10-19T16:00:00+03:00

- Action: Confirmed pytest outcome for `-k cap5_flat_air`.
- Result: **1 passed**, 26 deselected (exit 0). Unit lock of CAP-5(d) flat-air multi-tick at FF clamp holds; not a live substitute.
- Evidence: `tests/test_hvac_app.py::test_cap5_flat_air_multi_tick_stays_at_ff_clamp PASSED`
- Open: Live plant still blocked

## 5 — live Exclusive Session — demand window captured

Session: human+agent · Timestamp: 2026-10-19T17:05–17:11+03:00

- Action: Production AD stopped (operator). Local `./scripts/run-appdaemon`. Earlier idle window had only `No heating demand; setpoint 0`. After operator created demand, captured ≥5 INFO ticks; stopped local AD.
- Result: **4A command series OK** — `command` steady at soft-floor clamp **40.00**, no climb toward 55. FF overlay missing → yaml commission `base=25`, `slope=1.2`, `comfort_ref=20`. Soft≠command at floor as expected.
- Evidence (AppDaemon INFO):
  ```
  outdoor=13.20 °C, u_ff=33.16, command=40.00
  outdoor=13.00 °C, u_ff=33.40, command=40.00
  outdoor=13.00 °C, u_ff=33.40, command=40.00
  outdoor=13.00 °C, u_ff=33.40, command=40.00
  outdoor=13.00 °C, u_ff=33.40, command=40.00
  ```
  Expected clamp from recorded params: `clamp(25 + 1.2×(20−T_out), 40, 55)` → at 13.2°C soft 33.16 / at 13.0°C soft 33.40 → **40**. CAP-7 mid-window: no param step (overlay absent; soft only tracked outdoor).
- Open: none for capture (close-out in ## 6)

## 6 — close-out — Production restore + disposition

Session: human+agent · Timestamp: 2026-10-19T17:12+03:00

- Action: Operator confirmed Production AppDaemon add-on restored; plant_setpoint spot confirmed; no dual-run; SWT/CAP-7/law code untouched.
- Result: Local AD was stopped before restore. Production **restored**. `plant_setpoint` confirmed by operator (numeric value not pasted — expected match to logged `command=40`). Command series remains **4A pass**. Near-setpoint flat-air shape detail still optional note from operator.
- Evidence: operator message «Production restored + plant_setpoint»; ## 5 INFO series; no production code diff
- Open: optional numeric plant_setpoint / y/Tr for the record only
