# Review log: Story 5.1 — flame short-on tracer

Target: PR #151 · feat/5-1-flame-short-on · 918debc

## 1 — Orientation — start
Session: unavailable · Timestamp: 2026-11-16T17:39:00+00:00

- Action: Opened walkthrough for story 5.1 / PR #151; created narrative+log; Intent block presented.
- Result: Target confirmed (tracer: remove supply trip + flame short-on). Working tree clean.
- Evidence: plan story-tracer-replace-supply-trip-with-flame-short-on-plan.md; PR #151; commit 918debc
- Open: Intent acceptance pending user
## 2 — Intent — Formal review

Session: unavailable · Timestamp: 2026-11-16T17:52:18+00:00

- Action: bmad-code-review on main...HEAD (PR #151); lenses blind-hunter, edge-case-hunter, verification-gap, intent-alignment; triage+route.
- Result: 5 patch (ch_active race+tests, since-None fall, closed-gate arm, ADV8 TRV assert, _flame_trip_app kwargs); 15 rejected; 0 defer/decision. Awaiting patch-handling choice.
- Evidence: triage /tmp/cr-5-1-triage-jjBjc3.md; plan Code Review 2026-11-16
- Open: user patch option 1/2/3; Intent still in progress

## 3 — Intent — Formal review patches applied

Session: unavailable · Timestamp: 2026-11-16T17:53:56+00:00

- Action: Applied all 5 patch findings; pytest 27 flame-focused + ruff clean.
- Result: ch_active_event wipes on new!=on OR closed gate; goldens for bounce/preserve/since-None fall/closed-gate arm/ADV8 TRV; `_flame_trip_app` forwards ch_active/flame_on. Plan patch boxes checked.
- Evidence: hvac_app.py ch_active_event; test_hvac_app.py new tests; plan Code Review 2026-11-16
- Open: Intent acceptance; dirty tree (uncommitted patches); code-review next-steps menu

## 4 — Intent — Test

Session: unavailable · Timestamp: 2026-11-16T17:54:39+00:00

- Action: `uv run pytest`; `uv run ruff check apps/ha_smart_hvac tests`
- Result: 352 passed; ruff clean. Verify commands from story 5.1 satisfied on current tree (includes review patches).
- Evidence: pytest 352; ruff All checks passed
- Open: Intent acceptance; dirty tree uncommitted

## 5 — Intent done → Broad strokes

Session: unavailable · Timestamp: 2026-11-16T17:55:36+00:00

- Action: User accepted Intent; presented Broad strokes; narrative checked Intent, filled Broad strokes map.
- Result: Intent done (Formal review + Test). Broad strokes in progress. Tree dirty (review patches + walkthrough + plan).
- Evidence: walkthrough-story-5-1-flame-short-on.md
- Open: Broad strokes acceptance; ask commit?

## 6 — Broad strokes — Demo

Session: unavailable · Timestamp: 2026-11-16T17:56:41+00:00

- Action: Offline demo of five Broad-strokes entry points; pytest goldens + code/example slices.
- Result: short-on latch 1; ADV8+latched 3; config flame 20; example parse 1; matrix 27 — all pass. Transcript saved.
- Evidence: demo-broad-strokes-transcript.md
- Open: Broad strokes acceptance; dirty tree / commit ask still open

## 6b — Broad strokes — Demo transcript rewritten

Session: unavailable · Timestamp: 2026-11-16T17:57:30+00:00

- Action: Rewrote demo-broad-strokes-transcript.md with code slices + pytest results for all five entry points.
- Result: 1+3+20+1+27 goldens shown; offline only.
- Evidence: _bmad-output/initiative-weather-swt-supply-trip/walkthrough-story-5-1-flame-short-on/demo-broad-strokes-transcript.md
- Open: Broad strokes acceptance; commit ask still open

## 7 — Broad strokes — commit+push

Session: unavailable · Timestamp: 2026-11-16T17:58:25+00:00

- Action: User requested commit+push of dirty tree (review patches + walkthrough + plan).
- Result: 84af911 pushed to origin/feat/5-1-flame-short-on. Working tree clean.
- Evidence: fix(flame): wipe since on CH-off even after state bounce
- Open: Broad strokes still in progress (not accepted)

## 8 — Broad strokes done → config/models slice

Session: unavailable · Timestamp: 2026-11-16T17:59:08+00:00

- Action: User accepted Broad strokes; presented config/models slice.
- Result: Broad strokes done. Current: config/models flame fields.
- Evidence: models.py HvacConfig; config.py parse_config/_KNOWN_KEYS
- Open: Slice acceptance; narrative/log dirty again after push

## 9 — Slice config/models — Test

Session: unavailable · Timestamp: 2026-11-16T17:59:34+00:00

- Action: `uv run pytest tests/test_config.py -k 'flame or legacy_water or apps_yaml_example or ignored'`; ruff on config/models/test_config.
- Result: 20 passed, 127 deselected; ruff clean.
- Evidence: test_config flame defaults/reject/truncate/legacy ignore/example
- Open: Slice acceptance; dirty narrative/log

## 10 — config/models done → hvac_app observe/latch slice

Session: unavailable · Timestamp: 2026-11-16T18:00:15+00:00

- Action: User accepted config/models; presented hvac_app observe/latch/clear slice.
- Result: Current block is flame observe/latch (supply path removed).
- Evidence: hvac_app.py flame_event/ch_active_event/_flame_observe_gate
- Open: Slice acceptance; dirty narrative/log

## 11 — Slice hvac_app observe — Test

Session: unavailable · Timestamp: 2026-11-16T18:00:50+00:00

- Action: pytest flame/ch_active/closed_gate_arm/fall_without_since/ungated_flame; ruff hvac_app+tests.
- Result: 27 passed, 101 deselected; ruff clean.
- Evidence: test_hvac_app flame matrix
- Open: Slice acceptance; dirty narrative/log

## 12 — Slice hvac_app observe — Formal review

Session: unavailable · Timestamp: 2026-11-16T18:13:26+00:00

- Action: Code review on main...HEAD hvac_app.py+test_hvac_app.py; lenses BH/ECH/VG/IA; triage.
- Result: 5 patch, 0 defer/decision, 9 rejected (ECH empty). Awaiting patch handling.
- Evidence: triage /tmp/cr-5-1-hvac-triage-VqMC0y.md; plan Code Review 2026-11-16 (hvac observe/latch slice)
- Open: user patch option 1/2/3

## 13 — Slice hvac_app observe — Formal review patches applied

Session: unavailable · Timestamp: 2026-11-16T18:28:54+00:00

- Action: Applied 5 patch findings; focused pytest 33 + spot checks; ruff clean.
- Result: latch after run_in; commissioned min/hold AC; orphan asserts; plant-off/idle armed-since wipe; e2e latch→expiry→curve.
- Evidence: hvac_app.py flame_event; new tests in test_hvac_app.py; plan boxes checked
- Open: code-review next-steps; slice still in progress; dirty tree

## 14 — hvac observe done → _run_demand/ADV8; commit+push

Session: unavailable · Timestamp: 2026-11-16T18:31:59+00:00

- Action: User accepted observe slice + requested commit+push; advanced to _run_demand/ADV8 slice.
- Result: Observe slice done. Staging review patches + walkthrough for push.
- Evidence: narrative current block ADV8; dirty tree includes hvac_app latch-after-run_in + tests
- Open: ADV8 slice in progress after push

## 15 — Slice _run_demand/ADV8 — Test

Session: unavailable · Timestamp: 2026-11-16T18:32:34+00:00

- Action: pytest latched_demand/hold_expiry/rising_edge/trv_runs_while_flame/idle Decision C/plant_off clear/e2e expiry; ruff.
- Result: 15 passed, 117 deselected; ruff clean.
- Evidence: test_hvac_app focused filter
- Open: Slice acceptance; dirty narrative/log

## 16 — Slice _run_demand/ADV8 — Formal review

Session: unavailable · Timestamp: 2026-11-16T18:40:00+00:00

- Action: Code review focused ADV8/latched demand/clears; BH/ECH/VG/IA; triage routed 6 patch.
- Result: 6 patch, 0 defer/decision, 9 rejected. Awaiting patch handling.
- Evidence: triage /tmp/cr-5-1-adv8-triage-*.md; plan Code Review ADV8 slice
- Open: user patch option 1/2/3

## 17 — Slice _run_demand/ADV8 — Formal review patches applied

Session: unavailable · Timestamp: 2026-11-16T20:26:29+00:00

- Action: Applied 6 patch findings (tests only); pytest 11 focused + ruff clean.
- Result: Latched retention/write-fail; closed-gate cancel/token; TRV control_event; ADV8 TRV valve+order; CH-off keep latch; Decision C token.
- Evidence: test_hvac_app.py new/updated goldens; plan ADV8 boxes checked
- Open: code-review next-steps; ADV8 slice still in progress; dirty tree

## 18 — ADV8 done → example/tests slice

Session: unavailable · Timestamp: 2026-11-16T20:27:08+00:00

- Action: User accepted _run_demand/ADV8; presented example yaml + tests flame matrix.
- Result: Current block example/tests. Dirty tree still has ADV8 review patches uncommitted.
- Evidence: apps.yaml.example; test_config/test_hvac_app
- Open: Slice acceptance; commit ask

## 19 — Slice example/tests — Test

Session: unavailable · Timestamp: 2026-11-16T20:27:37+00:00

- Action: pytest config flame/example/legacy (20); hvac flame matrix (39); ruff apps/ha_smart_hvac tests; rg trip keys absent from example.
- Result: All pass; example flame keys present, no boiler_water/r_max/hold; ruff clean on Python packages.
- Evidence: test_config + test_hvac_app filters; apps.yaml.example L14-18
- Open: Slice acceptance; dirty tree

## 20 — example/tests done → Periphery

Session: unavailable · Timestamp: 2026-11-16T20:28:32+00:00

- Action: User accepted example/tests; presented Periphery.
- Result: Current block Periphery. Dirty tree still uncommitted.
- Evidence: deferred-work; plan; party memlog; walkthrough folder
- Open: Periphery acceptance; commit ask; then Wrap-up
