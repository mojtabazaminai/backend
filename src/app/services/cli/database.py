from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config


def _alembic_config() -> Config:
    src_dir = Path(__file__).resolve().parents[3]
    config_path = src_dir / "alembic.ini"
    config = Config(str(config_path))
    config.set_main_option("script_location", str(src_dir / "migrations"))
    return config


def db_migrate() -> None:
    command.upgrade(_alembic_config(), "head")


def db_diff(message: str) -> None:
    command.revision(_alembic_config(), message=message, autogenerate=True, stdout=True)


def db_prepare(message: str) -> None:
    command.revision(_alembic_config(), message=message, autogenerate=True)
