# Walkthrough: PR #63 — remove water-path LADRC/ωc (CAP-4)

Target: [PR #63](https://github.com/zhmachenkov-d/ha_smart_hvac/pull/63) (`feat/1-2-remove-ladrc-water-path` → `main`).

Current block: **(none — all blocks done)**

## Blocks

- [x] **1. Intent** — done
- [x] **2. Broad strokes** — done
- [x] **3. Runtime delete** — done
- [x] **4. Config and yaml contract** — done
- [x] **5. Critical Zone API purge** — done
- [x] **6. Tests and absence locks** — done
- [x] **7. Periphery** — done

---

### 1. Intent

Source: plan frozen Intent in [story-remove-ladrc-and-c-from-the-water-path-plan.md](../epic-weather-curve-swt-only/story-remove-ladrc-and-c-from-the-water-path-plan.md) (ticket 1.2 / CAP-4).

**Problem:** After story 1.1, water-path LADRC/ωc and CZ-as-SWT symbols still sit dormant — CAP-4 requires removal, not dormancy.

**Approach:** Delete LADRC + ωc tuner/persistence + blow-up helpers, strip ladrc/tune yaml/config, purge `select_critical_zone`/`ControlDecision`; rewrite tests so CAP-5 and keepers stay green. ADR/CONTEXT → entry 1.3.

---

### 2. Broad strokes

Weather-curve demand path stays; this PR removes the dormant LADRC/ωc/CZ-driver surface around it.

1. [hvac_app.py](../../../apps/ha_smart_hvac/hvac_app.py) — FF-only `control_tick`; no LADRC construct/helpers.
2. [config.py](../../../apps/ha_smart_hvac/config.py) + [models.py](../../../apps/ha_smart_hvac/models.py) — no `ladrc` / `tune_state_path` / `Ladrc*` / `ControlDecision`.
3. [coordinator.py](../../../apps/ha_smart_hvac/coordinator.py) — `has_heating_demand` only; picker gone.
4. [apps.yaml.example](../../../apps.yaml.example) — no `ladrc:` block.
5. [test_hvac_app.py](../../../tests/test_hvac_app.py) + [test_config.py](../../../tests/test_config.py) — CAP-5 keepers + parse/absence smoke; old LADRC suites deleted.

---

### 3. Runtime delete

`initialize` only parses config and schedules the tick. Demand writes `clamp(u_ff)`; idle writes `0`; plant-off only logs. Deleted modules: `ladrc.py`, `ladrc_tuner.py` (ωc persist/load/`publish_sensor` gone with them). Blow-up/guard/residue helpers removed from the app module.

- [hvac_app.py — initialize / control_tick](../../../apps/ha_smart_hvac/hvac_app.py#L18-L67)
- Deleted: `apps/ha_smart_hvac/ladrc.py`, `apps/ha_smart_hvac/ladrc_tuner.py`

---

### 4. Config and yaml contract

`parse_config` no longer requires or stores `ladrc` / `tune_state_path`. Example yaml is FF + zones only. Leftover `ladrc:` in gitignored house `apps/apps.yaml` is ignored by parse — operator must strip before Exclusive Session.

- [config.py — parse_config](../../../apps/ha_smart_hvac/config.py)
- [models.py — HvacConfig](../../../apps/ha_smart_hvac/models.py#L61-L70)
- [apps.yaml.example](../../../apps.yaml.example)

---

### 5. Critical Zone API purge

`select_critical_zone` and `ControlDecision` are removed. Heating Demand for SWT remains the any-zone boolean `has_heating_demand`. CAP-7 may later identify a max-error zone for rise-rate only — not restored here.

- [coordinator.py](../../../apps/ha_smart_hvac/coordinator.py)

---

### 6. Tests and absence locks

`_tick_app` is `_config` only. CAP-5 (a–e) plus idle/off assert no `_ladrc`/`_tuner`/`_blow_up_*`. `test_ladrc.py` / `test_ladrc_tuner.py` deleted; parse/example smoke and module/CZ absence live in `test_config.py`. Coordinator keeps `has_heating_demand_*` only.

- [test_hvac_app.py](../../../tests/test_hvac_app.py)
- [test_config.py](../../../tests/test_config.py)
- [test_coordinator.py](../../../tests/test_coordinator.py)

---

### 7. Periphery

- [__init__.py](../../../apps/ha_smart_hvac/__init__.py) — docstring off “LADRC”.
- Plan + deferred-work under `_bmad-output/…` (party deferred CZ entry superseded).
- Out of scope this PR: ADR 0002/0003, CONTEXT, AGENTS, `knowledge/`.
