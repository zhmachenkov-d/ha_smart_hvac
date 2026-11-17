# Walkthrough — PR #41: Package C latch hygiene

Target: [PR #41](https://github.com/zhmachenkov-d/ha-smart-hvac/pull/41) (`fix/omega-c-package-c-latch-hygiene` → `main`, commits `3435c63` + `754b30d`)
Focus: human review of full PR #41 (Package C latch hygiene + epic retro / party trail)
Current block: closed — walkthrough complete; wrap-up: commit/push + merge PR #41 + delete feature branch

## Blocks

- [x] **Intent** — done
- [x] **Broad strokes** — done
- [x] **clear_steady on latch** — done
- [x] **Episode WARN (_blow_up_warned)** — done
- [x] **Hass-stubbed control_tick locks** — done
- [x] **Periphery** — done

## Intent

Source: [plan-package-c-latch-hygiene.md](../plan-package-c-latch-hygiene.md) (frozen Intent + Decisions).

**Problem:** After R4 skip-adapt, `LadrcTuner._steady_ticks` stays hot so the first unlatched tick can immediately propose upward ωc and undo decay. Separately, trip + fail-write never sticks the latch, so `should_warn` fires every 60 s. R6 locks are mostly mirrors/inspect and miss both seams.

**Approach:** Package C (retro / product-team): (1) `clear_steady()` when `latch_at_start`; (2) app-level `_blow_up_warned` so fail-write does not spam WARNING while sticky/decay stay after successful write only; (3) Hass-stubbed `control_tick` tests locking AI-1+AI-2 only; (4) companion R4 + WARN episode wording.

**Decisions (plan review 2026-10-17):**
- Q1: Clear `_blow_up_warned` on every successful demand tick that ends with `_blow_up_latch is False`, plus `_hands_off` / `_go_idle` / no-demand clears. Never clear on fail-write early-return.
- Q2: No special zone-change clear for warned; only Q1 / idle paths.
- Q3: Episode WARN gate only in app (`guard.should_warn and not self._blow_up_warned`); `guard_u_track` unchanged.
- Q4: Integration tests seed `tuner._steady_ticks` / `_blow_up_latch` (and `LadrcState` if needed); force trip via low `u_track_max` and/or high zone error; mock only Hass I/O.
- Q5: Stub locks AI-1+AI-2 only; multi-tick decay-persist and write-on-change legs deferred (see initiative `deferred-work.md`).
- Q6: Required companion updates for `clear_steady` and `_blow_up_warned`.

**Review notes (Intent):**
1. Frozen Intent matches shipped Package C: `clear_steady()` on `latch_at_start`; `_blow_up_warned` gates WARN before write; sticky/decay/ESO only after successful `_write_setpoint`; fail-write early-returns unchanged.
2. Q1–Q3 clear paths present (healthy demand latch False; `_hands_off` / `_go_idle` / no-demand); no zone-change clear for warned (Q2).
3. Hass-stubbed tests lock rebound, fail-write once, fail-then-success sticky+decay, episode clear, re-arm, idle clears; R4 companion + deferred-work Q5 + memlog Q1–Q6 align.
4. No Intent gaps vs code.
5. Formal review (bmad-code-review): 3 patch applied (unlatched steady lock; initialize warned; sticky warned assert); 2 defer (ADR 0003; retro close-out); 8 rejected; `test_hvac_app.py` 73 passed.

## Broad strokes

What the change is: Package C hardens two R4 recovery seams — clear residual steady while latched, and gate blow-up WARNING once per episode without sticking latch on fail-write — plus Hass-stubbed locks and planning artifacts from the epic retro.

Entry points (open in this order):

1. [clear_steady on latch_at_start](../../../apps/hvac/hvac_app.py#L217) — skip adapt + clear steady while latched
2. [episode WARN gate](../../../apps/hvac/hvac_app.py#L286) — `should_warn and not _blow_up_warned` before write
3. [sticky after successful write + clear warned](../../../apps/hvac/hvac_app.py#L300) — sticky/decay only post-write; clear warned when latch False
4. [`_tick_app` + integration tests](../../../tests/test_hvac_app.py#L806) — rebound / fail-write / fail-then-success / episode clear / re-arm / idle
5. [R4 companion](../control-tick-behaviors.md) — clear_steady + Episode WARN wording

**Review notes (Broad strokes):**
1. Five entry points cover latch clear_steady, episode WARN gate, sticky-after-write + warned clear, Hass stubs, and R4 companion — enough to grasp Package C without listing every test or planning file.
2. Decay persist and directional/strict-apply paths are pre-existing R4/R1/2; correctly absent from Broad strokes.
3. Retro / memlog / plan / deferred-work belong in Periphery (focus B); formal-review locks (unlatched steady, initialize) sit under entry 4’s test umbrella.
4. No Broad strokes gaps vs Intent.

## clear_steady on latch

While latch is already active at tick start, R4 skips `maybe_adapt`. Package C also calls `clear_steady()` so `_steady_ticks` cannot stay warm across the latched window and fire an upward ωc proposal on the first healthy unlatched tick, undoing decay.

- [latch_at_start branch](../../../apps/hvac/hvac_app.py#L217) — `clear_steady()` then skip adapt
- [test_control_tick_post_latch_clear_steady_no_upward_rebound](../../../tests/test_hvac_app.py#L865) — warm steady + latched ticks then unlatched; ωc does not rise
- [test_control_tick_unlatched_does_not_clear_steady](../../../tests/test_hvac_app.py#L897) — unlatched path increments steady (latched-only clear)
- [R4 skip-adapt bullet](../control-tick-behaviors.md) — documents clear_steady on latch_at_start

**Review notes (clear_steady on latch):**
1. `latch_at_start` branch clears steady and sets `new_omega_c = None`; unlatched path calls `maybe_adapt` only — matches Intent AI-1.
2. Rebound stub locks warm→latched clear (`_steady_ticks == 0`) then first unlatched `_steady_ticks == 1` with ωc unchanged; unlatched stub locks mid-range steady increment (formal-review patch).
3. Inspect skip-block also requires `clear_steady` inside `if latch_at_start`. Soft: rebound forces latch each tick rather than sticky→natural clear — accepted earlier as low.
4. No gaps for this slice.
5. Test: rebound + unlatched + inspect skip-adapt — 3 passed (`uv run pytest`); live Exclusive Session not run.

## Episode WARN (_blow_up_warned)

Sticky latch still requires successful `_write_setpoint`. Fail-write early-returns before sticky, so trip + unreadable plant would re-warn every tick. App flag `_blow_up_warned` gates WARNING once per episode; clears on successful demand ending latch False and on idle/hands_off/no-demand — never on fail-write early-return.

- [warn gate + set](../../../apps/hvac/hvac_app.py#L286) — emit once; set `_blow_up_warned`
- [post-write sticky + clear warned](../../../apps/hvac/hvac_app.py#L300) — sticky/decay after write; clear warned when latch False
- [hands_off / go_idle](../../../apps/hvac/hvac_app.py#L354) — clear warned with latch
- [initialize](../../../apps/hvac/hvac_app.py#L173) — both flags False
- [R4 Episode WARN](../control-tick-behaviors.md) — app gate independent of sticky
- [test_initialize_sets_blow_up_flags_false](../../../tests/test_hvac_app.py#L917) — initialize pins both flags
- [fail_write_warns_once](../../../tests/test_hvac_app.py#L935) — one WARNING; latch stays False
- [fail_then_success](../../../tests/test_hvac_app.py#L957) — sticky + decay; no second WARN; warned stays True
- [episode_clear](../../../tests/test_hvac_app.py#L1010) — asserts `_blow_up_warned is False`
- [warn_rearms](../../../tests/test_hvac_app.py#L1030) — WARNING emits again after clear
- [idle_paths_clear_blow_up_warned](../../../tests/test_hvac_app.py#L1081) — idle/hands_off/no-demand clear

**Review notes (Episode WARN):**
1. Gate is app-only (`should_warn and not _blow_up_warned`); set before write; fail-write early-returns before sticky — Q3 + sticky-after-write intact.
2. Q1 clear on successful demand with latch False; idle/hands_off/no-demand clear with latch; initialize pins both flags; no zone-change clear (Q2).
3. Stubs cover fail-write once, fail-then-success (warned stays True while sticky), episode clear, re-arm, idle. Soft: re-arm swaps `u_track_max` via config surgery (already low in formal review).
4. No gaps for this slice.
5. Test: initialize + fail-write + fail-then-success + episode clear + re-arm + idle/inspect — 8 passed; live Exclusive Session not run.

## Hass-stubbed control_tick locks

`_tick_app` builds a Hass-stubbed `HvacApp` (parse_config thermal numbers, MagicMock I/O) and drives `control_tick` phases. Locks AI-1+AI-2 only; multi-tick decay-persist and write-on-change remain deferred.

- [`_tick_app`](../../../tests/test_hvac_app.py#L806) — stub recipe
- Named tests in the two slices above
- [deferred-work.md](../deferred-work.md) — Q5 deferrals recorded

**Review notes (Hass-stubbed locks):**
1. `_tick_app` matches Q4 recipe: `parse_config` thermal args, `__new__`, MagicMock Hass I/O, seed latch/warned/steady; trip via low `u_track_max` / high error.
2. Named stubs lock AI-1+AI-2 (+ formal-review unlatched + initialize); no Hass-stubbed multi-tick decay-persist or equal-value write-on-change — Q5 / deferred-work.
3. R6 mirrors still cover decay helpers and `_write_setpoint` equality separately — intentional split, not a Package C gap.
4. Soft: some scenarios inline duplicate `get_state` (already low in formal review). No gaps for this slice.
5. Test: Package C stub cluster 9 passed; full `test_hvac_app.py` 73 passed. Live Exclusive Session not run.

## Periphery

- [epic retrospective](../epic-gate-omega-c-on-saturation/epic-gate-omega-c-on-saturation-retrospective.md) — accepted-with-open-items; Package C from AI-1..AI-3
- [party memlog](../../party-mode/memories/product-team/.memlog.md) — product-team chose Package C + Q1–Q6 trail
- [plan-package-c-latch-hygiene.md](../plan-package-c-latch-hygiene.md) — frozen Intent; status built; Code Review patches applied
- [deferred-work.md](../deferred-work.md) — Q5 stub legs + ADR/retro close-out notes from formal review

**Review notes (Periphery):**
1. Retro records Package C choice (AI-1..AI-3); memlog has Q1–Q6; plan `status: built` with Code Review patches checked.
2. `deferred-work.md` holds Q5 stub deferrals plus formal-review ADR/retro hygiene — matches focus B without blocking the code path.
3. Soft: retro action-item table / open Q#2 still read as pre-build open items (explicitly deferred close-out note). No Periphery gaps that change Package C ship.
