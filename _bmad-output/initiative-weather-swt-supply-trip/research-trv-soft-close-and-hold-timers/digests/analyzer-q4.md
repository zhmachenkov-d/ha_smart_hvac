# Analyzer Q4 @ 2ec1908

Coverage almost entirely mocked HvacApp in tests/test_hvac_app.py (~35 test_trv_*, flame/hold suite) plus tests/test_config.py parse contracts. No TRV tests outside test_hvac_app.py; no live AppDaemon timer integration.

TRV: floor, overshoot latch/clear, plant-off 100, runs while flame latched, independent of demand, accuracy listen→control_event, equal-float skip, no valve_opening writes.

Flame hold: run_in schedule after successful trip write, expiry TRV-then-prelude, cancel on clear paths, orphan token guards, idle write-fail keeps latch disarms hold.

Config: valve_closure_floor, pair-mandatory mapping, flame_trip_hold_s parse only.
