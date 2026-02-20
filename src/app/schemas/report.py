from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class Color(str, Enum):
    GREEN = "#348E32"
    ORANGE = "#D97706"
    RED = "#DC2626"
    GRAY = "#787777ff"


class Grain(str, Enum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"
    UNKNOWN = "unknown"


class Span(str, Enum):
    MONTH = "month"
    THREE_MONTHS = "3months"
    SIX_MONTHS = "6months"
    YEAR = "year"
    UNKNOWN = "unknown"


class Indicator(str, Enum):
    TIME_ON_MARKET = "time_on_market"
    SALES_PROBABILITY = "sales_probability"
    SALES_VOLUME = "sales_volume"
    AVERAGE_PRICE = "average_price"
    AVERAGE_PRICE_PER_SQUARE_FOOT = "average_price_per_square_foot"
    UNKNOWN = "unknown"


class Status(str, Enum):
    MORE = "more"
    LESS = "less"
    UNKNOWN = "unknown"


class Comparison(BaseModel):
    feature: str
    value: str
    status: Status
    color: Color


class SimilarListingsItem(BaseModel):
    listing_key: str
    building_area: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    address: str = ""
    comparisons: List[Comparison]
    precedence: int


class SimilarListings(BaseModel):
    title: str
    description: str
    listing_key: str
    items: List[SimilarListingsItem]


class TimeSeries(BaseModel):
    title: str
    description: str
    time_grain: Grain
    span: Span
    indicator: Indicator
    time_series_items: List[float]


class MathematicalFormula(BaseModel):
    formula_type: str
    coefficients: List[float]
    domain: List[float]
    r_squared: Optional[float] = None
    formula_expression: str


class SpectrumPoint(BaseModel):
    projection: float
    probability: float


class Spectrum(BaseModel):
    title: str
    description: str
    listing_key: str
    indicator: Indicator
    probability: float
    projection: float
    tail_color: Color
    tail_text: str
    head_color: Color
    head_text: str
    spectrum_points: Optional[List[SpectrumPoint]] = None
    mathematical_formula: Optional[MathematicalFormula] = None
    price_range: Optional[List[float]] = None
    probability_range: Optional[List[float]] = None


class SuggestionItem(BaseModel):
    title: str
    description: str
    projection: float
    status: Status
    color: Color


class Suggestion(BaseModel):
    description: str
    suggestion_items: List[SuggestionItem]


class Textual(BaseModel):
    title: str
    description: str
    listing_key: str
    what: str
    why: str
    how: Suggestion


class GeographicalItem(BaseModel):
    latitude: float
    longitude: float
    radius: Optional[float] = None
    intensity: Optional[float] = None


class Geographical(BaseModel):
    title: str
    description: str
    listing_key: str
    indicator: Indicator
    similar_only: bool
    span: Span
    listing_geographical_info: GeographicalItem
    geographical_items: List[GeographicalItem]


class SpiderItem(BaseModel):
    indicator: Indicator
    upper_bound: float
    lower_bound: float
    actual_value: float


class Spider(BaseModel):
    title: str
    description: str
    listing_key: str
    arms: int
    spider_items: List[SpiderItem]


class Overall(BaseModel):
    title: str
    listing_key: str
    projection: float
    status: Status
    color: Color
    overall_items: List[str]


class AppliedChange(BaseModel):
    feature: str
    from_value: float
    to_value: float


class BaseMetrics(BaseModel):
    expected_close_price: float
    sale_probability: float
    list_price: float
    price_ratio: float


class NewMetrics(BaseModel):
    expected_close_price: float
    sale_probability: float
    price_ratio: float


class UpliftMetrics(BaseModel):
    expected_close_price_delta: float
    expected_close_price_delta_pct: float
    sale_probability_delta: float


class Scenario(BaseModel):
    scenario_id: str
    message: str
    applied_changes: List[AppliedChange]
    new: NewMetrics
    uplift: UpliftMetrics


class UpgradeImpact(BaseModel):
    property_id: str
    base: BaseMetrics
    scenarios: List[Scenario]
