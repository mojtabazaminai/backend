from typing import Any, Dict, List
from elasticsearch import AsyncElasticsearch
from ...core.config import settings
from ...schemas.property import PropertySummary, PropertySuggestion, PropertyPrice

DEFAULT_SUGGEST_LIMIT = 10
MAX_SUGGEST_LIMIT = 25


def _clamp_suggest_limit(limit: int) -> int:
    if limit <= 0:
        return DEFAULT_SUGGEST_LIMIT
    if limit > MAX_SUGGEST_LIMIT:
        return MAX_SUGGEST_LIMIT
    return limit


def _title_case(value: str | None) -> str:
    parts = (value or "").strip().split()
    if not parts:
        return ""
    return " ".join(part[:1].upper() + part[1:].lower() if part else "" for part in parts)


class PropertyService:
    def __init__(self, es_client: AsyncElasticsearch):
        self.es_client = es_client
        self.index = settings.ELASTICSEARCH_INDEX

    async def search_properties(
        self, 
        query: str | None = None, 
        page: int = 1, 
        limit: int = 10,
        filters: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        es_query: Dict[str, Any] = {"bool": {"must": []}}
        
        if query:
            es_query["bool"]["must"].append({
                "multi_match": {
                    "query": query,
                    "fields": ["listing_key^3", "city^2", "state_or_province^2", "postal_code", "property_type"],
                    "type": "best_fields",
                    "operator": "and"
                }
            })
            
        if filters:
            for key, value in filters.items():
                if value:
                    if isinstance(value, list):
                         es_query["bool"]["must"].append({"terms": {key: value}})
                    else:
                         es_query["bool"]["must"].append({"term": {key: value}})

        if not es_query["bool"]["must"]:
            es_query = {"match_all": {}}

        from_ = (page - 1) * limit

        response = await self.es_client.search(
            index=self.index,
            query=es_query,
            from_=from_,
            size=limit,
            track_total_hits=True
        )

        hits = response["hits"]["hits"]
        total = response["hits"]["total"]["value"]

        properties = []
        for hit in hits:
            source = hit["_source"]
            properties.append(self._map_hit_to_summary(source))

        return {
            "properties": properties,
            "total": total
        }

    async def suggest_properties(self, query: str, limit: int = 10) -> List[PropertySuggestion]:
        query = query.strip()
        if not query:
            return []
        limit = _clamp_suggest_limit(limit)

        body: Dict[str, Any] = {
            "size": limit,
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "type": "bool_prefix",
                                "fields": [
                                    "unparsed_address^3",
                                    "city^2",
                                    "postal_code",
                                    "state_or_province",
                                ],
                            }
                        }
                    ]
                }
            },
            "_source": [
                "listing_key",
                "unparsed_address",
                "city",
                "state_or_province",
                "postal_code",
            ],
        }
        response = await self.es_client.search(index=self.index, body=body)
        hits = response.get("hits", {}).get("hits", [])

        result = []
        for hit in hits:
            source = hit.get("_source", {})
            listing_key = source.get("listing_key", "")
            line1 = (source.get("unparsed_address") or "").strip()
            if not listing_key or not line1:
                continue

            result.append(PropertySuggestion(
                listing_key=listing_key,
                line1=line1,
                city=_title_case(source.get("city")),
                state=(source.get("state_or_province") or "").strip().upper(),
                postal_code=(source.get("postal_code") or "").strip(),
                category="Addresses",
            ))

        return result

    def _map_hit_to_summary(self, source: Dict[str, Any]) -> PropertySummary:
        return PropertySummary(
            id=source.get("listing_key", ""),
            name=source.get("unparsed_address"),
            city=source.get("city"),
            state=source.get("state_or_province"),
            postal_code=source.get("postal_code"),
            image_url=source.get("primary_photo_url"),
            price=PropertyPrice(
                amount=source.get("list_price"),
                currency="USD",
                period="sale"
            ),
            rating=0 
        )
