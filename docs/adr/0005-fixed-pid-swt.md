---
status: accepted
---

# Fixed-gain PID Set Water Temperature

The HVAC App commands Set Water Temperature from a fixed-gain PI term on weighted demand-zone air error under Plant Management and Heating Demand gates. Demand command is `round-to-0.1(clamp(base_water_temp + u_pid))`. This supersedes ADR 0004 (weather-curve / CAP-7 SWT). Outdoor Temperature, Weather Feedforward, CAP-7 rise-rate auto-correct, and `ff_auto_correct_state.json` are not on the water path or live commissioning. Optional online RLS retune of Kp/Ki is ADR 0006.

## SWT gates

When Plant Management is on and Heating Demand is present, the HVAC App writes the demand command above. When Plant Management is on and there is no Heating Demand (idle), it writes `0` and clears PID ephemeral state (∫). When Plant Management is off, it does not write Set Water Temperature and clears PID ephemeral state — not “write 0”.

The HVAC App owns the OpenTherm Set Water Temperature write. The Multi-Zone Coordinator computes Zone Errors, Heating Demand, and Critical Zone selection for diagnostics and logging only — it does not drive Set Water Temperature.

## Tick vs event

The same Plant Management / Heating Demand gate law runs on the periodic `control_tick` path and the event path. `initialize` invokes one explicit first `control_tick` (same tick path). Only `control_tick` (init or periodic) advances PID ∫ and steps RLS per ADR 0006 when adaptive. Demand SWT may also write on a gated-demand rising edge without advancing ∫ or stepping RLS.

- **Initialize:** after a successful schedule, `initialize` runs one full `control_tick` so the first demand command does not wait a full `control_interval`.
- **Periodic `control_interval`** (`control_tick`): on demand, evaluates PI, may write the demand command, and may advance ∫. Weight-unusable demand fail: write `0` and clear ∫.
- **Event path** (`listen_state` → `control_event`): re-evaluates on change of Plant Management, any configured zone air temperature, or any configured thermostat’s `hvac_action` or setpoint (`temperature` attribute) — not Outdoor. Shared gate prelude may clear on idle / plant-off / no-valid-zones. Rising-edge into **gated demand** (Plant Management on **and** Heating Demand — including plant turning on while zones already demand) may write demand SWT with current gains **without** advancing ∫ and **without** stepping RLS; the edge does not reset `control_interval`. After a successful demand-path write, further zone air / setpoint events neither write demand SWT nor advance ∫ until idle / plant-off / fail clear (a skipped write, e.g. unreadable plant, leaves the edge open for a later event). Weight-unusable on the demand-edge path takes the same fail as a tick: write `0` and clear ∫.

Accepted consequence: an idle or no-valid-zones clear on the event path writes `0` and resets ∫ immediately; demand SWT can resume on the next rising-edge into gated demand or the next `control_tick` (≤ `control_interval`) without waiting solely for the timer. Plant-off on the event path clears ∫ and does not write (plant may remain at the last demand command until a later write).

There is no debounce. The write throttle is the equal-float skip on Set Water Temperature plant readback. Unreadable or non-finite plant readback skips the write and does not advance ∫; when the plant already reads the command, the service call is skipped and ∫ still advances on the tick path (R7). Changing Heating Demand inputs must update those listeners in the same change. Periodic cadence remains; an event-only loop is a non-goal.

## PI law and anti-windup

```
e = Tset_w − Tair_w   (weighted averages over demand zones)
u_pid = kp·e + ki·∫
command = round-to-0.1(clamp(base_water_temp + u_pid, setpoint_min, setpoint_max))
```

Units: `e` in °C air; ∫ in °C·h; `kp` in °C water per °C air; `ki` in 1/h so the I-term `ki·∫` is °C water, bounded by `i_term_min` / `i_term_max`. Each demand tick that steps adds `e·control_interval/3600` (configured interval, not measured elapsed time).

Anti-windup: I-term clamps plus same-sign SWT-saturation freeze (no ∫ step when raw is above `setpoint_max` with `e > 0`, or below `setpoint_min` with `e < 0`). Gains, weights, base, and the same `setpoint_min` / `setpoint_max` clamp bounds commission from yaml.

## Out of scope

Weather Feedforward / CAP-7 commissioning, Outdoor as a control listener, and Critical Zone closed-loop air→water tracking. Optional RLS adaptive gains: ADR 0006.
