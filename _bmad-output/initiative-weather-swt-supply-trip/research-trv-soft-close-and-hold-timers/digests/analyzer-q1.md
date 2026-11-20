# Analyzer Q1 @ 2ec1908

Commissioned = both valve_closure and accuracy set; _apply_trv_law skips otherwise (hvac_app.py:404-407). Runs before _gate_prelude on control_tick (239), control_event (256), _flame_trip_hold_expired (165); not on flame_event/ch_active_event.

Plant on: t_zone vs setpoint+|accuracy| for floor vs 100+latch; latched path uses t_zone vs setpoint only; latch keyed by closure id; write-gated add/discard via _write_number. Floor default 80. Plant off: write 100, does not clear _trv_overshoot_latched.

Load-bearing: hvac_app.py:398 (_apply_trv_law), :379 (_write_number), :45 (_trv_overshoot_latched), :421-466 hysteresis, models.py:17-18 commissioned, config.py:135-137 pair-mandatory.

Not found: valve_opening writes; clearing overshoot latch on plant-off; TRV gated on Heating Demand/Outdoor/Critical Zone.
