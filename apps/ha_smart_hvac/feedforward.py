"""Outdoor-temperature weather feedforward."""

from __future__ import annotations

from ha_smart_hvac.models import WeatherFeedforwardConfig


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def quantize_command(raw: float, lo: float, hi: float) -> float:
    """Snap clamp(raw) to the 0.1 °C grid inside [lo, hi]; else clamp(raw)."""
    c = round(clamp(raw, lo, hi), 1)
    if c > hi:
        c = round(c - 0.1, 1)
    if c < lo:
        c = round(c + 0.1, 1)
    if c < lo or c > hi:
        return clamp(raw, lo, hi)
    return c


def weather_feedforward(outdoor_temp: float, config: WeatherFeedforwardConfig) -> float:
    """Linear baseline water setpoint from outdoor temperature."""
    return config.base + config.slope * (config.comfort_ref - outdoor_temp)
