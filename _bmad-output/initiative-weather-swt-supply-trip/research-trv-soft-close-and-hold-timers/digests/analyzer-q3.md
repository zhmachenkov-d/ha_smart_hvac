# Analyzer Q3 @ 2ec1908

Schedule only in flame_event after successful SWT 0 trip write: bump token, run_in(_flame_trip_hold_expired, flame_trip_hold_s, token=), store handle, set latch (hvac_app.py:198-207). Default hold 900s (config.py:234-239).

_disarm_flame_trip_hold: clear since, bump token, cancel_timer (152-158). _clear_flame_trip_state: latch False + disarm (147-150). Cancels via plant-off hands_off, rising-edge under latch, hold expiry start; _go_idle disarms only (latch clear after successful idle write 0).

Callback: orphan token check → clear → _apply_trv_law → _gate_prelude → optional _run_demand (160-170).

Not found: second schedule path besides flame_event.
