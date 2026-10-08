"""Conversions for the UniFi Protect floodlight LED level (1-6)."""

from __future__ import annotations

from typing import Any

MIN_LED_LEVEL = 1
MAX_LED_LEVEL = 6


def valid_led_level(value: Any) -> int | None:
    """
    Return a Protect ``ledLevel`` as an int, or None if it is not 1-6.

    The API spec types ``ledLevel`` as a number, so a whole-number float such
    as ``3.0`` is accepted. Booleans, fractions and out-of-range values are not.

    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if isinstance(value, float) and not value.is_integer():
        return None
    level = int(value)
    if MIN_LED_LEVEL <= level <= MAX_LED_LEVEL:
        return level
    return None


def percent_to_led_level(percent: float) -> int:
    """Convert a 0-100 brightness percentage to a Protect LED level (1-6)."""
    return max(MIN_LED_LEVEL, min(MAX_LED_LEVEL, round(percent * MAX_LED_LEVEL / 100)))


def led_level_to_percent(level: Any) -> int | None:
    """Convert a Protect LED level (1-6) to a 0-100 percentage, or None."""
    led_level = valid_led_level(level)
    if led_level is None:
        return None
    return round(led_level * 100 / MAX_LED_LEVEL)
