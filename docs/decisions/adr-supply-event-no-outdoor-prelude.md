# Supply event Plant∧Demand only (never Outdoor prelude)

Supply rise-rate observation runs on `supply_event` gated by Plant Management on ∧ Heating Demand only — it must not call `_gate_prelude` or require a readable Outdoor Temperature. Outdoor remains on the CAP-8 tick/`control_event` path. Recorded from story 2.1 plan Intent Always (`story-tracer-supply-rise-rate-trip-plan.md`) and commits `fbe647f` / `d7e5262`, because mixing Outdoor into the trip path would block latching when Outdoor flakes and contradicts the epic’s “every supply change under demand” law.
