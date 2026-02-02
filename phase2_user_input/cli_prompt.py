"""
CLI helper for collecting user input (Phase 2).

This module keeps all direct `input()` calls isolated, so validation and
normalization remain easily testable in pure functions.
"""

from __future__ import annotations

from typing import Optional

from .models import RawUserInput


def prompt_user_for_input() -> RawUserInput:
    """
    Prompt the user for city and price information via CLI.

    Returns:
        RawUserInput with unvalidated, unnormalized strings.
    """
    city = input("Enter city: ").strip()
    price_text = input(
        "Enter your budget (number like 800, or range like 500-1200). Leave blank for no preference: "
    ).strip()

    return RawUserInput(city=city, price_text=price_text)

