from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from .config import settings


class MongoClient:
    def __init__(self) -> None:
        self.client: AsyncIOMotorClient | None = None

    def get_client(self) -> AsyncIOMotorClient:
        if self.client is None:
            self.client = AsyncIOMotorClient(settings.MONGODB_URL)
        return self.client

    def get_database(self) -> AsyncIOMotorDatabase:
        return self.get_client()[settings.MONGODB_DB]

    def close(self) -> None:
        if self.client is not None:
            self.client.close()


mongo_client = MongoClient()
