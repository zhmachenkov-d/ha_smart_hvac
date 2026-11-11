"""Outdoor-temperature weather feedforward."""

from __future__ import annotations

from ha_smart_hvac.models import WeatherFeedforwardConfig


def weather_feedforward(outdoor_temp: float, config: WeatherFeedforwardConfig) -> float:
    """Linear baseline water setpoint from outdoor temperature."""
    return config.base + config.slope * (config.comfort_ref - outdoor_temp)
