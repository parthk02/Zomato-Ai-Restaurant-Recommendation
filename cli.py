"""
End-to-end CLI entry point to exercise Phases 1–5.

Flow:
- Phase 1: load and clean the Zomato dataset into an in-memory store.
- Phase 2: collect, validate, and normalize user input (city + price).
- Phase 3: fetch candidate restaurants that match city and price.
- Phase 4: call the LLM (Groq) to score and describe recommendations.
- Phase 5: present recommendations nicely in the terminal.
"""

from __future__ import annotations

from typing import List, Sequence, Optional
import sys

from phase1_data_ingestion.pipeline import build_phase1_store
from phase2_user_input.cli_prompt import prompt_user_for_input
from phase2_user_input.validation import InputNormalizer, InputValidator
from phase3_integration.repository import RestaurantRepository
from phase3_integration.service import RecommendationPreparationService
from phase4_recommendation.llm_client import GroqAPIClient
from phase4_recommendation.service import LLMRecommendationService
from phase5_display.presenter import format_recommendations_text


def _find_city_column(df) -> Optional[str]:
    """
    Try to find a column that represents city, in a case-insensitive way.
    """
    for col in df.columns:
        if str(col).strip().lower() == "city":
            return col
    return None


def _build_validator_from_store() -> InputValidator:
    """
    Build an InputValidator using the list of cities present in the dataset.
    """
    store = build_phase1_store()
    if store.is_empty():
        # No data; validator will accept any city (not ideal, but safe).
        return InputValidator()

    city_col = _find_city_column(store.data)
    if city_col is None:
        # Fallback: no city column discovered, accept any city.
        return InputValidator()

    cities: List[str] = (
        store.data[city_col].dropna().astype(str).str.strip().str.lower().unique().tolist()
    )
    return InputValidator(allowed_cities=cities)


def _get_raw_input_from_args_or_prompt(argv: Sequence[str]):
    """
    If CLI args are provided, use them as input; otherwise, prompt.

    Usage:
      python cli.py <city> [price_text]
    """
    if len(argv) >= 1:
        city = argv[0]
        price_text = argv[1] if len(argv) >= 2 else ""
        from phase2_user_input.models import RawUserInput

        return RawUserInput(city=city, price_text=price_text)

    return prompt_user_for_input()


def main(argv: Sequence[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    print("Loading Zomato dataset (Phase 1)...")
    store = build_phase1_store()
    print(f"Loaded {store.count()} restaurants.\n")

    validator = _build_validator_from_store()
    normalizer = InputNormalizer()
    repository = RestaurantRepository(store=store)
    prep_service = RecommendationPreparationService(
        repository=repository, validator=validator, normalizer=normalizer
    )

    raw_input = _get_raw_input_from_args_or_prompt(argv)
    result = prep_service.prepare(raw_input)

    if not result.is_valid:
        print("\nThere were problems with your input:")
        for err in result.errors:
            print(f"- {err.field}: {err.message}")
        return

    assert result.normalized_input is not None
    assert result.candidates is not None
    candidates = result.candidates

    if candidates.empty:
        print("\nNo restaurants matched your criteria.")
        return

    # Phase 4 – call Groq LLM for recommendations.
    try:
        llm_client = GroqAPIClient()  # expects GROQ_API_KEY in environment
    except ValueError as exc:
        print(
            "\nGroq API key is not configured. "
            "Set the GROQ_API_KEY environment variable and try again."
        )
        print(f"Details: {exc}")
        return

    rec_service = LLMRecommendationService(llm_client=llm_client)
    recommendations = rec_service.recommend(result.normalized_input, candidates)

    # Phase 5 – present results.
    print()
    print(format_recommendations_text(recommendations))


if __name__ == "__main__":
    main()

