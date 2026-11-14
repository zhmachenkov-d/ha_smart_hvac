# Idle trip clear: disarm hold always; latch after idle write 0

On idle (`_go_idle`), the App always cancels the hold timer and wipes supply samples; `_supply_trip_latched` becomes false only when the idle SWT `0` write succeeds. Plant-off uses full `_clear_trip_state` (no write). Recorded from story 2.1 Decision C in `story-tracer-supply-rise-rate-trip-plan.md` and commits `d7e5262` / related review harden, because clearing the latch before a confirmed idle write would drop trip enforcement while the plant may still read a non-zero setpoint.
