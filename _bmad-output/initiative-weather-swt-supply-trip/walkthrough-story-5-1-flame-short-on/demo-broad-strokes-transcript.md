# Demo: Story 5.1 Broad strokes
Generated: 2026-11-16T17:56:50+00:00

Exercised offline (no Exclusive Session). Five Broad-strokes entry points in order.

## 1. Observe gate + flame_event (`hvac_app.py` ~L133)

```python
def _flame_observe_gate(self) -> bool:
    """Plant on ∧ Heating Demand ∧ ch_active on ∧ ¬latch — no Outdoor."""
    ...
    if self.get_state(config.ch_active) != "on":
        return False
    ...
    return has_heating_demand(zones)

def flame_event(...):
    """Flame short-on observe/latch — Plant∧Demand∧ch_active∧¬latch only."""
    gate_open = self._flame_observe_gate()
    if old == "off" and new == "on":
        if gate_open:
            self._flame_on_since = self._monotonic()
        else:
            self._flame_on_since = None
        return
    # short on→off under open gate → write 0 + latch
```

Short-on latch golden:

```
.                                                                        [100%]
1 passed in 0.35s
```

(`test_flame_short_on_latches_and_writes_zero`)

## 2. ADV8 hold expiry + latched demand (`hvac_app.py` ~L160)

```python
def _flame_trip_hold_expired(self, kwargs: dict) -> None:
    """Hold elapsed: clear, TRV law, then Outdoor prelude + demand (ADV8)."""
    self._clear_flame_trip_state()
    self._apply_trv_law()
    outcome = self._gate_prelude()
    ...
    self._run_demand(zones, outdoor)

def _run_demand(...):
    if self._flame_trip_latched:
        ...  # keep SWT 0; no weather curve / CZ log
```

```
...                                                                      [100%]
3 passed in 0.35s
```

(`test_flame_hold_expiry_gated_runs_trv_then_curve`, `test_latched_demand_writes_zero_no_ff`, `test_flame_hold_expiry_closed_gate_clears_only`)

## 3. Config flame fields (`config.py` ~L221)

```python
flame_on = _entity_id(_require(args, "flame_on"), label="flame_on")
ch_active = _entity_id(_require(args, "ch_active"), label="ch_active")
flame_on_min_s = _number(args, "flame_on_min_s", _DEFAULT_FLAME_ON_MIN_S)
...
flame_trip_hold_s = int(hold_raw)  # fractional truncate; >= 1
```

```
....................                                                     [100%]
20 passed, 127 deselected in 0.34s
```

## 4. `apps.yaml.example` flame placeholders (~L14)

```yaml
  outdoor_temperature: sensor.YOUR_OUTDOOR_TEMPERATURE
  # Flame short-on trip (min True duration; hold = whole seconds latched at SWT 0).
  flame_on: binary_sensor.YOUR_FLAME_ON
  ch_active: binary_sensor.YOUR_CH_ACTIVE
  flame_on_min_s: 300
  flame_trip_hold_s: 900
```

Parse asserts flame keys present, trip keys absent:

```
.                                                                        [100%]
1 passed in 0.35s
```

(`test_parse_apps_yaml_example`)

## 5. Flame matrix goldens (`test_hvac_app.py` ~L1077+)

```
...........................                                              [100%]
27 passed, 101 deselected in 0.37s
```

Latch / clear / CH wipe+preserve / since-None fall / closed-gate arm / TRV-while-latched / ADV8.

## Summary

Offline demo only — house `apps.yaml` / live `flame_on`+`ch_active` are story 5.2 + Exclusive Session.
