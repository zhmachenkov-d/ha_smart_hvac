# Demo: Story 7.3 Slice — ADR 0008 TRV + Event path
Generated: 2026-11-21T10:22:00+00:00

Offline read of `docs/adr/0008-weather-curve-trv-flame-swt.md` for this slice’s Places.

## Checklist (story Req 2 / entry 1 Reqs 1–7)

| Clause | Where | Result |
| --- | --- | --- |
| Plant-off SWT parenthetical: closure 100 + cancel hold | L11 SWT gates | **Match** |
| Event path: no commissioned accuracy listener | L27 Event path | **Match** (Plant/Outdoor/zone air/hvac_action/setpoint only) |
| Live cite list: no three overshoot/accuracy decisions | L8 Cite list | **Match** (prelude + flame decisions only; not adr-trv-write/plant-off/accuracy) |
| Prelude + flame-observe negative fence; never opening; ConfigError accuracy; CZ not TRV | L32 | **Match** |
| House-idle floor+arm once; no re-arm; idle expiry→100 stay; orphan no-op; demand enum; return-to-idle; plant-off 100+cancel | L34 | **Match** |
| CAP-7 out | L56 | **Match** |

## Open order

1. `docs/adr/0008-weather-curve-trv-flame-swt.md:11` — plant-off parenthetical  
2. `:27` — Event path inventory  
3. `:8` — live cite list  
4. `:31`–`:34` — § TRV soft-close  

## Verdict

**Slice ADR satisfied.** One file carries the full house-idle SoT for agent law.
