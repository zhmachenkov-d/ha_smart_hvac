---
status: accepted
---

# Weather-curve-only Set Water Temperature

The HVAC App commands Set Water Temperature from Weather Feedforward alone under Plant Management and Heating Demand gates. This supersedes ADR 0002 (LADRC on Critical Zone air) and ADR 0003 (online ωc auto-tune on water). The full CAP-7 rise-rate auto-correct contract lives in `_bmad-output/initiative-weather-curve-zone-actuators/epic-weather-curve-swt-only/spike-ff-rise-rate-auto-correct-rule-decision.md` — cite that for Signal/Law/Guards edge tables; do not treat this ADR as a dump of those tables.

## SWT gates

When Plant Management is on and Heating Demand is present, the HVAC App writes `clamp(u_ff)`. When Plant Management is on and there is no Heating Demand (idle), it writes `0` and clears ephemeral / water-path state. When Plant Management is off, it does not write Set Water Temperature and clears ephemeral / water-path state. Idle and plant-off never delete or rewrite `ff_auto_correct_state.json`.

The HVAC App owns the OpenTherm Set Water Temperature write. The Multi-Zone Coordinator computes Zone Errors, Heating Demand, and Critical Zone selection for CAP-7 only — it does not own the plant write. There is no ADRC Controller term on this path.

## Feedforward law and CAP-6 commission

```
u_ff = base + slope × (comfort_ref − T_out)
```

CAP-6 commissions `base`, `slope`, and `comfort_ref` from yaml only. No new Home Assistant entities for Weather Feedforward.

## CAP-7 rise-rate auto-correct (summary)

**Signal.** Critical Zone = the zone with the largest Zone Error among zones with Heating Demand. That selection feeds FF parameters only — never SWT closed-loop / air→water tracking.

**Rate.** Over a W15 window of 15 samples on the selected zone:

```
r_obs = (T_now − T_window_start) / (15 × control_interval / 3600)   # °C/h
```

Default `r_expected = 0.25` °C/h.

**Knobs.** Adapt `base` and `slope` only; `comfort_ref` stays commission-only. One knob per tick (I1) at summary level — full hysteresis / outdoor-gate rules are in the spike.

**Persistence (B1).** Store adapted params in `ff_auto_correct_state.json` under the AppDaemon app directory, shape `{"base","slope"}` (+ optional `version`). Load: yaml commission → JSON overlay of `base`/`slope` when valid. Persist only when params actually changed **and** the SWT write succeeded; write is atomic, and I/O failure soft-fails (log warning; do not abort the tick after SWT already wrote). Ephemeral state (rise-rate window, steady count, I1 `previous`, selected-zone id) is not persisted. Ops delete the JSON file to restore yaml commission. Idle / plant-off never clears the file.

“Clear” on plant-on idle and plant-off means clear that ephemeral / water-path state only — not the persisted JSON.

## Non-goals

No air→SWT tracking / `u_track`. No LADRC or ωc on the water path. No adapting `comfort_ref`. No new HA entities for FF or auto-correct.
