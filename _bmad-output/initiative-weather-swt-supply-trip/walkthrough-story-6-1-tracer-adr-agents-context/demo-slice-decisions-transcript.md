# Demo: Story 6.1 — Slice Decisions (idle flame + zombies)
Generated: 2026-11-17T10:13:30+00:00

Offline spot-read of decision notes in this slice.

## 1. Live Decision C

`docs/decisions/adr-idle-flame-clear-after-write.md`

| Check | Result |
| --- | --- |
| Title Idle flame clear | L1 |
| Always `_disarm_flame_trip_hold` | OK |
| Clear `_flame_trip_latched` only after successful idle SWT `0` | OK |
| Plant-off → `_clear_flame_trip_state` | OK |

## 2. Historical zombies (banner)

| File | Banner | Forward link to live Decision C |
| --- | --- | --- |
| `adr-idle-trip-clear-after-write.md` | OK L1 | OK |
| `adr-supply-event-no-outdoor-prelude.md` | OK L1 | n/a |
| `adr-write-gated-supply-trip-latch.md` | OK L1 | n/a |
| `adr-trip-hold-token-orphan-guard.md` | OK L1 | n/a |

## 3. TRV before water prelude

`docs/decisions/adr-trv-before-water-prelude.md`

| Check | Result |
| --- | --- |
| Title includes tick / control_event / hold expiry | OK |
| Body lists flame hold expiry | OK |
| No `supply_event` | OK |
| Flame observe/latch do not run `_apply_trv_law` | OK |

## 4. Live flame/TRV notes not demoted (sanity)

Sampled `adr-flame-observe-gate-no-outdoor.md`, `adr-write-gated-flame-latch.md`, `adr-trv-accuracy-shared-control-event.md` — no Historical banner.

## Verdict

Live Decision C present; supply-era notes demoted; TRV prelude updated; live flame/TRV decisions untouched.
