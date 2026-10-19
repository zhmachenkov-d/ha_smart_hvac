# Walkthrough: PR #66 — CAP-7 FF rise-rate auto-correct decision (spike 1.4)

Target: [PR #66](https://github.com/zhmachenkov-d/ha_smart_hvac/pull/66) (`spike/1-4-ff-rise-rate-auto-correct-rule` → `main`).

Current block: **Wrap-up** (awaiting follow-through choice — all review blocks done)

## Blocks

- [x] **1. Intent** — done
- [x] **2. Broad strokes** — done
- [x] **3. Signal and Law** — done
- [x] **4. Guards, Persistence, Non-goals** — done
- [x] **5. Epic Notes HITL** — done
- [x] **6. Periphery** — done

---

### 1. Intent

Source: frozen Intent in [spike-ff-rise-rate-auto-correct-rule-plan.md](../epic-weather-curve-swt-only/spike-ff-rise-rate-auto-correct-rule-plan.md#L23-L27).

**Problem:** Stories 1.3 (ADR/docs) and 1.5 (CAP-7 implementation) are blocked until the rise-rate signal, adaptation law, guards, persistence shape, and explicit non-goals for Weather Feedforward auto-correct are written down — without inventing an air→SWT tracking term.

**Approach:** Time-boxed design spike: decision note at the spike’s Decision target path (Signal / Law / Guards / Persistence / Non-goals + G1 direction smoke table), draft epic Notes Decision for Denys, stop. No runtime CAP-7 code and no offline script in this ticket.

---

### 2. Broad strokes

Docs-only CAP-7 contract lock. Entry points:

1. [Decision note](../epic-weather-curve-swt-only/spike-ff-rise-rate-auto-correct-rule-decision.md) — accepted CAP-7 contract (Signal / Law / Guards / Persistence / Non-goals + G1).
2. [Plan](../epic-weather-curve-swt-only/spike-ff-rise-rate-auto-correct-rule-plan.md) — frozen Intent + planning Decisions the note encodes.
3. [Epic Notes](../epic-weather-curve-swt-only/epic-weather-curve-swt-only.md#L48-L54) — Decision (2026-10-19, Denys) … accepted pointer.
4. [Spike ticket](../epic-weather-curve-swt-only/spike-ff-rise-rate-auto-correct-rule.md#L32-L47) — AC the decision must satisfy.

---

### 3. Signal and Law

Max-error Heating Demand zone feeds FF params only (not SWT). W15 rolling rise-rate on that zone; I1 one-knob (CS-base + outdoor hysteresis); N2+G25 nudges `base` or `slope`; `comfort_ref` stays commission-only.

- [Signal](../epic-weather-curve-swt-only/spike-ff-rise-rate-auto-correct-rule-decision.md#L19-L67) — selection pool, W15/R025 (1A+1B), Z1 / 4A / M2 edges.
- [Law](../epic-weather-curve-swt-only/spike-ff-rise-rate-auto-correct-rule-decision.md#L71-L171) — I1, W-skip, N2+G25, P1, E2, [G1 rows 1–4](../epic-weather-curve-swt-only/spike-ff-rise-rate-auto-correct-rule-decision.md#L161-L168) (mild→base / far→slope direction smoke).

---

### 4. Guards, Persistence, Non-goals

N-both OR-freezes; D-cmd / 2C commit vs computed `clamp(u_ff)`; B1 JSON overlay on yaml commission; explicit non-goals so 1.5 cannot restore air→SWT tracking.

- [Guards](../epic-weather-curve-swt-only/spike-ff-rise-rate-auto-correct-rule-decision.md#L174-L215)
- [Persistence](../epic-weather-curve-swt-only/spike-ff-rise-rate-auto-correct-rule-decision.md#L218-L237)
- [Non-goals](../epic-weather-curve-swt-only/spike-ff-rise-rate-auto-correct-rule-decision.md#L241-L248)

---

### 5. Epic Notes HITL

Epic Notes “Unknown” rise-rate line replaced by an accepted Decision pointer naming operator Denys and the decision file.

- [Epic Notes — Decision (2026-10-19, Denys)](../epic-weather-curve-swt-only/epic-weather-curve-swt-only.md#L54)

---

### 6. Periphery

- [Spike ticket](../epic-weather-curve-swt-only/spike-ff-rise-rate-auto-correct-rule.md) — spike 1.4 scope and AC.
- [Plan](../epic-weather-curve-swt-only/spike-ff-rise-rate-auto-correct-rule-plan.md#L6) — status `built`.
- [Party-mode memlog](../../party-mode/memories/installed/.memlog.md#L58-L79) — append trail for spike 1.4 planning dig.
