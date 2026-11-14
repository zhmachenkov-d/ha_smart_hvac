"""Tests for weather feedforward."""

import pytest

from ha_smart_hvac.feedforward import clamp, quantize_command, weather_feedforward
from ha_smart_hvac.models import WeatherFeedforwardConfig


@pytest.mark.parametrize(
    "value,expected",
    [(39.9, 40.0), (40.0, 40.0), (47.5, 47.5), (55.0, 55.0), (55.1, 55.0)],
)
def test_clamp_bounds(value: float, expected: float) -> None:
    assert clamp(value, 40.0, 55.0) == expected


@pytest.mark.parametrize(
    ("raw", "lo", "hi", "expected"),
    [
        (60.0, 40.0, 55.06, 55.0),  # max with 2 decimals → ≤ hi
        (30.0, 42.04, 55.0, 42.1),  # min with 2 decimals → ≥ lo
        (41.96, 40.0, 55.0, 42.0),  # on-grid bounds unchanged
        (55.03, 55.01, 55.06, 55.03),  # no grid point → clamp(raw) off-grid
    ],
)
def test_quantize_command_grid_snap(
    raw: float, lo: float, hi: float, expected: float
) -> None:
    assert quantize_command(raw, lo, hi) == pytest.approx(expected)


def test_linear_formula() -> None:
    config = WeatherFeedforwardConfig(base=25, slope=1.2, comfort_ref=20)
    # u_ff = 25 + 1.2 * (20 - outdoor)
    assert weather_feedforward(0.0, config) == 25 + 1.2 * 20
    assert weather_feedforward(20.0, config) == 25.0
    assert weather_feedforward(10.0, config) == 25 + 1.2 * 10


def test_commission_defaults_formula() -> None:
    config = WeatherFeedforwardConfig()
    # defaults base=37, slope=0.9, comfort_ref=20
    assert weather_feedforward(10.0, config) == 37 + 0.9 * 10
    assert weather_feedforward(10.0, config) == 46.0
    assert weather_feedforward(20.0, config) == 37.0


def test_negative_slope_allowed() -> None:
    config = WeatherFeedforwardConfig(base=40, slope=-0.5, comfort_ref=20)
    assert weather_feedforward(10.0, config) == 40 + (-0.5) * 10
