# Source — user PID+RLS example (2026-11-07)

Intent input from the product owner session: replace Weather Feedforward with multi-zone adaptive PID (RLS) for Bosch Gaz 6000 via OpenTherm. Session decisions narrowed scope (fixed PID first; HA entity write; 300s tick; no direct OT daemon). The sketch below is historical intent, not the accepted design.

## Accepted deviations from this sketch

- No weather term; configurable `base_water_temp` + PID correction.
- OpenTherm only through existing Home Assistant Set Water Temperature entity.
- Fixed PID before RLS.
- `control_interval` default 300s; demand SWT write and PID advance only on that tick.
- Round SWT to 0.1 °C; skip write when unchanged.
- Project `setpoint_min` / `setpoint_max` clamp only.

## Sketch (as provided)

```python
# Adaptive PID with RLS (ARX y(k)=a1*y(k-1)+b0*u(k-1)), forgetting_factor≈0.98
# Multi-zone weighted current/setpoint + max zone error
# loop_interval = 300
# target_boiler_temp = base_water_temp (e.g. 40) + pid_output
# OpenTherm ID 1 setpoint / ID 25 boiler water temp (illustrative)
```

Full pasted daemon classes (`AdaptivePIDWithRLS`, `OpenThermInterfaceMock`, `BoschMultiZoneDaemon`) live in the chat transcript that opened this initiative; do not treat mock OT or numpy RLS as in-scope for the first epic.
