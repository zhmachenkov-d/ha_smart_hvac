# Demo: Story 7.3 Slice — CONTEXT + AGENTS
Generated: 2026-11-21T11:02:00+00:00

Offline spot-read vs story Req 3 / ADR 0008 house-idle soft-close.

## Checklist

| Clause | CONTEXT | AGENTS | Result |
| --- | --- | --- | --- |
| Plant-off → closure 100 + cancel hold | L38 | L32 | **Match** |
| House-idle floor + hold (80/300); no re-arm; idle expiry→100; orphan no-op; any demand→100; return-to-idle | L62 | L35 | **Match** (demand = “any Heating Demand”, not full enum) |
| Closure-only; leftover `accuracy` ConfigError | L62 | L35 | **Match** |
| No `_trv_overshoot_latched` / overshoot live law | absent | absent | **Match** |
| Event listeners: no accuracy soft-close listen | L58 (Weather FF listeners) | L38 | **Match** |
| AGENTS only inside `bmad:context`; Verified stamp unchanged | — | L2 stamp `2026-11-17` / `928b2b6…` | **Match** |

## Open order

1. `CONTEXT.md:38` → `:61`–`:62`  
2. `AGENTS.md:2` (stamp) → `:32` → `:35` → `:38`  

## Verdict

**Slice CONTEXT+AGENTS satisfied** under Reading C (compressed demand wording). Residual vs ADR enum accepted earlier.
