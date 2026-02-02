## Zomato AI Restaurant Recommendation System

AI-powered restaurant recommendation system built on top of the `ManikaSaini/zomato-restaurant-recommendation` dataset, Groq LLM, a FastAPI backend, and a Next.js + Tailwind frontend.

The app recommends restaurants based on **city** and **budget (for two)**, and uses Groq to generate human-friendly explanations for each recommendation.

---

## High-Level Architecture

- **Phase 1 – Data Ingestion** (`phase1_data_ingestion/`)
  - Loads the Zomato dataset from Hugging Face.
  - Cleans and normalizes core fields (`city`, `approx_cost(for two people)`).
  - Stores data in an in-memory `InMemoryRestaurantStore`.

- **Phase 2 – User Input** (`phase2_user_input/`)
  - Models raw and normalized user input.
  - Validates `city` and `price_text` (`"800"` or `"500-1200"`).
  - Normalizes to canonical `city` + numeric price range and bucket.

- **Phase 3 – Integration / Orchestration** (`phase3_integration/`)
  - `RestaurantRepository` filters restaurants by city and price.
  - `RecommendationPreparationService` connects validation, normalization, and repository to produce a candidate set.

- **Phase 4 – Recommendation (LLM / Groq)** (`phase4_recommendation/`)
  - Builds an LLM prompt from user preferences + candidate table.
  - Uses `GroqAPIClient` to call Groq Chat Completions API.
  - Parses JSON response into `RecommendedRestaurant` objects.
  - Robust error handling via `LLMRecommendationError`.

- **Phase 5 – Display** (`phase5_display/`)
  - CLI-oriented presenter that formats recommendations nicely for text output.

- **API Backend** (`api_backend/`)
  - FastAPI app exposing:
    - `GET /health` – health check.
    - `GET /cities` – list of available cities.
    - `GET /price-range` – min/max price in dataset.
    - `POST /recommendations` – full pipeline with Groq LLM.

- **Frontend** (`frontend/`)
  - Next.js 14 (App Router) + React + Tailwind CSS.
  - Clean, modern single-page UI for city + budget selection and listing recommendations.

---

## Prerequisites

- **Python**: 3.11+ (project uses virtual env at `.venv/`)
- **Node.js**: 18+ (for Next.js frontend)
- **Groq API Key**: required for AI explanations
  - Get a key from the Groq console.

---

## Backend Setup (FastAPI + Groq)

From the project root (`Build Hour 1`):

```bash
pip install -r requirements.txt
```

### Configure Groq API Key

Create a `.env` file in the **project root** (same folder as `requirements.txt`):

```env
GROQ_API_KEY=YOUR_GROQ_API_KEY_HERE
```

The backend uses `python-dotenv` and `phase4_recommendation/llm_client.py` to load this automatically.

### Run the Backend

From the project root:

```bash
python -m uvicorn api_backend.main:app --reload
```

The API will be available at:

- `http://127.0.0.1:8000`
- Docs at `http://127.0.0.1:8000/docs`

### Key Endpoints

- `GET /health`
  - Returns `{ "status": "ok", "restaurants_loaded": <int> }`
- `GET /cities`
  - Returns `{ "cities": ["bangalore", "mumbai", ...] }`
- `GET /price-range`
  - Returns `{ "min": <float>, "max": <float> }`
- `POST /recommendations`
  - Request:
    ```json
    { "city": "Bangalore", "price_text": "800" }
    ```
  - Response:
    ```json
    {
      "recommendations": [
        {
          "name": "Some Restaurant",
          "city": "bangalore",
          "cuisines": "Indian, Chinese",
          "price_for_two": 800.0,
          "rating": 4.5,
          "reason": "Short AI explanation"
        }
      ]
    }
    ```

Errors are returned with structured JSON (400 for validation, 503/502 for LLM issues).

---

## Frontend Setup (Next.js + Tailwind)

The frontend lives in the `frontend/` directory and assumes the backend is running on `http://127.0.0.1:8000`.

From `frontend/`:

```bash
cd frontend
npm install
npm run dev
```

By default Next.js will start on `http://localhost:3000` (or another free port, e.g. `3002`).

### Frontend Features

- **Inputs**
  - City dropdown:
    - Populated from `GET /cities`.
    - Falls back to a default city list if the endpoint fails.
  - Budget slider:
    - Uses `GET /price-range` to derive min/max.
    - Shows current selection and full range.

- **Results**
  - Shows count tile:
    - “Showing N restaurants – City: X – Budget: ₹Y for two”.
  - Recommendation cards:
    - Name, city, cuisines (tags), price for two, rating, and “Why this restaurant?” (reason from LLM).
  - De-duplicates restaurants by name + city.
  - **Sorting options**:
    - AI order (original LLM order).
    - Rating (high → low / low → high).
    - Price (low → high / high → low).

- **States**
  - Loading state while fetching recommendations.
  - Empty state when no results.
  - Inline validation messages for city/budget errors.
  - Graceful messages when LLM/backend is unavailable.

---

## CLI Usage (Optional)

There is also a CLI entrypoint (`cli.py`) that runs Phases 1–5 end-to-end:

```bash
python cli.py Bangalore 800
```

Or interactively:

```bash
python cli.py
```

You will be prompted for:

- City
- Budget (for two people)

The CLI will then print top matching restaurants and their details.

---

## Tests

Tests are organized by phase and layer:

- `tests_phase1/` – data ingestion/cleaning
- `tests_phase2/` – user input validation/normalization
- `tests_phase3/` – repository and prep service
- `tests_phase4/` – LLM service and Groq client configuration
- `tests_phase5/` – presenter formatting
- `tests_api/` – FastAPI endpoint tests (with mocked LLM)
- `tests_integration/` – end-to-end CLI and API tests (with fake LLM)

Run all tests with:

```bash
python -m pytest -q
```

---

## Notes & Next Steps

- This project is structured for clarity and extensibility:
  - Easy to swap out Groq for another LLM provider.
  - Easy to replace in-memory storage with a real database.
  - Frontend is decoupled from backend via a clear JSON API.
- Possible enhancements:
  - Add authentication / rate limiting.
  - Introduce a vector database for semantic restaurant similarity.
  - Deploy the backend and frontend to a cloud environment.

