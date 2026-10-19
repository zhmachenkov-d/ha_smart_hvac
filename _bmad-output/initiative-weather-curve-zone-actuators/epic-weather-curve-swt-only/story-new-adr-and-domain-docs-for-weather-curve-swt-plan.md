---
title: 'New ADR and domain docs for weather-curve SWT'
type: 'feature'
ticket: '3'
created: '2026-10-19'
status: built
baseline_revision: '7bed334b308bcf2c949f0de52eff2d505801518a'
route: 'full'
route_source: 'auto'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/initiative-weather-curve-zone-actuators/spec-weather-curve-swt-only/spec-weather-curve-swt-only.md'
  - '{project-root}/_bmad-output/initiative-weather-curve-zone-actuators/epic-weather-curve-swt-only/spike-ff-rise-rate-auto-correct-rule-decision.md'
  - '{project-root}/.cursor/skills/grill-with-docs/ADR-FORMAT.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Live domain docs still describe LADRC on Critical Zone air plus ωc auto-tune as the SWT path, while code (stories 1.1–1.2) already runs weather-curve-only SWT and spike 1.4 has locked CAP-7 formula/persistence — maintainers and agents will reintroduce the old model.

**Approach:** Add ADR 0004 superseding 0002/0003; rewrite CONTEXT, AGENTS (inside `bmad:context`), and house-calibration for weather-curve SWT, yaml FF commission (CAP-6), and CAP-7 rise-rate auto-correct summary; keep `apps.yaml.example` documenting FF `base`/`slope`/`comfort_ref`.

## Boundaries & Constraints

**Always:**
- Create exactly `docs/adr/0004-weather-curve-swt.md` with YAML frontmatter `status: accepted` (ADR-FORMAT optional Status; required here). Add the same style Status frontmatter on 0002 and 0003 only — bodies unchanged:
  ```yaml
  ---
  status: superseded by ADR-0004
  ---
  ```
- **Decision (covers):** Ticket covers stay CAP-4/CAP-6; story 1.3 still writes CAP-7 formula/persistence prose in ADR/house-calibration (epic Notes + verify). Runtime CAP-7 remains story 1.5.
- **Decision (OpenTherm ownership):** The **HVAC App** owns the OpenTherm Set Water Temperature write (`clamp(u_ff)` under the gates below). The **Multi-Zone Coordinator** computes Zone Errors, Heating Demand, and Critical Zone selection for CAP-7 only — it does not own the plant write. No ADRC Controller term.
- **Decision (clear semantics):** “Clear” on plant-on idle and plant-off means clear **water-path / CAP-7 ephemeral** state (rise-rate window, steady count, I1 `previous`, selected-zone id — per spike). It does **not** delete or rewrite `ff_auto_correct_state.json`; adapted `base`/`slope` persist until ops delete that file. Plant Management off wording: no SWT write + clear ephemeral / water-path state (not “controller state” / LADRC).
- **ADR 0004 MUST-floor** (every item must appear; omit any → incomplete). Full Signal/Law/Guards edge tables stay in `spike-ff-rise-rate-auto-correct-rule-decision.md` — cite that path; do not dump them into the ADR:
  1. SWT gates: PM on + Heating Demand → `clamp(u_ff)`; plant-on idle → write `0` + clear ephemeral; plant-off → no write + clear ephemeral (JSON untouched)
  2. FF law: `u_ff = base + slope × (comfort_ref − T_out)`
  3. CAP-6: yaml-only commission of `base`/`slope`/`comfort_ref`; no new HA entities
  4. CAP-7 signal: Critical Zone = max Zone Error among Heating Demand zones; feeds **FF params only** (never SWT closed-loop)
  5. CAP-7 rate: W15 `r_obs = (T_now − T_window_start) / (15 × control_interval / 3600)` °C/h; default `r_expected = 0.25` °C/h
  6. CAP-7 knobs: adapt `base` and `slope` only; `comfort_ref` commission-only; one knob per tick (I1) at summary level
  7. CAP-7 persistence B1: `ff_auto_correct_state.json` under the **AppDaemon app directory**; `{"base","slope"}` (+ optional `version`); yaml → JSON overlay; persist only when params actually changed **and** SWT write succeeded; ephemeral not persisted; ops delete JSON to restore commission; idle/off never clears the file
  8. Non-goals: no air→SWT tracking / `u_track`; no LADRC/ωc on water; no adapting `comfort_ref`; no new HA entities
  9. Pointer: full contract = `_bmad-output/initiative-weather-curve-zone-actuators/epic-weather-curve-swt-only/spike-ff-rise-rate-auto-correct-rule-decision.md`
- **CONTEXT Language rewrites (required):**
  - **Remove** entries: ADRC Controller, LADRC, Controller Bandwidth (ωc), Observer Bandwidth (ωo), LADRC Auto-Tune, Extended State Observer, MADRC (depth stays in `knowledge/` only; no CONTEXT pointers required).
  - **Rewrite** Zone Error: drop “cannot become the Critical Zone” / SWT-selection implication; eligible errors feed Heating Demand and CAP-7 Critical Zone selection only.
  - **Rewrite** Critical Zone: max-error Heating Demand zone for CAP-7 FF rise-rate only — never SWT closed-loop driver.
  - **Rewrite** Weather Feedforward: outdoor baseline that **is** Set Water Temperature under the gates (`clamp(u_ff)`), not “added to LADRC tracking”.
  - **Rewrite** Multi-Zone Coordinator: Zone Errors / Heating Demand / Critical Zone for CAP-7; does not own OpenTherm write.
  - **Rewrite** Plant Management: off → no SWT write + clear ephemeral / water-path state (not “controller state”).
  - **Rewrite** example dialogue: HVAC App writes `clamp(u_ff)` or idle `0`; Critical Zone only as rise-rate source when discussing auto-correct.
- house-calibration **depth cap (operator-level only):** yaml FF commission (`base`/`slope`/`comfort_ref`); rise-rate auto-correct adapts `base`/`slope`; name `ff_auto_correct_state.json` in AppDaemon app dir + ops delete to restore commission; optional one-line W15 / `r_expected` summary; link ADR 0004 (+ 0001 for Exclusive Session). Drop LADRC/`b0`/`ωo`/`ωc` / `ladrc_tune_state` / “no FF auto-tune”. **Do not** paste ε/δ/I1 hysteresis/Guards/G1 tables — those stay in ADR pointer → spike.
- `apps.yaml.example` continues to show `weather_feedforward.base`/`slope`/`comfort_ref`; do **not** add `auto_correct` nest here (story 1.5).
- Edit AGENTS facts **inside** `<!-- bmad:context -->`: ADR catalog = **0001 Exclusive Session + 0004 weather-curve SWT** (not live 0002/0003); conventions = plant-off / plant-on idle clear semantics above; remove “clears LADRC” and “Online auto-tune adjusts ωc only”.
- **Decision (Critical Zone):** Keep the name; redefine as above. Multi-Zone Coordinator computes Zone Errors / Heating Demand and that selection for auto-correct.
- **Decision (LADRC terms):** Remove per CONTEXT Language rewrites list above.

**Never:**
- Touch `apps/ha_smart_hvac/**`, `tests/**`, or invent CAP-7 thresholds beyond the accepted spike decision.
- Rewrite ADR 0002/0003 bodies into weather-curve law; delete knowledge LADRC pages; implement CAP-7 runtime; change house entity IDs / commit `apps/apps.yaml`.
- Add HA entities for FF; lower `setpoint_min`; restore air→SWT tracking language as current behavior.
- Reintroduce LADRC/ADRC/ωc/ESO/MADRC as live Language entries or dialogue; use Critical Zone as an SWT air-loop driver.
- Clear or rewrite `ff_auto_correct_state.json` on idle/plant-off in docs; dump CAP-7 Guards/P1/G1 into house-calibration.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| ADR catalog | Reader opens `docs/adr/` / AGENTS list | 0004 present + `status: accepted`; 0002/0003 Status = superseded by ADR-0004; AGENTS lists 0001 + 0004 only | N/A |
| SWT ownership | CONTEXT / ADR / dialogue | HVAC App writes `clamp(u_ff)`; Coordinator does not own plant write | N/A |
| Clear semantics | idle / plant-off prose | Clear ephemeral; JSON file untouched | N/A |
| FF commission | house-calibration + `apps.yaml.example` | `base`/`slope`/`comfort_ref` yaml-documented; no HA entities | N/A |
| CAP-7 summary | ADR MUST-floor + house-cal operator note | B1 path under app dir; edges → spike; no Guards dump in calib | N/A |
| Stale LADRC claims | rg CONTEXT / AGENTS / house-calibration | No current-behavior CZ/LADRC/ωc/ADRC/`u_track`/`ladrc:` SWT claims | Historical ADR 0002/0003 bodies OK under Status superseded |

</frozen-after-approval>

## Code Map

- `docs/adr/0001-exclusive-session-against-production-ha.md` — leave; still valid Exclusive Session.
- `docs/adr/0002-ladrc-critical-zone-control.md`, `0003-online-ladrc-omega-c-auto-tune.md` — prepend Status YAML frontmatter only (`status: superseded by ADR-0004`); keep historical prose.
- **Create** `docs/adr/0004-weather-curve-swt.md` — frontmatter `status: accepted` + prose covering MUST-floor 1–9. Style: short ADR-FORMAT; `##` only if MUST-floor clarity needs it.
- `.cursor/skills/grill-with-docs/ADR-FORMAT.md` — Status + numbering rules to reuse.
- `CONTEXT.md` — apply CONTEXT Language rewrites list (remove LADRC family; rewrite Zone Error, Critical Zone, Weather Feedforward, Multi-Zone Coordinator, Plant Management, dialogue).
- `AGENTS.md` (inside `bmad:context`) — ADR list 0001+0004; conventions for idle/off clear + no ωc claim.
- `docs/house-calibration.md` — rewrite intro + §§3–6 / out-of-scope under **depth cap**; keep §1 wiring + §2 clamps.
- `apps.yaml.example` L13–16 — verify FF keys remain; no `auto_correct` nest.
- `_bmad-output/.../spike-ff-rise-rate-auto-correct-rule-decision.md` — CAP-7 full contract (do not edit).
- Out of scope: `apps/ha_smart_hvac/**`, `tests/**`, `knowledge/**`.

## Tasks & Acceptance

**Execution:**
- [x] `docs/adr/0004-weather-curve-swt.md` -- Create with `status: accepted` + MUST-floor 1–9; no alternate slug -- CAP-4/6/7 docs
- [x] `docs/adr/0002-ladrc-critical-zone-control.md` + `docs/adr/0003-online-ladrc-omega-c-auto-tune.md` -- Prepend exact Status YAML block above; bodies unchanged -- supersede
- [x] `CONTEXT.md` -- Apply CONTEXT Language rewrites list (ownership, clear semantics, Zone Error, CZ, FF, Coordinator, PM, dialogue; remove LADRC family) -- domain
- [x] `AGENTS.md` -- Inside `bmad:context`: catalog 0001+0004; conventions match clear/ownership decisions -- agents
- [x] `docs/house-calibration.md` -- Operator-level rewrite under depth cap; AppDaemon app-dir JSON; link 0004; drop LADRC/ωc -- CAP-6/7 ops
- [x] `apps.yaml.example` -- Confirm FF `base`/`slope`/`comfort_ref` still documented -- verify

**Acceptance Criteria:**
- Given ADR 0004, when read, then `status: accepted` and every MUST-floor item 1–9 is present (including W15 `r_obs`, B1 filename + AppDaemon app dir, clear≠JSON-delete, spike pointer).
- Given ADR 0002 and 0003, when frontmatter is read, then `status: superseded by ADR-0004` and bodies are byte-unchanged aside from that frontmatter.
- Given CONTEXT.md Language + dialogue, when inspected, then: HVAC App owns SWT write; Coordinator does not; Zone Error / Critical Zone / Weather Feedforward / Plant Management match Always rewrites; LADRC/ADRC/ωc/ωo/Auto-Tune/ESO/MADRC entries are absent.
- Given AGENTS.md inside `bmad:context`, when read, then ADR list is 0001 + 0004 (not live 0002/0003) and conventions match plant-off / plant-on idle clear semantics (no “clears LADRC” / ωc-only auto-tune).
- Given house-calibration.md, when followed by an operator, then FF yaml commission + rise-rate auto-correct at operator depth (no Guards/P1/G1 dump; no `ladrc:` / ωc persist); JSON named under AppDaemon app dir with ops-delete restore.
- Given `apps.yaml.example`, when inspected, then `weather_feedforward` still documents `base`/`slope`/`comfort_ref`.

## Implementation Notes

- 2026-10-19: Created ADR 0004 (`status: accepted`) covering MUST-floor 1–9; superseded 0002/0003 via Status frontmatter only (bodies byte-unchanged). Rewrote CONTEXT Language + dialogue (dropped LADRC family; CZ = CAP-7 rise-rate only; HVAC App owns SWT). Updated AGENTS `bmad:context` catalog to 0001+0004 and clear/JSON-untouched conventions. Rewrote house-calibration under operator depth cap (yaml FF + B1 JSON + ops-delete). Verified `apps.yaml.example` FF keys unchanged (no `auto_correct` nest). Verification: stale-phrase `rg` empty on CONTEXT/AGENTS/house-cal; Status/accepted/JSON/app-dir `rg` OK; body diffs vs baseline clean for 0002/0003.

## Plan Change Log

- 2026-10-19 party review: covers stay CAP-4/6 with CAP-7 docs in 1.3; fixed slug `0004-weather-curve-swt.md`; replaced vague CAP-7 summary with ADR MUST-floor 1–9 (Amelia+Grumbal). KEEP: 1A Critical Zone rename, 2A drop LADRC Language, spike pointer for edges, no `auto_correct` nest in example.
- 2026-10-19 plan review (patch all): OpenTherm ownership = HVAC App; clear = ephemeral only / JSON untouched; CONTEXT Language rewrite checklist + stronger ACs; B1 AppDaemon app dir; house-cal depth cap; Status YAML snippet + 0004 `accepted`; AGENTS 0001+0004 AC; tighter `rg`. KEEP: MUST-floor 1–9, 1A/2A, covers decision, spike pointer.

## Review Triage Log

- 2026-10-19 Review plan pass: high×3 (ownership, CONTEXT AC, clear semantics) + medium×5 (Zone Error, B1 path, house-cal depth, Status snippet, AGENTS AC) + low×2 (0004 accepted, rg) → **patch all** applied to plan.
- 2026-10-19 quick pass 1:
  - medium / patch — `docs/house-calibration.md` “What is not calibrated here” bullet `Air→SWT tracking / LADRC on water` reads as dormant LADRC-in-scope-elsewhere; rewrite to state removed / not on water path (CAP-4).
  - medium / patch — `docs/house-calibration.md` §1 `plant_management` + §5 step 6 omit JSON untouched on plant-off; add pairing already present in §4 / CONTEXT / AGENTS.

## Design Notes

ADR 0004 = MUST-floor 1–9 + `status: accepted`, still short. house-calibration stays operator-thin. CONTEXT drops LADRC family; Critical Zone only for CAP-7.

## Verification

**Commands:**
- `rg -n "drive the LADRC|LADRC tracking|Online auto-tune adjusts|clears LADRC|ladrc_tune_state|There is no online feedforward auto-tune|ADRC Controller|LADRC Auto-Tune|Extended State Observer|u_track|ladrc:" CONTEXT.md AGENTS.md docs/house-calibration.md` -- expected: no matches
- `rg -n "0002|0003|0004|weather_feedforward|ff_auto_correct_state|AppDaemon app" AGENTS.md docs/adr docs/house-calibration.md apps.yaml.example` -- expected: AGENTS cites 0001+0004 only as live; 0002/0003 Status superseded; 0004 accepted; example FF keys; JSON + app dir in 0004 and/or house-cal
- Manual Language headings in CONTEXT: Zone Error, Critical Zone, Weather Feedforward, Multi-Zone Coordinator, Plant Management rewritten; no ADRC/LADRC/ωc/ESO/MADRC headings
- Manual: ADR 0004 + house-calibration intro — operator can commission FF from yaml and understands rise-rate auto-correct at summary level without reading the spike
