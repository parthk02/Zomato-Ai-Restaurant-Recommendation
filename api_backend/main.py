"""
FastAPI application exposing the Zomato AI recommendation pipeline.

Endpoints:
- GET  /health           : Basic health check.
- GET  /cities           : List of available cities in the dataset.
- POST /recommendations  : Full pipeline (Phases 2–5) with Groq LLM.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import List, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from phase1_data_ingestion.pipeline import build_phase1_store
from phase2_user_input.models import RawUserInput
from phase2_user_input.validation import InputNormalizer, InputValidator
from phase3_integration.repository import RestaurantRepository
from phase3_integration.service import RecommendationPreparationService
from phase4_recommendation.llm_client import GroqAPIClient
from phase4_recommendation.models import RecommendedRestaurant
from phase4_recommendation.service import (
    LLMRecommendationError,
    LLMRecommendationService,
)


app = FastAPI(title="Zomato AI Recommendation Service")

# Allow local frontends (e.g., file://, localhost) to call the API during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Startup: build dataset store and shared services ---

_STORE = build_phase1_store()


def _find_city_column(df: pd.DataFrame) -> Optional[str]:
    for col in df.columns:
        if str(col).strip().lower() == "city":
            return col
    return None


def _find_price_column(df: pd.DataFrame) -> Optional[str]:
    target = "approx_cost(for two people)"
    for col in df.columns:
        if str(col).strip().lower() == target.lower():
            return col
    return None


city_col = _find_city_column(_STORE.data)
if city_col is not None:
    _CITIES: List[str] = (
        _STORE.data[city_col]
        .dropna()
        .astype(str)
        .str.strip()
        .str.lower()
        .unique()
        .tolist()
    )
else:
    _CITIES = []

price_col = _find_price_column(_STORE.data)
if price_col is not None:
    _PRICE_MIN = float(_STORE.data[price_col].min())
    _PRICE_MAX = float(_STORE.data[price_col].max())
else:
    # Sensible defaults if column is missing.
    _PRICE_MIN = 100.0
    _PRICE_MAX = 3000.0

_validator = InputValidator(allowed_cities=_CITIES or None)
_normalizer = InputNormalizer()
_repository = RestaurantRepository(store=_STORE)
_prep_service = RecommendationPreparationService(
    repository=_repository, validator=_validator, normalizer=_normalizer
)


# --- Pydantic models ---


class RecommendationRequest(BaseModel):
    city: str = Field(..., description="City name, e.g., 'Bangalore'")
    price_text: Optional[str] = Field(
        None,
        description="Budget text: '800' or '500-1200'. Optional.",
        examples=["800", "500-1200"],
    )


class RecommendationError(BaseModel):
    field: str
    message: str


class RecommendationItem(BaseModel):
    name: str
    city: Optional[str] = None
    cuisines: Optional[str] = None
    price_for_two: Optional[float] = None
    rating: Optional[float] = None
    reason: Optional[str] = None


class RecommendationResponse(BaseModel):
    recommendations: List[RecommendationItem]


class ErrorResponse(BaseModel):
    errors: List[RecommendationError]


# --- Endpoints ---


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "restaurants_loaded": _STORE.count()}


@app.get("/cities")
def list_cities() -> dict:
    return {"cities": _CITIES}


@app.get("/price-range")
def get_price_range() -> dict:
    return {"min": _PRICE_MIN, "max": _PRICE_MAX}


@app.post(
    "/recommendations",
    response_model=RecommendationResponse,
    responses={400: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
def get_recommendations(payload: RecommendationRequest):
    # Phase 2–3: validate, normalize, and fetch candidates.
    raw = RawUserInput(city=payload.city, price_text=payload.price_text or "")
    prep_result = _prep_service.prepare(raw)

    if not prep_result.is_valid:
        raise HTTPException(
            status_code=400,
            detail=[
                {"field": err.field, "message": err.message}
                for err in prep_result.errors
            ],
        )

    assert prep_result.normalized_input is not None
    assert prep_result.candidates is not None

    if prep_result.candidates.empty:
        return RecommendationResponse(recommendations=[])

    # Phase 4: call Groq LLM via GroqAPIClient.
    try:
        llm_client = GroqAPIClient()  # expects GROQ_API_KEY to be set
    except ValueError as exc:
        raise HTTPException(
            status_code=503,
            detail=[{"field": "llm", "message": str(exc)}],
        ) from exc

    llm_service = LLMRecommendationService(llm_client=llm_client)
    try:
        recs: List[RecommendedRestaurant] = llm_service.recommend(
            prep_result.normalized_input, prep_result.candidates
        )
    except LLMRecommendationError as exc:
        raise HTTPException(
            status_code=502,
            detail=[{"field": "llm", "message": str(exc)}],
        ) from exc

    # Phase 5: convert to response DTOs.
    items = [RecommendationItem(**asdict(r)) for r in recs]
    return RecommendationResponse(recommendations=items)


