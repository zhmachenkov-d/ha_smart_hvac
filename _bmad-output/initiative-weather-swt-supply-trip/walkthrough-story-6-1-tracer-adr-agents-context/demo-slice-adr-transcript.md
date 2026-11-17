# Demo: Story 6.1 — Slice ADR 0008 + historical 0007 / pointers
Generated: 2026-11-17T10:01:00+00:00

Offline spot-read of the slice places in order.

## 1. ADR 0008 live MUST-floor

`docs/adr/0008-weather-curve-trv-flame-swt.md`

| Check | Result |
| --- | --- |
| `status: accepted` | L2 |
| Title curve + TRV + flame | L5 |
| Agent-law cite includes `adr-zone-rising-edge-decision-a.md` | L8 |
| Sections: SWT gates / Flame trip latch / Idle clear | L10 / L36 / L48 |
| Clear paths name rising-edge `_clear_flame_trip_state` | under Flame trip latch |

**Observed:** Accepted live SoT; CAP-7 out in Out of scope.

## 2. ADR 0007 historical

`docs/adr/0007-weather-curve-supply-trip-swt.md`

| Check | Result |
| --- | --- |
| `status: superseded by ADR-0008` | L2 |
| Historical banner → live ADR-0008 | L7 |
| Body still supply-trip era (past tense “commanded”) | L9 |
| Explicit historical + “follow ADR-0008” | L11 |

**Observed:** Demoted without rewriting into TRV/flame.

## 3. Live-pointers 0004–0006

| File | status | Live water law |
| --- | --- | --- |
| `0004-weather-curve-swt.md` | superseded by ADR-0005 (unchanged) | ADR-0008 (L5) |
| `0005-fixed-pid-swt.md` | superseded by ADR-0008 | ADR-0008 (L5) |
| `0006-optional-rls-adaptive-pid.md` | superseded by ADR-0008 | ADR-0008 (L5) |

**Observed:** All live-pointers cite 0008; 0005/0006 status retargeted.

## 4. house-calibration

| Check | Result |
| --- | --- |
| Lead includes flame / `ch_active` / TRV anti-cycle | L2 |
| Live water law → ADR 0008 + anti-cycle wiring sentence | L6 |

**Observed:** Pointer + lead definition aligned with 0008 era (no full §1 table — Intent Never).

## Verdict

Slice holds: 0008 is live law; 0007 historical; pointers and house-calibration retarget correctly.
