# Review log: Story 1.7 Live Exclusive Session windup check

Target: plan story-live-exclusive-session-windup-check-plan.md (ticket 7). Live plant evidence — not PR review.

Disposition: **blocked** pending human Exclusive Session.

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

## 5 — live Exclusive Session — pending human

Session: human · Timestamp: *pending*

- Action: Stop Production AppDaemon add-on → `./scripts/run-appdaemon` → confirm preflight shape → capture INFO over ≥300 s (≈5 ticks) → HA spot `plant_setpoint` vs `command` → Ctrl+C → **always** restart Production add-on.
- Result: *pending*
- Evidence: Paste AppDaemon lines here, e.g. `outdoor=… °C, u_ff=…, command=…` for each tick in the window. Score **4A**: `command` steady at FF clamp (document expected clamp from outdoor + current FF params); soft≠command at floor OK. CAP-7 co-step with clamp = not fail; climb above clamp toward 55 = fail.
- Open: Operator run; agent will fill Action/Result/Evidence once logs are provided

## 6 — close-out — Production restore + disposition

Session: *pending*

- Action: After any live attempt (pass / fail / blocked / write failure), confirm Production AppDaemon add-on restored; no dual-run; leave SWT/CAP-7/law code untouched.
- Result: *N/A — session not opened this seed*. Seed disposition remains **blocked**.
- Evidence: Operator confirmation of add-on restart; this log + narrative Outcome table
- Open: Human must complete ## 5–6 before ticket acceptance criteria can go green
