"""Golden ARX+RLS step and IMC map guards."""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from unittest.mock import patch

import pytest

from ha_smart_hvac.rls import (
    EPS,
    LAMBDA,
    MAX_STATE_BYTES,
    P0,
    RlsState,
    copy_durable,
    durable_equal,
    gains_within_rails,
    imc_gains,
    load_rls_state,
    rls_step,
    save_rls_state,
)


def test_rls_state_cold_start_defaults() -> None:
    state = RlsState()
    assert state.theta == [0.0, 0.0]
    assert state.p == [[P0, 0.0], [0.0, P0]]
    assert state.y_prev is None
    assert state.last_u is None
    assert state.adapted_kp is None
    assert state.adapted_ki is None


def test_rls_golden_first_step_from_zero_theta() -> None:
    """Hand-checked forgetting-RLS update from Design Notes equations."""
    state = RlsState()
    y_prev, u_prev, y = 50.0, 45.0, 51.0
    phi = [y_prev, u_prev]
    p_phi = [P0 * phi[0], P0 * phi[1]]
    denom = LAMBDA + phi[0] * p_phi[0] + phi[1] * p_phi[1]
    k = [p_phi[0] / denom, p_phi[1] / denom]
    e = y  # θ₀ = 0
    expected_theta = [k[0] * e, k[1] * e]
    expected_p = [
        [(P0 - k[0] * p_phi[0]) / LAMBDA, (0.0 - k[0] * p_phi[1]) / LAMBDA],
        [(0.0 - k[1] * p_phi[0]) / LAMBDA, (P0 - k[1] * p_phi[1]) / LAMBDA],
    ]

    assert rls_step(state, y=y, y_prev=y_prev, u_prev=u_prev) is True

    assert state.theta[0] == pytest.approx(expected_theta[0])
    assert state.theta[1] == pytest.approx(expected_theta[1])
    assert state.p[0][0] == pytest.approx(expected_p[0][0])
    assert state.p[0][1] == pytest.approx(expected_p[0][1])
    assert state.p[1][0] == pytest.approx(expected_p[1][0])
    assert state.p[1][1] == pytest.approx(expected_p[1][1])


def test_imc_gains_valid_arx() -> None:
    a1, b0, ts = 0.9, 0.1, 300.0
    gains = imc_gains(a1, b0, ts)
    assert gains is not None
    kp, ki = gains
    tau = -ts / math.log(a1)
    assert kp == pytest.approx((1.0 - a1) / b0)
    assert ki == pytest.approx(kp * 3600.0 / tau)


@pytest.mark.parametrize(
    ("a1", "b0", "ts"),
    [
        (0.0, 0.1, 300.0),
        (1.0, 0.1, 300.0),
        (-0.1, 0.1, 300.0),
        (1.1, 0.1, 300.0),
        (0.9, 0.0, 300.0),
        (0.9, EPS, 300.0),
        (0.9, -0.1, 300.0),  # K < 0
        (0.9, 0.1, 0.0),
        (0.9, 0.1, -1.0),
        (1.0 - EPS / 2, 0.1, 300.0),  # |1−a1|≤eps inside (0,1)
    ],
)
def test_imc_gains_rejects_invalid(a1: float, b0: float, ts: float) -> None:
    assert imc_gains(a1, b0, ts) is None


def test_rls_step_skips_when_denom_unusable() -> None:
    """Zero/near-zero denom must not mutate θ/P (no ZeroDivision / poison)."""
    state = RlsState()
    state.theta = [0.5, 0.2]
    state.p = [[0.0, 0.0], [0.0, 0.0]]  # φᵀPφ = 0 → denom = λ only is fine…
    # Force denom ≤ EPS: P such that φᵀPφ = −λ (with φ=[1,0]).
    state.p = [[-LAMBDA, 0.0], [0.0, 0.0]]
    before_theta = state.theta[:]
    before_p = [row[:] for row in state.p]

    assert rls_step(state, y=1.0, y_prev=1.0, u_prev=0.0) is False

    assert state.theta == before_theta
    assert state.p == before_p


@pytest.mark.parametrize(
    ("kp", "ki", "expected"),
    [
        (1.0, 2.0, True),  # interior
        (0.0, 0.0, True),  # inclusive mins
        (10.0, 100.0, True),  # inclusive maxes
        (-0.1, 2.0, False),
        (10.1, 2.0, False),
        (1.0, -0.1, False),
        (1.0, 100.1, False),
    ],
)
def test_gains_within_rails(kp: float, ki: float, expected: bool) -> None:
    assert (
        gains_within_rails(kp, ki, kp_min=0.0, kp_max=10.0, ki_min=0.0, ki_max=100.0)
        is expected
    )


def test_gains_within_rails_min_eq_max() -> None:
    assert gains_within_rails(2.0, 3.0, 2.0, 2.0, 3.0, 3.0) is True
    assert gains_within_rails(2.1, 3.0, 2.0, 2.0, 3.0, 3.0) is False


def _filled_state() -> RlsState:
    state = RlsState()
    state.theta = [0.9, 0.1]
    state.p = [[1.0, 0.2], [0.2, 3.0]]
    state.last_u = 45.0
    state.adapted_kp = 1.5
    state.adapted_ki = 12.0
    state.y_prev = 50.0  # ephemeral; must not round-trip
    return state


def test_save_load_field_equality(tmp_path: Path) -> None:
    path = tmp_path / "rls_state.json"
    state = _filled_state()
    assert save_rls_state(path, state) is True
    loaded = load_rls_state(path)
    assert loaded is not None
    assert durable_equal(loaded, copy_durable(state))
    assert loaded.adapted_issue is None
    assert not path.with_name(path.name + ".tmp").exists()


def test_save_load_null_adapted_and_last_u(tmp_path: Path) -> None:
    path = tmp_path / "rls_state.json"
    state = RlsState()
    state.theta = [0.8, 0.2]
    state.p = [[2.0, 0.0], [0.0, 2.0]]
    assert save_rls_state(path, state) is True
    loaded = load_rls_state(path)
    assert loaded is not None
    assert loaded.last_u is None
    assert loaded.adapted_kp is None
    assert loaded.adapted_ki is None


def test_load_ignores_unknown_keys_and_coerces_ints(tmp_path: Path) -> None:
    path = tmp_path / "rls_state.json"
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "theta": [1, 0],
                "p": [[1, 0], [0, 1]],
                "last_u": 42,
                "adapted_kp": 2,
                "adapted_ki": 3,
                "extra": "ignored",
                "y_prev": 99.0,
            }
        ),
        encoding="utf-8",
    )
    loaded = load_rls_state(path)
    assert loaded is not None
    assert loaded.theta == [1.0, 0.0]
    assert loaded.p == [[1.0, 0.0], [0.0, 1.0]]
    assert loaded.last_u == 42.0
    assert loaded.adapted_kp == 2.0
    assert loaded.adapted_ki == 3.0
    assert loaded.adapted_issue is None


def _bad_payloads() -> list[str]:
    base = {"theta": [0.9, 0.1], "p": [[1, 0], [0, 1]], "last_u": None}
    return [
        "{not json",
        json.dumps({"version": 2, **base}),
        json.dumps({"version": 1.0, **base}),
        json.dumps(base),  # missing version
        json.dumps({"version": 1, "theta": [0.9, 0.1], "p": [[1, 0], [0, 1]]}),
        json.dumps(
            {"version": 1, "theta": [0.9], "p": [[1, 0], [0, 1]], "last_u": None}
        ),
        json.dumps(
            {
                "version": 1,
                "theta": [0.9, float("nan")],
                "p": [[1, 0], [0, 1]],
                "last_u": None,
            }
        ),
        json.dumps(
            {
                "version": 1,
                "theta": [0.9, 0.1],
                "p": [[1, 0], [0, 1]],
                "last_u": float("nan"),
            }
        ),
        json.dumps(
            {
                "version": 1,
                "theta": [0.9, 0.1],
                "p": [[1, 0], [0, 1]],
                "last_u": float("inf"),
            }
        ),
        json.dumps(
            {
                "version": 1,
                "theta": [True, 0.1],
                "p": [[1, 0], [0, 1]],
                "last_u": None,
            }
        ),
        json.dumps(
            {
                "version": 1,
                "theta": [0.9, 0.1],
                "p": [[1, 0], [0, 1]],
                "last_u": True,
            }
        ),
        '{"version": 1, "theta": ['
        + "1" * 400
        + ', 0.1], "p": [[1, 0], [0, 1]], "last_u": null}',
    ]


@pytest.mark.parametrize("payload", _bad_payloads())
def test_load_corrupt_or_bad_shape_returns_none(tmp_path: Path, payload: str) -> None:
    path = tmp_path / "rls_state.json"
    path.write_text(payload, encoding="utf-8")
    assert load_rls_state(path) is None


def test_load_oversize_returns_none(tmp_path: Path) -> None:
    path = tmp_path / "rls_state.json"
    path.write_bytes(b"{" + b"x" * (MAX_STATE_BYTES) + b"}")
    assert load_rls_state(path) is None


def test_load_missing_returns_none(tmp_path: Path) -> None:
    assert load_rls_state(tmp_path / "missing.json") is None


def test_load_adapted_missing_sets_issue(tmp_path: Path) -> None:
    path = tmp_path / "rls_state.json"
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "theta": [0.9, 0.1],
                "p": [[1.0, 0.0], [0.0, 1.0]],
                "last_u": None,
            }
        ),
        encoding="utf-8",
    )
    loaded = load_rls_state(path)
    assert loaded is not None
    assert loaded.adapted_issue == "missing"
    assert loaded.adapted_kp is None
    assert loaded.adapted_ki is None


def test_load_adapted_mismatch_sets_issue(tmp_path: Path) -> None:
    path = tmp_path / "rls_state.json"
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "theta": [0.9, 0.1],
                "p": [[1.0, 0.0], [0.0, 1.0]],
                "last_u": 1.0,
                "adapted_kp": 2.0,
                "adapted_ki": None,
            }
        ),
        encoding="utf-8",
    )
    loaded = load_rls_state(path)
    assert loaded is not None
    assert loaded.adapted_issue == "mismatch"


def test_load_adapted_non_finite_sets_issue(tmp_path: Path) -> None:
    path = tmp_path / "rls_state.json"
    path.write_text(
        '{"version": 1, "theta": [0.9, 0.1], "p": [[1, 0], [0, 1]],'
        ' "last_u": null, "adapted_kp": NaN, "adapted_ki": 1.0}',
        encoding="utf-8",
    )
    loaded = load_rls_state(path)
    assert loaded is not None
    assert loaded.adapted_issue == "non_finite"


def test_save_oserror_returns_false_tmp_absent(tmp_path: Path) -> None:
    path = tmp_path / "rls_state.json"
    tmp_path.chmod(0o555)
    try:
        assert save_rls_state(path, _filled_state()) is False
        assert not path.exists()
        assert not path.with_name(path.name + ".tmp").exists()
    finally:
        tmp_path.chmod(0o755)


def test_save_unlink_failure_logs_warning(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    path = tmp_path / "rls_state.json"
    state = _filled_state()

    with (
        patch("ha_smart_hvac.rls.os.replace", side_effect=OSError("replace failed")),
        patch("pathlib.Path.unlink", side_effect=OSError("unlink failed")),
        caplog.at_level(logging.WARNING, logger="ha_smart_hvac.rls"),
    ):
        assert save_rls_state(path, state) is False
    assert any("tmp may remain" in r.message for r in caplog.records)


def test_save_rejects_non_finite_and_mismatched_adapted(tmp_path: Path) -> None:
    path = tmp_path / "rls_state.json"
    bad_theta = RlsState()
    bad_theta.theta = [float("nan"), 0.1]
    assert save_rls_state(path, bad_theta) is False
    assert not path.exists()

    mismatch = RlsState()
    mismatch.adapted_kp = 1.0
    mismatch.adapted_ki = None
    assert save_rls_state(path, mismatch) is False
    assert not path.exists()

    bad_last_u = RlsState()
    bad_last_u.last_u = float("nan")
    assert save_rls_state(path, bad_last_u) is False
    assert not path.exists()

    bad_last_u_inf = RlsState()
    bad_last_u_inf.last_u = float("inf")
    assert save_rls_state(path, bad_last_u_inf) is False
    assert not path.exists()


def test_load_adapted_bool_sets_non_finite_issue(tmp_path: Path) -> None:
    path = tmp_path / "rls_state.json"
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "theta": [0.9, 0.1],
                "p": [[1.0, 0.0], [0.0, 1.0]],
                "last_u": None,
                "adapted_kp": True,
                "adapted_ki": 1.0,
            }
        ),
        encoding="utf-8",
    )
    loaded = load_rls_state(path)
    assert loaded is not None
    assert loaded.adapted_issue == "non_finite"
    assert loaded.adapted_kp is None
    assert loaded.adapted_ki is None


def test_copy_durable_does_not_share_lists() -> None:
    state = _filled_state()
    snap = copy_durable(state)
    state.theta[0] = 0.0
    state.p[0][0] = 0.0
    assert snap.theta[0] == 0.9
    assert snap.p[0][0] == 1.0
