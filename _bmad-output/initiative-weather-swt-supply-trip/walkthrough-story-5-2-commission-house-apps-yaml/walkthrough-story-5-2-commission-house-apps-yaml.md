# Walkthrough: Story 5.2 — Commission house apps.yaml for flame short-on
Target: house [apps/apps.yaml](../../../apps/apps.yaml) (gitignored) · backup [apps/apps.yaml.pre-5.2](../../../apps/apps.yaml.pre-5.2) · epic [tickets.toml](../tickets/epic-replace-supply-trip-with-flame/tickets/tickets.toml) entry id 2 · branch `feat/5-2-commission-house-apps-yaml-flame` (tracks origin)

**Current block:** Wrap-up (done — commit+push to PR #152; story marked done; merge deferred)

## Blocks
- [x] **Intent** — done (Formal review 6 patches; Second opinion accept; Test OK)
- [x] **Broad strokes** — done (Test + Demo)
- [x] **Slice: House flame keys + drop supply trip** — done (Formal review 2 patches; Test ALL_PASS)
- [x] **Slice: Plan / verification artifact** — done (Second opinion accept; Test Verification OK)
- [x] **Periphery** — done (Test ALL_PASS)
- [x] **Wrap-up** — done (commit+push to PR #152; story marked done; merge deferred)

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
Plant block swaps legacy supply-trip `boiler_water` for confirmed flame short-on keys (min True duration + hold seconds); header notes flame + pre-5.2 backup; Outdoor/plant/FF/zones/TRVs stay byte-identical to the backup.

- [apps/apps.yaml](../../../apps/apps.yaml) (header flame + backup comments) — documents commission purpose
- [apps/apps.yaml](../../../apps/apps.yaml) (`flame_on` / `ch_active` / `flame_on_min_s: 300` / `flame_trip_hold_s: 900`) — required flame listeners + timings
- [apps/apps.yaml.pre-5.2](../../../apps/apps.yaml.pre-5.2) (`boiler_water`) — baseline proving trip key removed and other IDs unchanged
- [apps/apps.yaml](../../../apps/apps.yaml) (outdoor / plant / FF / zones) — retained entity values unchanged vs backup

Review notes: Formal review — 2 patch (header); 2/2 applied. Test — ALL_PASS after comment patches.

---

### Slice: Plan / verification artifact
House yaml stays gitignored; the tracked story surface is the plan: post-edit Code Map, runnable Verification (key-level trip absence + ID-stability + parse_config), Plan Change Log, and Code Review checkoffs from this walkthrough.

- [story-commission-house-apps-yaml-for-flame-short-on-plan.md](../tickets/epic-replace-supply-trip-with-flame/tickets/story-commission-house-apps-yaml-for-flame-short-on-plan.md) (Code Map) — post-edit inventory
- [story-commission-house-apps-yaml-for-flame-short-on-plan.md](../tickets/epic-replace-supply-trip-with-flame/tickets/story-commission-house-apps-yaml-for-flame-short-on-plan.md) (Verification) — runnable offline asserts + ignore
- [story-commission-house-apps-yaml-for-flame-short-on-plan.md](../tickets/epic-replace-supply-trip-with-flame/tickets/story-commission-house-apps-yaml-for-flame-short-on-plan.md) (Plan Change Log / Code Review) — history + review patches checked

Review notes: Second opinion — accept as written; Test — plan Verification + ignore + ID stability OK.

---

### Periphery
- [apps.yaml.example](../../../apps.yaml.example) — shape reference only; not edited this story
- [initiative-weather-swt-supply-trip.md](../initiative-weather-swt-supply-trip.md) Notes — confirmed house flame entity IDs (2026-11-15)
- [.gitignore](../../../.gitignore) (`apps/apps.yaml` / `apps/apps.yaml.*`) — keeps house commission + backup untracked
- [tickets.toml](../tickets/epic-replace-supply-trip-with-flame/tickets/tickets.toml) (entry id 2) — epic leaf for this HITL commission
- [demo-broad-strokes-transcript.md](./demo-broad-strokes-transcript.md) — walkthrough demo artifact

Review notes: Test — gitignore + tickets + Notes + demo OK.

---

### Wrap-up
House commission is on disk (gitignored); tracked follow-through is committing remaining walkthrough dirt, pushing to `feat/5-2-commission-house-apps-yaml-flame` / PR #152, then mark story done — no Exclusive Session. Merge deferred unless the owner asks.

Review notes: User confirmed commit + push + mark done (1–3); merge deferred (4).
