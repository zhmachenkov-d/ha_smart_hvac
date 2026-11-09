---
title: 'Persist RLS state JSON across PID clears'
type: 'feature'
ticket: '3'
created: '2026-11-09'
status: done
baseline_revision: '6c8e2404ee3aae7704beb17cc922de1c5cf6388c'
route: 'full'
route_source: 'auto'
risk: 'medium'
review: 'quick'
review_source: 'pinned'
lenses_ran:
  - quick
review_loop_iteration: 1
context:
  - _bmad-output/initiative-pid/tickets/epic-rls-pid-retune/rls-adaptive-algorithm.md
  - docs/adr/0005-fixed-pid-swt.md
  - docs/adr/0004-weather-curve-swt.md
---

<!-- Read order: 1 Intent → 2 Implementation map → 3 Matrix → 4 Boundaries (reference) → 5 Decision index -->

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Reloading the App loses the learned RLS model (θ, P, and related durable fields) because entries 1–2 keep that state in memory only. Story R2 adds `rls_state.json` on disk. Idle, plant-off, and other ephemeral clear paths must not delete or rewrite that file.

**Approach:** Persist `theta`, `p`, `last_u`, `adapted_kp`, and `adapted_ki` to `rls_state.json` under `self.app_dir` (same artifact pattern as the removed `ff_auto_correct_state.json`; historical FF persistence prose lives in ADR 0004, live SWT law is ADR 0005). When adaptive is on: load on `initialize` if the file is valid; save after a successful demand `_write_setpoint` only when the durable snapshot differs from the last successful save (in-memory `_last_saved`) or a disk-rewrite force flag is set. Ephemeral clears (`_clear_pid_ephemeral`, idle via `_go_idle`, plant-off clear-only) never touch the file or the fallback latch (entry 2). The latch stays in memory only; every `initialize` sets latch to False. ADR/CONTEXT/AGENTS updates for RLS stay in entry 4.

## Boundaries & Constraints

**Always:**
- **File / payload.** `rls_state.json` under AppDaemon `app_dir`. Max size before parse: **64 KiB**; larger → whole-file reject. Payload: `version` (int `1` only), `theta` (len-2), `p` (2×2), `last_u` (finite float or JSON `null`), `adapted_kp` / `adapted_ki` (both finite floats or both JSON `null`). Coerce JSON numbers with `float()` (ints OK). Required keys include `last_u` (null allowed); missing `last_u` → whole-file reject. Unknown keys ignored. `version` missing, non-int, or ≠ `1` → whole-file reject.
- **Load (adaptive on only).** After config parse and fresh `RlsState()` / latch=False. Missing file → silent cold defaults; seed `_last_saved` from a **deep copy** of durable fields; no force flag. Read/`OSError`, corrupt JSON, wrong shape, non-finite θ/P/`last_u` (when non-null), bad version, oversize, or θ that makes `imc_gains(theta[0], theta[1], control_interval)` return `None` → WARNING + cold defaults; set **disk-rewrite force** so the next successful demand write replaces the bad/ignored file; seed `_last_saved` from cold deep copy. Operator delete of the file = reset to cold defaults on next adaptive-on initialize.
- **Partial adapted drop (OQ6 B).** After a structurally valid load: if `adapted_*` missing, non-finite, mismatched nullness, or outside inclusive rails (`gains_within_rails` in the App — no rails args on `load_rls_state`) → both adapted `None`; do **not** set the fallback latch on load; log **one WARNING** with a reason token (`missing` | `non_finite` | `mismatch` | `out_of_rail`); overlay θ/P/`last_u`; set **disk-rewrite force** so the next successful demand write scrubs on-disk adapted; seed `_last_saved` from post-drop deep copy.
- **Valid load INFO.** When a valid file overlays successfully (including after adapted drop), log one INFO that `rls_state.json` was loaded (covers adaptive off→on re-enable of a lingering file).
- **Persist gate.** Adaptive on; demand `_write_setpoint` returns True (including equal-float skip); and (field snapshot ≠ last successful save **or** disk-rewrite force). Field-level dirty (not FF per-tick `params_changed`). Update `_last_saved` (deep copy) and clear force only after `save_rls_state` returns True. Soft-fail: retry every dirty/forced demand tick; WARNING **once per fail episode** (first fail, silent while still failing, re-WARN after a successful save then a later fail). Tick continues after SWT already succeeded. Demand write True after reject (θ/P may have updated; adapted may be null/parked) still persists when dirty/forced.
- **Accepted loss (OQ3 unchanged).** No persist when `_write_setpoint` returns False after an RLS step; no shutdown/terminate persist. Dirty RAM may be lost on reload until a later successful demand write — accepted.
- **Dirty compare.** Logical fields only: deep-copied `theta`, `p`, `last_u`, `adapted_kp`, `adapted_ki`. Never via file bytes/JSON text; never share list references with `RlsState`; no quantize-on-save.
- **Clears.** Idle (`_go_idle`), plant-off (clear-only in `_gate_prelude`), no-valid-zones, weights-unusable: never read/write/delete the JSON; never change latch (entry 2). ∫ / `y_prev` clear rules unchanged.
- **Latch.** Never on disk. Every `initialize` → latch False (reload after a latched episode restores adapted from JSON if valid — **accepted**; latch is process-local health, not durable). `y_prev` never from JSON.
- **Helpers.** Pure `load_rls_state` / `save_rls_state` (Path in). Save: UTF-8 text, atomic `*.tmp` + `os.replace`, no fsync required (mirror removed FF). On save `OSError`: best-effort tmp unlink → False; if unlink fails, log WARNING that tmp may remain. `save_rls_state` returns False (no write) if in-memory durable fields are non-finite or adapted nullness is mismatched. Adaptive off: neither load nor save; lingering file unused.
- Tick-only RLS step, demand SWT law, rails/unhealthy latch, Weather/FF absence, and Exclusive Session stay unchanged.

**Never:**
- Persisting the fallback latch, `_integral`, or `y_prev`.
- Deleting or rewriting the JSON on clear paths; changing latch on those paths from this story.
- Loading or saving RLS JSON while adaptive is off.
- Restoring outdoor temperature or feedforward state, or editing ADR/CONTEXT/AGENTS for RLS (entry 4).
- Numpy / external RLS process.
- Dirty compare via file bytes; quantize-on-save; sharing mutable θ/P lists between `_last_saved` and `RlsState`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Adaptive on, durable fields change, demand write OK | Snapshot ≠ last successful save | Atomic rewrite; `_last_saved` deep-copy updated; force cleared | Soft-fail: episode WARNING; `_last_saved`/force unchanged |
| Adaptive on, same snapshot, no force, write OK | Snapshot == `_last_saved` | No save / file unchanged | N/A |
| Adaptive on, force set, same snapshot, write OK | Disk-rewrite force after bad/partial load | Persist current RAM snapshot; clear force | Soft-fail as above |
| Adaptive on, write True after reject | θ/P updated; adapted parked/null | Persist when dirty/forced | Soft-fail as above |
| Adaptive on, RLS stepped, write False | Plant unreadable / write fails | No persist; RAM keeps θ/P | Accepted loss until later write True |
| Persist I/O fail while dirty/forced | Soft OSError | Retry each demand tick; WARNING once per fail episode | Prior file may remain; tmp best-effort unlink |
| Save OSError; tmp created | tmp exists | `save_rls_state` False; tmp absent if unlink OK | If unlink fails: WARNING tmp may remain |
| Save with non-finite or mismatched adapted in RAM | Invalid durable snapshot | `save_rls_state` False; no file write | N/A |
| Idle (`_go_idle`) | Clear ∫ + `y_prev`; may write SWT 0 | File unchanged; latch unchanged | N/A |
| Plant-off | Clear ∫ + `y_prev` only; no SWT write | File unchanged; latch unchanged | N/A |
| No-zones / weights-unusable | Clear path as today | File unchanged; latch unchanged | N/A |
| Initialize after latched episode, valid JSON | Was latched pre-restart | Overlay durable fields; latch False; seed `_last_saved`; adapted may return | Accepted (latch not durable) |
| Initialize, valid JSON, adaptive on | Cold start | Overlay; latch False; `y_prev` None; INFO loaded; seed deep-copy `_last_saved` | Adapted drop → reason WARNING + force |
| Initialize, missing JSON | Cold start | Defaults; seed `_last_saved`; no required WARNING | N/A |
| Initialize, corrupt / OSError / oversize / bad version / IMC-invalid θ | File unusable | Cold defaults; WARNING; force set; seed cold `_last_saved` | Next write True rewrites file |
| Initialize, v1 + unknown keys | Otherwise valid | Overlay known fields; extras ignored; INFO loaded | N/A |
| Adaptive off | Initialize / demand | No load; no save; file untouched | N/A |
| Adaptive off→on later | Lingering file valid | Load as adaptive-on initialize (INFO) | N/A |
| Operator deletes `rls_state.json` | Next adaptive-on initialize | Cold defaults | N/A |
| Dirty RAM; App stop before next demand write True | Reload | Last successful file (or cold) loads; unsaved dirty lost | Accepted loss |

## Decision index (2026-11-09)

| ID | Rule |
|----|------|
| OQ1 **B** | Persist `theta`, `p`, `last_u`, `adapted_kp`, `adapted_ki`. |
| OQ2 **A** | Filename `rls_state.json`. |
| OQ3 **A** | Save only after successful demand write when dirty/forced; write False / shutdown = accepted loss. |
| OQ4 **A** | Missing → silent cold; corrupt/unreadable → WARNING + cold; operator delete resets. |
| OQ5 **A** | Adaptive off: neither load nor save. |
| OQ6 **B** | Partial adapted drop on load; no latch on load; reason WARNING + force rewrite. |
| Fork 1 **B→W1** | Level-dirty vs last successful save; retry each tick; WARNING once per fail episode (review renegotiated repeat-WARN). |
| Fork 2 **C** | Reload → latch False; clears never touch file or latch. |
| Fork 3 **C** | Field dirty-spec; deep-copy seed; no-rewrite when equal and not forced. |
| Fork 4 **A** | Reuse `gains_within_rails` in App after load. |
| **A2** | No quantize; dirty never via file bytes; save→`load_rls_state` field equality test. |
| **B2** | One adapted-drop WARNING with reason token. |
| **D1** | `version` int `1` or whole-file reject; unknown keys ignored. |
| **F3** | Best-effort tmp unlink; AC: tmp absent or unlink-failure WARNING. |
| Review | 64 KiB cap; IMC-invalid θ reject; force rewrite after bad/partial load; UTF-8 no fsync; plant-off row split; latch-restore accepted; ADR 0005 context + 0004 historical. |

</frozen-after-approval>

## Implementation map

**`apps/ha_smart_hvac/rls.py`**
- [x] `STATE_FILENAME = "rls_state.json"`.
- [x] `load_rls_state(path)`: reject oversize; parse UTF-8 JSON; require `version is int and == 1`; coerce numbers with `float()`; require `last_u` key (null OK); finite θ/P/`last_u`; adapted null-pair or both finite; ignore unknown keys; return structured result or `None`.
- [x] `save_rls_state(path, state) -> bool`: reject non-finite / mismatched adapted; UTF-8 `*.tmp` + `os.replace`; on `OSError` best-effort unlink (WARNING if unlink fails) → False. No fsync. Keep `rls_step` / IMC / `gains_within_rails` unchanged.

**`apps/ha_smart_hvac/hvac_app.py`**
- [x] `_state_path()`; adaptive-on load after `_rls = RlsState()`; IMC check with `control_interval`; OQ6 B via `gains_within_rails` + reason WARNING; INFO on successful load; deep-copy `_last_saved`; disk-rewrite force as locked; persist after write True when dirty or forced; clears never touch file/latch; latch never loaded/saved.

**Durable snapshot helper**
- [x] Deep-copy + `==` on `theta`, `p`, `last_u`, `adapted_kp`, `adapted_ki` only.

**`apps.yaml.example` + `docs/house-calibration.md`**
- [x] Ops: with adaptive enabled, delete `rls_state.json` under the AppDaemon app directory to reset learned RLS state. Do not disable `adaptive` to reset.

**Tests**
- [x] `tests/test_rls.py` — save→load field equality via helpers; corrupt/oversize/bad version→None; extras ignored; int coerce; missing `last_u`→None; OSError→False; tmp absent or unlink-failure path; save rejects non-finite / mismatched adapted.
- [x] `tests/test_hvac_app.py` — restore after persist; no rewrite when equal; force rewrite after corrupt/adapted-drop; idle vs plant-off leave file+latch; adaptive off no I/O; adapted-drop reason WARNING; soft-fail episode WARNING; write False after RLS → no persist; IMC-invalid file → cold + force.

## Design Notes

- Persist gate is field-level dirty vs deep-copied last successful save (plus force), not FF per-tick `params_changed`. Soft-fail WARNING is once per fail episode while retries continue.
- Latch is process-local: reload clears it even when adapted reload from JSON — accepted; do not persist latch.

## Acceptance Criteria

- Given adaptive on and a demand tick that changes durable fields, when `_write_setpoint` succeeds, then `rls_state.json` matches the in-memory durable snapshot and `_last_saved` updates (force cleared).
- Given equal durable snapshot and no force, when demand write succeeds, then save is not invoked / file unchanged.
- Given disk-rewrite force after bad or partial load, when demand write succeeds, then the file is rewritten to the current RAM snapshot even if fields match `_last_saved`.
- Given initialize with adaptive on and a valid file, then durable fields overlay (adapted may drop with one reason WARNING + force), latch is False, `y_prev` is None, INFO notes load, and `_last_saved` is a deep copy so an unchanged non-forced demand tick does not rewrite.
- Given initialize with missing file, then cold defaults and no required WARNING.
- Given initialize with unusable file (corrupt, read OSError, oversize, bad version, IMC-invalid θ), then WARNING, cold defaults, and force set.
- Given valid v1 JSON with unknown keys, then known fields overlay and extras are ignored.
- Given idle (`_go_idle`) or plant-off clear, then the file is not deleted or rewritten, latch is unchanged, and ∫ / `y_prev` clear as today.
- Given `pid.adaptive` false, then neither load nor save runs.
- Given save I/O failure after SWT write True, then an episode WARNING is logged, the tick does not abort, `_last_saved`/force unchanged, and tmp is absent or an unlink-failure WARNING was logged.
- Given `_write_setpoint` False after an RLS step, then no persist runs (accepted loss).
- Given `uv run pytest` and `uv run ruff check`, then both succeed.

## Plan Change Log

- 2026-11-09 party: forks 1B/2C/3C/4A + A2/B2/D1/F3.
- 2026-11-09 review patch-all: force rewrite after bad/partial load; IMC-invalid reject; 64 KiB cap; load OSError=corrupt; int coerce; required `last_u`; save validates finite/adapted pair; deep-copy dirty; W1 soft-fail WARNING; accepted write-False/shutdown loss; plant-off row split; latch-restore accepted; adapted-drop reason token; UTF-8 no fsync; F3 unlink-fail WARNING; ops note; ADR 0005 context; Intent/Decision index/Implementation map prose+structure.

## Review Triage Log

- 2026-11-09 · loop 1 · lenses adversarial, edge-case-hunter, structure, prose · **patch-all** applied into plan (this revision). Structure MOVE/MERGE/CUT absorbed into Read order + Implementation map + Decision index; empty Implementation Notes / Verification headings removed.
- 2026-11-09 · code review quick · `_load_rls_overlay` IMC gate vs persist-after-reject · verdict `false` · route reject · evidence: frozen load rule requires IMC-invalid θ → WARNING + cold + force; persist-after-reject intentionally can write that θ, and the next initialize is the IMC-invalid matrix row — App-authored cold/reject θ failing reload is specified, not a deviation.
- 2026-11-09 · code review quick · `load_rls_state` 64 KiB after full `read_bytes` · verdict `low` · route patch · **resolved** — `stat().st_size` before `read_bytes`; residual stat→read TOCTOU closed with post-read `len(data)` check in the 2026-11-09 code-review patch pass.

## Code Review

### 2026-11-09

**Code review complete.** 0 `decision-needed`, 11 `patch`, 0 `defer`, 14 rejected.

- [x] [Review][Patch] float() OverflowError on huge JSON ints aborts load/initialize [`apps/ha_smart_hvac/rls.py:139`]
- [x] [Review][Patch] Soft-fail path untested for last_saved/force retention under force rewrite [`tests/test_hvac_app.py:2086`]
- [x] [Review][Patch] Non-finite last_u rejection untested in load and save [`tests/test_rls.py:195`]
- [x] [Review][Patch] Adapted-drop disk scrub write not exercised after force [`tests/test_hvac_app.py:1827`]
- [x] [Review][Patch] JSON bools coerced into numeric durable fields [`apps/ha_smart_hvac/rls.py:136`]
- [x] [Review][Patch] Latched-restore test never places the app in a latched episode [`tests/test_hvac_app.py:2171`]
- [x] [Review][Patch] 64 KiB cap has stat→read TOCTOU residual [`apps/ha_smart_hvac/rls.py:176`]
- [x] [Review][Patch] Missing-file race after is_file warns and force-rewrites [`apps/ha_smart_hvac/hvac_app.py:113`]
- [x] [Review][Patch] Plan Implementation map checkboxes not marked done [`story-persist-rls-state-json-across-pid-clears-plan.md:105`]
- [x] [Review][Patch] Plan triage log leaves pre-stat size finding open [`story-persist-rls-state-json-across-pid-clears-plan.md:151`]
- [x] [Review][Patch] Unsavable RAM and I/O failures share one soft-fail message [`apps/ha_smart_hvac/hvac_app.py:152`]

**Rejected**
- R4 tmp-unlink via module `_LOG` — false: pure helper cannot use `HvacApp.log`; F3 only requires a WARNING
- R8 mkdtemp without teardown — low / rarely visible in CI; call-site cleanup is more than a direct fix
- R9 memlog fork 1 “not W1” — false: chronological fork then review renegotiation; plan is source of truth
- R10 ops notes omit rewrite timing — false: matches locked Implementation map ops bullet
- R11 frozen snapshot mutable lists — false: unreachable; callers replace snapshots wholesale
- R19 save assumes 2×2 without shape guards — false: defensive for unreachable `RlsState` shapes
- R22 description vs durable-field scope — false: descriptive; diff implements verify contract
- R23 ambiguous “fail” — false: clears vs soft-fail I/O are separate surfaces
- R24 pytest/ruff not in diff — false: gate outcomes live outside the patch text
- R25 latch reload beyond verify wording — false: plan-locked acceptance
- R26 ops docs beyond ticket text — false: plan Implementation map ops task
- R27 schema/I/O beyond starting intent — false: locked Boundaries
- R28 planning/ticket meta in diff — false: expected BMAD artifacts
