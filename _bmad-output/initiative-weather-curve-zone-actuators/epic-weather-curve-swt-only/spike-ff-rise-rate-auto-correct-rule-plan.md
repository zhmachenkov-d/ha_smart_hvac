---
title: 'FF rise-rate auto-correct rule (spike)'
type: 'feature'
ticket: 4
created: '2026-10-19'
status: done
baseline_revision: '134ba74c3109268c141a9d7c75f8613df86bab3e'
route: 'full'
route_source: 'auto'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 2
context:
  - '{project-root}/_bmad-output/initiative-weather-curve-zone-actuators/epic-weather-curve-swt-only/spike-ff-rise-rate-auto-correct-rule.md'
  - '{project-root}/_bmad-output/initiative-weather-curve-zone-actuators/spec-weather-curve-swt-only/spec-weather-curve-swt-only.md'
  - '{project-root}/docs/adr/0003-online-ladrc-omega-c-auto-tune.md'
  - '{project-root}/_bmad-output/initiative-weather-curve-zone-actuators/forge-weather-curve-zone-actuators/forge-weather-curve-zone-actuators.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Stories 1.3 (ADR/docs) and 1.5 (CAP-7 implementation) are blocked until the rise-rate signal, adaptation law, guards, persistence shape, and explicit non-goals for Weather Feedforward auto-correct are written down — without inventing an air→SWT tracking term.

**Approach:** Time-boxed design spike: decision note at the spike’s Decision target path (Signal / Law / Guards / Persistence / Non-goals + G1 direction smoke table), draft epic Notes Decision for Denys, stop. No runtime CAP-7 code and no offline script in this ticket.

## Boundaries & Constraints

**Always:**
- Rise-rate source = zone with largest Zone Error among zones with Heating Demand; selection feeds FF params only.
- SWT command stays `clamp(weather_feedforward)` under Plant Management + Heating Demand.
- CAP-6 commission for `base`/`slope`/`comfort_ref` stays yaml-only / no HA entities (epic Notes 2026-10-18). E2 may add yaml `weather_feedforward.auto_correct` knobs without HA entities and without changing CAP-6 success text.
- Decision concrete enough that 1.5 and 1.3 invent nothing; Denys HITL before 1.5.

**Never:**
- Critical Zone / max-error air as SWT closed-loop driver; any air term on SWT command.
- New HA entities for FF / auto-correct.
- Resurrect ωc / LADRC on water; leave formula or persistence for 1.5 to invent.

## I/O & Edge-Case Matrix

| Scenario | Expected |
|----------|----------|
| Happy path (demand, steady, full W15, \|error\|≥ε, \|e_r\|>δ, SWT write ok) | N2+G25; in-memory commit; SWT post-nudge; JSON only if write ok (2C) |
| Zone switch / selected drop (4A) / M2 non-finite / empty snapshots | Freeze; flush window + `clear_steady` + clear ephemeral/`previous`; no adapt |
| Plant-off / no demand / outdoor unavailable | Skip adapt; flush + `clear_steady` + clear ephemeral; do **not** clear/rewrite FF JSON |
| Command at setpoint_max / min (D-cmd block) | No param mutate; SWT on prior params; no JSON; relieving ok |
| Bounds no-op (Δ then clamp leaves params unchanged) | No JSON write (3A); SWT may still use unchanged params |
| Restart with valid JSON | Yaml defaults then overlay `base`/`slope`; ephemeral state empty |
| Restart missing/corrupt JSON | Yaml only; warn; do not rewrite file until next successful adapt commit |

## Decisions (from planning)

- **Persistence (B1):** `ff_auto_correct_state.json` in AppDaemon app dir; `{"base", "slope"}` (+ optional `version: 1`). Load: yaml → overlay if valid and in bounds. Missing/corrupt/OOB → yaml only, warn, no rewrite until next persist. Persist only when params actually changed **and** SWT write succeeded (2C); not on bounds-no-op (3A). No auto-reset on plant-off/outdoor-unavailable; ops delete JSON to restore commission. No HA entities.
- **Adapted parameters:** `base` and `slope`; `comfort_ref` commission-only.
- **Identifiability (I1) + gate:** One knob per tick. Let `d = |T_out − comfort_ref|`. Same-tick order: (1) if previous knob unset → **CS-base** (`base`); (2) then apply hysteresis with code constant `outdoor_gate_hysteresis_k = 2` — switch to **slope** when `d ≥ outdoor_gate_delta_k + hysteresis`; switch to **base** when `d ≤ outdoor_gate_delta_k − hysteresis`; while between, keep previous (after CS-base fill). Defaults: `outdoor_gate_delta_k = 12`. Never both knobs same tick. Example: restart + `d ≥ gate+hysteresis` → CS-base then immediately slope that tick.
- **W-skip (warm outdoor):** If `(comfort_ref − T_out) ≤ 0`, freeze **slope** nudges only — do **not** force base. When I1 has selected slope and slope is frozen this way, **skip adapt** (no base fallback). If I1 is on **base** while `T_out ≥ comfort_ref`, base nudges may still run (W-skip does not freeze base).
- **Rise-rate (W15 / R025) — 1B rolling + 1A append:** Ring buffer of up to 15 finite samples on the **same** selected zone. **Append (1A):** each non-flush demand tick with finite selected-zone temp appends one sample (even during ε/δ/W-skip/incomplete-steady freezes). Incomplete (<15) → skip adapt. When full: `T_window_start` = oldest, `T_now` = newest; `r_obs = (T_now − T_window_start) / (15 × control_interval / 3600)` hours (`control_interval` in **seconds**; default 60 s → denom 0.25 h). Physical span ~14×dt; **denom stays 15×dt**. Flush clears the buffer. `r_expected` default 0.25 °C/h.
- **N-both freezes (OR):** Skip adapt if any of: plant-off; outdoor unavailable; no Heating Demand; empty snapshots; steady below `min_steady_ticks`; incomplete W15 (<15 samples); zone-switch/4A-drop/M2/plant-off/no-demand/outdoor-unavailable/empty-snapshots flush path; `|zone_error| < ε`; `|e_r| ≤ δ`; W-skip (I1 on slope while `(comfort_ref − T_out) ≤ 0`). Near-setpoint **or** in-band rate each alone freezes. Do not compute `e_r` until W15 is full.
- **P1 scalars (code constants unless E2):** `ε = 0.3 °C`; `δ = 0.10` °C/h (magnitude; freeze when `|e_r| ≤ δ`); `min_steady_ticks = 15`; `outdoor_gate_hysteresis_k = 2`; max_rate `base ±0.1` / `slope ±0.01` per tick; bounds `base ∈ [15, 40]`, `slope ∈ [0.5, 2.5]`.
- **Steady + window lifetime:** +1 steady each demand tick with same selected zone, finite zone temp, and not on a flush path. Every `clear_steady` / flush path **also flushes** the rise-rate window **and** clears ephemeral including `previous`: zone switch, 4A drop, M2, plant-off, no demand, outdoor unavailable, empty snapshots.
- **Ephemeral (not persisted):** previous I1 knob, rise-rate window buffer, steady count, selected-zone id. Restart → all empty; then CS-base + yaml/JSON overlay for params only.
- **I1 `previous` advance (3C):** Update `previous` whenever I1 is **evaluated** on a non-flush demand tick (incl. incomplete W15, `|zone_error| < ε`, `|e_r| ≤ δ`, W-skip, D-cmd block, bounds no-op). Do **not** advance on flush paths — those clear ephemeral including `previous`.
- **Error / nudge (N2 + G25):** Define `e_r = r_obs − r_expected` (°C/h). When not frozen and `|e_r| > δ`: `u = clamp((r_expected − r_obs) / e_sat, -1, +1)` with `e_sat = 0.25` (= `−e_r / e_sat` clamped); `Δ = u × max_rate` on active knob; then clamp to bounds. Equivalent gains: `k_base = max_rate_base / e_sat = 0.40`, `k_slope = 0.040`. Decision note **copies** these symbols — no new thresholds.
- **Selection pool:** Max Zone Error only among zones with Heating Demand (`has_heating_demand` / `zone_error > 0` as today). Feeds FF params only — not SWT.
- **Signal edges (C1) + drop (4A) + M2:** **4A (primary unreadable path):** previously selected zone **absent** from this tick’s snapshots (live `_read_zones` omits `None` temps) → Z1 (flush + `clear_steady` + clear ephemeral; no adapt). Zone identity change among present demand zones → Z1. **M2:** selected zone **present** but `zone_temp` non-finite → same flush path. Do **not** invent a separate M2-on-`None`-in-snapshot path under current reads. Ties → T-hold (keep previous while still in max-error tie set among demand zones; else lexicographic `zone.name`). Empty snapshots → no-zones idle + full flush path.
- **D-cmd / commit / SWT (2B + 2C):** Same-tick: propose `Δ` → D-cmd vs **computed** pre-nudge `clamp(u_ff)` (not plant entity) — block raise@`setpoint_max`, lower@`setpoint_min`; relieving ok. If blocked: no param mutate; SWT prior params; no JSON. If allowed and post-bounds params **changed**: apply in-memory; SWT from **post-nudge** `clamp(u_ff)`; write JSON **only if** that SWT write succeeds (2C). If SWT write fails: keep in-memory params; **no** JSON write; no rollback of in-memory.
- **Bounds no-op (3A):** If after bounds clamp params are unchanged → not a successful persist commit; **no** JSON write (SWT may still run with unchanged params).
- **JSON commit timing:** Write/update `ff_auto_correct_state.json` only when params actually changed **and** SWT write succeeded (2C). No write on idle/skip/D-cmd-block/bounds-no-op/SWT-fail ticks.
- **HITL (D1):** Operator **Denys**. Implement: decision note + **draft** epic Notes line (not `accepted`); **replace** the epic Notes “Unknown: exact rise-rate…” line with a pointer that spike 4 draft Decision supersedes it (still pending accept). After Denys explicitly accepts: finalize `Decision (YYYY-MM-DD, Denys): … accepted`. Chat-only ok without Notes finalize ≠ accept for 1.5.
- **Commission (E2):** Yaml nest `weather_feedforward.auto_correct` with `outdoor_gate_delta_k`, `r_expected_c_per_h`, `near_setpoint_eps_k`, `e_sat_c_per_h` (defaults 12 / 0.25 / 0.3 / 0.25). Missing nest → defaults. All other scalars = code constants. Extends yaml surface; does not amend CAP-6 success wording or allow HA entities (epic yaml-only Decision stands).
- **Offline (G1):** Direction smoke table (4–6 rows) inside decision note only — no script/runtime prototype.

</frozen-after-approval>

## Code Map

- `apps/ha_smart_hvac/feedforward.py:8-10` / `models.py:51-54` / `config.py:44-51` — FF law + yaml parse; do not change in this spike.
- `apps.yaml.example:13-16` — example FF keys; 1.5 may document `auto_correct` nest.
- `apps/ha_smart_hvac/coordinator.py:8-15` + `models.py:32-47` — demand gate + `zone_error`; no max-error selector yet (1.5); historical `max(zones, key=zone_error)` among demand.
- `docs/adr/0003-online-ladrc-omega-c-auto-tune.md` — guard/persist *shape* only; not the CAP-7 law.
- Create: `_bmad-output/.../spike-ff-rise-rate-auto-correct-rule-decision.md`
- Update Notes: `_bmad-output/.../epic-weather-curve-swt-only.md`

## Tasks & Acceptance

**Execution:**
- [x] `_bmad-output/.../spike-ff-rise-rate-auto-correct-rule-decision.md` -- Signal / Law / Guards / Persistence / Non-goals encoding frozen Decisions + G1 smoke table -- CAP-7 contract for 1.3/1.5.
- [x] `_bmad-output/.../epic-weather-curve-swt-only.md` -- **replace** the “Unknown: exact rise-rate…” Notes line with a **draft** Decision pointer (summary, path, Denys; not `accepted`) -- supersedes Unknown; pending HITL.
- [x] HITL finalize (Denys) -- after explicit accept, set epic Notes line to `… accepted` -- unblocks 1.5; not agent-self-accept.

**Acceptance Criteria:**
- Given locked max-error Heating Demand zone rule, when the decision note is written, then Signal defines **1B+1A** rolling W15 (append rule, `r_obs`, denom), **4A**/M2/Z1/T-hold, selection pool = demand zones only, and flush paths clear ephemeral.
- Given linear FF params, when the decision note is written, then Law states I1/CS-base + hysteresis constant, **3C** `previous` advance, N2+G25, E2 yaml knobs vs code constants, and yaml+JSON overlay interaction.
- Given Plant Management / Heating Demand and SWT clamps, when the decision note is written, then Guards use N-both **OR** freezes (incl. incomplete W15) + **2B/2C** D-cmd/commit/SWT/JSON + **3A** bounds-no-op, and Non-goals forbid air→SWT tracking.
- Given restarts, when the decision note is written, then Persistence matches B1 (file, load/corrupt, commit only on changed+write-ok, no plant-off JSON clear).
- Given Denys reviews the note, when he explicitly accepts, then epic Notes carry finalized `Decision (…, Denys): … accepted` (Unknown line already replaced at draft) and 1.5 may start.

## Implementation Notes

- 2026-10-19: intent_gap loopback — human locked **W-skip** + **CS-base**; also froze window-flush-with-clear_steady, M2=`None`/non-finite, W15 hours from `control_interval`, Unknown-line replace on draft Notes.
- 2026-10-19: implement-review intent_gap — human locked **1B** rolling W15, **2B** adapt-then-command, **3C** I1 previous on evaluate, **4A** selected-zone drop ≡ Z1.
- 2026-10-19: plan review — human locked **1A** append, **2C** JSON iff SWT write ok, **3A** bounds-no-op no JSON; **patch all** P1–P9.

## Plan Change Log

- 2026-10-19 review patch: N-both OR freeze; plant-off ≠ JSON clear; HITL draft/finalize split; I1 hysteresis + full W15 + steady/commit/T-hold fallback frozen; matrix/Design Notes aligned; E2 cites epic yaml-only; trim duplicates (~token cut, Keep full plan).
- 2026-10-19 intent_gap resolve: W-skip (warm→skip adapt, no base force); CS-base cold-start; clear_steady always flushes window; M2 defined; W15 denom = 15×dt; draft Notes replaces Unknown line. KEEP: prior frozen locks (I1/P1/N2/B1/C1/D1/E2/G1) and G1 table requirement.
- 2026-10-19 pre-approve review patch: freeze `e_r = r_obs − r_expected`; CS-base then I1 same tick; ephemeral list; Task2=replace Unknown; base may nudge when warm if I1 on base; `control_interval` seconds; `k = max_rate/e_sat`. KEEP: W-skip/CS-base and all prior locks.
- 2026-10-19 intent_gap resolve (quick pass 2): **1B** rolling 15-sample buffer + denom 15×dt; **2B** propose→D-cmd on pre-nudge command→commit+JSON→SWT post-nudge (block = no mutate); **3C** advance I1 `previous` on evaluate not flush; **4A** selected zone absent from snapshots ≡ Z1. KEEP: all prior locks.
- 2026-10-19 plan review patch: **1A** append every non-flush demand tick; **2C** JSON only if SWT write ok (computed D-cmd); **3A** bounds-no-op → no JSON; P1–P9 (M2 vs 4A, empty/outdoor flush+ephemeral, incomplete W15 in N-both, δ magnitude, hysteresis const, selection pool, matrix/AC). KEEP: 1B/2B/3C/4A and prior locks.

## Review Triage Log

- 2026-10-19 quick pass 1 (resolved before re-implement):
  - high / intent_gap → **resolved W-skip** — warm+slope → skip adapt, no base force.
  - medium / intent_gap → **resolved CS-base** — unset previous → base, then I1 same tick.
  - medium / patch → **resolved** — every `clear_steady` flushes window.
  - low / patch → **resolved** — M2 = non-finite or `None`/unreadable.
  - medium / patch → **resolved** — W15 hours = 15×`control_interval`(seconds)/3600.
  - medium / patch → **resolved** — draft Notes **replaces** Unknown line.
- 2026-10-19 plan review (pre-approve): patched `e_r` definition; CS-base→I1 order; ephemeral list; Task2 replace; triage marked resolved; nits (seconds, base-ok-when-warm, k=max_rate/e_sat).
- 2026-10-19 quick pass 2 (implement review → intent_gap loopback; artifacts reverted):
  - high / intent_gap → **resolved 1B** — rolling 15-sample buffer; `T_window_start`=oldest; denom stays 15×dt.
  - high / intent_gap → **resolved 2B** — propose→D-cmd(pre-nudge)→commit+JSON→SWT(post-nudge); block = no mutate.
  - medium / intent_gap → **resolved 3C** — advance I1 `previous` on evaluate; not on flush.
  - medium / intent_gap → **resolved 4A** — selected zone missing from snapshots ≡ Z1 flush.
  - false — `.memlog.md` in diff: pre-existing party dirty tree (present at session start); not a spike Task deliverable defect.
- 2026-10-19 plan review (pre-approve after 1B/2B/3C/4A):
  - invent → **resolved 1A** — append sample each non-flush demand tick with finite selected temp.
  - invent → **resolved 2C** — D-cmd vs computed pre-nudge; JSON only if SWT write ok.
  - invent → **resolved 3A** — bounds no-op → no JSON.
  - patch → **resolved P1–P9** — M2=non-finite in snapshot; 4A=absent; empty/outdoor flush+ephemeral; incomplete W15 in N-both; δ=0.10 magnitude; hysteresis_k=2; demand-only selection; matrix/AC encode locks.
- 2026-10-19 quick pass 3 (re-implement review):
  - medium / patch → **resolved** — G1 rows 1–2 now mild (`d ≤ gate−hyst`) → base; rows 3–4 far → slope.
  - false — spike ticket Notes still list persistence open: plan forbids writing ticket files; B1 is locked in decision note (1.5 source of truth).
  - false — `.memlog.md` in diff: pre-existing party dirty tree; not a spike Task deliverable.

## Design Notes

Encode frozen Decisions only (incl. 1A/1B/2B/2C/3A/3C/4A, W-skip, CS-base, flush clears ephemeral). Structure: Signal, Law (+ G1 table), Guards, Persistence, Non-goals.

## Verification

**Manual checks:**
- Decision note at target path with required headings + G1 table.
- Epic Notes: Unknown rise-rate line replaced by draft Decision pointer; `accepted` only after Denys HITL.
- No Python CAP-7 / offline script in this spike.
