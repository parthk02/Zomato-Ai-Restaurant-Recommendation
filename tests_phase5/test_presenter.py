"""
Tests for Phase 5 presenter formatting logic.
"""

from __future__ import annotations

from phase4_recommendation.models import RecommendedRestaurant
from phase5_display.presenter import format_recommendations_text


def test_presenter_handles_no_recommendations() -> None:
    text = format_recommendations_text([])
    assert "No recommendations" in text


def test_presenter_formats_single_recommendation() -> None:
    rec = RecommendedRestaurant(
        name="Test Place",
        city="bangalore",
        cuisines="Indian, Chinese",
        price_for_two=800.0,
        rating=4.5,
        reason="Matches your budget and rating preferences.",
    )

    text = format_recommendations_text([rec])

    assert "1. Test Place (bangalore)" in text
    assert "price_for_two=800" in text
    assert "rating=4.5" in text
    assert "Cuisines: Indian, Chinese" in text
    assert "Reason: Matches your budget and rating preferences." in text


def test_presenter_limits_max_items() -> None:
    recs = [
        RecommendedRestaurant(name=f"Place {i}") for i in range(1, 6)
    ]

    text = format_recommendations_text(recs, max_items=3)

    # Should only list first 3 items.
    assert "1. Place 1" in text
    assert "2. Place 2" in text
    assert "3. Place 3" in text
    assert "4. Place 4" not in text

