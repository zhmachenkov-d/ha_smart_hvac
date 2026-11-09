---
title: 'Tracer: RLS adaptive Kp/Ki on control tick'
type: 'feature'
ticket: '1'
created: '2026-11-08'
status: 'built'
baseline_revision: '4568fac2332a66eda2748c08808cde5aac52f100'
route: 'full'
route_source: 'auto'
risk: 'high'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - _bmad-output/initiative-pid/tickets/epic-rls-pid-retune/rls-adaptive-algorithm.md
  - CONTEXT.md
  - AGENTS.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Fixed-gain PID is live, but optional online retune of `kp`/`ki` via ARX+RLS is missing; commissioning has no adaptive switch or boiler-water `y` entity.

**Approach:** Add pure-Python ARX+RLS (in-memory only). Default `pid.adaptive` to off. Add top-level `boiler_water` as RLS `y` (required when adaptive is on). On a `control_tick` demand path with the plant available, step RLS and apply the existing `clamp(base+u_pid)` law using adapted gains from the documented IMC map. When adaptive is off, keep the existing yaml fixed-gain path.

## Boundaries & Constraints

**Always:**
- Same demand gates as fixed PID: Plant Management on + Heating Demand; SWT law remains round-0.1(clamp(`base_water_temp` + `u_pid`)); Kd = 0.
- RLS steps at most once per `control_interval` on `control_tick` demand only; never on `control_event` (including while demand remains true).
- `u` = last commanded rounded **demand** SWT: update only when demand `_write_setpoint(command)` returns True (readable plant, including equal-float skip); idle/plant-off/no-valid-zones/weights-unusable write of 0 must not change last `u`.
- `y` = top-level `boiler_water` only (never demand-zone air). Adaptive on requires non-empty stripped entity id at parse (ConfigError); adaptive off may omit `boiler_water`.
- Cold start: yaml `kp`/`ki` until first successful RLS step + valid IMC map; θ₀=`[a1,b0]=[0,0]`, P₀=`1e4·I`, λ=`0.98`. Step only when prior demand `u` and prior `y_prev` exist and current `y` is finite.
- On any PID ephemeral clear (idle / plant-off / no-valid-zones / weights-unusable): clear `y_prev` (force one seed-only tick before the next RLS step); keep in-memory θ/P, last demand `u`, and last-good adapted kp/ki.
- On finite `y` when not stepping: always `y_prev←y` (refresh). After a successful step: `y_prev←y`. Non-finite `y`: no step, do not change `y_prev`.
- Weather Feedforward, CAP-7, Outdoor listeners stay absent; Critical Zone stays log-only. In-memory RLS only (JSON = entry 3). Rails/unhealthy hardening = entry 2.

**Never:**
- numpy / external RLS process; Exclusive Session policy changes; Heating Demand definition changes; gain min/max rails or unhealthy fallback hardening (entry 2); JSON persistence (entry 3); ADR/CONTEXT/AGENTS RLS docs (entry 4); restoring outdoor/FF yaml as live commissioning.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Adaptive off / omitted | Demand tick, plant readable | yaml kp/ki; RLS not stepped; SWT as existing fixed PID | No error expected |
| Adaptive on, plant readable, prior u, prior y_prev, finite y | Demand tick | RLS steps once (φ=`[y_prev,u_prev]`); if IMC valid+finite gains, use adapted kp/ki; ∫ on write True; then y_prev←y | Non-finite y → no step; y_prev unchanged; keep prior gains |
| Adaptive on, plant readable, prior u, no y_prev, finite y | Demand tick | No step; seed y_prev←y; yaml or last-good gains; demand write runs | Seed-only after clear or cold start |
| Adaptive on, plant readable, no prior u, finite y | Demand tick | No step; y_prev←y (refresh); yaml or last-good; demand write runs | — |
| Adaptive on, plant readable, boiler_water unreadable | Demand tick | No RLS step; y_prev unchanged; demand write/∫ follow plant R7 only | WARNING on y read; do not treat as plant-unreadable |
| Adaptive on, plant unreadable | Demand tick | No RLS step; no ∫ advance (R7) | WARNING as today |
| Adaptive on, demand still true, `control_event` | Event path | No RLS step; no ∫; no SWT write | — |
| Clear: idle / plant-off / no-valid-zones / weights-unusable | Prelude / `_go_idle` | No RLS step; ∫ cleared; y_prev cleared; θ/P + last demand u + last-good kept; idle 0 does not overwrite last u | — |
| Adaptive on, missing/whitespace-only `boiler_water` | Parse | ConfigError; app does not start | Fail closed |
| Adaptive on, `control_interval` / Ts used in IMC ≤ 0 | Should not parse (existing) | If reached, treat IMC map invalid | Keep prior gains |

## Decisions (2026-11-08)

- OQ1 **B** — IMC closed-form from `(a₁,b₀)` (Design Notes); not a paste from the meeting transcript.
- OQ2 **B** → party fork2 **B1** — top-level `boiler_water`; required (strip nonempty) when adaptive on; RLS `y` never weighted air.
- OQ3 **A** — yaml until first valid adapted gains; θ₀=`[0,0]`, λ=`0.98`; P₀=`1e4·I`; eps=`1e-9` (fork7 **A**).
- Party fork1 **A** — rails/unhealthy stay entry 2; tracer may publish any **finite** adapted gains from a valid IMC map.
- Party fork4 **A** — last `u` = last demand write True only; persist across clears; idle 0 must not overwrite.
- Party fork5 **A** — last-good adapted kp/ki persist across clears with RLS θ/P.
- Party fork6 **A** + review — first finite y seeds; step needs prior u and y_prev; on non-step finite y always refresh y_prev; clear paths wipe y_prev so the next tick is seed-only (no idle-spanning φ).
- Review — forgetting-RLS update equations locked in Design Notes; IMC also requires `τ>eps` and finite kp/ki; equal-skip counts as successful demand write for last `u`.

</frozen-after-approval>

## Code Map

- `apps/ha_smart_hvac/hvac_app.py` — `control_tick` / `_gate_prelude` / `_run_demand` / `_write_setpoint` / `_clear_pid_ephemeral` / `_go_idle`. Wire: (1) last demand SWT only when demand `_write_setpoint` returns True, never from idle 0; (2) optional RLS before `evaluate_demand` when adaptive + plant readable + priors + finite boiler_water y; (3) pass last-good adapted or yaml gains; (4) on ephemeral clear, clear y_prev only among RLS bookkeeping — keep θ/P, last u, last-good gains; (5) never step on `control_event`.
- `apps/ha_smart_hvac/pid.py` — unchanged PI law; no air-`y` helper for RLS.
- `apps/ha_smart_hvac/models.py` — `PidConfig.adaptive: bool = False`; `HvacConfig.boiler_water: str | None = None`.
- `apps/ha_smart_hvac/config.py` — parse `adaptive` as YAML bool only (ConfigError otherwise); top-level `boiler_water`; ConfigError when adaptive and strip(boiler_water) empty.
- `apps/ha_smart_hvac/rls.py` (**new**) — ARX+forgetting RLS + IMC map (Design Notes); in-memory θ/P.
- `apps.yaml.example` — `pid.adaptive: false`; commented `boiler_water` (required when adaptive true).
- `tests/test_rls.py`, `tests/test_config.py`, `tests/test_hvac_app.py` — matrix + RLS golden step + B1 ConfigError + event-no-step + clear-reseeds-y_prev.
- Do not restore feedforward/ladrc; do not register Outdoor listeners.

## Design Notes

- **Plant available (write/∫):** plant **setpoint** readable (`_read_float(plant_setpoint)`), matching R7. **Identification:** separate — needs finite `boiler_water` y; unreadable y does not by itself skip ∫.
- **Tick order (demand path):** One plant-setpoint snapshot per demand tick shared by the RLS gate and the demand write (no mid-tick re-read divergence). If adaptive on and `y` finite: always seed/refresh `y_prev←y` after the gate checks (including when plant is unreadable). Step RLS only when that snapshot shows plant readable **and** prior `u` **and** prior `y_prev` exist — φ=`[y_prev,u_prev]` *before* `evaluate_demand`. If `y` non-finite → no step, leave `y_prev`. After demand `_write_setpoint(command)` returns True → update last demand SWT. On any clear → wipe `y_prev` only among RLS sample bookkeeping.
- Entry 2 owns rails/unhealthy. This story: reject non-finite or IMC-invalid maps (keep yaml until first success, else last-good). Gains outside future min/max rails stay out of scope.
- Persistence APIs out of scope; keep RLS fields on the App instance for entry 3.

**Forgetting RLS (locked):** θ=`[a1, b0]^T`, φ=`[y_prev, u_prev]^T`, measurement `y`, λ=`0.98`:

```
e = y - φ·θ
K = (P φ) / (λ + φ·P·φ)
θ ← θ + K e
P ← (P - K φᵀ P) / λ
```

Init: θ=`[0,0]`, P=`1e4·I`. Use pure Python floats/lists (no numpy).

**IMC map (locked):** ARX ⇒ `G(z)=b₀/(z−a₁)`. `Ts=control_interval` (s):

```
# valid only when 0 < a1 < 1, |b0| > eps, |1-a1| > eps, Ts > 0,
# τ > eps, K > 0, and kp/ki finite
K  = b0 / (1 - a1)
τ  = -Ts / ln(a1)
λc = τ
kp = τ / (K * λc)           # = (1 - a1) / b0
ki = kp * 3600 / τ
```

`eps`=`1e-9`. If map invalid → do not publish new adapted gains.

## Tasks & Acceptance

**Execution:** Implement per Code Map and Design Notes; cover the I/O matrix in tests.

**Acceptance Criteria:**
- Given `pid.adaptive` omitted or false, when a demand `control_tick` runs, then yaml gains drive SWT and RLS is never stepped.
- Given `pid.adaptive: true` without a strip-nonempty `boiler_water`, when config is parsed, then ConfigError is raised.
- Given `pid.adaptive: true` with non-bool adaptive value (e.g. string/int), when config is parsed, then ConfigError is raised.
- Given adaptive on, plant readable, prior demand `u`, prior `y_prev`, and finite `boiler_water` y, when a demand tick runs, then RLS steps once and after a valid finite IMC map the commanded SWT uses adapted kp/ki.
- Given adaptive on, prior `u`, no `y_prev`, finite y, when a demand tick runs, then RLS does not step and `y_prev` is seeded.
- Given adaptive on, no prior `u`, finite y, when a demand tick runs, then RLS does not step and `y_prev←y`.
- Given adaptive on, plant readable, `boiler_water` unreadable, when a demand tick runs, then RLS does not step, `y_prev` is unchanged, and ∫ follows plant readability only.
- Given adaptive on and plant setpoint unreadable, when a demand tick runs, then RLS does not step and ∫ does not advance.
- Given adaptive on and Heating Demand still true, when `control_event` runs, then RLS does not step, ∫ does not advance, and SWT is not written.
- Given idle, plant-off, no-valid-zones, or weights-unusable clear, when clear runs, then RLS does not step; `y_prev` is cleared; θ/P, last demand `u`, and last-good adapted kp/ki remain; idle 0 does not overwrite last `u`.
- Given adaptive on with last-good adapted gains after a clear, when demand returns, then after one seed-only tick (new `y_prev`) subsequent ticks with priors may step; evaluate_demand uses last-good until a new valid map replaces them.
- Given demand `_write_setpoint` returns True via equal-float skip, when that demand tick completes, then last demand `u` equals the commanded value.
- Given you run `uv run pytest` and `uv run ruff check`, then both succeed.

## Implementation Notes

## Plan Change Log

- 2026-11-08 party: forks 1–7 / meta C locked (rails entry 2; B1 boiler_water; last u; last-good; y_prev seed; P₀/eps); companion + tickets.toml synced.
- 2026-11-08 review A: idle-spanning φ blocked (clear y_prev); y_prev refresh on non-step; last u on write True incl. equal-skip; boiler_water unreadable vs plant; RLS equations locked; IMC τ/finite guards; whitespace + bool parse; no-valid-zones/weights clear; control_event AC; structure/prose condense.

## Review Triage Log
- 2026-11-09 code review: applied 8 patches — rls_step denom/finite guards; one plant snapshot per demand tick for RLS+write; Design Notes tick-order; IMC-invalid keeps last-good test; plant-unreadable last_u assert; weights-unusable no-step assert; imc |1−a1|≤eps case; companion clear list.

- 2026-11-08 plan review (adversarial, edge-case-hunter, structure, prose): user chose **A** — apply items 1–7 + structure/prose into plan. Patched: idle reseed; y_prev refresh; equal-skip last u; boiler_water unreadable row; RLS update equations; IMC finite/τ/Ts guards; whitespace/bool ConfigError; clear-path completeness; control_event AC; Design Notes before Tasks; Decisions own section; Change Log condensed; Verification folded into AC; Approach/tick-order prose clarified. Deferred none for this tracer (rails remain entry 2 by fork1 A).
- 2026-11-08 code review (quick): `hvac_app._maybe_rls_step` early-returns on unreadable plant before reading `boiler_water` — **medium** / **patch**. Evidence: frozen Always requires `y_prev←y` on finite y when not stepping; plant-unreadable matrix/AC forbid only step+∫; code returned before y read so seed/refresh never ran. Patched: read y first; always seed/refresh; skip step only when plant unreadble or missing last_u.
- 2026-11-08 code review (quick): `tickets.toml` entry 1 description/verify/notes claim clears keep `y_prev` — **low** / **patch**. Evidence: frozen Always/matrix clear `y_prev`; runtime already matched plan. Patched: entry 1 text now says clears wipe `y_prev`, keep θ/P, last u, last-good.


## Code Review

### 2026-11-09
**Code review complete.** 0 `decision-needed`, 8 `patch`, 0 `defer`, 9 rejected. Decision F2 → patch (A).

- [x] [Review][Patch] Plant readability TOCTOU — snapshot plant once per demand tick for RLS gate + write [`apps/ha_smart_hvac/hvac_app.py:122`] — resolved decision: A
- [x] [Review][Patch] rls_step lacks numerical guards (denom / non-finite θ,P) [`apps/ha_smart_hvac/rls.py:37`]
- [x] [Review][Patch] Design Notes tick-order prose contradicts Always/code on y_prev refresh when plant unreadable [`story-tracer-rls-adaptive-kp-ki-on-control-tick-plan.md` Design Notes]
- [x] [Review][Patch] Missing app test — IMC-invalid step keeps last-good/yaml gains and SWT [`tests/test_hvac_app.py`]
- [x] [Review][Patch] Missing assertion — plant-unreadable demand tick leaves last_u unchanged [`tests/test_hvac_app.py:1110`]
- [x] [Review][Patch] Missing assertion — weights-unusable clear does not step RLS [`tests/test_hvac_app.py:1202`]
- [x] [Review][Patch] Missing unit case — imc_gains rejects |1−a1|≤eps inside (0,1) [`tests/test_rls.py`]
- [x] [Review][Patch] Companion Persistence clear list incomplete (omits no-valid-zones / weights-unusable) [`rls-adaptive-algorithm.md:25`]

Rejected:
- R2 apps.yaml.example boiler_water comment placement — low; fail-closed when enabling adaptive; comment reshuffle low value now.
- R3 assert boiler_water under -O — false; parse invariant; unreachable.
- R7 empty Implementation Notes — low; cosmetic plan hygiene.
- R8 companion JSON persistence framing — false; epic-scoped HOW; entry 3 owns JSON.
- R9 water-ARX IMC vs air-error PI rationale — false; agreed algorithm shape.
- R10 non-string boiler_water silent drop when adaptive off — low; unused key; later ConfigError.
- R12 no log when IMC refuses — low; entry 2 is the natural unhealthy signal place.
- R19 epic R4 unhealthy vs entry 2 deferral — false; intentional tracer scope.
- R20/R21 Verify subset / singular plant language — false; intentional supersets/splits.
