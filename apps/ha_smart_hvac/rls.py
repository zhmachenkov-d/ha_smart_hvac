"""ARX + forgetting RLS with IMC map for adaptive Kp/Ki."""

from __future__ import annotations

import json
import logging
import math
import os
from dataclasses import dataclass, field
from pathlib import Path

LAMBDA = 0.98
P0 = 1e4
EPS = 1e-9

STATE_FILENAME = "rls_state.json"
MAX_STATE_BYTES = 64 * 1024

_LOG = logging.getLogger(__name__)


@dataclass
class RlsState:
    """In-memory RLS bookkeeping; survives PID ephemeral clears except y_prev."""

    theta: list[float] = field(default_factory=lambda: [0.0, 0.0])  # [a1, b0]
    p: list[list[float]] = field(default_factory=lambda: [[P0, 0.0], [0.0, P0]])
    y_prev: float | None = None
    last_u: float | None = None
    adapted_kp: float | None = None
    adapted_ki: float | None = None


@dataclass(frozen=True)
class RlsDurableSnapshot:
    """Deep-copied durable fields for dirty compare and JSON I/O."""

    theta: list[float]
    p: list[list[float]]
    last_u: float | None
    adapted_kp: float | None
    adapted_ki: float | None
    adapted_issue: str | None = None  # missing | non_finite | mismatch (load only)


def copy_durable(state: RlsState) -> RlsDurableSnapshot:
    """Deep-copy durable fields; never share list refs with ``state``."""
    return RlsDurableSnapshot(
        theta=[state.theta[0], state.theta[1]],
        p=[[state.p[0][0], state.p[0][1]], [state.p[1][0], state.p[1][1]]],
        last_u=state.last_u,
        adapted_kp=state.adapted_kp,
        adapted_ki=state.adapted_ki,
    )


def durable_equal(a: RlsDurableSnapshot, b: RlsDurableSnapshot) -> bool:
    """Field equality on durable snapshot (ignores ``adapted_issue``)."""
    return (
        a.theta == b.theta
        and a.p == b.p
        and a.last_u == b.last_u
        and a.adapted_kp == b.adapted_kp
        and a.adapted_ki == b.adapted_ki
    )


def rls_step(state: RlsState, *, y: float, y_prev: float, u_prev: float) -> bool:
    """One forgetting-RLS update; mutates ``state.theta`` and ``state.p``.

    Returns True when θ/P were committed. Leaves ``theta``/``p`` unchanged and
    returns False when denom is unusable or the update would produce non-finite
    values (no mid-tick poison / ZeroDivisionError).
    """
    phi = [y_prev, u_prev]
    theta = state.theta
    p = state.p
    lam = LAMBDA

    p_phi = [
        p[0][0] * phi[0] + p[0][1] * phi[1],
        p[1][0] * phi[0] + p[1][1] * phi[1],
    ]
    denom = lam + phi[0] * p_phi[0] + phi[1] * p_phi[1]
    if not math.isfinite(denom) or abs(denom) <= EPS:
        return False
    k = [p_phi[0] / denom, p_phi[1] / denom]
    e = y - (phi[0] * theta[0] + phi[1] * theta[1])
    new_theta = [theta[0] + k[0] * e, theta[1] + k[1] * e]
    # P ← (P − K φᵀ P) / λ; φᵀP = (Pφ)ᵀ when P is symmetric
    new_p = [
        [(p[0][0] - k[0] * p_phi[0]) / lam, (p[0][1] - k[0] * p_phi[1]) / lam],
        [(p[1][0] - k[1] * p_phi[0]) / lam, (p[1][1] - k[1] * p_phi[1]) / lam],
    ]
    if not all(math.isfinite(v) for v in new_theta):
        return False
    if not all(math.isfinite(v) for row in new_p for v in row):
        return False
    theta[0], theta[1] = new_theta
    p[0][0], p[0][1] = new_p[0]
    p[1][0], p[1][1] = new_p[1]
    return True


def gains_within_rails(
    kp: float,
    ki: float,
    kp_min: float,
    kp_max: float,
    ki_min: float,
    ki_max: float,
) -> bool:
    """Inclusive band check for adapted kp/ki proposals."""
    return kp_min <= kp <= kp_max and ki_min <= ki <= ki_max


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


def _coerce_finite_float(value: object) -> float | None:
    """Coerce a JSON number (int/float) to a finite float; reject bools."""
    # bool is a subclass of int — reject before the int/float allow-list.
    if type(value) is bool or type(value) not in (int, float):
        return None
    try:
        out = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(out):
        return None
    return out


def _finite_pair(values: object) -> list[float] | None:
    if not isinstance(values, list) or len(values) != 2:
        return None
    a = _coerce_finite_float(values[0])
    b = _coerce_finite_float(values[1])
    if a is None or b is None:
        return None
    return [a, b]


def _parse_adapted(
    raw: dict,
) -> tuple[float | None, float | None, str | None]:
    """Return (kp, ki, issue). issue is set when adapted must be dropped."""
    has_kp = "adapted_kp" in raw
    has_ki = "adapted_ki" in raw
    if not has_kp or not has_ki:
        return None, None, "missing"

    kp_raw = raw["adapted_kp"]
    ki_raw = raw["adapted_ki"]
    if kp_raw is None and ki_raw is None:
        return None, None, None
    if kp_raw is None or ki_raw is None:
        return None, None, "mismatch"
    kp = _coerce_finite_float(kp_raw)
    ki = _coerce_finite_float(ki_raw)
    if kp is None or ki is None:
        return None, None, "non_finite"
    return kp, ki, None


def load_rls_state(path: Path) -> RlsDurableSnapshot | None:
    """Load durable RLS JSON; None on missing/unusable whole file."""
    try:
        if path.stat().st_size > MAX_STATE_BYTES:
            return None
        data = path.read_bytes()
    except OSError:
        return None
    if len(data) > MAX_STATE_BYTES:
        return None
    try:
        raw = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(raw, dict):
        return None

    version = raw.get("version")
    if type(version) is not int or version != 1:
        return None
    if "last_u" not in raw:
        return None

    theta = _finite_pair(raw.get("theta"))
    if theta is None:
        return None
    p_raw = raw.get("p")
    if not isinstance(p_raw, list) or len(p_raw) != 2:
        return None
    p0 = _finite_pair(p_raw[0])
    p1 = _finite_pair(p_raw[1])
    if p0 is None or p1 is None:
        return None

    last_u_raw = raw["last_u"]
    if last_u_raw is None:
        last_u: float | None = None
    else:
        last_u = _coerce_finite_float(last_u_raw)
        if last_u is None:
            return None

    adapted_kp, adapted_ki, adapted_issue = _parse_adapted(raw)
    return RlsDurableSnapshot(
        theta=theta,
        p=[p0, p1],
        last_u=last_u,
        adapted_kp=adapted_kp,
        adapted_ki=adapted_ki,
        adapted_issue=adapted_issue,
    )


def durable_fields_savable(state: RlsState) -> bool:
    if not all(math.isfinite(v) for v in state.theta):
        return False
    if not all(math.isfinite(v) for row in state.p for v in row):
        return False
    if state.last_u is not None and not math.isfinite(state.last_u):
        return False
    kp, ki = state.adapted_kp, state.adapted_ki
    if (kp is None) ^ (ki is None):
        return False
    if kp is not None and (not math.isfinite(kp) or not math.isfinite(ki)):  # type: ignore[arg-type]
        return False
    return True


def save_rls_state(path: Path, state: RlsState) -> bool:
    """Atomically write durable RLS JSON. False on validation or OSError."""
    if not durable_fields_savable(state):
        return False
    payload = (
        json.dumps(
            {
                "version": 1,
                "theta": [float(state.theta[0]), float(state.theta[1])],
                "p": [
                    [float(state.p[0][0]), float(state.p[0][1])],
                    [float(state.p[1][0]), float(state.p[1][1])],
                ],
                "last_u": None if state.last_u is None else float(state.last_u),
                "adapted_kp": (
                    None if state.adapted_kp is None else float(state.adapted_kp)
                ),
                "adapted_ki": (
                    None if state.adapted_ki is None else float(state.adapted_ki)
                ),
            },
            indent=2,
        )
        + "\n"
    )
    tmp = path.with_name(path.name + ".tmp")
    try:
        tmp.write_text(payload, encoding="utf-8")
        os.replace(tmp, path)
        return True
    except OSError:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            _LOG.warning("RLS state tmp may remain after save failure: %s", tmp)
        return False
