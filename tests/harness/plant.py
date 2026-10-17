"""Discrete cascade lag plant K/(Ts+1)^n (Euler @ dt)."""

from __future__ import annotations


class CascadeLagPlant:
    """Cascade first-order lags; y is the last state."""

    def __init__(self, K: float, T: float, n: int, dt: float, y0: float = 0.0) -> None:
        if n < 1:
            raise ValueError("n must be >= 1")
        if T <= 0.0:
            raise ValueError("T must be > 0")
        if dt <= 0.0:
            raise ValueError("dt must be > 0")
        self.K = K
        self.T = T
        self.n = n
        self.dt = dt
        self._x = [y0] * n

    @property
    def y(self) -> float:
        return self._x[-1]

    def step(self, u: float) -> float:
        """One forward-Euler sample; returns new y."""
        x = self._x
        new_x = [0.0] * self.n
        new_x[0] = x[0] + self.dt * (self.K * u - x[0]) / self.T
        for i in range(1, self.n):
            new_x[i] = x[i] + self.dt * (x[i - 1] - x[i]) / self.T
        self._x = new_x
        return self.y
