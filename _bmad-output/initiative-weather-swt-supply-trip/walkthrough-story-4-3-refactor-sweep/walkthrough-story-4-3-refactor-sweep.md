# Walkthrough: Story 4.3 — Refactor sweep
Target: [PR #148](https://github.com/zhmachenkov-d/ha_smart_hvac/pull/148) · branch `chore/4-3-trv-refactor-sweep` · `e1a3c81`

**Current block:** Wrap-up (done — commit+push; merge deferred)

## Blocks
- [x] **Intent** — done (Formal review clean; Second opinion accept; Test 335 pytest + ruff)
- [x] **Broad strokes** — done (Test 15; Demo transcript)
- [x] **Slice: Accuracy listen + `_entity_id` strip** — done (Formal review 1 defer; Test 10)
- [x] **Slice: Prelude-isolation + expanded goldens** — done (Formal review 2 defer; Test 5)
- [x] **Slice: Deferred prune** — done (Test ALL_PASS; Second opinion accept)
- [x] **Periphery** — done (Test ALL_PASS)
- [x] **Wrap-up** — done (commit+push; merge deferred)


---

### Intent
Source: frozen Intent from plan [story-refactor-sweep-plan.md](../tickets/epic-trv-idle-max-close/tickets/story-refactor-sweep-plan.md) (Problem + Approach).

**Problem:** Epic 4 deferred notes still call out open TRV soft-close leftovers from 4.1: no accuracy-entity listener, missing prelude-isolation and expanded multi-TRV goldens, and `_entity_id` accepting whitespace-only ids.

**Approach:** Close those four deferred items only — listen accuracy → `control_event`, add the named ACs, strip entity ids at parse, then prune this epic’s deferred-work bullets. No flame/SWT/house-yaml scope; leave epic-3 deferred bullets alone.

Review notes: Formal review — clean (17 rejected); Second opinion — accept; Test — 60 focused + full pytest, ruff clean; deferred epic-4 settled / epic-3 remain.

---

### Broad strokes
Accuracy listen re-enters the shared `control_event` → TRV-law path; parse strips entity ids; new ACs lock prelude isolation and multi-TRV/cold-start; deferred prune closes epic-4 leftovers only.

1. [hvac_app.py](../../../apps/ha_smart_hvac/hvac_app.py) (`_register_control_listeners` ~L73) — commissioned `accuracy` → `listen_state(control_event, …)`
2. [config.py](../../../apps/ha_smart_hvac/config.py) (`_entity_id` ~L118) — `strip()` then reject empty; return stripped
3. [test_hvac_app.py](../../../tests/test_hvac_app.py) (TRV ACs ~L1992+) — accuracy re-apply, prelude-isolation, multi/mixed, cold-start
4. [test_config.py](../../../tests/test_config.py) (~L598+) — whitespace-only `ConfigError`; padded ids stored stripped
5. [deferred-work.md](../deferred-work.md) (Settled epic-4) — prune A–D leftovers; epic-3 bullets remain

Review notes: Test — 15 entry-point pytest; Demo — [demo-broad-strokes-transcript.md](demo-broad-strokes-transcript.md) (listen + strip + ACs + deferred Settled).

---

### Slice: Accuracy listen + `_entity_id` strip
Commissioned TRV `accuracy` joins the existing `control_event` listeners (no TRV-only callback), so an accuracy change re-runs `_apply_trv_law` like plant/outdoor/zone. `_entity_id` strips whitespace, rejects empty, and returns the stripped id for TRV and house/zone entity fields.

1. [hvac_app.py](../../../apps/ha_smart_hvac/hvac_app.py) (`_register_control_listeners` L73–74) — `listen_state(control_event, thermo.accuracy)` when set
2. [config.py](../../../apps/ha_smart_hvac/config.py) (`_entity_id` L118–125) — strip → empty `ConfigError` → return stripped
3. [config.py](../../../apps/ha_smart_hvac/config.py) (outdoor/boiler/plant ~L217–224) — same helper on house-level entity fields
4. [test_hvac_app.py](../../../tests/test_hvac_app.py) (`test_initialize_trv_mapping_listens_on_climate_attrs`, `test_trv_accuracy_state_change_reapplies_law`) — accuracy listen yes / closure listen no; accuracy event re-applies floor
5. [test_config.py](../../../tests/test_config.py) (whitespace/padded ~L598+) — reject whitespace-only; store padded as stripped

Review notes: Formal review — 0 patch, 1 defer (AGENTS/CONTEXT); Test — 10 focused pytest + ruff clean; spot-check listen + strip OK.

---

### Slice: Prelude-isolation + expanded goldens
`control_tick` / `control_event` always run `_apply_trv_law` before `_gate_prelude`, so Outdoor-fail or empty-zone idle still leave TRV law having run; each TRV uses its own zone/setpoint/accuracy reads (sibling unread does not block a readable TRV). New goldens lock multi-TRV independent latches, mixed plain-string skip, and cold-start overshoot latch on initialize.

1. [hvac_app.py](../../../apps/ha_smart_hvac/hvac_app.py) (`control_tick` / `control_event` ~L231–249) — `_apply_trv_law` then `_gate_prelude`
2. [hvac_app.py](../../../apps/ha_smart_hvac/hvac_app.py) (`_apply_trv_law` ~L389) — per-TRV own-reads; skip when own inputs unreadable
3. [test_hvac_app.py](../../../tests/test_hvac_app.py) (`test_trv_outdoor_fail_*`, `test_trv_empty_zone_*`, `test_trv_sibling_*` ~L2000+) — prelude-isolation ACs
4. [test_hvac_app.py](../../../tests/test_hvac_app.py) (`test_trv_multi_*`, `test_trv_cold_start_*` ~L2089+) — multi/mixed + cold-start goldens
Review notes: Formal review — 2 defer (accuracy Outdoor-fail event; empty-zone spy); 11 rejected; Test — 5 prelude/golden pytest + ruff; tick/event TRV-before-prelude, supply has no TRV.

---

### Slice: Deferred prune
Story product prune removed epic-4 TRV soft-close leftover bullets and recorded Settled with the 4.1 idle-overshoot cite; epic-3 AGENTS/CONTEXT/ADR hygiene bullets stay on purpose. Walkthrough Formal reviews then added separate defers (accuracy listener inventory; Outdoor-fail event; empty-zone spy) — not reopening A–D.

1. [deferred-work.md](../deferred-work.md) (Settled epic-4) — A–D leftovers closed; idle-overshoot cites `test_trv_independent_of_heating_demand`
2. [deferred-work.md](../deferred-work.md) (epic-3 bullets above Settled) — remain on purpose
3. [tickets.toml](../tickets/epic-trv-idle-max-close/tickets/tickets.toml) (entry 3) — verify names prune + epic-3 remain
4. [deferred-work.md](../deferred-work.md) (2026-11-16 walkthrough CR deferrals) — AGENTS/CONTEXT accuracy listen; Outdoor-fail event; empty-zone spy

Review notes: Test — ALL_PASS; Second opinion — accept Deferred prune as written (Settled thin on A/B/D list; epic-3 still says settle-in-entry-4 stale pointer).

---

### Periphery
Planning/process artifacts shipped with the sweep; not runtime law.

1. [story-refactor-sweep-plan.md](../tickets/epic-trv-idle-max-close/tickets/story-refactor-sweep-plan.md) — frozen Intent + A–D execution/AC + Code Review appendices
2. [tickets.toml](../tickets/epic-trv-idle-max-close/tickets/tickets.toml) (entry 3) — description/verify name A–D + prune
3. [party-mode .memlog.md](../../party-mode/memories/installed/.memlog.md) — party gap-hunt trail for this plan

Review notes: Test — ALL_PASS (plan Intent/CR; tickets.toml entry 3 A–D+prune; memlog gap-hunt).

---

### Wrap-up
Review of PR #148 / story 4.3 complete through Periphery. Likely follow-through: commit walkthrough artifacts, push to `chore/4-3-trv-refactor-sweep`, keep PR #148 open (merge when ready).

Review notes: commit+push to PR #148; merge deferred.
