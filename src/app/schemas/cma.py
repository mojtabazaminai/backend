from __future__ import annotations

from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Comparables request: discriminated union on "strategy"
# ---------------------------------------------------------------------------


class _ComparablesBase(BaseModel):
    subject_listing_key: str | None = None
    subject_property: dict[str, Any] | None = None
    top_k: int | None = None
    skip_same_address: bool | None = None
    include_details: bool | None = None


class LLMComparablesRequest(_ComparablesBase):
    strategy: Literal["llm"] = "llm"
    city_name: str | None = None
    candidate_properties: list[dict[str, Any]] | None = None
    prefilter_count: int | None = None
    similarity_prompt: str | None = None
    similarity_columns: list[str] | None = None
    model_name: str | None = None
    base_url: str | None = None
    api_key: str | None = None


class BaselineComparablesRequest(_ComparablesBase):
    strategy: Literal["baseline"] = "baseline"
    city_name: str | None = None
    max_candidates: int | None = None
    h3_resolution: int | None = None


class MLComparablesRequest(_ComparablesBase):
    strategy: Literal["ml"] = "ml"
    city_name: str | None = None
    max_candidates: int | None = None
    h3_resolution: int | None = None
    ranker_model_path: str | None = None


class VectorComparablesRequest(_ComparablesBase):
    strategy: Literal["vector"] = "vector"
    collection_name: str
    prefilter_count: int | None = None
    qdrant_url: str | None = None
    qdrant_api_key: str | None = None
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    embedding_model_override: str | None = None
    embedding_columns_override: list[str] | None = None


ComparablesRequest = Annotated[
    Union[
        LLMComparablesRequest,
        BaselineComparablesRequest,
        MLComparablesRequest,
        VectorComparablesRequest,
    ],
    Field(discriminator="strategy"),
]


# ---------------------------------------------------------------------------
# Comparables response models
# ---------------------------------------------------------------------------


class PropertySummary(BaseModel):
    listing_key: str | None = None
    address: str | None = None
    city: str | None = None
    postal_code: str | None = None
    property_type: str | None = None
    property_sub_type: str | None = None
    standard_status: str | None = None
    list_price: float | None = None
    close_price: float | None = None
    beds: int | None = None
    baths: float | None = None
    living_area: float | None = None
    year_built: int | None = None
    latitude: float | None = None
    longitude: float | None = None

    model_config = {"extra": "allow"}


class SimilarityRow(BaseModel):
    candidate_id: str | None = None
    listing_key: str | None = None
    address: str | None = None
    city: str | None = None
    postal_code: str | None = None
    property_type: str | None = None
    property_sub_type: str | None = None
    distance_km: float | None = None
    geo_rank: int | None = None
    llm_rank: int | None = None
    list_price: float | None = None
    close_price: float | None = None
    beds: int | None = None
    baths: float | None = None
    living_area: float | None = None
    year_built: int | None = None

    model_config = {"extra": "allow"}


class TimingLog(BaseModel):
    step: str | None = None
    duration_ms: float | None = None
    selected_count: int | None = None

    model_config = {"extra": "allow"}


class ComparablesResponse(BaseModel):
    run_id: int | None = None
    strategy: str | None = None
    subject_summary: PropertySummary | None = None
    selected_listing_keys: list[str] = []
    selected_rows: list[SimilarityRow] | None = None
    selected_full_records: list[dict[str, Any]] | None = None
    similarity_reason: str | None = None
    timing_logs: list[TimingLog] = []
    total_duration_ms: float | None = None

    model_config = {"extra": "allow"}


# ---------------------------------------------------------------------------
# Report request
# ---------------------------------------------------------------------------


class ReportRequest(BaseModel):
    subject_listing_key: str | None = None
    subject_property: dict[str, Any] | None = None
    comparable_listing_keys: list[str]
    city_name: str | None = None
    sections: list[str] | None = None


# ---------------------------------------------------------------------------
# Report response models
# ---------------------------------------------------------------------------


class AdjustmentItem(BaseModel):
    sale_price: float | None = None
    adj_sqft: int | None = None
    adj_beds: int | None = None
    adj_baths: int | None = None
    adj_garage: int | None = None
    adj_condition: int | None = None
    adj_age: int | None = None
    adj_lot: int | None = None
    net_adjustment: int | None = None
    net_pct: float | None = None
    adjusted_price: int | None = None
    adjusted_ppsf: int | None = None
    sqft_diff: float | None = None
    bed_diff: int | None = None
    bath_diff: float | None = None
    garage_diff: int | None = None
    age_diff: int | None = None

    model_config = {"extra": "allow"}


class Valuation(BaseModel):
    low: int | None = None
    likely: int | None = None
    high: int | None = None
    avg: int | None = None
    median_ppsf: int | None = None

    model_config = {"extra": "allow"}


class Pricing(BaseModel):
    aggressive: int | None = None
    market: int | None = None
    aspirational: int | None = None

    model_config = {"extra": "allow"}


class MarketStats(BaseModel):
    total_sold: int | None = None
    total_active: int | None = None
    median_price: float | None = None
    median_dom: float | None = None
    avg_sp_lp: float | None = None
    median_ppsf: float | None = None
    absorption_rate: float | None = None
    months_supply: float | None = None

    model_config = {"extra": "allow"}


class TrendItem(BaseModel):
    month: str | None = None
    month_num: int | None = None
    year: int | None = None
    volume: int | None = None
    median_price: float | None = None
    median_dom: float | None = None

    model_config = {"extra": "allow"}


class AgentStats(BaseModel):
    homes_sold: int | None = None
    avg_dom: int | None = None
    list_to_sale: float | None = None
    total_volume: float | None = None

    model_config = {"extra": "allow"}


class Confidence(BaseModel):
    overall: int | None = None
    grade: str | None = None
    comp_quality: int | None = None
    recency: int | None = None
    stability: int | None = None
    adj_depth: int | None = None
    variance: int | None = None
    sample: int | None = None

    model_config = {"extra": "allow"}


class ReportResponse(BaseModel):
    listing_key: str | None = None
    subject: dict[str, Any] | None = None
    comps: list[dict[str, Any]] = []
    adjustments: list[AdjustmentItem] | None = None
    valuation: Valuation | None = None
    pricing: Pricing | None = None
    market: MarketStats | None = None
    trends: list[TrendItem] | None = None
    agent: AgentStats | None = None
    confidence: Confidence | None = None
    price_direction: float | None = None

    model_config = {"extra": "allow"}
