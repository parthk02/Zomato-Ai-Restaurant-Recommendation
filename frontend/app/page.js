"use client";

import { useEffect, useState } from "react";

const API_BASE = "http://127.0.0.1:8000";
const FALLBACK_CITIES = [
  "bangalore",
  "mumbai",
  "delhi",
  "chennai",
  "hyderabad",
  "pune",
];

export default function HomePage() {
  const [cities, setCities] = useState([]);
  const [city, setCity] = useState("");
  const [budgetValue, setBudgetValue] = useState("");
  const [priceMin, setPriceMin] = useState(100);
  const [priceMax, setPriceMax] = useState(3000);
  const [cityError, setCityError] = useState("");
  const [budgetError, setBudgetError] = useState("");
  const [message, setMessage] = useState(
    "Start by selecting a city and budget above."
  );
  const [sortOption, setSortOption] = useState("llm");
  const [isLoading, setIsLoading] = useState(false);
  const [recommendations, setRecommendations] = useState([]);

  useEffect(() => {
    async function loadInitialData() {
      try {
        const [citiesResp, priceResp] = await Promise.all([
          fetch(`${API_BASE}/cities`),
          fetch(`${API_BASE}/price-range`),
        ]);

        if (citiesResp.ok) {
          const citiesData = await citiesResp.json();
          const apiCities = citiesData.cities || [];
          setCities(apiCities.length ? apiCities : FALLBACK_CITIES);
        } else {
          // Backend reachable but /cities failed – use fallback.
          setCities(FALLBACK_CITIES);
        }

        if (priceResp.ok) {
          const priceData = await priceResp.json();
          const min = Number(priceData.min) || 100;
          const max = Number(priceData.max) || 3000;
          setPriceMin(min);
          setPriceMax(max);
          setBudgetValue(String(Math.round((min + max) / 2)));
        } else {
          setBudgetValue("800");
        }
      } catch {
        // Backend not reachable yet – use fallbacks so UI stays usable.
        setCities(FALLBACK_CITIES);
        setBudgetValue("800");
      }
    }
    loadInitialData();
  }, []);

  async function handleSubmit() {
    setCityError("");
    setBudgetError("");
    setMessage("");

    if (!city.trim()) {
      setCityError("Please select a city.");
      return;
    }

    setIsLoading(true);
    setRecommendations([]);

    try {
      const resp = await fetch(`${API_BASE}/recommendations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ city, price_text: budgetValue || null }),
      });

      if (resp.status === 400) {
        const detail = await resp.json();
        const errs = detail?.detail || [];
        errs.forEach((e) => {
          if (e.field === "city") setCityError(e.message);
          if (e.field === "price_text") setBudgetError(e.message);
        });
        if (!errs.length) {
          setMessage("Please review your input and try again.");
        }
        return;
      }

      if (resp.status === 503) {
        setMessage(
          "AI service is temporarily unavailable. Please try again later."
        );
        return;
      }

      if (resp.status === 502) {
        const detail = await resp.json();
        const errs = detail?.detail || [];
        const msg =
          (errs[0] && errs[0].message) ||
          "AI service returned an invalid response. Please try again.";
        setMessage(msg);
        return;
      }

      const data = await resp.json();
      const recs = data.recommendations || [];

      // Deduplicate by (name, city) to avoid repeated entries.
      const unique = [];
      const seen = new Set();
      for (const r of recs) {
        const key = `${(r.name || "").toLowerCase()}|${(r.city || "").toLowerCase()}`;
        if (seen.has(key)) continue;
        seen.add(key);
        unique.push(r);
      }

      if (!unique.length) {
        setMessage("No restaurants found for this city and budget.");
      } else {
        setRecommendations(unique);
        setMessage("");
      }
    } catch {
      setMessage("Unable to reach the backend. Check if the API is running.");
    } finally {
      setIsLoading(false);
    }
  }

  const displayCity =
    city && typeof city === "string"
      ? city.charAt(0).toUpperCase() + city.slice(1)
      : "";

  function getSortedRecommendations() {
    const recs = [...recommendations];
    if (sortOption === "rating_desc") {
      return recs.sort((a, b) => (b.rating || 0) - (a.rating || 0));
    }
    if (sortOption === "rating_asc") {
      return recs.sort((a, b) => (a.rating || 0) - (b.rating || 0));
    }
    if (sortOption === "price_asc") {
      return recs.sort(
        (a, b) => (a.price_for_two || Infinity) - (b.price_for_two || Infinity)
      );
    }
    if (sortOption === "price_desc") {
      return recs.sort(
        (a, b) => (b.price_for_two || 0) - (a.price_for_two || 0)
      );
    }
    // "llm" → keep original order.
    return recs;
  }

  const sortedRecommendations = getSortedRecommendations();

  return (
    <div className="space-y-8">
      {/* Header */}
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold text-slate-900 sm:text-3xl">
          Zomato AI Restaurant Recommendations
        </h1>
        <p className="max-w-2xl text-sm text-slate-500">
          Discover the best restaurants in your city using AI-powered
          recommendations.
        </p>
      </header>

      {/* Input Card */}
      <section className="rounded-xl border border-slate-200 bg-surface shadow-sm">
        <div className="space-y-6 p-5 sm:p-6">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <label
                htmlFor="city"
                className="text-xs font-medium uppercase tracking-wide text-slate-500"
              >
                City
              </label>
              <select
                id="city"
                className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm outline-none transition focus:border-slate-500 focus:ring-1 focus:ring-slate-500"
                value={city}
                onChange={(e) => setCity(e.target.value)}
              >
                <option value="">Select a city...</option>
                {cities.map((c) => (
                  <option key={c} value={c}>
                    {c.charAt(0).toUpperCase() + c.slice(1)}
                  </option>
                ))}
              </select>
              {cityError && (
                <p className="text-xs text-rose-600/90">{cityError}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <label
                htmlFor="budget"
                className="text-xs font-medium uppercase tracking-wide text-slate-500"
              >
                Budget (for two people)
              </label>
              <input
                id="budget"
                type="range"
                min={priceMin}
                max={priceMax}
                step={50}
                value={budgetValue}
                onChange={(e) => setBudgetValue(e.target.value)}
                className="w-full accent-accent"
              />
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span>
                  Range: ₹{Math.round(priceMin)} – ₹{Math.round(priceMax)}
                </span>
                <span className="text-slate-600">
                  Selected: <span className="font-medium">₹{budgetValue}</span> for two
                </span>
              </div>
              {budgetError && (
                <p className="text-xs text-rose-600/90">{budgetError}</p>
              )}
            </div>
          </div>

          <div className="flex flex-col items-start gap-2 sm:flex-row sm:items-center sm:justify-between">
            <button
              type="button"
              onClick={handleSubmit}
              disabled={isLoading}
              className="inline-flex items-center justify-center rounded-full bg-accent px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-red-700 disabled:cursor-not-allowed disabled:bg-slate-400"
            >
              {isLoading ? "Getting Recommendations..." : "Get Recommendations"}
            </button>
            <p className="text-xs text-slate-400">
              Uses Groq LLM to generate explanations.
            </p>
          </div>
        </div>
      </section>

      {/* Loading */}
      {isLoading && (
        <section className="flex items-center gap-2 text-sm text-slate-500">
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600" />
          <span>Finding the best restaurants for you…</span>
        </section>
      )}

      {/* Results */}
      <section className="space-y-3">
        <h2 className="text-lg font-medium text-slate-900">
          Recommended Restaurants
        </h2>

        {sortedRecommendations.length > 0 && (
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-600 sm:text-sm">
            <div className="flex flex-wrap items-center gap-2">
              <span>
                Showing{" "}
                <span className="font-semibold">
                  {sortedRecommendations.length}
                </span>{" "}
                restaurants
              </span>
              {displayCity && (
                <>
                  <span className="hidden text-slate-400 sm:inline">•</span>
                  <span>
                    City:{" "}
                    <span className="font-medium text-slate-800">
                      {displayCity}
                    </span>
                  </span>
                </>
              )}
              <span className="hidden text-slate-400 sm:inline">•</span>
              <span>
                Budget:{" "}
                <span className="font-medium text-slate-800">
                  ₹{budgetValue}
                </span>{" "}
                for two
              </span>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-[11px] text-slate-500 sm:text-xs">
                Sort by
              </span>
              <select
                value={sortOption}
                onChange={(e) => setSortOption(e.target.value)}
                className="rounded-md border border-slate-300 bg-white px-2 py-1 text-xs text-slate-800 shadow-sm outline-none focus:border-slate-500 focus:ring-1 focus:ring-slate-500"
              >
                <option value="llm">AI order</option>
                <option value="rating_desc">Rating (high to low)</option>
                <option value="rating_asc">Rating (low to high)</option>
                <option value="price_asc">Price (low to high)</option>
                <option value="price_desc">Price (high to low)</option>
              </select>
            </div>
          </div>
        )}

        {message && (
          <p className="text-sm text-slate-500" data-testid="results-message">
            {message}
          </p>
        )}

        <div className="space-y-4">
          {sortedRecommendations.map((r) => (
            <article
              key={`${r.name}-${r.city}-${r.price_for_two}`}
              className="rounded-xl border border-slate-200 bg-surface p-4 shadow-sm"
            >
              <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-start">
                <div>
                  <h3 className="text-base font-semibold text-slate-900">
                    {r.name}
                  </h3>
                  {r.city && (
                    <p className="mt-0.5 flex items-center gap-1 text-xs text-slate-500">
                      <span className="inline-block h-1.5 w-1.5 rounded-full bg-slate-400" />
                      <span>
                        {r.city.charAt(0).toUpperCase() + r.city.slice(1)}
                      </span>
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-3 text-xs text-slate-600">
                  {r.rating != null && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-1">
                      <span className="text-yellow-500">★</span>
                      <span>{r.rating.toFixed(1)}</span>
                    </span>
                  )}
                  {r.price_for_two != null && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-1">
                      <span>₹</span>
                      <span>{Math.round(r.price_for_two)}</span>
                      <span className="text-slate-400">for two</span>
                    </span>
                  )}
                </div>
              </div>

              {r.cuisines && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {r.cuisines.split(",").map((cuisine) => (
                    <span
                      key={cuisine.trim()}
                      className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600"
                    >
                      {cuisine.trim()}
                    </span>
                  ))}
                </div>
              )}

              {r.reason && (
                <div className="mt-4 space-y-1">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Why this restaurant?
                  </p>
                  <p className="text-sm text-slate-800">{r.reason}</p>
                </div>
              )}
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}

