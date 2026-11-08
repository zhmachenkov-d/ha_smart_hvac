"""ARX + forgetting RLS with IMC map for adaptive Kp/Ki (in-memory)."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

LAMBDA = 0.98
P0 = 1e4
EPS = 1e-9


@dataclass
class RlsState:
    """In-memory RLS bookkeeping; survives PID ephemeral clears except y_prev."""

    theta: list[float] = field(default_factory=lambda: [0.0, 0.0])  # [a1, b0]
    p: list[list[float]] = field(default_factory=lambda: [[P0, 0.0], [0.0, P0]])
    y_prev: float | None = None
    last_u: float | None = None
    adapted_kp: float | None = None
    adapted_ki: float | None = None


def rls_step(state: RlsState, *, y: float, y_prev: float, u_prev: float) -> None:
    """One forgetting-RLS update; mutates ``state.theta`` and ``state.p``."""
    phi = [y_prev, u_prev]
    theta = state.theta
    p = state.p
    lam = LAMBDA

    p_phi = [
        p[0][0] * phi[0] + p[0][1] * phi[1],
        p[1][0] * phi[0] + p[1][1] * phi[1],
    ]
    denom = lam + phi[0] * p_phi[0] + phi[1] * p_phi[1]
    k = [p_phi[0] / denom, p_phi[1] / denom]
    e = y - (phi[0] * theta[0] + phi[1] * theta[1])
    theta[0] += k[0] * e
    theta[1] += k[1] * e
    # P ← (P − K φᵀ P) / λ; φᵀP = (Pφ)ᵀ when P is symmetric
    for i in range(2):
        for j in range(2):
            p[i][j] = (p[i][j] - k[i] * p_phi[j]) / lam


def imc_gains(a1: float, b0: float, ts: float) -> tuple[float, float] | None:
    """Map ARX ``(a1, b0)`` to ``(kp, ki)``; None when the map is invalid."""
    if not (0.0 < a1 < 1.0):
        return None
    if abs(b0) <= EPS or abs(1.0 - a1) <= EPS or ts <= 0.0:
        return None
    plant_k = b0 / (1.0 - a1)
    if plant_k <= 0.0:
        return None
    tau = -ts / math.log(a1)
    if tau <= EPS:
        return None
    kp = (1.0 - a1) / b0  # ≡ τ / (K · λc) with λc = τ
    ki = kp * 3600.0 / tau
    if not (math.isfinite(kp) and math.isfinite(ki)):
        return None
    return kp, ki
