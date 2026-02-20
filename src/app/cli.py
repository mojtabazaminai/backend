#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime
import logging
import sys

from app.core.kafka import kafka_client
from app.core.mongodb import mongo_client
from app.core.search.elasticsearch import es_client
from app.services.cli import (
    DEFAULT_CRAWL_WINDOW,
    db_diff,
    db_migrate,
    db_prepare,
    ensure_indices,
    init_all,
    init_db,
    init_kafka_storage,
    init_postgres_data,
    parse_duration,
    promote_pending_notifications,
    replay_poison_messages,
    reindex_properties,
    run_crawl,
    run_crawl_csv,
    run_crawl_foursquare,
    run_crawl_foursquare_debug,
)

def _normalize_db_commands(argv: list[str]) -> list[str]:
    if not argv:
        return argv
    token = argv[0]
    for prefix in ("db:migrate:", "db:diff:", "db:prepare:"):
        if token.startswith(prefix):
            service = token[len(prefix):]
            return [prefix[:-1], "--service", service, *argv[1:]]
    if token == "init:kafka":
        return ["init_kafka", *argv[1:]]
    if token == "init:db":
        return ["db:init", *argv[1:]]
    return argv


def _parse_datetime(value: str):
    return datetime.fromisoformat(value)


async def main_async(args: argparse.Namespace) -> None:
    try:
        if args.command == "crawl:run":
            window = DEFAULT_CRAWL_WINDOW if args.since is None else parse_duration(args.since)
            await run_crawl(window)
            return
        if args.command == "crawl:run:csv":
            await run_crawl_csv()
            return
        if args.command == "crawl:foursquare":
            await run_crawl_foursquare()
            return
        if args.command == "crawl:foursquare:debug":
            await run_crawl_foursquare_debug(
                ne_lat=args.ne_lat,
                ne_lon=args.ne_lon,
                sw_lat=args.sw_lat,
                sw_lon=args.sw_lon,
            )
            return
        if args.command == "db:elasticsearch:migrate":
            result = await ensure_indices(indices=args.indices)
            print(result)
            return
        if args.command == "db:migrate":
            db_migrate()
            return
        if args.command == "db:diff":
            message = args.message or args.service or "schema"
            db_diff(message)
            return
        if args.command == "db:prepare":
            message = args.message or args.service or "schema"
            db_prepare(message)
            return
        if args.command == "search:reindex":
            result = await reindex_properties(start_after=args.start_after, batch_size=args.batch_size)
            print(result)
            return
        if args.command == "queue:poison:replay":
            result = await replay_poison_messages(
                limit=args.limit,
                poison_topic=args.poison_topic,
                original_topic_header=args.original_topic_header,
                original_topic=args.original_topic,
                idle_timeout_seconds=args.idle_timeout,
                group_id=args.group_id,
            )
            print(result)
            return
        if args.command == "notification:pending:promote":
            result = await promote_pending_notifications(now=args.now)
            print(result)
            return
        if args.command == "init":
            result = await init_all()
            print(result)
            return
        if args.command == "db:init":
            result = await init_db()
            print(result)
            return
        if args.command == "init_kafka":
            result = init_kafka_storage()
            print(result)
            return
        if args.command == "init:postgres":
            result = init_postgres_data()
            print(result)
            return
        raise ValueError(f"Unknown command {args.command}")
    finally:
        await kafka_client.close_producer()
        mongo_client.close()
        await es_client.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ZaminAI CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    crawl_parser = subparsers.add_parser("crawl:run", help="Crawl MLS properties since a window")
    crawl_parser.add_argument("--since", help="Duration window like 30m, 6h, 2d (default 24h)")

    subparsers.add_parser("crawl:run:csv", help="Crawl MLS properties from CSV dumps")
    subparsers.add_parser("crawl:foursquare", help="Crawl Foursquare POIs in San Diego")

    debug_parser = subparsers.add_parser("crawl:foursquare:debug", help="Debug Foursquare crawler for a bounding box")
    debug_parser.add_argument("--ne-lat", type=float, required=True, help="Northeast latitude")
    debug_parser.add_argument("--ne-lon", type=float, required=True, help="Northeast longitude")
    debug_parser.add_argument("--sw-lat", type=float, required=True, help="Southwest latitude")
    debug_parser.add_argument("--sw-lon", type=float, required=True, help="Southwest longitude")

    es_parser = subparsers.add_parser(
        "db:elasticsearch:migrate",
        help="Create configured Elasticsearch indexes if they are missing",
    )
    es_parser.add_argument(
        "--indices",
        help="Comma-separated index names (defaults to ELASTICSEARCH_INDEX)",
    )

    db_migrate_parser = subparsers.add_parser(
        "db:migrate",
        help="Run Alembic migrations to head",
    )
    db_migrate_parser.add_argument("--service", help="Service name (optional, for parity with Go CLI)")

    db_diff_parser = subparsers.add_parser(
        "db:diff",
        help="Generate an Alembic autogenerate diff to stdout",
    )
    db_diff_parser.add_argument("--service", help="Service name (used for message)")
    db_diff_parser.add_argument("--message", help="Migration message override")

    db_prepare_parser = subparsers.add_parser(
        "db:prepare",
        help="Create an Alembic migration file using autogenerate",
    )
    db_prepare_parser.add_argument("--service", help="Service name (used for message)")
    db_prepare_parser.add_argument("--message", help="Migration message override")

    reindex_parser = subparsers.add_parser(
        "search:reindex",
        help="Reindex properties from Postgres into Elasticsearch",
    )
    reindex_parser.add_argument("--batch-size", type=int, help="Batch size (default 500, max 5000)")
    reindex_parser.add_argument("--start-after", help="Listing key to resume after")

    replay_parser = subparsers.add_parser(
        "queue:poison:replay",
        help="Replay messages from a poison topic back to their original topics",
    )
    replay_parser.add_argument("--limit", type=int, help="Max messages to replay (default 10)")
    replay_parser.add_argument("--poison-topic", help="Poison topic name override")
    replay_parser.add_argument(
        "--original-topic-header",
        default="poisoned_topic",
        help="Header key that stores the original topic",
    )
    replay_parser.add_argument("--original-topic", help="Fallback original topic if header missing")
    replay_parser.add_argument("--idle-timeout", type=float, default=2.0, help="Idle timeout seconds")
    replay_parser.add_argument("--group-id", help="Consumer group ID override")

    promote_parser = subparsers.add_parser(
        "notification:pending:promote",
        help="Promote due notifications to pending",
    )
    promote_parser.add_argument("--now", type=_parse_datetime, help="Override current time (ISO 8601)")

    subparsers.add_parser("init", help="Initialize postgres data dir, elasticsearch indices, and kafka storage")
    subparsers.add_parser("db:init", help="Initialize database schemas and tables")
    subparsers.add_parser("init_kafka", help="Initialize Kafka storage (devbox)")
    subparsers.add_parser("init:postgres", help="Initialize Postgres data directory if empty")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args(_normalize_db_commands(sys.argv[1:]))
    asyncio.run(main_async(args))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
