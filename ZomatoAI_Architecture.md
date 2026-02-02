## Zomato AI Restaurant Recommendation Service – Architecture

### Overview
- **Goal**: Recommend Zomato restaurants based on **city** and **price** using the `ManikaSaini/zomato-restaurant-recommendation` dataset on Hugging Face.
- **Approach**: Build a modular system in 5 development phases: data ingestion, user input handling, integration/orchestration, recommendation logic, and user-facing display.
- **Tech Stack (suggested)**:
  - **Backend**: Python (FastAPI / Flask) or Node.js (Express)
  - **Data & Features**: Pandas / SQL DB, optional vector DB for semantic similarity
  - **AI/ML**: Simple filters → heuristic scoring → (optionally) trained recommender model
  - **Frontend**: Web UI (React / simple HTML) or API client (Postman, mobile app later)

---

## STEP 1 – Input the Zomato Data

### Objectives
- **Ingest** the Zomato dataset from Hugging Face.
- **Standardize** schema (city, location, cuisines, average cost, rating, votes, etc.).
- **Store** data in a query-efficient layer optimized for city- and price-based filtering.

### Components
- **Data Source Layer**
  - `HFDatasetLoader`:
    - Reads the `ManikaSaini/zomato-restaurant-recommendation` dataset (via Hugging Face API or downloaded CSV).
    - Validates schema and handles missing values (e.g., unrated restaurants, null cuisines).
- **Data Processing & Enrichment**
  - `DataCleaner`:
    - Normalizes city names, price formats, and text fields.
    - Standardizes currencies and price units into a common numeric field (e.g., average cost for two).
  - `FeatureEngineer` (optional in phase 1, expandable later):
    - Derives features like `price_bucket` (low/medium/high), `is_family_friendly`, `is_date_place`, etc.
- **Storage Layer**
  - Option A (simple): In-memory store (Pandas DataFrame) for early development and demos.
  - Option B (scalable): Relational DB (PostgreSQL/MySQL) or document store (MongoDB) with indices on:
    - `city`
    - `price` / `price_bucket`
    - `rating`
  - Optional: Vector DB (e.g., for embedding restaurant descriptions and cuisines) can be added in a later phase.

### Data Flow
1. System starts → `HFDatasetLoader` pulls dataset.
2. `DataCleaner` and `FeatureEngineer` run transformations.
3. Cleaned, enriched dataset is stored in the selected storage engine, ready for querying.

---

## STEP 2 – User Input

### Objectives
- Collect **city** and **price** constraints from users in a structured way.
- Validate and normalize these inputs before they reach the recommendation engine.

### Components
- **User Interface Layer**
  - Simple UI form (or API contract) with fields:
    - `city` (string, e.g., "Bangalore")
    - `price_preference` (numeric range or bucket: "low", "mid", "high" or min/max budget)
    - Optional: `cuisine_preference`, `min_rating`, `occasion` (e.g., “friends”, “date”).
- **Input Validation & Normalization**
  - `InputValidator`:
    - Ensures city is non-empty and maps to known cities in the dataset.
    - Checks that price values are numeric and within allowed range or maps to buckets.
  - `InputNormalizer`:
    - Normalizes city (case folding, trimming, mapping aliases like "Bengaluru" → "Bangalore").
    - Converts price preference to internal `price_bucket` or `(min_price, max_price)` constraints.

### Data Flow
1. User submits city and price details through UI/API.
2. `InputValidator` validates fields and returns structured errors if invalid.
3. `InputNormalizer` converts user inputs into canonical internal representations.
4. Normalized inputs are passed to the orchestration layer.

---

## STEP 3 – Integrate (Orchestration & APIs)

### Objectives
- Connect user inputs, data store, and recommendation logic into a cohesive API.
- Maintain a clear separation between transport (HTTP), business logic, and data access.

### Components
- **API Layer**
  - `RecommendationController` (HTTP endpoint):
    - Endpoint: `POST /recommendations`
    - Request body: normalized user input (city, price, optional filters).
    - Response: list of recommended restaurants with key attributes (name, cuisine, rating, price, link).
- **Orchestration / Service Layer**
  - `RecommendationService`:
    - Validates and normalizes request (or delegates to Step 2 components).
    - Calls data access methods to retrieve candidate restaurants.
    - Invokes recommendation engine to rank/filter candidates.
    - Formats response DTOs for the API layer.
- **Data Access Layer**
  - `RestaurantRepository`:
    - Provides methods like:
      - `get_by_city_and_price(city, price_range | price_bucket)`
      - `get_by_ids(list_of_ids)`
    - Hides underlying storage implementation details (DataFrame vs DB).

### Data Flow
1. API receives request with user input.
2. `RecommendationController` forwards to `RecommendationService`.
3. `RecommendationService` queries `RestaurantRepository` for candidate set.
4. Candidate set and user preferences are passed to the recommendation engine.
5. Ranked recommendations are returned to `RecommendationController` and then to client.

---

## STEP 4 – Recommendation (AI/ML Logic)

### Objectives
- Implement the core **recommendation logic** using city and price as primary filters.
- Allow progressive enhancement: start with rule-based filtering, then add AI-based ranking.

### Phased Recommendation Logic
- **Phase 4.1 – Baseline Filtering**
  - `RuleBasedRecommender`:
    - Filter by:
      - City = user city
      - Price in user’s desired range/bucket
    - Sort by:
      - Higher rating
      - More votes
    - Return top N (e.g., 10) recommendations.

- **Phase 4.2 – Heuristic Scoring**
  - Extend `RuleBasedRecommender` to use a composite score:
    - \\( score = w_1 \cdot rating + w_2 \cdot \text{log}(votes + 1) - w_3 \cdot \text{price\_distance} \\)
    - Price distance measures how far the restaurant is from the user’s ideal price.
  - Add penalties/boosts for:
    - Highly rated but slightly more expensive places.
    - Popular cuisines in that city.

- **Phase 4.3 – AI/ML-based Recommender (Optional Enhancement)**
  - `MLRecommender`:
    - Use dataset features to train a model (e.g., gradient boosting, neural network, or matrix factorization if there are user signals).
    - Inputs: city, price, cuisines, rating, etc.
    - Output: relevance score for each restaurant given user preferences.
  - Optional: semantic embeddings for:
    - Restaurant names, cuisines, and descriptions.
    - Use a vector DB to find similar restaurants to ones that match simple filters.

### Components
- **Recommendation Engine Abstraction**
  - `IRecommender` interface:
    - Method: `recommend(user_preferences, candidate_restaurants) → ranked_list`.
  - Implementations:
    - `RuleBasedRecommender`
    - `MLRecommender` (plugged in later without changing API layer).

### Data Flow
1. `RecommendationService` sends user preferences and candidate restaurants to `IRecommender`.
2. `IRecommender` implementation computes scores and sorts candidates.
3. Top N restaurants are returned for formatting and display.

---

## STEP 5 – Display to the User

### Objectives
- Present recommended restaurants in a clear, usable format.
- Keep UI and response formats flexible for future channels (web, mobile, chat, voice).

### Components
- **Response Formatting**
  - `RecommendationPresenter`:
    - Transforms internal restaurant objects into UI-friendly DTOs:
      - Fields: `name`, `address`, `city`, `cuisines`, `price_for_two`, `rating`, `votes`, `zomato_link`.
    - Optional: includes explanation fields (e.g., “Matched your price range and >4.0 rating”).
- **UI Layer (Client)**
  - For a web client:
    - Results list/grid showing:
      - Restaurant name and rating prominently.
      - Tags for cuisines and price level.
      - Quick filters for adjusting price or rating without resubmitting city.
  - For an API-only client:
    - Consistent JSON structure enabling any frontend or chatbot to consume:
      - `recommendations: [ {restaurant}, ... ]`
      - `meta: { request_id, city, price_preference, generated_at }`

### Data Flow
1. Ranked restaurants from recommendation engine are passed to `RecommendationPresenter`.
2. `RecommendationPresenter` formats data for the chosen client (JSON/HTML).
3. API returns formatted recommendations to the user-facing channel.

---

## Phase-wise Development Summary (5 Steps)

- **STEP 1 – Input the Zomato Data**
  - Implement dataset ingestion from Hugging Face.
  - Clean, normalize, and store restaurant records in a queryable format.

- **STEP 2 – User Input**
  - Design and implement user input contract (city, price).
  - Add validation and normalization logic for city and price preferences.

- **STEP 3 – Integrate**
  - Build `POST /recommendations` endpoint.
  - Implement `RecommendationService` and `RestaurantRepository` to orchestrate flow.

- **STEP 4 – Recommendation**
  - Start with rule-based filtering and sorting by rating/votes.
  - Introduce heuristic scoring and (optionally) ML-based recommender and embeddings.

- **STEP 5 – Display to the User**
  - Create `RecommendationPresenter` for consistent response shaping.
  - Build or integrate a UI/client to render the recommendations clearly to users.

