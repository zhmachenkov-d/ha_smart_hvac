---
title: 'FF rise-rate auto-correct rule — decision'
type: 'decision'
covers: [CAP-7]
created: '2026-10-19'
status: 'accepted'
source_plan: 'spike-ff-rise-rate-auto-correct-rule-plan.md'
---

# FF rise-rate auto-correct rule (CAP-7)

Contract for stories **1.3** (ADR/docs) and **1.5** (implementation). Encode only the locked spike decisions; do not invent thresholds, formulas, or persistence shapes beyond this note.

**Operator:** Denys. Accepted 2026-10-19 — epic Notes finalized; story 1.5 may start from this contract.

---

## Signal

### Selection pool

Among zones with Heating Demand (`has_heating_demand` / `zone_error > 0` as today), select the zone with the **largest Zone Error**. That selection feeds **FF params only** — never the SWT command.

**Ties (T-hold):** Keep the previous selected zone while it remains in the max-error tie set among demand zones; otherwise break ties by lexicographic `zone.name`.

### Rise-rate window (W15 / R025) — 1B rolling + 1A append

- Ring buffer of up to **15** finite air-temperature samples on the **same** selected zone.
- **Append (1A):** each non-flush demand tick with a finite selected-zone temperature appends one sample — including ticks frozen by ε / δ / W-skip / incomplete-steady / incomplete W15.
- Incomplete buffer (`< 15` samples) → **skip adapt**. Do **not** compute `e_r` until W15 is full.
- When full: `T_window_start` = oldest sample, `T_now` = newest.

```
r_obs = (T_now − T_window_start) / (15 × control_interval / 3600)   # °C/h
```

- `control_interval` is in **seconds** (default 60 s → denominator **0.25 h**).
- Physical span is ~14×dt; **denominator stays 15×dt**.
- Default expected rate: `r_expected = 0.25` °C/h (`r_expected_c_per_h`).
- Flush clears the buffer (see flush paths below).

### Zone identity / readability edges (C1, 4A, M2)

| Code | Condition | Action |
|------|-----------|--------|
| **Z1** | Zone identity change among present demand zones | Flush + `clear_steady` + clear ephemeral; no adapt |
| **4A** (primary unreadable) | Previously selected zone **absent** from this tick’s snapshots (`_read_zones` omits `None` temps) | Same as Z1 |
| **M2** | Selected zone **present** but `zone_temp` non-finite | Same as Z1 |
| Empty snapshots | No zones | No-zones idle + full flush path |

Do **not** invent a separate M2-on-`None`-in-snapshot path under current reads (absent ⇒ 4A).

### Steady count + window lifetime

- `+1` steady each demand tick with the **same** selected zone, finite zone temp, and **not** on a flush path.
- Every `clear_steady` / flush path **also flushes** the rise-rate window **and** clears ephemeral including `previous`:
  - zone switch, 4A drop, M2, plant-off, no demand, outdoor unavailable, empty snapshots.

### Ephemeral state (not persisted)

- Previous I1 knob (`previous`)
- Rise-rate window buffer
- Steady count
- Selected-zone id

Restart → all empty; then CS-base + yaml/JSON overlay for params only.

---

## Law

### Adapted parameters

| Parameter | Role |
|-----------|------|
| `base` | Adapted |
| `slope` | Adapted |
| `comfort_ref` | Commission-only (never auto-corrected) |

FF law unchanged: `u_ff = base + slope × (comfort_ref − T_out)`; SWT under Plant Management + Heating Demand stays `clamp(u_ff)`.

### Identifiability (I1) + CS-base + hysteresis

One knob per tick. Let `d = |T_out − comfort_ref|`.

Same-tick order:

1. If `previous` unset → **CS-base** (select `base`).
2. Then apply hysteresis with code constant `outdoor_gate_hysteresis_k = 2`:
   - switch to **slope** when `d ≥ outdoor_gate_delta_k + hysteresis`
   - switch to **base** when `d ≤ outdoor_gate_delta_k − hysteresis`
   - while between, keep previous (after CS-base fill)

Defaults: `outdoor_gate_delta_k = 12`. Never both knobs same tick.

**Example:** restart + `d ≥ gate + hysteresis` → CS-base then immediately slope that tick.

### I1 `previous` advance (3C)

Update `previous` whenever I1 is **evaluated** on a non-flush demand tick — including incomplete W15, `|zone_error| < ε`, `|e_r| ≤ δ`, W-skip, D-cmd block, bounds no-op.

Do **not** advance on flush paths — those clear ephemeral including `previous`.

### W-skip (warm outdoor)

If `(comfort_ref − T_out) ≤ 0`:

- Freeze **slope** nudges only — do **not** force base.
- When I1 has selected **slope** and slope is frozen this way → **skip adapt** (no base fallback).
- When I1 is on **base** while `T_out ≥ comfort_ref`, base nudges may still run (W-skip does not freeze base).

### Error / nudge (N2 + G25)

```
e_r = r_obs − r_expected                         # °C/h
```

When not frozen and `|e_r| > δ`:

```
u = clamp((r_expected − r_obs) / e_sat, -1, +1)  # ≡ −e_r / e_sat clamped
Δ = u × max_rate                                 # on active knob
```

Then clamp params to bounds. Equivalent gains: `k_base = max_rate_base / e_sat = 0.40`, `k_slope = 0.040`.

No new thresholds beyond the scalars below.

### P1 scalars

| Symbol | Default | Source |
|--------|---------|--------|
| `ε` (`near_setpoint_eps_k`) | 0.3 °C | E2 yaml (else default) |
| `δ` | 0.10 °C/h (magnitude; freeze when `|e_r| ≤ δ`) | code constant |
| `e_sat` (`e_sat_c_per_h`) | 0.25 °C/h | E2 yaml (else default) |
| `r_expected` (`r_expected_c_per_h`) | 0.25 °C/h | E2 yaml (else default) |
| `min_steady_ticks` | 15 | code constant |
| `outdoor_gate_delta_k` | 12 | E2 yaml (else default) |
| `outdoor_gate_hysteresis_k` | 2 | code constant |
| max_rate `base` / `slope` | ±0.1 / ±0.01 per tick | code constants |
| bounds `base` / `slope` | `[15, 40]` / `[0.5, 2.5]` | code constants |

### Commission (E2)

Yaml nest `weather_feedforward.auto_correct` with:

- `outdoor_gate_delta_k`
- `r_expected_c_per_h`
- `near_setpoint_eps_k`
- `e_sat_c_per_h`

Defaults: `12` / `0.25` / `0.3` / `0.25`. Missing nest → defaults. All other scalars = code constants.

Extends yaml surface only; does **not** amend CAP-6 success wording or allow HA entities (epic yaml-only Decision stands). CAP-6 commission for `base` / `slope` / `comfort_ref` stays yaml-only.

### Yaml + JSON overlay

Load: yaml defaults → overlay `base` / `slope` from JSON if valid and in bounds. `comfort_ref` always from yaml. See Persistence.

### G1 — direction smoke table (offline; no script)

| # | Situation | Active knob | Expected Δ sign on knob | Notes |
|---|-----------|-------------|-------------------------|-------|
| 1 | Mild / near-comfort (`d ≤ gate−hyst`), slow rise (`r_obs < r_expected − δ`), I1 → base | `base` | **+** (raise curve) | Under-response → hotter baseline |
| 2 | Mild / near-comfort (`d ≤ gate−hyst`), fast rise (`r_obs > r_expected + δ`), I1 → base | `base` | **−** (lower curve) | Over-response → cooler baseline |
| 3 | Far from comfort (`d ≥ gate+hyst`), slow rise, I1 → slope | `slope` | **+** | Steepen outdoor response |
| 4 | Far from comfort, fast rise, I1 → slope | `slope` | **−** | Flatten outdoor response |
| 5 | Warm outdoor `(comfort_ref − T_out) ≤ 0`, I1 → slope | — | **skip** | W-skip: no slope nudge, no base fallback |
| 6 | Warm outdoor, I1 → base, slow rise | `base` | **+** allowed | W-skip does not freeze base |

---

## Guards

### N-both freezes (OR)

Skip adapt if **any** of:

1. Plant Management off
2. Outdoor temperature unavailable
3. No Heating Demand
4. Empty snapshots
5. Steady count below `min_steady_ticks`
6. Incomplete W15 (`< 15` samples)
7. Zone-switch / 4A-drop / M2 / plant-off / no-demand / outdoor-unavailable / empty-snapshots flush path
8. `|zone_error| < ε` (near-setpoint)
9. `|e_r| ≤ δ` (in-band rate) — only after W15 is full
10. W-skip (I1 on slope while `(comfort_ref − T_out) ≤ 0`)

Near-setpoint **or** in-band rate each alone freezes. Do not compute `e_r` until W15 is full.

On plant-off / no demand / outdoor unavailable: skip adapt; flush + `clear_steady` + clear ephemeral; do **not** clear or rewrite FF JSON.

### D-cmd / commit / SWT (2B + 2C)

Same-tick order:

1. Propose `Δ` on the active knob.
2. **D-cmd** vs **computed** pre-nudge `clamp(u_ff)` (not the plant entity):
   - block raise when command already at `setpoint_max`
   - block lower when command already at `setpoint_min`
   - relieving moves OK
3. If blocked: no param mutate; SWT from prior params; no JSON.
4. If allowed and post-bounds params **changed**: apply in-memory; SWT from **post-nudge** `clamp(u_ff)`; write JSON **only if** that SWT write succeeds (2C).
5. If SWT write fails: keep in-memory params; **no** JSON write; no rollback of in-memory.

### Bounds no-op (3A)

If after bounds clamp the params are unchanged → not a successful persist commit; **no** JSON write (SWT may still run with unchanged params).

### JSON commit timing

Write/update `ff_auto_correct_state.json` only when params actually changed **and** SWT write succeeded (2C). No write on idle / skip / D-cmd-block / bounds-no-op / SWT-fail ticks.

---

## Persistence

### Store (B1)

- File: `ff_auto_correct_state.json` in the AppDaemon app directory.
- Shape: `{"base", "slope"}` (+ optional `version: 1`).
- No HA entities.

### Load

1. Start from yaml-commissioned `base` / `slope` / `comfort_ref`.
2. If JSON valid and in bounds → overlay `base` / `slope`.
3. Missing / corrupt / out-of-bounds → yaml only; warn; do **not** rewrite the file until the next successful adapt commit.

### Persist

- Only when params actually changed **and** SWT write succeeded (2C).
- Not on bounds-no-op (3A).
- No auto-reset on plant-off or outdoor-unavailable; ops delete the JSON file to restore commission defaults.
- Steady / window / I1 `previous` / selected-zone id are **not** persisted.

---

## Non-goals

- Critical Zone / max-error air as an SWT **closed-loop** driver; any air term on the SWT command.
- New HA entities for FF / auto-correct.
- Resurrect ωc / LADRC on water under another name.
- Adapting `comfort_ref`.
- Offline scripts or runtime CAP-7 prototypes in this spike (G1 is the direction table above only).
- Leaving formula, guards, or persistence for 1.5 to invent.

---

## References

- Spike ticket: `spike-ff-rise-rate-auto-correct-rule.md`
- Plan (frozen intent): `spike-ff-rise-rate-auto-correct-rule-plan.md`
- Spec CAP-7 / Constraints: `../spec-weather-curve-swt-only/spec-weather-curve-swt-only.md`
- Guard/persist *shape* prior art only: `docs/adr/0003-online-ladrc-omega-c-auto-tune.md` (not the CAP-7 law)
- Forge locked FF / rejected air→SWT: `../forge-weather-curve-zone-actuators/forge-weather-curve-zone-actuators.md`
