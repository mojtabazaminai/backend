from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
from typing import Any

from app.core.setup import create_tables
from app.services.cli.elasticsearch import ensure_indices


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def init_kafka_storage() -> dict[str, Any]:
    root = _repo_root()
    meta_path = root / ".devbox" / "kafka" / "data" / "meta.properties"
    if meta_path.exists():
        return {"skipped": True, "reason": "meta.properties exists"}

    kafka_storage = shutil.which("kafka-storage.sh")
    if not kafka_storage:
        raise RuntimeError("kafka-storage.sh not found in PATH")

    config_path = root / "devbox.d" / "kafka" / "server.properties"
    if not config_path.exists():
        raise RuntimeError(f"Missing kafka config at {config_path}")

    uuid = subprocess.check_output([kafka_storage, "random-uuid"], text=True).strip()
    subprocess.run(
        [kafka_storage, "format", "-t", uuid, "-c", str(config_path)],
        check=True,
    )
    return {"skipped": False, "uuid": uuid}


def init_postgres_data() -> dict[str, Any]:
    pgdata = os.environ.get("PGDATA")
    if not pgdata:
        return {"skipped": True, "reason": "PGDATA not set"}

    pgdata_path = Path(pgdata)
    if pgdata_path.exists() and any(pgdata_path.iterdir()):
        return {"skipped": True, "reason": "PGDATA not empty"}

    initdb = shutil.which("initdb")
    if not initdb:
        raise RuntimeError("initdb not found in PATH")

    subprocess.run([initdb], check=True)
    return {"skipped": False, "path": str(pgdata_path)}


async def init_all() -> dict[str, Any]:
    results: dict[str, Any] = {}
    results["postgres"] = init_postgres_data()
    results["elasticsearch"] = await ensure_indices()
    results["kafka"] = init_kafka_storage()
    return results


async def init_db() -> dict[str, Any]:
    await create_tables()
    return {"initialized": True}
