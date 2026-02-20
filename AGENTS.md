# Repository Guidelines

## Project Structure & Module Organization
- `src/app/`: Python FastAPI application (API routes, services, CRUD, models, schemas).
- `src/migrations/`: Alembic migrations for the PostgreSQL schema.
- `src/alembic.ini`: Alembic configuration.
- `go_project/`: Legacy Go microservices; the repository is actively refactoring these into the Python codebase.
- `docker-compose.yml`, `Dockerfile`: Local development and container setup.

## Build, Test, and Development Commands
- `docker-compose up`: Start API, Postgres, Redis, Mailpit, and worker containers.
- `cd src && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`: Run the API locally with hot reload.
- `cd src && alembic upgrade head`: Apply migrations to the latest schema.
- `cd src && alembic revision --autogenerate -m "description"`: Create a new migration from model changes.
- `arq app.core.worker.settings.WorkerSettings`: Run the background worker.
- `ruff check .` / `ruff check . --fix`: Lint and auto-fix.
- `mypy .`: Type checking.

## Coding Style & Naming Conventions
- Python 3.11+; use 4-space indentation.
- Prefer type hints on public functions and service methods.
- Follow FastAPI conventions: routers in `api/v1/`, services in `services/`, CRUD in `crud/`.
- Run `ruff` and `mypy` before submitting changes.

## Testing Guidelines
- No Python test suite is currently present.
- If you add tests, place them under `src/tests/` and name files `test_*.py`.
- Prefer pytest; document any new test commands you introduce.

## Commit & Pull Request Guidelines
- Commit message conventions are not established (only an initial commit exists).
- Use clear, imperative messages (e.g., "Add user search endpoint").
- PRs should include: a short summary, testing notes (commands + results), and any required config changes (e.g., `.env` keys).

## Configuration & Environment Tips
- Copy `src/.env.example` to `src/.env` and set `SECRET_KEY` (`openssl rand -hex 32`).
- Core settings live in `src/app/core/config.py` and load from `src/.env`.
