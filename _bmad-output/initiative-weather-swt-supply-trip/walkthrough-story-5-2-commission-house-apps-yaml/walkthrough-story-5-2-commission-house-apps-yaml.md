# Walkthrough: Story 5.2 — Commission house apps.yaml for flame short-on
Target: house [apps/apps.yaml](../../../apps/apps.yaml) (gitignored) · backup [apps/apps.yaml.pre-5.2](../../../apps/apps.yaml.pre-5.2) · epic [tickets.toml](../tickets/epic-replace-supply-trip-with-flame/tickets/tickets.toml) entry id 2 · branch `feat/5-2-commission-house-apps-yaml-flame` (tracks origin)

**Current block:** Broad strokes (in progress)

## Blocks
- [x] **Intent** — done (Formal review 6 patches; Second opinion accept; Test OK)
- [ ] **Broad strokes** — in progress
- [ ] **Slice: House flame keys + drop supply trip**
- [ ] **Slice: Plan / verification artifact**
- [ ] **Periphery**
- [ ] **Wrap-up**

---

### Intent
Source: frozen Intent from plan [story-commission-house-apps-yaml-for-flame-short-on-plan.md](../tickets/epic-replace-supply-trip-with-flame/tickets/story-commission-house-apps-yaml-for-flame-short-on-plan.md) (Problem + Approach).

**Problem:** House `apps/apps.yaml` still commissions legacy `boiler_water` and lacks `flame_on` / `ch_active`, so the 5.1 flame short-on law cannot load on the live house.

**Approach:** HITL-update local gitignored `apps/apps.yaml`: remove supply-trip keys (`boiler_water`; `r_max` / supply hold if present); add confirmed `flame_on` / `ch_active` plus explicit `flame_on_min_s: 300` / `flame_trip_hold_s: 900`; leave all other entity IDs unchanged; no Exclusive Session.

Review notes: Formal review patches applied (6/6); Second opinion — accept as written; Test — parse_config + ignore + ID stability OK.

---

### Broad strokes
House yaml drops supply-trip `boiler_water` and commissions flame short-on keys; plan is the tracked verify artifact; backup proves ID stability; example/config are shape/offline-verify only (not edited).

1. [apps/apps.yaml](../../../apps/apps.yaml) (`flame_on` / `ch_active` / 300 / 900) — live house commission (gitignored)
2. [apps/apps.yaml.pre-5.2](../../../apps/apps.yaml.pre-5.2) — pre-edit backup for ID-stability diff
3. [story-commission-house-apps-yaml-for-flame-short-on-plan.md](../tickets/epic-replace-supply-trip-with-flame/tickets/story-commission-house-apps-yaml-for-flame-short-on-plan.md) — tracked plan + Verification
4. [apps.yaml.example](../../../apps.yaml.example) — shape reference only (not edited)
5. [config.py](../../../apps/ha_smart_hvac/config.py) (`parse_config`) — offline verify path (not edited)

Review notes: Test — house diff + untouched example/config + parse_config OK. Demo — transcript demo-broad-strokes-transcript.md.

---

### Slice: House flame keys + drop supply trip

---

### Slice: Plan / verification artifact

---

### Periphery

---

### Wrap-up