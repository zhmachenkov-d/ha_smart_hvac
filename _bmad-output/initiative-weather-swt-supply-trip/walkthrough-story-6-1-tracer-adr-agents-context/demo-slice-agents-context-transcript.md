# Demo: Story 6.1 — Slice AGENTS + CONTEXT
Generated: 2026-11-17T10:06:30+00:00

Offline spot-read of agent-facing domain SoT.

## 1. AGENTS.md — Where things are + Conventions

| Check | Line | Result |
| --- | --- | --- |
| Live SoT = ADR 0008; do not follow 0004–0007 | L18 | OK |
| `knowledge/` not live until story 6.2 | L20 | OK |
| Plant-off → `_clear_flame_trip_state` (no SWT write) | L32 | OK |
| Decision C: disarm always; clear latch after idle write-0 | L33 | OK |
| Demand = `round-to-0.1(clamp(u_ff))`; CAP-7 out | L34 | OK |
| TRV before prelude (tick / event / hold expiry) | L35 | OK |
| Flame short-on; rising-edge `_clear_flame_trip_state`; prelude zones guard | L36 | OK |
| Dual-gate Outdoor vs `_flame_observe_gate` | L37 | OK |
| Critical Zone diagnostics-only | L39 | OK |
| No live `supply_event` / `_supply_trip` | — | OK (none) |

## 2. CONTEXT.md — glossary

| Check | Line | Result |
| --- | --- | --- |
| Outdoor / Weather Feedforward + `accuracy` on `control_event` | L54 / L58 | OK |
| **TRV soft-close** | L61–62 | OK |
| **Flame short-on trip** (post-patch clear wording) | L65–66 | OK |
| **Supply rise-rate trip** = Historical + `_Avoid_` | L69–71 | OK |
| Supply terms only in that historical block | L70–71 | OK |

## Verdict

AGENTS + CONTEXT teach curve + TRV + flame under ADR 0008; supply rise-rate is demoted; knowledge deferred to 6.2.
