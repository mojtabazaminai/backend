# CMA API Reference

Base URL: `http://localhost:8000`

All `/api/v1/*` endpoints require an `X-API-Key` header when the `FASTAPI_API_KEY` environment variable is set. If the variable is empty or unset, authentication is disabled.

Interactive docs are available at `/docs` (Swagger UI) and `/redoc` (ReDoc) when the server is running.

---

## Health Check

### `GET /health`

Returns server status.

**Response**

```json
{ "status": "ok" }
```

---

## Find Comparable Properties

### `POST /api/v1/comparables`

Finds properties similar to a given subject using one of four strategies. The request body is a **discriminated union** — set the `strategy` field to select the search method.

All strategies share these base fields:

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `strategy` | `string` | yes | — | One of `"llm"`, `"baseline"`, `"ml"`, `"vector"` |
| `subject_listing_key` | `string` | one of these | — | MLS listing key to look up the subject from the database |
| `subject_property` | `object` | one of these | — | Inline subject property dict (skips DB lookup) |
| `top_k` | `integer` | no | `5` | Number of comparables to return (1–100) |
| `skip_same_address` | `boolean` | no | `false` | Exclude candidates at the same address as the subject |

> **Subject resolution:** provide `subject_listing_key` **or** `subject_property` (at least one is required). When `subject_listing_key` is given, the property is fetched from PostgreSQL and `city_name` is automatically resolved from the record if not provided.

---

### Strategy: `llm`

Uses geo-prefiltering (Haversine distance) to select top N candidates, then sends them to an LLM which ranks and selects the best comparables.

**Additional fields**

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `city_name` | `string` | no | from subject | City to query candidates from. Auto-resolved from subject if omitted. |
| `candidate_properties` | `list[object]` | no | — | Supply your own candidate list (bypasses DB query). Must provide this **or** `city_name` **or** `subject_listing_key`. |
| `prefilter_count` | `integer` | no | `50` | Number of geo-nearest candidates to pass to the LLM (1–5000) |
| `similarity_prompt` | `string` | no | server default | Custom system prompt for the LLM similarity ranker |
| `similarity_columns` | `list[string]` | no | auto-detected | Property columns to include in the LLM prompt |
| `model_name` | `string` | no | `OPENAI_MODEL` env | LLM model identifier |
| `base_url` | `string` | no | `OPENAI_BASE_URL` env | LLM API base URL |
| `api_key` | `string` | no | `OPENAI_API_KEY` env | LLM API key override |

**Example request**

```json
{
  "strategy": "llm",
  "subject_listing_key": "305707732",
  "top_k": 5,
  "prefilter_count": 50
}
```

---

### Strategy: `baseline`

Ranks candidates using a rule-based scoring algorithm (no LLM). Candidates are selected from the same H3 hex region.

**Additional fields**

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `city_name` | `string` | no | from subject | City to query candidates from. Auto-resolved from subject if omitted. |
| `max_candidates` | `integer` | no | `500` | Maximum candidate pool size (1–5000) |
| `h3_resolution` | `integer` | no | `7` | H3 hex resolution for spatial bucketing (1–15) |

**Example request**

```json
{
  "strategy": "baseline",
  "subject_listing_key": "305707732",
  "top_k": 5
}
```

---

### Strategy: `ml`

Ranks candidates using a trained LightGBM model. Same spatial bucketing as `baseline`.

**Additional fields**

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `city_name` | `string` | no | from subject | City to query candidates from. Auto-resolved from subject if omitted. |
| `max_candidates` | `integer` | no | `500` | Maximum candidate pool size (1–5000) |
| `h3_resolution` | `integer` | no | `7` | H3 hex resolution for spatial bucketing (1–15) |
| `ranker_model_path` | `string` | no | server default | Path to a custom LightGBM model file |

**Example request**

```json
{
  "strategy": "ml",
  "subject_listing_key": "305707732",
  "city_name": "Apple Valley",
  "top_k": 5
}
```

---

### Strategy: `vector`

Uses embedding-based semantic search via Qdrant. The subject property is embedded and matched against a pre-indexed collection.

**Additional fields**

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `collection_name` | `string` | **yes** | — | Qdrant collection to search |
| `prefilter_count` | `integer` | no | — | Optional geo prefilter before vector search |
| `qdrant_url` | `string` | no | `QDRANT_URL` env | Qdrant server URL |
| `qdrant_api_key` | `string` | no | `QDRANT_API_KEY` env | Qdrant API key |
| `openai_api_key` | `string` | no | `OPENAI_API_KEY` env | API key for embedding model |
| `openai_base_url` | `string` | no | `OPENAI_BASE_URL` env | Base URL for embedding model |
| `embedding_model_override` | `string` | no | server default | Custom embedding model name |
| `embedding_columns_override` | `list[string]` | no | server default | Property columns to embed |

**Example request**

```json
{
  "strategy": "vector",
  "subject_listing_key": "305707732",
  "collection_name": "apple_valley_props",
  "top_k": 5
}
```

---

### Comparables Response

All strategies return the same response shape.

```json
{
  "run_id": 42,
  "strategy": "llm",
  "subject_summary": { "listing_key": "305707732", "address": "12352 Lakota Road, ...", "..." : "..." },
  "selected_listing_keys": ["305797766", "305488755", "305224264"],
  "selected_rows": [ { "candidate_id": "305797766", "..." : "..." } ],
  "selected_full_records": [ { "listing_key": "305797766", "..." : "..." } ],
  "similarity_reason": "Selected based on proximity, similar square footage, ...",
  "timing_logs": [ { "step": "geo_prefilter", "duration_ms": 142.35, "selected_count": 50 } ],
  "total_duration_ms": 3241.57
}
```

| Field | Type | Description |
|---|---|---|
| `run_id` | `integer \| null` | Database run ID (if persisted) |
| `strategy` | `string` | The strategy that was used |
| `subject_summary` | `PropertySummary` | Compact summary of the subject property |
| `selected_listing_keys` | `list[string]` | Listing keys of selected comparables |
| `selected_rows` | `list[SimilarityRow]` | Summary rows with distance/rank info per comparable |
| `selected_full_records` | `list[CompRecord]` | Full property records for each comparable (includes enrichment fields like `distance_km`, `similarity_score`, `h3_index`) |
| `similarity_reason` | `string` | Human-readable explanation of why these comps were selected |
| `timing_logs` | `list[TimingLog]` | Per-step performance breakdown |
| `total_duration_ms` | `float` | Total wall-clock time in milliseconds |

**`PropertySummary` fields:** `listing_key`, `address`, `city`, `postal_code`, `property_type`, `property_sub_type`, `standard_status`, `list_price`, `close_price`, `beds`, `baths`, `living_area`, `year_built`, `latitude`, `longitude`

**`SimilarityRow` fields:** `candidate_id`, `listing_key`, `address`, `city`, `postal_code`, `property_type`, `property_sub_type`, `distance_km`, `geo_rank`, `llm_rank`, `list_price`, `close_price`, `beds`, `baths`, `living_area`, `year_built`

---

## Generate CMA Report

### `POST /api/v1/reports`

Generates a Comparative Market Analysis report for a subject property against a set of comparable properties. Computes adjustments, valuation ranges, market statistics, trends, and confidence scores.

**Request body**

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `subject_listing_key` | `string` | one of these | — | MLS listing key for the subject property |
| `subject_property` | `object` | one of these | — | Inline subject property dict |
| `comparable_listing_keys` | `list[string]` | **yes** | — | Listing keys of comparable properties (1–20) |
| `city_name` | `string` | no | from subject | City for market stats lookup. Auto-resolved from subject if omitted. |
| `sections` | `list[string]` | no | all | Sections to include in the response (see below). Omit for all sections. |

**Selectable sections**

When `sections` is provided, only the listed sections are populated in the response. Unrequested sections return `null`. When omitted, all sections are returned (backward compatible).

| Section | Description |
|---|---|
| `adjustments` | Per-comp price adjustments for sqft, beds, baths, garage, condition, age, lot |
| `valuation` | Value range (low / likely / high / avg) and median price per sqft |
| `pricing` | Pricing tiers: aggressive, market, aspirational |
| `market` | City-level market statistics (sold count, active count, median price, DOM, absorption rate) |
| `trends` | Monthly trend data (volume, median price, median DOM) for the last 6 months |
| `agent` | Listing agent performance stats (homes sold, avg DOM, list-to-sale ratio, volume) |
| `confidence` | CMA confidence score with breakdown (comp quality, recency, stability, etc.) |
| `price_direction` | Percentage indicating price trend direction |

The three core fields — `listing_key`, `subject`, and `comps` — are **always** returned regardless of the `sections` filter.

**Example — all sections (default)**

```json
{
  "subject_listing_key": "305707732",
  "comparable_listing_keys": ["305797766", "305488755", "305224264"]
}
```

**Example — only market and trends**

```json
{
  "subject_listing_key": "305707732",
  "comparable_listing_keys": ["305797766", "305488755", "305224264"],
  "sections": ["market", "trends"]
}
```

---

### Report Response

```json
{
  "listing_key": "305707732",
  "subject": { "listing_key": "305707732", "..." : "..." },
  "comps": [ { "listing_key": "305797766", "..." : "..." } ],
  "adjustments": [ { "sale_price": 400000, "..." : "..." } ],
  "valuation": { "low": 45229, "likely": 233733, "high": 358379, "avg": 233733, "median_ppsf": 279 },
  "pricing": { "aggressive": 225000, "market": 240000, "aspirational": 360000 },
  "market": { "total_sold": 10243, "..." : "..." },
  "trends": [ { "month": "2025-04", "..." : "..." } ],
  "agent": { "homes_sold": 0, "avg_dom": 0, "list_to_sale": 0, "total_volume": 0 },
  "confidence": { "overall": 71, "grade": "B-", "..." : "..." },
  "price_direction": 36.8
}
```

| Field | Type | Description |
|---|---|---|
| `listing_key` | `string \| null` | Subject listing key |
| `subject` | `PropertyRecord` | Full subject property record |
| `comps` | `list[CompRecord]` | Full comparable property records |
| `adjustments` | `list[AdjustmentItem] \| null` | Per-comp adjustment breakdown |
| `valuation` | `Valuation \| null` | Estimated value range |
| `pricing` | `Pricing \| null` | Pricing strategy tiers |
| `market` | `MarketStats \| null` | City-level market snapshot |
| `trends` | `list[TrendItem] \| null` | Monthly market trends |
| `agent` | `AgentStats \| null` | Listing agent performance |
| `confidence` | `Confidence \| null` | CMA confidence assessment |
| `price_direction` | `float \| null` | Price trend direction (%) |

Fields are `null` when excluded by the `sections` filter.

#### `AdjustmentItem`

| Field | Type | Description |
|---|---|---|
| `sale_price` | `float` | Comparable's sale price |
| `adj_sqft` | `integer` | Dollar adjustment for square footage difference |
| `adj_beds` | `integer` | Dollar adjustment for bedroom count difference |
| `adj_baths` | `integer` | Dollar adjustment for bathroom count difference |
| `adj_garage` | `integer` | Dollar adjustment for garage difference |
| `adj_condition` | `integer` | Dollar adjustment for condition difference |
| `adj_age` | `integer` | Dollar adjustment for age difference |
| `adj_lot` | `integer` | Dollar adjustment for lot size difference |
| `net_adjustment` | `integer` | Sum of all adjustments |
| `net_pct` | `float` | Net adjustment as percentage of sale price |
| `adjusted_price` | `integer` | Sale price after all adjustments |
| `adjusted_ppsf` | `integer` | Adjusted price per square foot |
| `sqft_diff` | `float` | Square footage difference (comp - subject) |
| `bed_diff` | `integer` | Bedroom count difference |
| `bath_diff` | `float` | Bathroom count difference |
| `garage_diff` | `integer` | Garage space difference |
| `age_diff` | `integer` | Year-built difference |

#### `Valuation`

| Field | Type | Description |
|---|---|---|
| `low` | `integer` | Low-end estimated value |
| `likely` | `integer` | Most likely estimated value |
| `high` | `integer` | High-end estimated value |
| `avg` | `integer` | Average of adjusted comp prices |
| `median_ppsf` | `integer` | Median adjusted price per square foot |

#### `Pricing`

| Field | Type | Description |
|---|---|---|
| `aggressive` | `integer` | Below-market price for quick sale |
| `market` | `integer` | Fair market value price |
| `aspirational` | `integer` | Above-market aspirational price |

#### `MarketStats`

| Field | Type | Description |
|---|---|---|
| `total_sold` | `integer` | Total properties sold in the city |
| `total_active` | `integer` | Currently active listings |
| `median_price` | `float` | Median sale price |
| `median_dom` | `float` | Median days on market |
| `avg_sp_lp` | `float` | Average sale-to-list price ratio |
| `median_ppsf` | `float` | Median price per square foot |
| `absorption_rate` | `float` | Market absorption rate (%) |
| `months_supply` | `float` | Months of inventory supply |

#### `TrendItem`

| Field | Type | Description |
|---|---|---|
| `month` | `string` | Month label (e.g. `"2025-04"`) |
| `month_num` | `integer` | Month number (1–12) |
| `year` | `integer` | Year |
| `volume` | `integer` | Number of sales |
| `median_price` | `float` | Median sale price that month |
| `median_dom` | `float` | Median days on market that month |

#### `AgentStats`

| Field | Type | Description |
|---|---|---|
| `homes_sold` | `integer` | Agent's total homes sold |
| `avg_dom` | `integer` | Agent's average days on market |
| `list_to_sale` | `float` | Agent's list-to-sale price ratio |
| `total_volume` | `float` | Agent's total sales volume |

#### `Confidence`

| Field | Type | Description |
|---|---|---|
| `overall` | `integer` | Overall confidence score (0–100) |
| `grade` | `string` | Letter grade (e.g. `"B-"`) |
| `comp_quality` | `integer` | Comparable quality sub-score |
| `recency` | `integer` | Data recency sub-score |
| `stability` | `integer` | Market stability sub-score |
| `adj_depth` | `integer` | Adjustment depth sub-score |
| `variance` | `integer` | Price variance sub-score |
| `sample` | `integer` | Sample size sub-score |

---

## Run History

### `GET /api/v1/runs`

Returns a list of past CMA runs from the SQLite audit trail.

**Query parameters**

| Param | Type | Default | Description |
|---|---|---|---|
| `limit` | `integer` | `20` | Maximum number of runs to return |
| `db_path` | `string` | server default | Custom SQLite database path |

**Response**

```json
{
  "runs": [
    {
      "id": 1,
      "created_at": "2025-12-15T14:30:00",
      "status": "success",
      "subject_listing_key": "305707732",
      "model_name": "gpt-4.1-mini",
      "output_markdown": "# CMA Report ...",
      "...": "..."
    }
  ]
}
```

| Field | Type | Description |
|---|---|---|
| `id` | `integer` | Run ID |
| `created_at` | `string` | ISO timestamp |
| `status` | `string` | `"success"` or `"error"` |
| `subject_listing_key` | `string \| null` | Subject listing key |
| `model_name` | `string \| null` | LLM model used |
| `base_url` | `string \| null` | LLM API base URL |
| `report_file_path` | `string \| null` | Path to generated markdown report |
| `error_message` | `string \| null` | Error details (if failed) |
| `columns_sent` | `list[string]` | Property columns included in prompts |
| `system_prompt` | `string \| null` | System prompt used |
| `task_prompt` | `string \| null` | Task prompt used |
| `user_prompt` | `string \| null` | User prompt sent to LLM |
| `subject_payload` | `PropertyRecord` | Full subject property |
| `comparable_payloads` | `list[CompRecord]` | Full comparable properties |
| `similarity_results` | `list[SimilarityRow]` | Similarity search results |
| `output_markdown` | `string \| null` | Generated CMA report (markdown) |
| `reasoning` | `string \| null` | LLM reasoning output |
| `similarity_prompt` | `string \| null` | Similarity prompt used |
| `similarity_user_prompt` | `string \| null` | Similarity user prompt |
| `similarity_reasoning` | `string \| null` | LLM reasoning for similarity selection |

---

## Error Responses

All endpoints return errors in this format:

```json
{
  "detail": "Comparable listing keys not found: ['999999']"
}
```

| Status | Meaning |
|---|---|
| `400` | Bad request — validation error, missing data, or processing failure |
| `401` | Unauthorized — missing or invalid `X-API-Key` header |
| `422` | Unprocessable Entity — request body fails Pydantic validation |
