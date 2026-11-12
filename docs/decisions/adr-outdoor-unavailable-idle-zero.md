# Outdoor unavailable under plant-on writes SWT 0

When Plant Management is on and Outdoor Temperature is missing or non-finite, the App clears the demand path via `_go_idle` (write Set Water Temperature `0` + WARN with entity id), not a plant-unreadable-style skip that leaves the prior SWT. Plant-off still does not read Outdoor and does not write. Recorded from story 1.1 plan Outdoor-fail lock A (`story-tracer-weather-curve-swt-law-plan.md`) and commits `17d4960e` / `75cae7cf`, because the fail-closed zero is surprising next to R7 write-skip and was an explicit party trade-off.
