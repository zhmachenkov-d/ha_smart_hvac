# Walkthrough: PR #70 — Auto-correct FF from max-error zone rise rate

Target: [PR #70](https://github.com/zhmachenkov-d/ha_smart_hvac/pull/70) (`feat/cap7-ff-rise-rate-auto-correct` → `main`).

Current block: **Wrap-up** (done — review finished)

## Blocks

- [x] **1. Intent** — done
- [x] **2. Broad strokes** — done
- [x] **3. Max-error demand zone selection** — done
- [x] **4. Pure CAP-7 adapt law** — done
- [x] **5. App runtime: overlay, flush, 2C persist** — done
- [x] **6. Config and yaml nest** — done
- [x] **7. Tests** — done
- [x] **8. Periphery** — done

---

### 1. Intent

Source: frozen Intent in [story-auto-correct-ff-from-max-error-zone-rise-rate-plan.md](../epic-weather-curve-swt-only/story-auto-correct-ff-from-max-error-zone-rise-rate-plan.md#L21-L25).

**Problem:** CAP-7 is documented (spike decision + ADR 0004) but not live — FF params stay at yaml commission and never adapt from the max-error demand zone’s air rise rate.

**Approach:** Implement the accepted spike contract so under Heating Demand the app selects that zone for rise-rate only, adapts `base`/`slope` (not `comfort_ref`), persists via B1 JSON only when params actually changed **and** SWT write succeeds, and keeps SWT as `clamp(u_ff)` with updated params — no air→SWT tracking.

---

### 2. Broad strokes

CAP-7 goes live: yaml commission + optional JSON overlay feed mutable runtime `base`/`slope`; demand ticks may nudge them from the max-error zone’s rise rate; SWT stays `clamp(u_ff)`.

1. [ff_auto_correct.py](../../../apps/ha_smart_hvac/ff_auto_correct.py) — pure `FfAutoCorrector` (window / I1 / nudge / guards / B1 load-save).
2. [hvac_app.py](../../../apps/ha_smart_hvac/hvac_app.py) — owns corrector lifecycle; flush ephemeral on plant-off / idle / no-demand; persist only on `params_changed and write_ok`.
3. [coordinator.py — select_max_error_demand_zone](../../../apps/ha_smart_hvac/coordinator.py#L18-L36) — CAP-7 signal (T-hold / lex among demand zones).
4. [config.py](../../../apps/ha_smart_hvac/config.py) + [models.py — AutoCorrectConfig](../../../apps/ha_smart_hvac/models.py#L57-L62) — optional `auto_correct` nest (E2 defaults).
5. [test_ff_auto_correct.py](../../../tests/test_ff_auto_correct.py) + [test_hvac_app.py](../../../tests/test_hvac_app.py) — pure law + Hass 2C / flush / CAP-5 keepers.

---

### 3. Max-error demand zone selection

Among zones with `zone_error > 0`, pick the largest error. T-hold keeps `previous_name` while it remains in the max-error tie set; otherwise lex `name`. Selection feeds rise-rate / FF params only — not SWT.

- [coordinator.py — select_max_error_demand_zone](../../../apps/ha_smart_hvac/coordinator.py#L18-L36)
- [test_coordinator.py](../../../tests/test_coordinator.py) — T-hold / lex / demand-pool

---

### 4. Pure CAP-7 adapt law

`process_demand` appends W15 before freeze early-returns, runs I1 (CS-base then hysteresis same tick), then may nudge `base` or `slope` under N2+G25 / deadband / near-ε / W-skip / D-cmd / bounds. Flush paths (4A absent, Z1 switch, M2 non-finite, empty select) clear ephemeral and hold prior `clamp(u_ff)`. Caller still owns SWT write + JSON.

- [FfAutoCorrector.process_demand](../../../apps/ha_smart_hvac/ff_auto_correct.py#L129-L207)
- [I1 — _evaluate_i1](../../../apps/ha_smart_hvac/ff_auto_correct.py#L209-L219)
- [B1 load/save](../../../apps/ha_smart_hvac/ff_auto_correct.py#L55-L76)

---

### 5. App runtime: overlay, flush, 2C persist

`initialize` builds the corrector from yaml, overlays `base`/`slope` from `ff_auto_correct_state.json` when valid (warn otherwise; `comfort_ref` stays yaml). Demand: `process_demand` → `_write_setpoint` → JSON only if params changed **and** write ok. Plant-off / outdoor-unavailable / empty zones / no-demand clear ephemeral and leave JSON untouched.

- [hvac_app.py — initialize / control_tick](../../../apps/ha_smart_hvac/hvac_app.py#L27-L82)
- [_load_ff_overlay / _persist_ff_state](../../../apps/ha_smart_hvac/hvac_app.py#L105-L127)

---

### 6. Config and yaml nest

Optional `weather_feedforward.auto_correct` nest maps to frozen `AutoCorrectConfig` (defaults 12 / 0.25 / 0.3 / 0.25). Missing nest → defaults; non-positive `e_sat` / `r_expected` rejected at parse. Example yaml documents omit=defaults and delete-JSON restore.

- [config.py — _parse_auto_correct](../../../apps/ha_smart_hvac/config.py#L45-L71)
- [models.py — AutoCorrectConfig](../../../apps/ha_smart_hvac/models.py#L57-L62)
- [apps.yaml.example](../../../apps.yaml.example)

---

### 7. Tests

Pure suite covers W15/1A, I1/CS-base, guards, B1 corrupt/OOB, bounds no-op. Hass suite covers plant-off/idle/no-demand flush (JSON untouched), write-fail keeps in-memory nudge without JSON, CAP-5 a–e unchanged, plus CAP-7 adapt≠additive. Config tests: missing nest → defaults; valid nest overrides.

- [test_ff_auto_correct.py](../../../tests/test_ff_auto_correct.py)
- [test_hvac_app.py](../../../tests/test_hvac_app.py)
- [test_config.py](../../../tests/test_config.py)
- [test_coordinator.py](../../../tests/test_coordinator.py)

---

### 8. Periphery

- [story-auto-correct-ff-from-max-error-zone-rise-rate-plan.md](../epic-weather-curve-swt-only/story-auto-correct-ff-from-max-error-zone-rise-rate-plan.md) — ticket plan (status built)
- [_bmad-output/party-mode/memories/installed/.memlog.md](../../party-mode/memories/installed/.memlog.md) — party-mode memlog bump
- Out of scope this PR: ADR/CONTEXT/AGENTS (1.3 done), house `apps/apps.yaml`, `knowledge/`
