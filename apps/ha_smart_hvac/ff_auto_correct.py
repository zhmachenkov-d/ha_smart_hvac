"""CAP-7 rise-rate auto-correct — pure law, guards, and B1 JSON (no Hass)."""

from __future__ import annotations

import json
import math
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ha_smart_hvac.coordinator import select_max_error_demand_zone
from ha_smart_hvac.feedforward import weather_feedforward
from ha_smart_hvac.models import (
    AutoCorrectConfig,
    WeatherFeedforwardConfig,
    ZoneSnapshot,
)

STATE_FILENAME = "ff_auto_correct_state.json"

WINDOW_SIZE = 15
RATE_ERROR_DEADBAND = 0.10  # δ °C/h
MIN_STEADY_TICKS = 15
OUTDOOR_GATE_HYSTERESIS_K = 2.0
MAX_RATE_BASE = 0.1
MAX_RATE_SLOPE = 0.01
BASE_MIN, BASE_MAX = 15.0, 40.0
SLOPE_MIN, SLOPE_MAX = 0.5, 2.5

Knob = Literal["base", "slope"]


@dataclass(frozen=True)
class DemandTickResult:
    """Result of a non-flush-or-flush demand tick before the SWT write."""

    command: float
    params_changed: bool


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def params_in_bounds(base: float, slope: float) -> bool:
    return (
        math.isfinite(base)
        and math.isfinite(slope)
        and BASE_MIN <= base <= BASE_MAX
        and SLOPE_MIN <= slope <= SLOPE_MAX
    )


def load_ff_state(path: Path) -> tuple[float, float] | None:
    """Load B1 JSON; return (base, slope) if valid and in bounds, else None."""
    try:
        raw = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    if not isinstance(raw, dict):
        return None
    try:
        base = float(raw["base"])
        slope = float(raw["slope"])
    except (KeyError, TypeError, ValueError):
        return None
    if not params_in_bounds(base, slope):
        return None
    return base, slope


def save_ff_state(path: Path, base: float, slope: float) -> None:
    path.write_text(
        json.dumps({"base": base, "slope": slope, "version": 1}, indent=2) + "\n"
    )


class FfAutoCorrector:
    """Mutable runtime FF params + ephemeral rise-rate / I1 state."""

    def __init__(
        self,
        *,
        auto_correct: AutoCorrectConfig,
        control_interval: int,
        base: float,
        slope: float,
        comfort_ref: float,
        setpoint_min: float,
        setpoint_max: float,
    ) -> None:
        self.auto_correct = auto_correct
        self.control_interval = control_interval
        self.base = base
        self.slope = slope
        self.comfort_ref = comfort_ref
        self.setpoint_min = setpoint_min
        self.setpoint_max = setpoint_max
        self._window: deque[float] = deque(maxlen=WINDOW_SIZE)
        self._steady = 0
        self._previous: Knob | None = None
        self._selected_zone_id: str | None = None

    def clear_ephemeral(self) -> None:
        self._window.clear()
        self._steady = 0
        self._previous = None
        self._selected_zone_id = None

    def ff_config(self) -> WeatherFeedforwardConfig:
        """Throwaway FF config from runtime base/slope + yaml comfort_ref."""
        return WeatherFeedforwardConfig(
            base=self.base,
            slope=self.slope,
            comfort_ref=self.comfort_ref,
        )

    def clamp_uff(self, outdoor: float) -> float:
        u_ff = weather_feedforward(outdoor, self.ff_config())
        return clamp(u_ff, self.setpoint_min, self.setpoint_max)

    def _hold(self, outdoor: float) -> DemandTickResult:
        return DemandTickResult(
            command=self.clamp_uff(outdoor),
            params_changed=False,
        )

    def process_demand(
        self, zones: list[ZoneSnapshot], outdoor: float
    ) -> DemandTickResult:
        """Demand-path CAP-7 tick: may mutate base/slope; caller writes SWT + JSON."""
        if self._selected_zone_id is not None and not any(
            z.name == self._selected_zone_id for z in zones
        ):
            # 4A — previously selected zone absent from this tick's snapshots
            self.clear_ephemeral()
            return self._hold(outdoor)

        selected = select_max_error_demand_zone(zones, self._selected_zone_id)
        if selected is None:
            self.clear_ephemeral()
            return self._hold(outdoor)

        if not math.isfinite(selected.zone_temp):
            # M2
            self.clear_ephemeral()
            return self._hold(outdoor)

        if (
            self._selected_zone_id is not None
            and selected.name != self._selected_zone_id
        ):
            # Z1 — zone identity change
            self.clear_ephemeral()
            return self._hold(outdoor)

        # Non-flush: append W15 before freeze early-returns (1A)
        self._selected_zone_id = selected.name
        self._window.append(selected.zone_temp)
        self._steady += 1

        knob = self._evaluate_i1(outdoor)

        if self._steady < MIN_STEADY_TICKS:
            return self._hold(outdoor)
        if len(self._window) < WINDOW_SIZE:
            return self._hold(outdoor)
        if abs(selected.zone_error) < self.auto_correct.near_setpoint_eps_k:
            return self._hold(outdoor)

        r_obs = self._r_obs()
        e_r = r_obs - self.auto_correct.r_expected_c_per_h
        if abs(e_r) <= RATE_ERROR_DEADBAND:
            return self._hold(outdoor)

        # W-skip: freeze slope only when (comfort_ref − T_out) ≤ 0
        if (self.comfort_ref - outdoor) <= 0 and knob == "slope":
            return self._hold(outdoor)

        u = clamp(
            (self.auto_correct.r_expected_c_per_h - r_obs)
            / self.auto_correct.e_sat_c_per_h,
            -1.0,
            1.0,
        )
        max_rate = MAX_RATE_BASE if knob == "base" else MAX_RATE_SLOPE
        delta = u * max_rate

        pre_cmd = self.clamp_uff(outdoor)
        du_ff = delta if knob == "base" else delta * (self.comfort_ref - outdoor)
        if du_ff > 0 and pre_cmd >= self.setpoint_max:
            return DemandTickResult(command=pre_cmd, params_changed=False)
        if du_ff < 0 and pre_cmd <= self.setpoint_min:
            return DemandTickResult(command=pre_cmd, params_changed=False)

        old_base, old_slope = self.base, self.slope
        if knob == "base":
            self.base = clamp(self.base + delta, BASE_MIN, BASE_MAX)
        else:
            self.slope = clamp(self.slope + delta, SLOPE_MIN, SLOPE_MAX)

        params_changed = self.base != old_base or self.slope != old_slope
        return DemandTickResult(
            command=self.clamp_uff(outdoor),
            params_changed=params_changed,
        )

    def _evaluate_i1(self, outdoor: float) -> Knob:
        """CS-base then hysteresis same tick; advances ``previous`` (3C)."""
        d = abs(outdoor - self.comfort_ref)
        gate = self.auto_correct.outdoor_gate_delta_k
        if self._previous is None:
            self._previous = "base"
        if d >= gate + OUTDOOR_GATE_HYSTERESIS_K:
            self._previous = "slope"
        elif d <= gate - OUTDOOR_GATE_HYSTERESIS_K:
            self._previous = "base"
        return self._previous

    def _r_obs(self) -> float:
        t_start = self._window[0]
        t_now = self._window[-1]
        hours = WINDOW_SIZE * self.control_interval / 3600.0
        return (t_now - t_start) / hours
