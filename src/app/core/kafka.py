from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from .config import settings


class KafkaClient:
    def __init__(self) -> None:
        self.producer: AIOKafkaProducer | None = None

    @staticmethod
    def _bootstrap_servers() -> list[str]:
        return [server.strip() for server in settings.KAFKA_BOOTSTRAP_SERVERS.split(",") if server.strip()]

    async def get_producer(self) -> AIOKafkaProducer:
        if self.producer is None:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self._bootstrap_servers(),
                client_id=settings.KAFKA_CLIENT_ID,
            )
            await self.producer.start()
        return self.producer

    async def create_consumer(self, *topics: str, group_id: str | None = None) -> AIOKafkaConsumer:
        consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=self._bootstrap_servers(),
            client_id=settings.KAFKA_CLIENT_ID,
            group_id=group_id or settings.KAFKA_CONSUMER_GROUP,
        )
        await consumer.start()
        return consumer

    async def close_producer(self) -> None:
        if self.producer is not None:
            await self.producer.stop()
            self.producer = None


kafka_client = KafkaClient()
