# Demo: Story 7.3 Intent — live docs ↔ house-idle soft-close
Generated: 2026-11-21T09:30:00+00:00

Offline spot-read on `main` after PR #166 (no Exclusive Session). Intent AC: live ADR/CONTEXT/AGENTS/knowledge teach house-idle floor+hold (tracer Reqs 1–7), not overshoot/accuracy soft-close; three decisions bannered historical.

## Checklist vs Intent / tracer Reqs 1–7

| Clause | Live surface | Result |
| --- | --- | --- |
| First all-idle → floor + arm hold once; no re-arm while holding | ADR 0008 §TRV; CONTEXT TRV; AGENTS TRV; `trv-soft-close.md` | **Match** |
| Idle hold expiry → 100 stay (no re-floor); orphan/token no-op | Same four | **Match** |
| Any Heating Demand → 100 + cancel/never arm; return-to-idle re-floor+arm | ADR + knowledge enumerate cold start / rising-edge / sustained; CONTEXT/AGENTS say “any Heating Demand” | **Match** (compressed on CONTEXT/AGENTS — known residual from plan follow-up note) |
| Plant-off → 100 + cancel hold | ADR SWT gates parenthetical + §TRV; CONTEXT; AGENTS | **Match** |
| Closure-only; leftover `accuracy` → ConfigError; no accuracy listen | ADR / AGENTS / knowledge; outdoor listener inventory has no accuracy | **Match** |
| Never `valve_opening_degree`; Critical Zone not TRV driver; CAP-7 out | All live soft-close surfaces | **Match** |
| No live overshoot / `_trv_overshoot_latched` teaching | Hygiene `rg` on live path set | **Clean** (0 hits) |
| Three overshoot/accuracy decisions historical → ADR 0008 | Leading banner lines on each | **Match** |
| Index TRV blurb not “plant-off keeps overshoot latch” | `knowledge/concepts/index.md` | **Match** (house-idle floor + hold) |
| AGENTS Verified stamp unchanged | `Verified 2026-11-17 against 928b2b6…` | **Match** |

## Hygiene commands (this demo)

```bash
rg -n '_trv_overshoot_latched|commissioned.*accuracy|accuracy.*control_event|overshoot-100|overshoot latch' \
  docs/adr/0008-weather-curve-trv-flame-swt.md CONTEXT.md AGENTS.md \
  knowledge/concepts/trv-soft-close.md knowledge/concepts/index.md knowledge/concepts/outdoor-temperature.md
# → no hits

rg -n 'CAP-7|ff_auto_correct_state' docs/adr/0008-weather-curve-trv-flame-swt.md CONTEXT.md AGENTS.md knowledge/concepts/
# → out-of-scope / avoid / historical only
```

## Anchors (open in order)

1. `docs/adr/0008-weather-curve-trv-flame-swt.md:31` — § TRV soft-close house-idle law
2. `CONTEXT.md:61` — TRV soft-close glossary
3. `AGENTS.md:35` — Conventions TRV bullet (`bmad:context`)
4. `knowledge/concepts/trv-soft-close.md:19` — Plant-off / Plant-on bullets
5. `docs/decisions/adr-trv-write-gated-overshoot-latch.md:1` — historical banner (same pattern on sibling two)

## Verdict

**Intent satisfied on `main`.** Residual (accepted earlier): CONTEXT/AGENTS compress demand flavors to “any Heating Demand” while ADR/knowledge enumerate; not rising-edge-only, not overshoot teaching. Entry 4 still owns deferred prune — out of this story.
