# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

This project is a Python/FastAPI refactor of the Go microservices in `go_project/`. The goal is to consolidate the Go services (user, property, notification, subscription, gateway) into a single Python backend while maintaining equivalent functionality.

## Build and Development Commands

```bash
# Local development with Docker
docker-compose up                    # Start all services (web, db, redis, mailpit, worker)
docker-compose up -d                 # Start in detached mode

# Run the dev server directly (requires local Python 3.11+)
cd src && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Database migrations (run from src/ directory)
cd src && alembic upgrade head       # Apply all migrations
cd src && alembic revision --autogenerate -m "description"  # Create new migration

# Background worker
arq app.core.worker.settings.WorkerSettings

# Linting and type checking
ruff check .                         # Lint
ruff check . --fix                   # Lint with auto-fix
mypy .                               # Type check

# Tests (via Docker)
docker-compose run pytest
```

## Architecture

### Layered Structure
The codebase follows a layered architecture within `src/app/`:

- **API Layer** (`api/v1/`): FastAPI route handlers. Routes are versioned under `/api/v1/`.
- **Services** (`services/`): Business logic. Services receive dependencies (db session, redis) via FastAPI's dependency injection.
- **CRUD** (`crud/`): Database operations using FastCRUD. Example: `crud_users = FastCRUD[User, ...]`
- **Models** (`models/`): SQLAlchemy models inheriting from `Base` (which combines `DeclarativeBase` + `MappedAsDataclass`).
- **Schemas** (`schemas/`): Pydantic models for request/response validation.

### Key Patterns

**Dependency Injection**: Services are instantiated via FastAPI dependencies in `api/dependencies.py`:
```python
async def get_users_service(db: AsyncSession, redis: Redis) -> UserService:
    return UserService(db, redis)
```

**Configuration**: All settings are in `core/config.py` using pydantic-settings. The `Settings` class inherits from multiple settings classes (PostgresSettings, RedisSettings, etc.). Config is loaded from `src/.env`.

**Database**: Async PostgreSQL via asyncpg + SQLAlchemy 2.0. Session obtained via `async_get_db()` dependency.

**Background Jobs**: Uses arq with Redis. Worker settings in `core/worker/settings.py`, job functions in `core/worker/functions.py`.

**Admin Interface**: CRUDAdmin mounted at `/admin` (configurable via `CRUD_ADMIN_MOUNT_PATH`).

### Infrastructure Services
- **PostgreSQL**: Primary database
- **Redis**: Caching (`core/utils/cache.py`), job queue, rate limiting
- **Elasticsearch**: Property search (`core/search/elasticsearch_client.py`)
- **Mailpit**: Local email testing (SMTP on port 1025, UI on port 8025)

## Environment Setup

1. Copy `.env.example` to `src/.env`
2. Generate a new `SECRET_KEY`: `openssl rand -hex 32`
3. Update database and other credentials
