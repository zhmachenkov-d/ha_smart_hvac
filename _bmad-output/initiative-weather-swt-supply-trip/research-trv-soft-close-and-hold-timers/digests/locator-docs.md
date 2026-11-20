# Locator digest — apps.yaml.example, CONTEXT, AGENTS, docs/, knowledge/ @ 2ec1908

## 1
- ADR 0008, adr-trv-write-gated-overshoot-latch, adr-trv-plant-off-no-latch-clear, knowledge/concepts/trv-soft-close.md, CONTEXT/AGENTS TRV sections, apps.yaml.example valve_closure_floor

## 2
- apps.yaml.example valve_closure+accuracy; adr-trv-accuracy-shared-control-event; CONTEXT/AGENTS accuracy listeners

## 3
- ADR 0008 flame hold; adr-write-gated-flame-latch; adr-flame-hold-expiry-trv-then-prelude; adr-idle-flame-clear-after-write; knowledge flame-short-on-trip; apps.yaml.example flame_*_s

## 4
- Only AGENTS.md pytest runner mention in this area; no test file docs

## 5
- No literal "requires accuracy" line; adr-trv-accuracy-shared-control-event and trv-soft-close knowledge document accuracy coupling

## 6
- Documented call sites match code: tick/event/hold expiry; flame handlers excluded
