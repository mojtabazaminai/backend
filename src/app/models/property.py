from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db.database import Base


class Property(Base):
    __tablename__ = "property"
    __table_args__ = {"schema": "public"}  # Assuming public schema for properties as per other potential tables

    # Primary Key
    listing_key: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    crawled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    modification_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    photos_change_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    price_change_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    on_market_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    off_market_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    close_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    listing_contract_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    contract_status_change_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Basic Info
    listing_id: Mapped[str] = mapped_column(String, nullable=True)
    universal_property_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    mls_status: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    standard_status: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    property_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    property_sub_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    virtual_tour_url_branded: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    virtual_tour_url_unbranded: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    internet_address_display_yn: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # Address
    unparsed_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    street_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    street_number_numeric: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    street_dir_prefix: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    street_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    street_suffix: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    street_suffix_modifier: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    street_dir_suffix: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    state_or_province: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    postal_code_plus4: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    county_or_parish: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    subdivision_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    cross_street: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    coordinates: Mapped[Optional[List[float]]] = mapped_column(JSONB, nullable=True)

    # Pricing
    list_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    original_list_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    close_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    association_fee: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    association_fee_frequency: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    tax_annual_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cap_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gross_scheduled_income: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_actual_rent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Details
    bedrooms_total: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bathrooms_total_integer: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bathrooms_full: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bathrooms_half: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    living_area: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lot_size_area: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lot_size_square_feet: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lot_size_acres: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lot_size_units: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    year_built: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    stories: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    stories_total: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    days_on_market: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    garage_spaces: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    carport_spaces: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    parking_total: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    photos_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    primary_photo_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Features (Arrays/JSON)
    appliances: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    heating: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    cooling: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    fireplace_features: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    flooring: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    interior_features: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    exterior_features: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    parking_features: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    lot_features: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    sewer: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    water_source: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    electric: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    utilities: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    community_features: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    construction_materials: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    roof: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    foundation_details: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True) # Not explicitly in Go struct but common
    accessibility_features: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    architectural_style: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    window_features: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    patio_and_porch_features: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    fencing: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    laundry_features: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    pool_features: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    spa_features: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    view: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    security_features: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    rent_includes: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    association_amenities: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    association_fee_includes: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    listing_terms: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    buyer_financing: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)

    pool_private_yn: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    waterfront_yn: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    association_yn: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # Schools
    elementary_school: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    middle_or_junior_school: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    high_school: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    elementary_school_district: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    high_school_district: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Remarks
    public_remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    private_remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Agents & Offices
    list_agent_full_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    list_agent_first_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    list_agent_last_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    list_agent_mls_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    list_agent_key: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    list_agent_email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    list_agent_phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    list_agent_direct_phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    list_agent_cell_phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    list_agent_preferred_phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    list_agent_preferred_phone_ext: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    list_agent_office_phone: Mapped[Optional[str]] = mapped_column(String, nullable=True) # Not standard but useful
    list_agent_state_license: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    list_agent_fax: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    list_agent_pager: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    list_agent_voice_mail: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    list_agent_toll_free_phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    list_agent_home_phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    list_agent_aor: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    list_office_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    list_office_key: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    list_office_mls_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    list_office_email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    list_office_phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    list_office_phone_ext: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    list_office_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    list_office_aor: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    list_broker_license: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    attribution_contact: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    buyer_agent_full_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    buyer_agent_key: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    buyer_agent_mls_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    buyer_agent_email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    buyer_agent_preferred_phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    buyer_agent_state_license: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    buyer_office_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    buyer_office_key: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    buyer_office_mls_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    buyer_office_email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    buyer_office_phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    co_list_agent_full_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    co_list_agent_mls_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    co_list_agent_preferred_phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    co_list_agent_office_phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    co_list_office_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    co_list_office_mls_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    co_list_office_phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    co_buyer_agent_full_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    co_buyer_agent_mls_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    co_buyer_agent_email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    co_buyer_agent_preferred_phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    co_buyer_office_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    co_buyer_office_mls_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    co_buyer_office_email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    co_buyer_office_phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    association_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Media (JSON)
    media: Mapped[Optional[List[dict]]] = mapped_column(JSONB, nullable=True)
