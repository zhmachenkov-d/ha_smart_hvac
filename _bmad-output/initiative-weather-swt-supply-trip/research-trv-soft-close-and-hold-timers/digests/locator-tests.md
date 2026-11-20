# Locator digest — area `tests/` @ 2ec1908

## 1 — TRV writes
- `tests/test_hvac_app.py:2106-2147` — floor, overshoot, latch, clear, plant-off
- `tests/test_hvac_app.py:2263` — floor override
- `tests/test_config.py:48,511` — floor defaults/override

## 2 — commission + accuracy listeners
- `tests/test_config.py:536,600` — commissioned mapping; reject partial
- `tests/test_hvac_app.py:2294,2338-2339` — listen accuracy→control_event; no closure listener
- `tests/test_hvac_app.py:2425` — accuracy state change reapplies law

## 3 — flame hold
- `tests/test_hvac_app.py:1080-1156` — latch, schedule, expiry e2e
- `tests/test_hvac_app.py:1516,1581,1595,1617,1923` — cancel/orphan/disarm
- `tests/test_config.py:126-331` — flame hold yaml parse

## 4 — how tested
- Primary: `tests/test_hvac_app.py` test_trv_* and flame hold suite
- Config: `tests/test_config.py` floor + flame + thermostat mapping

## 5 — accuracy in tests
- Reject closure-only / accuracy-only; abs(accuracy) overshoot tests

## 6 — spies
- `_apply_trv_law` spies in hold-expiry and outdoor-fail/empty-zone tests
- `_trv_overshoot_latched` asserted throughout test_trv_*
