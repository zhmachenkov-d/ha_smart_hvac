# Demo: Story 4.3 Broad strokes

Generated: 2026-11-16T10:13:00+02:00

Exercised offline (no Exclusive Session). Shows the five Broad-strokes entry points in order.

## 1. Accuracy → control_event listen (`hvac_app.py:73`)

```
    def _register_control_listeners(self) -> None:
        """Re-evaluate gate on plant / outdoor / zone air / thermo attrs / accuracy."""
        config = self._config
        self.listen_state(self.control_event, config.plant_management)
        self.listen_state(self.control_event, config.outdoor_temperature)
        for zone in config.zones:
            self.listen_state(self.control_event, zone.temperature)
            for thermo in zone.thermostats:
                self.listen_state(
                    self.control_event, thermo.climate, attribute="hvac_action"
                )
                self.listen_state(
                    self.control_event, thermo.climate, attribute="temperature"
                )
                if thermo.accuracy is not None:
                    self.listen_state(self.control_event, thermo.accuracy)
```

Initialize asserts accuracy entity listen and no closure listen:

```
.                                                                        [100%]
1 passed in 0.32s
```

## 2. `_entity_id` strip-then-keep (`config.py:118`)

```
def _entity_id(raw: Any, *, label: str) -> str:
    if not isinstance(raw, str):
        raise ConfigError(f"{label} must be a non-empty entity id")
    stripped = raw.strip()
    if not stripped:
        raise ConfigError(f"{label} must be a non-empty entity id")
    return stripped

```

```
........                                                                 [100%]
8 passed in 0.31s
```

## 3–4. TRV ACs + config goldens (`test_hvac_app.py:1992+`, `test_config.py:598+`)

```
..............                                                           [100%]
14 passed, 244 deselected in 0.35s
```

## 5. Deferred prune (`deferred-work.md` Settled)

```
# Deferred work

- source_plan: `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-weather-curve-swt-restore/tickets/story-detach-pid-rls-from-live-swt-and-example-commissioning-plan.md`
  summary: AGENTS.md / CONTEXT.md / ADR 0005–0006 still describe live PID/∫/RLS SWT after FF detach
  evidence: Intent Always forbids rewriting those agent/domain docs in this story (epic 3 owns supersede); contradiction remains for agents/operators until epic 3.

- source_plan: `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-supersede-pid-domain-docs/tickets/story-delete-dead-pid-rls-modules-plan.md`
  summary: Epic-1 deferred-work bullet still frames AGENTS/CONTEXT/ADR PID supersede as outstanding after epic 3.1 already rewrote those surfaces
  evidence: Pre-existing defer from detach story; not caused by pid/rls file delete — settle or prune in entry 4 refactor sweep

- source_plan: `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-supersede-pid-domain-docs/tickets/story-delete-dead-pid-rls-modules-plan.md`
  summary: docs/decisions/adr-cap8-shared-ff-demand-writer.md still warns about AGENTS sticky-latch prose until epic 3
  evidence: Historical CAP-8 note; AGENTS already updated in 3.1 — cosmetic lag, not caused by module delete

- source_plan: `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-supersede-pid-domain-docs/tickets/story-delete-dead-pid-rls-modules-plan.md`
  summary: AGENTS.md still says knowledge/ may lag until story 3.2 after 3.2 merged
  evidence: Agent-context stale pointer; Intent Never forbids AGENTS rewrite in 3.3 — entry 4 / docs hygiene

## Deferred from: code review of story-delete-dead-pid-rls-modules-plan (2026-11-14)
- Stale epic-1 deferred-work bullet still frames AGENTS/CONTEXT/ADR PID supersede as outstanding — pre-existing; not caused by module delete; settle/prune in entry 4

## Settled: epic-4 TRV soft-close leftovers (story-refactor-sweep)
- Expanded-goldens idle-overshoot half already covered by 4.1 `test_trv_independent_of_heating_demand` (+ core overshoot); remaining A–D closed in this sweep.
```

Note: epic-3 AGENTS/CONTEXT/ADR bullets remain above the Settled heading; only epic-4 leftovers are closed.
