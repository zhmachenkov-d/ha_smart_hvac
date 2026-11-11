<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent
**Problem:** Live demand SWT still follows fixed PID (`base_water_temp + u_pid`), not the outdoor weather curve, while Plant Management / Heating Demand gates are on. Outdoor and Weather Feedforward are gone from config, listeners, and `apps.yaml.example`.

**Approach:** Restore demand SWT as `command = quantize_command(u_ff, setpoint_min, setpoint_max)` with `u_ff = base + slope × (comfort_ref − T_out)` from yaml Weather Feedforward and Outdoor Temperature; re-register Outdoor as a control listener; commission `outdoor_temperature` + `weather_feedforward` in `apps.yaml.example`. Leave `pid.py` / `rls.py` on disk (unwired on the demand path) for entry 2; no CAP-7 / `ff_auto_correct_state.json`; no docs/ADR rewrite (epic 3).

**Sequencing gloss:** *entry 1* = this story; *entry 2/3* = later stories in this epic (PID/RLS strip, house HITL); *epic 3* = docs/ADR/AGENTS rewrite initiative track. Until epic 3, **this plan overrides** AGENTS.md / CONTEXT.md demand-law bullets that still describe PID SWT, Outdoor-not-in-listeners, or sticky `_gated_demand`.

**Demand write contract (CAP-8):**
- Tick and event share one FF demand writer; delete sticky `_gated_demand` and rising-edge-only `_run_demand_edge`.
- `control_event` → `_gate_prelude` → same `_run_demand(zones, outdoor)` whenever prelude returns demand (Outdoor, zone air, setpoint, `hvac_action` — not rising-edge only).
- Equal-float skip remains the write throttle. Initialize still runs one full tick after schedule.

## Boundaries & Constraints
**Always:**
- Demand law: `command = quantize_command(u_ff, setpoint_min, setpoint_max)` where `u_ff = base + slope × (comfort_ref − T_out)`; reuse `quantize_command` from `pid.py` (clamp then 0.1 °C grid). Entry 2 must move or re-export `quantize_command` before deleting `pid.py`.
- Weather Feedforward: require non-empty `outdoor_temperature` entity id and a `weather_feedforward` mapping. Omitted numeric keys default `base=37`, `slope=0.9`, `comfort_ref=20`. After coerce, each of `base`/`slope`/`comfort_ref` must be `math.isfinite` or `ConfigError`. Whitelist FF subkeys to `base` / `slope` / `comfort_ref` only — unknown keys (incl. `auto_correct`) → `ConfigError`. Negative `slope` is allowed (commissioning choice).
- **Config break accepted:** requiring Outdoor + FF is a breaking parse vs today’s house `apps/apps.yaml`. Post-merge Production AppDaemon fails `ConfigError` until entry 3 HITL commissions those keys (do not edit house entity IDs in this story).
- Gates unchanged in meaning: plant-off → no SWT write + clear ephemeral water-path state (PID ∫ / `y_prev` until entry 2/4; `_clear_pid_ephemeral`); plant-on, no Heating Demand → write `0` + clear ephemeral water-path state; Heating Demand = thermostat `hvac_action == "heating"`.
- **Prelude order (match `b862db4`):** (1) plant-off → clear ephemeral + `_hands_off`, return `None` — **no** Outdoor read, **no** SWT write; (2) read Outdoor — if unavailable/non-finite → clear ephemeral + `_go_idle` (write `0`, WARN with entity id), return `None`; (3) zones — if none valid → clear + `_go_idle`; (4) no Heating Demand → clear + write `0` (idle INFO); (5) else return `(zones, outdoor)`.
- Unavailable / non-finite Outdoor under plant-on: clear ephemeral water-path state and `_go_idle` (write `0`; no curve command) — pre-PID weather prelude, **not** plant-unreadable skip. If `_go_idle`’s write is skipped because plant is unreadable, still clear ephemeral and WARN; SWT may remain at prior value (same R7 write-skip reality).
- If computed `u_ff` is non-finite under demand: clear ephemeral + `_go_idle`; do not call `quantize_command` / HA with non-finite.
- Outdoor is among `listen_state` control listeners with plant / zone air / thermostat `hvac_action` / setpoint.
- On demand, tick and event both run the same FF writer (see Intent CAP-8). Under held demand, zone air / setpoint / `hvac_action` events also refresh `quantize_command(u_ff, …)` (or equal-float skip) — not Outdoor-only.
- Under plant-on + Heating Demand + finite Outdoor, weights-unusable / non-finite weighted error must **not** force idle `0`; command stays Outdoor FF only. Prelude still needs valid zones for Heating Demand detection; no-valid-zones → idle `0`. Critical Zone (`select_max_error_demand_zone`) stays diagnostics / log only.
- R1 supply rise-rate latch: in **this story**, treat latch as always clear on demand writes (FF authoritative). Epic 2 owns persistent latch later; entry 1 does not add latch hooks.
- Demand success log (replace PID `_log_demand_success` / `PidResult` shape): `outdoor=`, `u_ff=`, `command=`, optional `critical_zone=`; no `u_pid=` / `e=` driving the command. Plant-unreadable skip: WARN only — no demand-success log; do not clear FF inputs; no ∫ / no RLS.
- `pid.adaptive` / `rls_state.json`: overlay stays inert on the FF demand path (no step/persist; `_rls.last_u` frozen across FF writes — update only if a future path re-wires RLS; ephemeral clears do not invent new last_u semantics beyond existing clear helpers). Do not expand adaptive coverage in this story.
- Stay inside AppDaemon `ha_smart_hvac` writing existing `plant_setpoint`.
- Example rails (OQ1-A): keep `apps.yaml.example` `setpoint_min: 50` / `setpoint_max: 60`; short comment that mild Outdoor may pin to min (defaults `base=37`/`slope=0.9`/`comfort_ref=20`, e.g. ~10 °C → `u_ff`≈46) until entry 3 house HITL — so operators do not read pinned 50 as “curve dead”.

**Never:**
- Restore CAP-7, `ff_auto_correct`, or `ff_auto_correct_state.json`.
- Delete `pid.py` / `rls.py` or strip `pid` / `base_water_temp` from example commissioning (entry 2); do not advance ∫ or step/persist RLS on the demand path in this story.
- Change Exclusive Session (ADR 0001), Heating Demand definition, or house `apps/apps.yaml` entity IDs (entry 3 HITL).
- Rewrite AGENTS.md / CONTEXT.md / ADR 0005–0006 / `knowledge/` (epic 3) — except live override noted in Intent until then.
- Drive SWT from Critical Zone or zone air error (no weighted-error gate on the FF demand write).

‡ **Rationale (party locks A/A/A):** Outdoor miss → `_go_idle` write `0` (not R7 skip); tests surgically forbid ∫/RLS-on-demand (drop unreachable blocks — no “leave compiling”); example rails stay 50/60 with pin comment. CAP-8 needs the latch gone so mid-demand events refresh SWT. `quantize_command` stays in `pid.py` only as interim before entry 2 relocation.

## Behavior & acceptance
| Scenario | Preconditions | Expected behavior | Test pointer |
| --- | --- | --- | --- |
| Happy demand tick/event | Plant on + Heating Demand + finite Outdoor | Write `quantize_command(u_ff, min, max)`; log `outdoor=`, `u_ff=`, `command=`; Critical Zone log-only; no ∫ / no RLS | `test_hvac_app` demand |
| Outdoor refresh under demand | Outdoor listener; still demand | Re-write new command or equal-float skip | event Outdoor |
| Other control event under held demand | Zone air / setpoint / `hvac_action`; still demand | Same FF writer (or equal-float skip) | event non-Outdoor |
| Weights-unusable under demand | Plant on + demand + finite Outdoor; weights bad | Still `quantize_command(u_ff, …)` — **not** idle `0` | demand weights |
| Plant on, no Heating Demand | Plant on; no heating | Write `0` + clear ephemeral water-path state | idle |
| Plant-off | Plant Management off | No SWT write + clear ephemeral; **no** Outdoor read; outdoor unavailable must not `_go_idle` | plant-off (+ outdoor miss) |
| Missing/invalid Outdoor | Plant on; Outdoor unavailable / non-finite | `_go_idle`: write `0` + clear; WARN entity id; no curve | outdoor-miss |
| Outdoor miss + plant unreadable | As outdoor-miss; plant NaN/unavailable | Clear ephemeral; write skipped (R7); WARN; no success log | outdoor-miss ∩ R7 |
| No valid zones | All zone temps bad | Write `0` + clear | existing |
| Plant unreadable on demand | Finite Outdoor; plant NaN/unavailable | Skip write; no clear of FF inputs; no ∫; no success log | plant-unreadable |
| Non-finite `u_ff` | Demand + outdoor finite; FF yields non-finite | Clear + `_go_idle`; no quantize/HA non-finite | u_ff guard |
| Critical Zone only | Multiple demand zones | Command from Outdoor FF only; `critical_zone=` in log | CZ log |
| Init under demand | Successful `initialize` | One full tick; FF write if gated | init tick |
| Init outdoor unavailable | Init tick; plant on; Outdoor bad | `_go_idle` `0`+clear; no FF write | init outdoor-miss |
| Example yaml | Parse `apps.yaml.example` | Outdoor + FF present (defaults); rails 50/60; pin comment; no CAP-7/`auto_correct`; `pid` nest may remain | `test_config` |
| FF parse validation | Bad/non-finite FF numerics or unknown FF subkeys | `ConfigError` | `test_config` |
| Modules on disk | After story | `pid.py`/`rls.py` may exist; demand does not advance ∫ or step/persist RLS (explicit negative); unreachable RLS-on-demand tests removed/rewritten | negative ∫/RLS |
| Adaptive inert | `pid.adaptive` true possible | No RLS step/persist on FF demand; `last_u` frozen across FF writes | no adaptive expand |

</frozen-after-approval>

## Code Map
Build order (historical weather refs: `a10c00d` / `b862db4`; removal `a305049` — do not revive CAP-7):

1. `apps/ha_smart_hvac/feedforward.py` — **add** `weather_feedforward(outdoor_temp, config) -> float` (linear law; no CAP-7).
2. `apps/ha_smart_hvac/models.py` — restore `WeatherFeedforwardConfig`; add `outdoor_temperature` + `weather_feedforward` on `HvacConfig`; keep `pid` / `base_water_temp` (entry 2).
3. `apps/ha_smart_hvac/config.py` — require Outdoor + FF mapping; defaults 37/0.9/20; finite + whitelist subkeys; stop ignoring outdoor/FF as legacy; keep pid parse (entry 2).
4. `apps/ha_smart_hvac/hvac_app.py` —
   - Listeners: Outdoor again among control listeners.
   - Prelude: order in Boundaries; Outdoor fail → `_go_idle`.
   - Demand: shared `_run_demand(zones, outdoor)` for tick **and** every eligible `control_event`; `quantize_command(u_ff, …)` + FF success log; delete `_gated_demand` / `_run_demand_edge`.
   - Stop `evaluate_demand` / `_gains_for_demand` / `_maybe_rls_step` / `_maybe_persist_rls` on demand; keep `_clear_pid_ephemeral` until entry 2/4.
5. `apps/ha_smart_hvac/pid.py` — leave; export `quantize_command` for demand (interim).
6. `apps/ha_smart_hvac/rls.py` — leave unwired on demand.
7. `apps/ha_smart_hvac/coordinator.py` — unchanged Heating Demand / Critical Zone helpers.
8. `apps.yaml.example` — Outdoor + `weather_feedforward` defaults; rails 50/60 + pin comment; no CAP-7; keep `pid` nest.
9. Tests — see Execution (formula, parse, gates, assert pairs, negatives).

## Tasks & Acceptance
**Execution:**
- [ ] `models.py` + `feedforward.py` + `config.py` — FF model/law; required Outdoor+FF; finite + whitelist; drop ignored-legacy outdoor/FF.
- [ ] `hvac_app.py` — prelude order; Outdoor listener; shared FF demand writer (drop latch/edge); FF log contract; stop PID/RLS on demand; CZ log-only; non-finite `u_ff` → `_go_idle`.
- [ ] `apps.yaml.example` — Outdoor + FF; rails 50/60 + mild-pin comment; no CAP-7; keep pid nest.
- [ ] `tests/test_feedforward.py` + `test_config.py` + `test_hvac_app.py` — cover Behavior & acceptance rows; update **all** shared fixtures (`_tick_args` / `_init_app` / parse stubs) with valid outdoor+FF; retire PID-demand / outdoor-ignored / unreachable RLS-on-demand; explicit negative ∫/RLS; Outdoor-miss vs plant-unreadable assert pair; plant-off+outdoor-miss no write; held-demand non-Outdoor event refresh; weights-unusable does not force `0`.

**Verification:**
- `uv run pytest` — all pass (Behavior table + negatives).
- `uv run ruff check apps/ha_smart_hvac tests` — clean.
- Manual (Exclusive Session): Plant on + Heating Demand — SWT tracks Outdoor-driven `quantize_command(u_ff, …)` when `u_ff` is inside rails (cold enough not pinned); mild Outdoor may stay at min 50 (OQ1-A). Idle → `0`. Plant-off → App does not write SWT.

Resolved forks (audit): Outdoor-fail A · zombie-PID/tests A · rails OQ1-A · review apply-all 2026-11-11.

**Status:** 2026-11-11 human Approve → `ready-for-dev` (party locks + review apply-all frozen). Risk high → implement with `review: auto`/`thorough` (not `quick`).

## Review Triage Log
| Lens | Finding | Verdict | Evidence / route |
| --- | --- | --- | --- |
| blind-hunter | Dead `_gains_for_demand` / `_maybe_rls_*` helpers remain in `hvac_app.py` | false | Intent/plan leave pid/rls on disk until entry 2; Code Map says stop calling on demand, not delete helpers. |
| blind-hunter | Adaptive force-rewrite / scrub coverage thinned | false | Remaining tests still cover load/force paths (`test_force_rewrite_stays_set_ff_demand_does_not_persist`, corrupt/IMC init cases). Demand path correctly does not persist. |
| blind-hunter | Happy-path log omits assert on `critical_zone=` | false | Log contract marks `critical_zone=` optional; `test_critical_zone_does_not_change_swt` asserts `critical_zone=zone_two` in INFO. |
| blind-hunter | No setpoint / `hvac_action` attribute-event refresh tests | false | `control_event` ignores listener args and re-reads state; zone-air held-demand refresh already exercises the shared writer. Attribute listeners remain registered in `initialize`. |
| blind-hunter | Mild Outdoor pin (rails 50/60, ~10 °C → command 50) untested | high | Same root as verification-gap: fixtures use 40/55 with in-band `u_ff`; skipping `quantize_command` would still pass. → patch (group: demand rail clamp). |
| blind-hunter | `apps.yaml.example` still presents `base_water_temp`/PID as commission | false | Plan Always/Never: keep `pid` nest and `base_water_temp` until entry 2. |
| blind-hunter | Execution tasks still `[ ]` while status `in-review` | false | Rejected: fix would edit this build's plan task checkboxes. |
| blind-hunter | Body Status footer still says `ready-for-dev` | false | Rejected: fix would edit plan body Status line (frontmatter is source of truth for workflow). |
| blind-hunter | No interim AGENTS.md / CONTEXT.md pointer | false | Intent Never/R5: no docs rewrite until epic 3; override is process gloss only. |
| blind-hunter | No config test for non-mapping `weather_feedforward` | low | Branch `weather_feedforward must be a mapping` exists; uncovered. → patch. |
| blind-hunter | No config test for non-string `outdoor_temperature` | low | Non-empty str guard exists; int/bool uncovered. → patch. |
| blind-hunter | Party `.memlog.md` bundled with code | false | Party-mode process artifact from approve; not a product defect. |
| blind-hunter | `test_feedforward` misses outdoor 10 → 46 pin arithmetic | high | Carried into demand rail-clamp patch group (same missing pin lock). |
| blind-hunter | `tickets.toml` notes still say ready-for-dev | false | Board notes lag is non-blocking; not a code defect for this change. |
| edge-case-hunter | (no findings) | — | Empty report `[]`. |
| verification-gap | Demand path never asserts FF rail clamp / grid when `u_ff` outside rails | high | Pre-verified gap: all demand outdoors yield in-band `u_ff` under fixture 40/55; deleting `quantize_command` would stay green. → patch (group: demand rail clamp). |
| intent-alignment | Diff implements R1+R2+R3 (+R4 plan locks); R5 docs deferred by omission | false | Descriptive audit — aligns with Intent; no defect. |
| intent-alignment | Equal-float skip also logs success / freezes `last_u` beyond throttle wording | false | Behavior retained from prior write path; plan success log still applies when write returns True on equal-float. |
| intent-alignment | Planning surfaces (plan/tickets/memlog) change outside pasted Intent | false | Expected build workflow artifacts; not a product divergence. |

## Code Review
### 2026-11-11
**Code review complete.** 0 `decision-needed`, 6 `patch`, 0 `defer`, 14 rejected.

- [x] [Review][Patch] Adaptive FF demand “no RLS step” asserted only via mock hooks [tests/test_hvac_app.py:1234]
- [x] [Review][Patch] Stale PID/latch language left in FF-era demand tests [tests/test_hvac_app.py:609]
- [x] [Review][Patch] Breaking Outdoor+FF ConfigError lacks operator-facing CHANGELOG note [CHANGELOG.md]
- [x] [Review][Patch] Example yaml header still frames pid/base_water_temp as live C4 commission [apps.yaml.example:5]
- [x] [Review][Patch] Live FF demand writer has no max-rail clamp assertion [tests/test_hvac_app.py]
- [x] [Review][Patch] Orphaned RLS test helpers after demand-path strip [tests/test_hvac_app.py:27]

#### Rejected
- R1 AGENTS/CONTEXT still PID law — false: epic 3 / Intent Never deferral
- R2 CONTEXT avoid-list vs restored FF — false: same docs deferral as R1
- R5 Outdoor before Heating Demand WARN on idle — false: plan prelude order b862db4
- R6 Equal-float still INFO-logs success — false: intentional write throttle; test locks it
- R8 Fixtures 40/55 miss example rails — false: dedicated mild-Outdoor pin test locks clamp
- R9 No setpoint/hvac_action attribute-event tests — false: control_event ignores args; zone-air covers shared writer
- R10 RLS suites deleted / helpers remain — false: plan leaves unwired until entry 2
- R11 last_u frozen vs plant under FF — false: plan Always freezes last_u
- R12 Plan hygiene Execution/Status lag — false: would edit plan; frontmatter is SoT
- R13 Party .memlog in changeset — false: process artifact
- R19 Live HA not in diff — false: operator verify surface; CI is unit tests
- R20 Epic R1 latch / R7 supply not in tracer — false: deferred to epic 2 by design
- R21 Leftover PID helpers (intent note) — false: same interim as R10
- R22 Attribute-event proxy coverage (intent note) — false: same as R9