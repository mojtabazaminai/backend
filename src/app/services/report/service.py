from typing import List

from ...models.property import Property
from ...schemas.property import PropertyBase
from ...schemas.report import (
    AppliedChange,
    BaseMetrics,
    Color,
    Comparison,
    Indicator,
    MathematicalFormula,
    NewMetrics,
    Scenario,
    SimilarListings,
    SimilarListingsItem,
    Spectrum,
    SpectrumPoint,
    Status,
    UpgradeImpact,
    UpliftMetrics,
)
from .client import InferenceClient


class ReportService:
    def __init__(self):
        self.client = InferenceClient()

    async def get_similar_listings(self, listing_key: str, property_data: Property) -> SimilarListings:
        # Convert property model to dict for inference service
        prop_dict = PropertyBase.model_validate(property_data).model_dump(mode="json")

        inference_resp = await self.client.post(
            "/api/v1/inference/similar", {"property_data": prop_dict, "limit": 10}
        )
        similar_items_data = inference_resp.get("similar_properties", [])

        items = []
        for idx, item in enumerate(similar_items_data):
            comparisons: List[Comparison] = []
            # Example comparison logic (simplified)
            if item.get("list_price") and property_data.list_price:
                diff = item["list_price"] - property_data.list_price
                if diff != 0:
                    status = Status.MORE if diff > 0 else Status.LESS
                    comparisons.append(
                        Comparison(
                            feature="List Price",
                            value=f"${abs(diff):,.0f}",
                            status=status,
                            color=Color.GREEN if status == Status.MORE else Color.ORANGE,
                        )
                    )

            items.append(
                SimilarListingsItem(
                    listing_key=item.get("property_id", ""),
                    building_area=item.get("building_area_total"),
                    bedrooms=item.get("bedrooms_total"),
                    bathrooms=item.get("bathrooms_total_integer"),
                    address=item.get("unparsed_address", ""),
                    comparisons=comparisons,
                    precedence=idx,
                )
            )

        return SimilarListings(
            title="Similar Listings",
            description="These Listings are the most similar to the one you are viewing.",
            listing_key=listing_key,
            items=items,
        )

    async def get_spectrum(
        self, listing_key: str, indicator: Indicator, property_data: Property
    ) -> Spectrum:
        prop_dict = PropertyBase.model_validate(property_data).model_dump(mode="json")

        analysis = await self.client.post(
            "/api/v1/inference/price-probability-analysis", {"property_data": prop_dict}
        )

        points = []
        for p in analysis.get("price_probability_analysis", []):
            points.append(
                SpectrumPoint(
                    projection=p["recommended_price"], probability=p["actual_probability"]
                )
            )

        math_formula = None
        if "mathematical_formula" in analysis:
            mf = analysis["mathematical_formula"]
            math_formula = MathematicalFormula(
                formula_type=mf["formula_type"],
                coefficients=mf["coefficients"],
                domain=mf["domain"],
                r_squared=mf.get("r_squared"),
                formula_expression=mf["formula_expression"],
            )

        return Spectrum(
            title=f"Probability Distribution of {indicator.value}",
            description="description",
            listing_key=listing_key,
            indicator=indicator,
            probability=analysis.get("current_sale_probability", 0.0),
            projection=analysis.get("current_list_price", 0.0),
            tail_color=Color.RED,
            tail_text="Low chance",
            head_color=Color.GREEN,
            head_text="High chance",
            spectrum_points=points,
            mathematical_formula=math_formula,
            price_range=analysis.get("price_bounds"),
            probability_range=analysis.get("achievable_probability_range"),
        )

    async def get_upgrade_impact(self, listing_key: str, property_data: Property) -> UpgradeImpact:
        prop_dict = PropertyBase.model_validate(property_data).model_dump(mode="json")

        resp = await self.client.post(
            "/api/v1/inference/upgrade-impact", {"property_data": prop_dict}
        )

        base = resp.get("base", {})
        scenarios_data = resp.get("scenarios", [])

        scenarios = []
        for s in scenarios_data:
            changes = [AppliedChange(**c) for c in s.get("applied_changes", [])]
            new_m = s.get("new", {})
            uplift_m = s.get("uplift", {})

            scenarios.append(
                Scenario(
                    scenario_id=s.get("scenario_id", ""),
                    message=s.get("message", ""),
                    applied_changes=changes,
                    new=NewMetrics(**new_m),
                    uplift=UpliftMetrics(**uplift_m),
                )
            )

        return UpgradeImpact(
            property_id=resp.get("property_id", ""),
            base=BaseMetrics(**base),
            scenarios=scenarios,
        )


report_service = ReportService()
