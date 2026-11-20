# Locator digest — area `apps/` @ 2ec1908

## 1 — TRV valve_closure_degree
- `apps/ha_smart_hvac/hvac_app.py:398 (_apply_trv_law) @ 2ec1908` — plant_on gate; requires valve_closure+accuracy; plant-off 100; overshoot latch vs floor
- `apps/ha_smart_hvac/hvac_app.py:379 (_write_number) @ 2ec1908` — equal-float skip; number/set_value
- `apps/ha_smart_hvac/hvac_app.py:45 (_trv_overshoot_latched) @ 2ec1908` — RAM latch set
- `apps/ha_smart_hvac/hvac_app.py:421-457 (latched add/discard) @ 2ec1908` — hysteresis
- `apps/ha_smart_hvac/hvac_app.py:239 (control_tick) @ 2ec1908` — calls TRV before prelude
- `apps/ha_smart_hvac/hvac_app.py:256 (control_event) @ 2ec1908` — same
- `apps/ha_smart_hvac/hvac_app.py:161 (_flame_trip_hold_expired) @ 2ec1908` — TRV before water
- `apps/ha_smart_hvac/config.py:261 (valve_closure_floor) @ 2ec1908` — parse floor
- `apps/ha_smart_hvac/models.py:91 (valve_closure_floor) @ 2ec1908` — field
- Empty under apps/: valve_opening driving TRV

## 2 — yaml commission + accuracy listeners
- `apps/ha_smart_hvac/config.py:128 (_parse_thermostat) @ 2ec1908` — mapping requires climate+valve_closure+accuracy
- `apps/ha_smart_hvac/models.py:17 (commissioned) @ 2ec1908` — both ids present
- `apps/ha_smart_hvac/hvac_app.py:74-75 (_register_control_listeners) @ 2ec1908` — listen_state accuracy → control_event

## 3 — flame hold timer
- `apps/ha_smart_hvac/hvac_app.py:172 (flame_event) @ 2ec1908` — short-on latch + run_in
- `apps/ha_smart_hvac/hvac_app.py:152 (_disarm_flame_trip_hold) @ 2ec1908` — cancel_timer + token bump
- `apps/ha_smart_hvac/hvac_app.py:160 (_flame_trip_hold_expired) @ 2ec1908` — orphan token guard then clear+TRV+prelude
- `apps/ha_smart_hvac/config.py:234 (flame_trip_hold_s) @ 2ec1908` — parse hold

## 4 — tests under apps/
- No test files under apps/
- `apps/ha_smart_hvac/config.py:61 (comment) @ 2ec1908` — notes external test guard

## 5 — accuracy requirement (code pointers only; history for historian)
- `apps/ha_smart_hvac/config.py:135-137 (_parse_thermostat) @ 2ec1908` — pair-mandatory
- Locator also listed commits 784fc71, eb79e95, ef4d7a0, b4d7603, e1a3c81 — for historian

## 6 — call sites
- `_apply_trv_law`: lines 165, 239, 256, definition 398
- `_trv_overshoot_latched`: 45, 421, 432, 457
