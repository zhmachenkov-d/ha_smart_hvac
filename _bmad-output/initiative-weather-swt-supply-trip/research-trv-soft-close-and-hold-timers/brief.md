# Brief — codebase research: TRV soft-close and hold timers

Repository: `/workspaces/ha-smart-hvac` (working directory)
Full commit: `2ec1908088a50a2a88fb157b9652532cbb46e704`
Short commit: `2ec1908`
Branch: `main` (informational only; research reads the commit alone)
File budget per analyzer: 15
History budget (historian): 10
Validation: `normal`

## Excluded from every search
- `_bmad-output/`
- `_bmad/`
- Any plans, specs, stories, or tickets folders under those paths

## Questions

1. **how** — How does the App, under Plant Management on, decide and write `valve_closure_degree` for each commissioned Sonoff TRV (including floor, overshoot latch behavior, and Plant Management off)?
2. **where / how** — How does thermostat yaml commission define a Sonoff TRV (`valve_closure`, `accuracy`), and when are `accuracy` entities registered as state listeners?
3. **how** — How does the flame short-on path schedule, cancel, and run its hold timer callback?
4. **how tested** — How are TRV soft-close behavior and hold/timer behavior covered in automated tests?
5. **why** — Why does commissioned TRV soft-close require `accuracy` (commit / PR history of the requirement)?
6. **what touches** — What call sites invoke `_apply_trv_law` or read/write TRV overshoot latch state?

## Areas (layout; locators)
- `apps/` (incl. `apps/ha_smart_hvac/`)
- `tests/`
- top-level + docs + knowledge: `apps.yaml.example`, `CONTEXT.md`, `AGENTS.md`, `docs/`, `knowledge/`
