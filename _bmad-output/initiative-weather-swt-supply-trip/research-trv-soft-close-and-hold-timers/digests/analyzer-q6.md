# Analyzer Q6 @ 2ec1908

_apply_trv_law defined hvac_app.py:398; called from _flame_trip_hold_expired:165, control_tick:239, control_event:256. initialize reaches it only via control_tick.

_trv_overshoot_latched: init :45; read :421; discard :432; add :457 — all inside _apply_trv_law only. No other apps/ production sites.
