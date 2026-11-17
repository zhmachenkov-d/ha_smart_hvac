# Idle flame clear: disarm hold always; latch after idle write 0

On idle (`_go_idle`), the App always disarms the flame hold via `_disarm_flame_trip_hold`; `_flame_trip_latched` becomes false only when the idle SWT `0` write succeeds. Plant-off uses full `_clear_flame_trip_state` (no write). Recorded from story 6.1 Decision C (party hole 1A) in `story-tracer-adr-agents-context-for-trv-flame-water-law-plan.md`, because clearing the flame latch before a confirmed idle write would drop short-on enforcement while the plant may still read a non-zero setpoint.
