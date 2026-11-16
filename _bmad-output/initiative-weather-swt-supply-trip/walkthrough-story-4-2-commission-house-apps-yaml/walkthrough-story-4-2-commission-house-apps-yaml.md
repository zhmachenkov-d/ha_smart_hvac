# Walkthrough: Story 4.2 — Commission house apps.yaml for TRV soft-close
Target: house [apps/apps.yaml](../../../apps/apps.yaml) (gitignored) · backup [apps/apps.yaml.pre-4.2](../../../apps/apps.yaml.pre-4.2) · epic entry 2

**Current block:** Wrap-up (done — commit+push to PR #147; merge deferred)

## Blocks
- [x] **Intent** — done (Formal review 5 patches; Second opinion accept; Test parse_config+ignore+ID stability)
- [x] **Broad strokes** — done (Test + Demo)
- [x] **Slice: House Sonoff mappings + floor** — done (Formal review 2 patches; Test ALL_PASS)
- [x] **Slice: Plan / verification artifact** — done (Second opinion accept; Test Verification OK)
- [x] **Periphery** — done (Test ALL_PASS)
- [x] **Wrap-up** — done (commit+push `1034c46` to PR #147; merge deferred)

---

### Intent
Source: frozen Intent from plan [story-commission-house-apps-yaml-for-trv-soft-close-plan.md](../tickets/epic-trv-idle-max-close/tickets/story-commission-house-apps-yaml-for-trv-soft-close-plan.md) (Problem + Approach).

**Problem:** House `apps/apps.yaml` still lists Sonoff TRVs as plain climate strings, so the 4.1 idle max-close law never commissions on the live house.

**Approach:** HITL-update local gitignored `apps/apps.yaml`: add `valve_closure_floor: 80` and map livingroom×2, bedroom, and childroom climates to the confirmed closure+accuracy number entities; leave generic climates as strings; do not change existing entity IDs; no Exclusive Session.

Review notes: Formal review patches applied (5/5); Second opinion — accept Intent as written; Test — parse_config + ignore + ID stability OK.

---

### Broad strokes
House yaml commissions floor + four Sonoff TRV mappings; generics stay plain strings; plan is the tracked verify artifact; parser already knows the shape from 4.1.

1. [apps/apps.yaml](../../../apps/apps.yaml) (`valve_closure_floor`, livingroom mappings) — live house commission (gitignored)
2. [apps/apps.yaml.pre-4.2](../../../apps/apps.yaml.pre-4.2) — pre-edit backup for ID-stability diff
3. [story-commission-house-apps-yaml-for-trv-soft-close-plan.md](../tickets/epic-trv-idle-max-close/tickets/story-commission-house-apps-yaml-for-trv-soft-close-plan.md) — tracked plan + Verification
4. [apps.yaml.example](../../../apps.yaml.example) — shape reference only (not edited)
5. [config.py](../../../apps/ha_smart_hvac/config.py) (`parse_config` / `_parse_thermostat`) — offline verify path (not edited)

Review notes: Test — house diff + untouched example/config + parse_config OK. Demo — transcript demo-broad-strokes-transcript.md.

---

### Slice: House Sonoff mappings + floor
Top-level `valve_closure_floor: 80` enables the 4.1 default; four Sonoff climates become `{climate, valve_closure, accuracy}` maps with confirmed number entities; bathroom / kitchen / wc stay plain climate strings so the TRV law never touches them.

- [apps/apps.yaml](../../../apps/apps.yaml) (`valve_closure_floor: 80`) — floor for idle max-close
- [apps/apps.yaml](../../../apps/apps.yaml) (living_room thermostats) — livingroom×2 commissioned
- [apps/apps.yaml](../../../apps/apps.yaml) (children_bedroom / bedroom) — childroom + bedroom commissioned
- [apps/apps.yaml](../../../apps/apps.yaml) (bathroom / kitchen / wc) — plain-string generics unchanged
- [apps/apps.yaml.pre-4.2](../../../apps/apps.yaml.pre-4.2) — baseline proving climate IDs and other entity values unchanged

Review notes: Formal review — 2 patch (header + floor comment); 2/2 applied. Test — ALL_PASS after comment patches.

---

### Slice: Plan / verification artifact
House yaml stays gitignored; the tracked story surface is the plan: post-edit Code Map, runnable Verification (`PYTHONPATH=apps` → safe_load → drop AD keys → parse_config asserts), Plan Change Log, and Code Review checkoffs from this walkthrough.

- [story-commission-house-apps-yaml-for-trv-soft-close-plan.md](../tickets/epic-trv-idle-max-close/tickets/story-commission-house-apps-yaml-for-trv-soft-close-plan.md) (Code Map) — post-edit inventory
- [story-commission-house-apps-yaml-for-trv-soft-close-plan.md](../tickets/epic-trv-idle-max-close/tickets/story-commission-house-apps-yaml-for-trv-soft-close-plan.md) (Verification) — runnable offline asserts + ignore/status
- [story-commission-house-apps-yaml-for-trv-soft-close-plan.md](../tickets/epic-trv-idle-max-close/tickets/story-commission-house-apps-yaml-for-trv-soft-close-plan.md) (Plan Change Log / Code Review) — history + review patches checked
Review notes: Second opinion — accept as written (hygiene gaps only). Test — plan Verification + ignore + ID stability OK.

---

### Periphery
- [apps.yaml.example](../../../apps.yaml.example) — shape reference only; not edited this story
- [initiative-weather-swt-supply-trip.md](../initiative-weather-swt-supply-trip.md) Notes — confirmed house TRV entity IDs (2026-11-15)
- [.gitignore](../../../.gitignore) (`apps/apps.yaml` / `apps/apps.yaml.*`) — keeps house commission + backup untracked
- [tickets.toml](../tickets/epic-trv-idle-max-close/tickets/tickets.toml) (entry id 2) — epic leaf for this HITL commission
- [demo-broad-strokes-transcript.md](./demo-broad-strokes-transcript.md) — walkthrough demo artifact

Review notes: Test — gitignore + tickets + Notes + demo OK.

---

### Wrap-up
House commission is on disk (gitignored); tracked follow-through is committing the plan + walkthrough on `feat/4-2-commission-trv-apps-yaml`, then PR / mark story done — no Exclusive Session.

Review notes: committed plan+walkthrough; pushed; house yaml remains local/gitignored.