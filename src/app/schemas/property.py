from datetime import datetime
from typing import List, Optional, Any, Dict

from pydantic import BaseModel, Field, ConfigDict


class PropertyMedia(BaseModel):
    media_url: str = Field(alias="MediaURL")
    media_type: str = Field(alias="MediaType")
    order: Optional[int] = Field(None, alias="Order")
    description: Optional[str] = Field(None, alias="Description")
    
    model_config = ConfigDict(populate_by_name=True)


class PropertyBase(BaseModel):
    listing_key: str
    created_at: datetime
    updated_at: datetime
    crawled_at: datetime
    modification_timestamp: Optional[datetime] = None
    photos_change_timestamp: Optional[datetime] = None
    price_change_timestamp: Optional[datetime] = None
    on_market_date: Optional[datetime] = None
    off_market_date: Optional[datetime] = None
    close_date: Optional[datetime] = None
    listing_contract_date: Optional[datetime] = None
    contract_status_change_date: Optional[datetime] = None

    listing_id: Optional[str] = None
    universal_property_id: Optional[str] = None
    mls_status: Optional[str] = None
    standard_status: Optional[str] = None
    property_type: Optional[str] = None
    property_sub_type: Optional[str] = None
    virtual_tour_url_branded: Optional[str] = None
    virtual_tour_url_unbranded: Optional[str] = None
    internet_address_display_yn: Optional[bool] = None

    unparsed_address: Optional[str] = None
    street_number: Optional[str] = None
    street_number_numeric: Optional[str] = None
    street_dir_prefix: Optional[str] = None
    street_name: Optional[str] = None
    street_suffix: Optional[str] = None
    street_suffix_modifier: Optional[str] = None
    street_dir_suffix: Optional[str] = None
    city: Optional[str] = None
    state_or_province: Optional[str] = None
    postal_code: Optional[str] = None
    postal_code_plus4: Optional[str] = None
    county_or_parish: Optional[str] = None
    subdivision_name: Optional[str] = None
    cross_street: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    coordinates: Optional[List[float]] = None

    list_price: Optional[float] = None
    original_list_price: Optional[float] = None
    close_price: Optional[float] = None
    association_fee: Optional[float] = None
    association_fee_frequency: Optional[str] = None
    tax_annual_amount: Optional[float] = None
    cap_rate: Optional[float] = None
    gross_scheduled_income: Optional[float] = None
    total_actual_rent: Optional[float] = None

    bedrooms_total: Optional[int] = None
    bathrooms_total_integer: Optional[int] = None
    bathrooms_full: Optional[int] = None
    bathrooms_half: Optional[int] = None
    living_area: Optional[float] = None
    lot_size_area: Optional[float] = None
    lot_size_square_feet: Optional[float] = None
    lot_size_acres: Optional[float] = None
    lot_size_units: Optional[str] = None
    year_built: Optional[int] = None
    stories: Optional[float] = None
    stories_total: Optional[int] = None
    days_on_market: Optional[int] = None
    garage_spaces: Optional[int] = None
    carport_spaces: Optional[int] = None
    parking_total: Optional[int] = None
    photos_count: Optional[int] = None
    primary_photo_url: Optional[str] = None

    appliances: Optional[List[str]] = None
    heating: Optional[List[str]] = None
    cooling: Optional[List[str]] = None
    fireplace_features: Optional[List[str]] = None
    flooring: Optional[List[str]] = None
    interior_features: Optional[List[str]] = None
    exterior_features: Optional[List[str]] = None
    parking_features: Optional[List[str]] = None
    lot_features: Optional[List[str]] = None
    sewer: Optional[List[str]] = None
    water_source: Optional[List[str]] = None
    electric: Optional[List[str]] = None
    utilities: Optional[List[str]] = None
    community_features: Optional[List[str]] = None
    construction_materials: Optional[List[str]] = None
    roof: Optional[List[str]] = None
    foundation_details: Optional[List[str]] = None
    accessibility_features: Optional[List[str]] = None
    architectural_style: Optional[List[str]] = None
    window_features: Optional[List[str]] = None
    patio_and_porch_features: Optional[List[str]] = None
    fencing: Optional[List[str]] = None
    laundry_features: Optional[List[str]] = None
    pool_features: Optional[List[str]] = None
    spa_features: Optional[List[str]] = None
    view: Optional[List[str]] = None
    security_features: Optional[List[str]] = None
    rent_includes: Optional[List[str]] = None
    association_amenities: Optional[List[str]] = None
    association_fee_includes: Optional[List[str]] = None
    listing_terms: Optional[List[str]] = None
    buyer_financing: Optional[List[str]] = None

    pool_private_yn: Optional[bool] = None
    waterfront_yn: Optional[bool] = None
    association_yn: Optional[bool] = None

    elementary_school: Optional[str] = None
    middle_or_junior_school: Optional[str] = None
    high_school: Optional[str] = None
    elementary_school_district: Optional[str] = None
    high_school_district: Optional[str] = None

    public_remarks: Optional[str] = None
    private_remarks: Optional[str] = None

    list_agent_full_name: Optional[str] = None
    list_agent_first_name: Optional[str] = None
    list_agent_last_name: Optional[str] = None
    list_agent_mls_id: Optional[str] = None
    list_agent_key: Optional[str] = None
    list_agent_email: Optional[str] = None
    list_agent_phone: Optional[str] = None
    list_agent_direct_phone: Optional[str] = None
    list_agent_cell_phone: Optional[str] = None
    list_agent_preferred_phone: Optional[str] = None
    list_agent_preferred_phone_ext: Optional[str] = None
    list_agent_office_phone: Optional[str] = None
    list_agent_state_license: Optional[str] = None
    list_agent_fax: Optional[str] = None
    list_agent_pager: Optional[str] = None
    list_agent_voice_mail: Optional[str] = None
    list_agent_toll_free_phone: Optional[str] = None
    list_agent_home_phone: Optional[str] = None
    list_agent_aor: Optional[str] = None

    list_office_name: Optional[str] = None
    list_office_key: Optional[str] = None
    list_office_mls_id: Optional[str] = None
    list_office_email: Optional[str] = None
    list_office_phone: Optional[str] = None
    list_office_phone_ext: Optional[str] = None
    list_office_url: Optional[str] = None
    list_office_aor: Optional[str] = None
    list_broker_license: Optional[str] = None
    attribution_contact: Optional[str] = None

    buyer_agent_full_name: Optional[str] = None
    buyer_agent_key: Optional[str] = None
    buyer_agent_mls_id: Optional[str] = None
    buyer_agent_email: Optional[str] = None
    buyer_agent_preferred_phone: Optional[str] = None
    buyer_agent_state_license: Optional[str] = None

    buyer_office_name: Optional[str] = None
    buyer_office_key: Optional[str] = None
    buyer_office_mls_id: Optional[str] = None
    buyer_office_email: Optional[str] = None
    buyer_office_phone: Optional[str] = None

    co_list_agent_full_name: Optional[str] = None
    co_list_agent_mls_id: Optional[str] = None
    co_list_agent_preferred_phone: Optional[str] = None
    co_list_agent_office_phone: Optional[str] = None

    co_list_office_name: Optional[str] = None
    co_list_office_mls_id: Optional[str] = None
    co_list_office_phone: Optional[str] = None

    co_buyer_agent_full_name: Optional[str] = None
    co_buyer_agent_mls_id: Optional[str] = None
    co_buyer_agent_email: Optional[str] = None
    co_buyer_agent_preferred_phone: Optional[str] = None

    co_buyer_office_name: Optional[str] = None
    co_buyer_office_mls_id: Optional[str] = None
    co_buyer_office_email: Optional[str] = None
    co_buyer_office_phone: Optional[str] = None

    association_name: Optional[str] = None

    media: Optional[List[Dict[str, Any]]] = None
    
    model_config = ConfigDict(from_attributes=True)


class PropertyPrice(BaseModel):
    amount: Optional[float]
    currency: str = "USD"
    period: str = "sale"


class PropertySummary(BaseModel):
    id: str
    name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    image_url: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    price: PropertyPrice
    rating: float = 0


class PropertyListResponse(BaseModel):
    properties: List[PropertySummary]
    total: int


class PropertySuggestion(BaseModel):
    listing_key: str
    line1: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    category: str = "address"


class PropertySuggestResponse(BaseModel):
    suggestions: List[PropertySuggestion]


class PropertyDetailResponse(BaseModel):
    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    area: Optional[float] = None
    amenities: List[str] = []
    images: List[str] = []
    primary_photo: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    price: PropertyPrice
    rating: float = 0
