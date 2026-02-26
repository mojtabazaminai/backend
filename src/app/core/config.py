import os
from enum import Enum

from pydantic import AliasChoices, Field, SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ElasticsearchSettings(BaseSettings):
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    ELASTICSEARCH_USERNAME: str | None = None
    ELASTICSEARCH_PASSWORD: str | None = None
    ELASTICSEARCH_API_KEY: str | None = None
    ELASTICSEARCH_INDEX: str = "properties"


class IngestSettings(BaseSettings):
    MLS_SOURCE: str = "local_file"
    MLS_STORAGE_LOCAL_DIRECTORY: str = "tmp/properties_dump"
    MLS_RAW_MESSAGE_TOPIC: str = "backend-ingest-mls-raw"

    MLS_REALTYFEED_URL: str = ""
    MLS_REALTYFEED_CLIENT_ID: str = ""
    MLS_REALTYFEED_CLIENT_SECRET: str = ""

    FOURSQUARE_API_KEY: str = ""


class AppSettings(BaseSettings):
    APP_NAME: str = "FastAPI app"
    APP_DESCRIPTION: str | None = None
    APP_VERSION: str | None = None
    LICENSE_NAME: str | None = None
    CONTACT_NAME: str | None = None
    CONTACT_EMAIL: str | None = None


class CryptSettings(BaseSettings):
    SECRET_KEY: SecretStr = SecretStr("secret-key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7


class FileLoggerSettings(BaseSettings):
    FILE_LOG_MAX_BYTES: int = 10 * 1024 * 1024
    FILE_LOG_BACKUP_COUNT: int = 5
    FILE_LOG_FORMAT_JSON: bool = True
    FILE_LOG_LEVEL: str = "INFO"

    # Include request ID, path, method, client host, and status code in the file log
    FILE_LOG_INCLUDE_REQUEST_ID: bool = True
    FILE_LOG_INCLUDE_PATH: bool = True
    FILE_LOG_INCLUDE_METHOD: bool = True
    FILE_LOG_INCLUDE_CLIENT_HOST: bool = True
    FILE_LOG_INCLUDE_STATUS_CODE: bool = True


class ConsoleLoggerSettings(BaseSettings):
    CONSOLE_LOG_LEVEL: str = "INFO"
    CONSOLE_LOG_FORMAT_JSON: bool = False

    # Include request ID, path, method, client host, and status code in the console log
    CONSOLE_LOG_INCLUDE_REQUEST_ID: bool = False
    CONSOLE_LOG_INCLUDE_PATH: bool = False
    CONSOLE_LOG_INCLUDE_METHOD: bool = False
    CONSOLE_LOG_INCLUDE_CLIENT_HOST: bool = False
    CONSOLE_LOG_INCLUDE_STATUS_CODE: bool = False


class DatabaseSettings(BaseSettings):
    pass


class SQLiteSettings(DatabaseSettings):
    SQLITE_URI: str = "./sql_app.db"
    SQLITE_SYNC_PREFIX: str = "sqlite:///"
    SQLITE_ASYNC_PREFIX: str = "sqlite+aiosqlite:///"


class MySQLSettings(DatabaseSettings):
    MYSQL_USER: str = "username"
    MYSQL_PASSWORD: str = "password"
    MYSQL_SERVER: str = "localhost"
    MYSQL_PORT: int = 5432
    MYSQL_DB: str = "dbname"
    MYSQL_SYNC_PREFIX: str = "mysql://"
    MYSQL_ASYNC_PREFIX: str = "mysql+aiomysql://"
    MYSQL_URL: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def MYSQL_URI(self) -> str:
        credentials = f"{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
        location = f"{self.MYSQL_SERVER}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
        return f"{credentials}@{location}"


class PostgresSettings(DatabaseSettings):
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str | None = None
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "postgres"

    POSTGRES_SYNC_PREFIX: str = "postgresql://"
    POSTGRES_ASYNC_PREFIX: str = "postgresql+asyncpg://"

    @computed_field
    @property
    def POSTGRES_URI(self) -> str:
        if self.POSTGRES_PASSWORD:
            credentials = f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
        else:
            credentials = self.POSTGRES_USER

        location = f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        return f"{credentials}@{location}"

    @computed_field
    @property
    def POSTGRES_SYNC_URL(self) -> str:
        return f"{self.POSTGRES_SYNC_PREFIX}{self.POSTGRES_URI}"

    @computed_field
    @property
    def POSTGRES_ASYNC_URL(self) -> str:
        return f"{self.POSTGRES_ASYNC_PREFIX}{self.POSTGRES_URI}"


class MongoDBSettings(BaseSettings):
    MONGODB_USER: str | None = None
    MONGODB_PASSWORD: str | None = None
    MONGODB_HOST: str = "localhost"
    MONGODB_PORT: int = 27017
    MONGODB_DB: str = "zaminai"
    MONGODB_URI: str | None = None

    @computed_field
    @property
    def MONGODB_URL(self) -> str:
        if self.MONGODB_URI:
            return self.MONGODB_URI
        if self.MONGODB_USER and self.MONGODB_PASSWORD:
            credentials = f"{self.MONGODB_USER}:{self.MONGODB_PASSWORD}@"
        else:
            credentials = ""
        return f"mongodb://{credentials}{self.MONGODB_HOST}:{self.MONGODB_PORT}/{self.MONGODB_DB}"


class KafkaSettings(BaseSettings):
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_CLIENT_ID: str = "zaminai-backend"
    KAFKA_CONSUMER_GROUP: str = "zaminai-ingest"

class FirstUserSettings(BaseSettings):
    ADMIN_NAME: str = "admin"
    ADMIN_EMAIL: str = "admin@admin.com"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "!Ch4ng3Th1sP4ssW0rd!"


class TestSettings(BaseSettings):
    ...


class RedisCacheSettings(BaseSettings):
    REDIS_CACHE_HOST: str = "localhost"
    REDIS_CACHE_PORT: int = 6379
    REDIS_CACHE_DB: int = 0
    REDIS_CACHE_PASSWORD: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def REDIS_CACHE_URL(self) -> str:
        if self.REDIS_CACHE_PASSWORD:
            credentials = f":{self.REDIS_CACHE_PASSWORD}@"
        else:
            credentials = ""
        return f"redis://{credentials}{self.REDIS_CACHE_HOST}:{self.REDIS_CACHE_PORT}/{self.REDIS_CACHE_DB}"


class ClientSideCacheSettings(BaseSettings):
    CLIENT_CACHE_MAX_AGE: int = 60


class RedisQueueSettings(BaseSettings):
    REDIS_QUEUE_HOST: str = "localhost"
    REDIS_QUEUE_PORT: int = 6379
    REDIS_QUEUE_DB: int = 0
    REDIS_QUEUE_PASSWORD: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def REDIS_QUEUE_PASSWORD_OR_NONE(self) -> str | None:
        if self.REDIS_QUEUE_PASSWORD:
            return self.REDIS_QUEUE_PASSWORD
        return None


class RedisRateLimiterSettings(BaseSettings):
    REDIS_RATE_LIMIT_HOST: str = "localhost"
    REDIS_RATE_LIMIT_PORT: int = 6379
    REDIS_RATE_LIMIT_DB: int = 0
    REDIS_RATE_LIMIT_PASSWORD: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def REDIS_RATE_LIMIT_URL(self) -> str:
        if self.REDIS_RATE_LIMIT_PASSWORD:
            credentials = f":{self.REDIS_RATE_LIMIT_PASSWORD}@"
        else:
            credentials = ""
        return f"redis://{credentials}{self.REDIS_RATE_LIMIT_HOST}:{self.REDIS_RATE_LIMIT_PORT}/{self.REDIS_RATE_LIMIT_DB}"


class DefaultRateLimitSettings(BaseSettings):
    DEFAULT_RATE_LIMIT_LIMIT: int = 10
    DEFAULT_RATE_LIMIT_PERIOD: int = 3600


class CRUDAdminSettings(BaseSettings):
    CRUD_ADMIN_ENABLED: bool = True
    CRUD_ADMIN_MOUNT_PATH: str = "/admin"

    CRUD_ADMIN_ALLOWED_IPS_LIST: list[str] | None = None
    CRUD_ADMIN_ALLOWED_NETWORKS_LIST: list[str] | None = None
    CRUD_ADMIN_MAX_SESSIONS: int = 10
    CRUD_ADMIN_SESSION_TIMEOUT: int = 1440
    SESSION_SECURE_COOKIES: bool = False

    CRUD_ADMIN_TRACK_EVENTS: bool = False
    CRUD_ADMIN_TRACK_SESSIONS: bool = False

    CRUD_ADMIN_REDIS_ENABLED: bool = False
    CRUD_ADMIN_REDIS_HOST: str = "localhost"
    CRUD_ADMIN_REDIS_PORT: int = 6379
    CRUD_ADMIN_REDIS_DB: int = 0
    CRUD_ADMIN_REDIS_PASSWORD: str | None = "None"
    CRUD_ADMIN_REDIS_SSL: bool = False


class EnvironmentOption(str, Enum):
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"


class EnvironmentSettings(BaseSettings):
    ENVIRONMENT: EnvironmentOption = EnvironmentOption.LOCAL


class CORSSettings(BaseSettings):
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    CORS_METHODS: list[str] = ["*"]
    CORS_HEADERS: list[str] = ["*"]
    ALLOW_ORIGINS: str = Field(default="", validation_alias=AliasChoices("ALLOW_ORIGINS", "allow_origins"))

    @computed_field
    @property
    def RESOLVED_CORS_ORIGINS(self) -> list[str]:
        extra_origins = [origin.strip() for origin in self.ALLOW_ORIGINS.split(",") if origin.strip()]
        if not extra_origins:
            return self.CORS_ORIGINS
        return list(dict.fromkeys([*self.CORS_ORIGINS, *extra_origins]))


class GoogleSettings(BaseSettings):
    GOOGLE_CLIENT_ID: str = "your-google-client-id"
    GOOGLE_CLIENT_SECRET: str = "your-google-client-secret"
    GOOGLE_REDIRECT_URL: str = "http://localhost:8000/api/v1/users/google/callback"


class EmailSettings(BaseSettings):
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str = "noreply@example.com"
    SMTP_FROM_NAME: str = "ZaminAI"
    SMTP_TLS: bool = False
    SMTP_SSL: bool = False


class PaymentSettings(BaseSettings):
    PAYMENT_PROVIDER: str = "mock"
    PAYMENT_STRIPE_SECRET_KEY: str | None = None
    PAYMENT_STRIPE_PRICE_ID: str = "price_mock"
    PAYMENT_STRIPE_SUCCESS_URL: str = "http://localhost:3000/checkout/success"
    PAYMENT_STRIPE_CANCEL_URL: str = "http://localhost:3000/checkout/cancel"
    PAYMENT_MOCK_CHECKOUT_BASE_URL: str = "http://localhost:3000/checkout/mock"


class APISettings(BaseSettings):
    GATEWAY_PRIVATE_HEADER_API_KEY: str = "your-private-api-key"


class CMASettings(BaseSettings):
    CMA_API_BASE_URL: str = "http://localhost:9000"
    CMA_API_KEY: str = ""
    CMA_API_TIMEOUT: int = 60


class Settings(
    AppSettings,
    SQLiteSettings,
    PostgresSettings,
    MongoDBSettings,
    CryptSettings,
    FirstUserSettings,
    TestSettings,
    RedisCacheSettings,
    ClientSideCacheSettings,
    RedisQueueSettings,
    RedisRateLimiterSettings,
    DefaultRateLimitSettings,
    CRUDAdminSettings,
    EnvironmentSettings,
    CORSSettings,
    FileLoggerSettings,
    ConsoleLoggerSettings,
    GoogleSettings,
    EmailSettings,
    PaymentSettings,
    APISettings,
    ElasticsearchSettings,
    KafkaSettings,
    IngestSettings,
    CMASettings,
):
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
