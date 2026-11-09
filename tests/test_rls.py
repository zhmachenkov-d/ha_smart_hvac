"""Golden ARX+RLS step and IMC map guards."""

from __future__ import annotations

import math

import pytest

from ha_smart_hvac.rls import (
    EPS,
    LAMBDA,
    P0,
    RlsState,
    gains_within_rails,
    imc_gains,
    rls_step,
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
