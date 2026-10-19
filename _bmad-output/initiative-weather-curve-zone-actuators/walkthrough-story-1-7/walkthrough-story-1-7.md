# Walkthrough: Story 1.7 — Live Exclusive Session windup check

Target: plan [story-live-exclusive-session-windup-check-plan.md](../epic-weather-curve-swt-only/story-live-exclusive-session-windup-check-plan.md) (ticket 7 / epic success signal). Spec success signal: [spec-weather-curve-swt-only.md](../spec-weather-curve-swt-only/spec-weather-curve-swt-only.md#success-signal).

Disposition: **pass (4A)** — Production restored; plant_setpoint confirmed; command series at FF soft-floor clamp.

Current block: none (optional: paste numeric plant_setpoint + y/Tr for the record)

## Blocks

- [x] **1. Intent** — seeded (4A)
- [x] **2. Procedure & pass rule (4A)** — seeded
- [x] **3. Preflight (yaml)** — agent read `apps/apps.yaml`; live Production-stopped / shape gate = human
- [x] **4. Live capture (5× window)** — INFO series captured 2026-10-19 (command=40 steady)
- [x] **5. Close-out** — Production AppDaemon add-on restored; disposition recorded

---

### 1. Intent

Source: frozen Intent in the story plan.

**Problem:** CAP-5 locks weather-curve-only SWT in pytest, but the epic success signal still needs a live Exclusive Session against the house: the old near-setpoint flat-air windup shape must not climb Set Water Temperature to `setpoint_max` via tracking.

**Approach:** Under Exclusive Session, reproduce that shape (near-zero Zone Error, flat air, moderate FF clamp with headroom; outdoor documented, ~+10°C ideal), capture operator notes / AppDaemon log evidence that `command` stays at the feedforward clamp, and record the run here — no control-law changes.

**HITL split:** human runs Exclusive Session + HA spots; agent fills this narrative + [walkthrough-story-1-7-log.md](./walkthrough-story-1-7-log.md).

---

### 2. Procedure & pass rule (4A)

#### Exclusive Session hygiene (ADR 0001)

1. Confirm Production AppDaemon add-on is **stopped** (not merely stoppable).
2. Abort if dual-run risk.
3. Run local AppDaemon: `./scripts/run-appdaemon`.
4. Capture evidence over the observation window.
5. Ctrl+C local AD.
6. **Always** restore (restart) the Production AppDaemon add-on — pass, fail, or blocked.

#### House timing (from `apps/apps.yaml`)

| Knob | Value | Notes |
|------|-------|--------|
| `control_interval` | **60** s | House yaml at seed time |
| Observation window | **5 × 60 = 300** s | Decision **3A** — ≈5 demand ticks |
| `setpoint_min` / `setpoint_max` | **40** / **55** | Min stays 40; do not change to chase soft water |
| FF commission (yaml) | `base=25`, `slope=1.2`, `comfort_ref=20` | CAP-7 may overlay `base`/`slope` from JSON |

#### Preflight shape (before claiming pass)

All required; outdoor ≠ +10°C alone is **not** a block (**2B**):

1. At least one demand zone with near-setpoint air (Zone Error ≈ 0.2°C class) and flat `y`.
2. Heating Demand present; Plant Management on.
3. Moderate FF clamp **below** `setpoint_max` with headroom (soft curve may floor at 40 — still the FF clamp, not windup).
4. Document actual Outdoor Temperature (ideal ~+10°C).

If shape unavailable (no flat near-setpoint demand, or clamp already pegged at max with no headroom): **do not claim pass** — reschedule or mark blocked; still restore Production add-on.

#### Expected clamp (commission reference vs live scoring)

Yaml commission (`base=25`, `slope=1.2`, `comfort_ref=20`) is a **reference only** — CAP-7 (**1A** live) may overlay `base`/`slope` via `_load_ff_overlay` / `ff_auto_correct_state.json`, so the live clamp can differ.

Before **4A** scoring, record the **loaded overlay or current runtime `base`/`slope`** (and `comfort_ref` from yaml), then recompute:

```
u_ff_soft = base + slope × (comfort_ref − T_out)
command   = clamp(u_ff_soft, 40, 55)
```

Yaml-only example at outdoor **+10°C** (CAP-5(d) mirror, commission params, no overlay): soft **37** → `command` **40**. Do **not** score the live run against that table unless recorded current params match commission.

#### Pass rule (**4A**)

Score by **FF clamp stability / expected clamp from recorded current FF params**, not by `command ==` logged soft `u_ff` and not by yaml commission alone:

- **Pass:** over ≈5 × house `control_interval`, AppDaemon INFO shows `command=` steady at the FF clamp (`clamp(soft u_ff)`), not climbing toward house `setpoint_max` via tracking. Soft≠command at floor/ceiling is OK.
- **CAP-7 confound (1A live):** if params adapt mid-window, soft `u_ff` and `command` may step together with `command` still equal to the **new** clamp — feedforward adapt, not tracking windup. Fail only if `command` climbs **above** the FF clamp toward `setpoint_max`.
- **Fail:** `command` climbs above the FF clamp toward `setpoint_max` (old tracking windup shape).
- **Incomplete:** write failure or AD dies mid-run — not a pass; restore Production add-on; retry later.

Primary log line (`hvac_app.py`): `outdoor=… °C, u_ff=…, command=…` — soft `u_ff` from `weather_feedforward`, clamped `command` from `result.command`. Do not invent `u_track` logging.

#### HA spot checks (human)

- `plant_setpoint` matches logged `command` (not ramping to 55).
- Demand zone(s) remain near-setpoint / flat during the window (or document departure).
- Note any CAP-7 param nudge if soft/`command` step together.

---

### 3. Evidence checklist

Fill during / after the live run; mirror excerpts into the log.

- [x] Production AppDaemon add-on confirmed **stopped** before local AD
- [x] `control_interval` + window length documented (60 s / 300 s at seed; re-confirm if yaml changed)
- [x] Outdoor Temperature documented (actual value) — 13.2→13.0 °C in window
- [x] Current FF params recorded (loaded overlay or runtime `base`/`slope` + yaml `comfort_ref`); expected clamp recomputed from those — not yaml commission alone — overlay missing; yaml 25/1.2/20 → clamp 40
- [x] Flat near-setpoint demand shape met (or blocked with reason — not outdoor-only) — demand present for window; operator accepted close-out (numeric y/Tr optional)
- [x] AppDaemon INFO series over ≥5 ticks: `outdoor` / soft `u_ff` / `command`
- [x] **4A** scoring note: `command` vs expected clamp (from recorded params) each tick; soft≠command at floor OK — command=40 all five ticks
- [x] CAP-7: if clamp stepped, `command` followed new clamp (not independent climb) — N/A no mid-window adapt
- [x] HA: `plant_setpoint` matches `command`; not at `setpoint_max` via windup — operator confirmed
- [x] Production AppDaemon add-on **restored** after session
- [x] No SWT / CAP-7 / law / production code changes for this story

---

### 4. Outcome

| Field | Value |
|-------|--------|
| Result | **pass (4A)** |
| Window | house `control_interval`=60 s → 5× = 300 s; live demand ticks 14:07–14:11 UTC |
| Outdoor / expected clamp | 13.2→13.0 °C; params yaml 25/1.2/20 (no overlay); soft 33.16→33.40 → clamp **40** |
| `command` series | five ticks all `command=40.00` (soft floor; soft≠command OK) |
| CAP-7 mid-window | none (overlay absent) |
| Production restore | **yes** (operator 2026-10-19) |
| `plant_setpoint` | operator confirmed (match to command=40; numeric not pasted) |
| Code diff | none (walkthrough artifacts only) |

Unit regression (not a live substitute): `uv run pytest tests/test_hvac_app.py -k cap5_flat_air` — see log.
