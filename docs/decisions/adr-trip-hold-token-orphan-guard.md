# Trip hold token invalidates orphan hold callbacks

Each armed hold callback carries a monotonic `token`; `_trip_hold_expired` no-ops when the token no longer matches, so a stale callback after clear→re-trip cannot clear the new latch or rewrite the weather curve. Recorded from story 2.1 review harden in `story-tracer-supply-rise-rate-trip-plan.md` and commit `d7e5262`, because AppDaemon `run_in` callbacks can outlive a cancelled timer narrative and the orphan path is surprising without an explicit invalidate rule.
