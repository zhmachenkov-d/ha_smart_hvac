# Walkthrough — PR #43: Package C deferred stub locks

Target: [PR #43](https://github.com/zhmachenkov-d/ha-smart-hvac/pull/43) (`test/omega-c-deferred-stub-locks` → `main`, commit `22482cb`)
Focus: human review of two Hass-stubbed `control_tick` locks deferred from Package C Q5 (tests only; no production behavior change)
Current block: closed — walkthrough complete; wrap-up: commit/push + clear deferred Q5 + merge PR #43 + delete feature branch

## Blocks

- [x] **Intent** — done
- [x] **Broad strokes** — done
- [x] **Multi-tick latched decay persist** — done
- [x] **Equal-value write-on-change side effects** — done
- [x] **Periphery** — done

## Intent

Source: [plan-package-c-deferred-stub-locks.md](../plan-package-c-deferred-stub-locks.md) (frozen-after-approval Intent).

**Problem:** Package C Q5 deferred two Hass-stubbed `control_tick` locks: multi-tick latched decay persist (mirrors cover helpers only) and equal-value write-on-change side effects (`_write_setpoint` unit tests cover equality skip only). R6 still has those seams unguarded through the real tick path.

**Approach:** Add two named `_tick_app` tests only — no production behavior change. (1) Multi-tick latched residue through real `control_tick` decreases and persists ωc. (2) Plant float equal to desired SWT skips `number/set_value` while post-write sticky/decay still run.

**Decisions (plan review 2026-10-17):**
- R1: Under trip/residue, desired SWT is `clamp(weather_feedforward(outdoor), setpoint_min, setpoint_max)` — not `setpoint_max`. With outdoor `0` and Package C weather config that is `49.0`.
- R2: Unavailable / fail-closed plant is already locked (Package C fail-write + R6(d)); no new Hass test for it.
- R3: Multi-tick AC requires ≥3 strict ωc decreases + JSON/reload match; floor-to-`omega_c_min` stays with mirrors.

**Review notes (Intent):**
1. Diff matches Intent — tests-only; both named locks; R1–R3 observed; no production edits.
2. Soft: [deferred-work.md](../deferred-work.md) Q5 bullets still open (plan Never — separate framing).

## Broad strokes

What the change is: two Hass-stubbed `control_tick` tests that lock Package C Q5 seams — multi-tick latched ωc decay persist, and equal-value write-on-change that still runs sticky+decay — without changing production.

Entry points (open in this order):

1. [`test_control_tick_multi_tick_latched_decay_persists`](../../../tests/test_hvac_app.py#L1107) — ≥3 latched ticks: strict ωc decrease + JSON/`LadrcTuner` reload
2. [`test_control_tick_equal_setpoint_skips_set_value_still_sticky_decays`](../../../tests/test_hvac_app.py#L1133) — plant=`clamp(u_ff)` skips `set_value`; sticky + one decay step
3. [`_tick_app`](../../../tests/test_hvac_app.py#L807) — Package C Hass stub recipe reused by both locks
4. [post-write sticky + decay](../../../apps/hvac/hvac_app.py#L299) — production path the stubs exercise (read-only in this PR)
5. [`_write_setpoint` equality skip](../../../apps/hvac/hvac_app.py#L440) — write-on-change seam the equal-value test locks through the tick

**Review notes (Broad strokes):**
1. Five entry points enough — both tests, `_tick_app`, sticky+decay, equality skip.
2. Mirrors / R6(c) unit locks correctly out of Broad strokes.

## Multi-tick latched decay persist

With latch already True and trip/residue numbers held, each successful `control_tick` skips adapt, keeps sticky latch, and commits a decayed ωc to the tuner state file. The Hass stub proves that wiring across ≥3 ticks — mirrors still own floor-to-`omega_c_min`.

- Setup: [`test_control_tick_multi_tick_latched_decay_persists`](../../../tests/test_hvac_app.py#L1109) — pinned `omega_c=0.10`, `u_track_max=50`, `zone_temp=15`, `outdoor=0`, `blow_up_latch=True`
- Loop: [≥3 strict decreases + latch holds](../../../tests/test_hvac_app.py#L1120)
- Persist: [JSON + `LadrcTuner` reload](../../../tests/test_hvac_app.py#L1126)
- Production order exercised: [skip-adapt when latched](../../../apps/hvac/hvac_app.py#L217) → [sticky](../../../apps/hvac/hvac_app.py#L300) → [decay commit](../../../apps/hvac/hvac_app.py#L320)
- Mirror floor coverage left alone: [`test_multi_tick_decay_persists_until_omega_c_min`](../../../tests/test_hvac_app.py#L607)

**Review notes (Multi-tick):**
1. R3 AC met; default plant ≠ desired so writes succeed each tick.
2. Soft: no exact `next_decayed_omega_c` magnitude assert; skip-adapt implied not direct.
3. Tested: Hass lock + mirror floor — both passed.

## Equal-value write-on-change side effects

Under the same trip/residue setup, plant float is preset to `clamp(weather_feedforward(0), min, max)` (`49.0`). `_write_setpoint` returns success without calling `number/set_value`, and post-write sticky + one decay step still run — the seam R6(c) unit tests never saw through `control_tick`.

- Desired: [R1 clamp via `weather_feedforward`](../../../tests/test_hvac_app.py#L1137) — assert `49.0`
- Stub: [`plant_setpoint=desired`, `blow_up_latch=False`](../../../tests/test_hvac_app.py#L1147) — sticky must set latch on this tick
- Expect: [`next_decayed_omega_c` one step](../../../tests/test_hvac_app.py#L1158); [no `number/set_value`](../../../tests/test_hvac_app.py#L1166); latch True
- Production: [`current == value` → True](../../../apps/hvac/hvac_app.py#L440) then [sticky](../../../apps/hvac/hvac_app.py#L300) + [decay](../../../apps/hvac/hvac_app.py#L320)
- Unit-only equality left in place: [`test_write_setpoint_skips_set_value_when_entity_float_equals`](../../../tests/test_hvac_app.py#L1193)

**Review notes (Equal-value):**
1. R1 + sticky-after-equality-success proven; exact one decay step.
2. Soft: asserts `number/set_value` only (plan).
3. Tested: Hass lock + R6(c) unit — 4 passed.

## Periphery

- [plan-package-c-deferred-stub-locks.md](../plan-package-c-deferred-stub-locks.md) — build plan (`status: built`); frozen Intent + AC for this PR
- [deferred-work.md](../deferred-work.md) — Q5 bullets still listed (plan Never: no framing note in this PR)
- [`weather_feedforward` import](../../../tests/test_hvac_app.py#L12) — enables R1 desired SWT in equal-value lock
- No ADR / apps / CI config changes in the PR diff

**Review notes (Periphery):**
1. Diff is plan + tests only; deferred Q5 framing left for wrap-up.
2. Full suite 75 passed; ruff clean; PR CI green.
