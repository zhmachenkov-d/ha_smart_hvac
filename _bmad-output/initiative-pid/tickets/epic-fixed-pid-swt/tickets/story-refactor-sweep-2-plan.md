---
title: '1.8 Refactor sweep 2'
type: 'refactor'
ticket: '8'
created: '2026-11-08'
status: done
baseline_revision: '4789d7986d6ebd6e5d84a4eac8049fd2ec172d0f'
route: 'full'
route_source: 'auto'
risk: 'medium'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The epic closes with these items still open. Write 0 + clear + log is written three ways in `hvac_app.py` (retro DU1). Rounding after the clamp can command above `setpoint_max` when the bounds have more than one decimal (EC1, breaks C1). `_last_commanded` is assigned and cleared but never read (D22). A non-finite weighted error (for example, float overflow from huge weights) gives `clamp(nan)`, which silently commands `setpoint_max` (1.7 split deferral). Misspelled zone sub-keys (`weigth: 3`) are silently ignored (1.7 review deferral).

**Approach:** One idle helper serves every write-0-and-clear path. The command is snapped to the 0.1 grid inside `[setpoint_min, setpoint_max]`. `_last_commanded` is deleted. `weighted_error` returns `None` for a non-finite `e`, so the existing weights-unusable idle path takes it. Unknown zone sub-keys are reported in `ignored_keys` as `zones[<name>].<key>`.

## Boundaries & Constraints

**Always:** The log text and level of each idle path stay as they are (no-demand is INFO; no-zones and weights-unusable are WARNING). The plant-off path still makes no write and still clears state. With bounds that have one decimal or fewer, the command equals today's `round(clamp(raw), 1)`. The R7 skip, the saturation freeze, ∫ units and listeners stay unchanged. The ephemeral clear inventory becomes ∫ only.

**Never:** No new config keys. No parse-time rejection of bounds with more than one decimal. No edits to AGENTS, CONTEXT, ADR or `knowledge/` (epic 2), and none to the house `apps/apps.yaml`. Do not change Heating Demand or the plant-off semantics.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Max with 2 decimals | `setpoint_max` 55.06, raw 60 | command 55.0 (≤ 55.06) | — |
| Min with 2 decimals | `setpoint_min` 42.04, raw 30 | command 42.1 (≥ 42.04) | — |
| On-grid bounds | 40/55, raw 41.96 | 42.0 (unchanged) | — |
| No grid point in bounds | min 55.01, max 55.06 | command = clamp(raw), off grid, inside bounds | — |
| Weight overflow | two demand zones, weight 1e308 each | write 0, ∫ cleared, WARNING "Demand zone weights unusable; setpoint 0" | no `setpoint_max` command |
| Misspelled zone key | zone `living` with `weigth: 3` | `ignored_keys` holds `zones[living].weigth`; weight 1.0; one WARNING at init | — |

</frozen-after-approval>

## Design Notes

Grid snap: `c = round(clamp(raw, lo, hi), 1)`; if `c > hi`, `c = round(c - 0.1, 1)`; if `c < lo`, `c = round(c + 0.1, 1)`; if `c` is still outside `[lo, hi]`, return `clamp(raw, lo, hi)` (off-grid, inside bounds — party lock). Rounding moves the value by at most 0.05, so one step inward is enough whenever a 0.1 grid point lies inside the bounds. `round(…, 1)` avoids the float artefacts that `floor(x*10)/10` produces. The saturation freeze keeps using `raw`, not the command.

The non-finite guard lives in `weighted_error`, so `evaluate_demand` returns `None` and `_run_demand` takes the weights-unusable idle path that already exists, with no new branch.

## Code Map

- `apps/ha_smart_hvac/hvac_app.py` -- `_go_idle` (L148–151) already does write 0 + clear + WARNING log; add `level` (default `"WARNING"`). Route no-demand (L77–81) through it with INFO and weights-unusable (L118–122) with WARNING. Plant-off (L67–70) stays `_clear_pid_ephemeral` + `_hands_off` with no write. Delete write-only `_last_commanded` (init L35, clear L61, assign L130 — never read; R7 skip is plant `current == value` in `_write_setpoint` L229–230). After delete, `_clear_pid_ephemeral` clears ∫ only and stays for plant-off.
- `apps/ha_smart_hvac/pid.py` -- add `import math`. Add `def quantize_command(raw: float, lo: float, hi: float) -> float` (algorithm in Design Notes); `evaluate_demand` L95 calls it instead of `round(clamp(...), 1)`. Saturation freeze (L98–105) keeps using `raw`, not the command. In `weighted_error` (L54–62), return `None` when `not math.isfinite(e)`; update the docstring. `evaluate_demand` already returns `None` when `e is None` → existing weights-unusable idle path.
- `apps/ha_smart_hvac/config.py` -- `_ignored_keys` (L156–166) also walks each zone mapping. Known zone keys: `name`, `temperature`, `thermostats`, `weight` (what `_parse_zone` L104–127 reads). Label `zones[<name>].<key>` with `str(name)` when it is a non-empty string, else the zone index; stringify unknown keys with `str(k)` like top-level / `pid.*`. `_parse_zone` still rejects a missing/non-string name before a successful return, so happy-path labels always use the name.
- `tests/test_hvac_app.py` -- remove every `_last_commanded` set/assert (~35 lines; grep). Keep `_integral` clear asserts. Rename `test_plant_drift_rewrites_command_despite_last_commanded` / `test_plant_unavailable_equal_last_commanded_no_integral_step` to drop "last_commanded". Assert idle log levels after the `_go_idle` routing: no-demand INFO; no-zones and weights-unusable WARNING. `_expected_command` may keep `round(clamp(...), 1)` — example bounds 40/55 are on-grid, so it stays equal to `quantize_command`; do not retarget it for two-decimal bounds. Add overflowing-weight idle case (plant gets 0, never max). Add initialize WARNING case (1.7 pattern) naming `zones[living].weigth`.
- `tests/test_pid.py` -- import `quantize_command`; cover EC1 matrix rows (max 55.06, min 42.04, on-grid, no grid point) and non-finite-`e` after `test_zero_weight_sum_returns_none` (L112).
- `tests/test_config.py` -- zone-key `ignored_keys` cases near existing ignored-key tests (L115+, L359+). Example yaml still reports none.
- `docs/house-calibration.md` L87 -- unknown zone sub-keys are also named in the WARNING (same line as other ignored keys).
- `_bmad-output/initiative-pid/deferred-work.md` -- append "Resolved in 1.8 refactor sweep 2" naming the three entry-8 items (runtime non-finite `e`, overflow weight, zone typo keys); leave epic-2-owned AGENTS/ADR/CONTEXT/knowledge entries as they are. After B, every open item in the file is either Resolved or names epic 2.

## Tasks & Acceptance

**Ship order:** one story, two merges — **A then B**. Acceptance is on the final tree after both. Do not combine A and B in one diff.

**Execution — A (app hygiene):**
- [ ] `apps/ha_smart_hvac/hvac_app.py` -- give `_go_idle` a level parameter and route all three write-0 paths through it; delete `_last_commanded` -- DU1, D22
- [ ] `tests/test_hvac_app.py` -- drop every `_last_commanded` set/assert; rename the two plant tests that name it; keep `_integral` clear asserts; assert no-demand INFO and no-zones / weights-unusable WARNING -- A only

**Execution — B (law, config, docs):**
- [ ] `apps/ha_smart_hvac/pid.py` -- add `import math` and `quantize_command`; grid-snap in `evaluate_demand`; non-finite-`e` guard in `weighted_error` -- EC1 and the runtime guard
- [ ] `apps/ha_smart_hvac/config.py` -- report unknown zone sub-keys with `str(k)` -- 1.7 review deferral
- [ ] `tests/test_pid.py`, `tests/test_hvac_app.py`, `tests/test_config.py` -- matrix rows (EC1 via `quantize_command`, non-finite `e`, overflow idle, zone `ignored_keys` + initialize WARNING); example yaml still reports none -- lock behavior
- [ ] `docs/house-calibration.md`, `_bmad-output/initiative-pid/deferred-work.md` -- doc line and "Resolved in 1.8"; full-file deferred audit -- no open item left unowned

**Acceptance Criteria:**
- Given `hvac_app.py`, when it is searched for `_write_setpoint(0.0)`, then the only call is inside `_go_idle`, and `_last_commanded` does not appear in `apps/` or `tests/`.
- Given a tick with demand and weights that overflow, when it runs, then the plant receives 0 (never `setpoint_max`) and ∫ is 0.
- Given an app tick with `setpoint_max` 55.06 and a raw command above it, when the tick writes, then the written value is ≤ 55.06.
- Given args with zone `living` and `weigth: 3`, when `parse_config` runs and the App initializes, then `ignored_keys` holds `zones[living].weigth` and one WARNING names that key.
- Given `deferred-work.md`, when it is read after this story, then every open item in the file is either marked Resolved or names epic 2 as its owner.

## Implementation Notes

Ship A first (idle helper + delete `_last_commanded`); plant behavior stays today's. Ship B second (`quantize_command`, non-finite `e`, zone `ignored_keys`, docs, deferred). Overflow app-test lands in B; it does not require A (inline write 0 already idles), but Accept runs only after both merges.

## Plan Change Log

- 2026-11-08 party: keep off-grid `clamp(raw)` fallback (Never: no parse reject of >1-decimal bounds). Ship 2b — one story, A→B two merges, Accept on final. AC deferred-work → full-file audit (3b), not only 1.5–1.7. Resolved-in-1.8 names the three entry-8 bullets.
- 2026-11-08 plan review: AC + initialize WARNING for zone typo; idle log-level asserts; Verification grep for sole write-0; Code Map `import math` / `quantize_command` / `str(k)`; `_expected_command` on-grid parity note + EC1 in `test_pid`; Design Notes moved above Code Map.

## Review Triage Log

- 2026-11-08 quick: `/tmp/story-1.8-diff-yc8FRg.diff` ship order A→B — **false** — git shows two commits `8f09384` (A) then `dbd56d3` (B); the unified baseline→HEAD review diff is the review artifact, not a single merge of A+B.
- 2026-11-08 quick: `_bmad-output/party-mode/memories/installed/.memlog.md` out-of-scope — **false** — neither A nor B commit touches memlog; the dirty working-tree hunk is prior party-mode planning, not this story's change.
- 2026-11-08 quick: `_log_demand_success` `command={result.command:.1f}` vs off-grid `quantize_command` — **low** → **patch** — party-lock can write `55.03` while `.1f` logs `55.0`; caused by B's off-grid fallback; smallest fix is format the actual command value without one-decimal rounding.

## Verification

**Commands:**
- `uv run pytest` -- expected: all green
- `uv run ruff check . && uv run ruff format --check .` -- expected: clean
- `grep -rn "_last_commanded" apps tests` -- expected: no output
- `grep -n '_write_setpoint(0' apps/ha_smart_hvac/hvac_app.py` -- expected: the only match is inside `_go_idle`
- `PYTHONPATH=apps uv run python -c "import yaml; from ha_smart_hvac.config import parse_config; c=parse_config(yaml.safe_load(open('apps.yaml.example'))['hvac']); assert not c.ignored_keys, c.ignored_keys"` -- expected: no assertion error
- `PYTHONPATH=apps uv run python -c "import yaml; from ha_smart_hvac.config import parse_config; c=parse_config(yaml.safe_load(open('apps/apps.yaml'))['hvac']); assert not c.ignored_keys, c.ignored_keys"` -- expected: the house yaml still reports none (skip it if `apps/apps.yaml` is absent)

## Code Review

### 2026-11-08
**Code review complete.** 0 `decision-needed`, 3 `patch`, 0 `defer`, 14 rejected.

- [x] [Review][Patch] Infinite weight_sum with finite e bypasses weights-unusable idle [`apps/ha_smart_hvac/pid.py:72-78`]
- [x] [Review][Patch] Off-grid demand-success log format is untested [`apps/ha_smart_hvac/hvac_app.py:132`]
- [x] [Review][Patch] Multi-zone ignored_keys coverage stops at the first zone [`apps/ha_smart_hvac/config.py:169-178`]

Rejected:
- R1 low — plan checkboxes vs built: meta hygiene, rarely visible
- R2 low — party memlog in diff: process noise, not product
- R3 false — memlog vs frozen-after-approval is sequential timeline, not contradiction
- R4 low — stale triage “patch” note; code already fixed in 6e9cf00
- R6 low — min-bound 42.04 already locked in quantize_command unit tests
- R7 false — index-label path unreachable on successful parse (name always valid)
- R8 low — weight-defaults-to-1.0 doc expansion outside plan Code Map
- R9 false — EC1 docs were not in plan scope for house-calibration
- R10 false — post-append deferred-work content satisfies Resolved-or-epic-2
- R11 low — AC vs Verification grep both match the same `_write_setpoint(0.0)` site
- R12 low — overflow test fixture style; assertions already correct
- R16 low — sole write-0 uniqueness already covered by Verification grep
- R17 false — duplicate of R10; full-file ownership holds
