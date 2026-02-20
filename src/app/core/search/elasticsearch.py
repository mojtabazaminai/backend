from elasticsearch import AsyncElasticsearch

from ..config import settings


class ElasticsearchClient:
    def __init__(self) -> None:
        self.client: AsyncElasticsearch | None = None

    @staticmethod
    def _get_auth_kwargs() -> dict[str, str | tuple[str, str]]:
        # API key takes precedence when both auth methods are configured.
        if settings.ELASTICSEARCH_API_KEY:
            return {"api_key": settings.ELASTICSEARCH_API_KEY}

        if settings.ELASTICSEARCH_USERNAME and settings.ELASTICSEARCH_PASSWORD:
            return {"basic_auth": (settings.ELASTICSEARCH_USERNAME, settings.ELASTICSEARCH_PASSWORD)}

        return {}

    def get_client(self) -> AsyncElasticsearch:
        if self.client is None:
            self.client = AsyncElasticsearch(
                hosts=[settings.ELASTICSEARCH_URL],
                verify_certs=False,  # For development
                **self._get_auth_kwargs(),
            )
        return self.client

    async def close(self) -> None:
        if self.client:
            await self.client.close()


es_client = ElasticsearchClient()
