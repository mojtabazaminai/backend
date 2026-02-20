from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
import json
import logging
from pathlib import Path
import threading

from ....schemas.ingest import Channel, Pager, RawProperty

logger = logging.getLogger(__name__)

DEFAULT_DUMP_DIR = "tmp/properties_dump"
TIMESTAMP_FORMATS = [
    "%Y-%m-%dT%H:%M:%S.%f%z",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
]


class CSVMLSClient:
    def __init__(self, directory: str | None = None) -> None:
        self.directory = Path(directory or DEFAULT_DUMP_DIR)
        self._files: list[Path] = []
        self._loaded = False
        self._lock = threading.Lock()
        self._iterator = _CSVIterator()

    async def get_properties_by_modified(self, pager: Pager, since: datetime) -> list[RawProperty]:
        if pager is None:
            pager = Pager.default()
        pager.page = max(pager.page, 1)
        if pager.limit < 1:
            pager.limit = Pager.default().limit
        if since.tzinfo is None:
            since = since.replace(tzinfo=timezone.utc)

        self._ensure_files()

        with self._lock:
            if not self._iterator.files:
                self._iterator.reset(self._files, since)
            elif self._iterator.since != since:
                self._iterator.reset(self._files, since)

            target_offset = pager.offset()
            if target_offset < self._iterator.matched:
                self._iterator.reset(self._files, since)

            self._iterator.fast_forward(target_offset)

            props: list[RawProperty] = []
            while len(props) < pager.limit:
                row = self._iterator.next_row()
                if row is None:
                    break
                props.append(row.property)
                self._iterator.matched += 1

            return props

    def _ensure_files(self) -> None:
        with self._lock:
            if self._loaded:
                return

            if not self.directory.exists():
                logger.warning("CSV MLS directory does not exist: %s", self.directory)
                self._loaded = True
                return

            self._files = sorted(
                [path for path in self.directory.iterdir() if path.is_file() and path.suffix == ".csv"]
            )
            self._loaded = True


@dataclass
class _PropertyRow:
    modified_at: datetime
    property: RawProperty


class _CSVIterator:
    def __init__(self) -> None:
        self.files: list[Path] = []
        self.since: datetime | None = None
        self.file_idx = 0
        self.reader: csv.reader | None = None
        self.current_file = None
        self.column_index: dict[str, int] = {}
        self.matched = 0

    def reset(self, files: list[Path], since: datetime) -> None:
        self.close_current()
        self.files = files
        self.since = since
        self.file_idx = 0
        self.reader = None
        self.current_file = None
        self.column_index = {}
        self.matched = 0

    def next_row(self) -> _PropertyRow | None:
        while True:
            if self.reader is None:
                if not self._open_next_file():
                    return None

            try:
                record = next(self.reader)  # type: ignore[arg-type]
            except StopIteration:
                self.close_current()
                continue

            row = _parse_row(record, self.column_index, self.since)
            if row is None:
                continue
            return row

    def fast_forward(self, target: int) -> None:
        while self.matched < target:
            row = self.next_row()
            if row is None:
                return
            self.matched += 1

    def _open_next_file(self) -> bool:
        if self.file_idx >= len(self.files):
            return False

        path = self.files[self.file_idx]
        self.file_idx += 1

        try:
            f = path.open("r", newline="", encoding="utf-8")
        except OSError as exc:
            logger.warning("Failed to open CSV file %s: %s", path, exc)
            return self._open_next_file()

        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            f.close()
            return self._open_next_file()

        column_index = _validate_header(header, path)
        if column_index is None:
            f.close()
            return self._open_next_file()

        self.current_file = f
        self.reader = reader
        self.column_index = column_index
        return True

    def close_current(self) -> None:
        if self.current_file is not None:
            self.current_file.close()
        self.current_file = None
        self.reader = None


def _validate_header(header: list[str], path: Path) -> dict[str, int] | None:
    column_index = {column.strip(): idx for idx, column in enumerate(header)}
    required = ["_id", "listing_id", "standard_status", "raw_api_data", "modification_timestamp"]
    for column in required:
        if column not in column_index:
            logger.warning("CSV file %s missing column %s", path, column)
            return None
    return column_index


def _parse_row(record: list[str], column_index: dict[str, int], since: datetime | None) -> _PropertyRow | None:
    listing_key = _get_value(record, column_index, "_id")
    listing_id = _get_value(record, column_index, "listing_id")
    standard_status = _get_value(record, column_index, "standard_status")
    raw_api_data = _get_value(record, column_index, "raw_api_data")
    modified_at_str = _get_value(record, column_index, "modification_timestamp")

    if not all([listing_key, listing_id, raw_api_data, modified_at_str]):
        return None

    modified_at = _parse_timestamp(modified_at_str)
    if modified_at is None:
        return None

    if since and modified_at < since:
        return None

    data = _normalize_raw_json(raw_api_data, listing_key)
    if data is None:
        return None

    crawled_at = None
    if "crawled_at" in column_index:
        crawled_at_str = _get_value(record, column_index, "crawled_at")
        if crawled_at_str:
            crawled_at = _parse_timestamp(crawled_at_str)

    prop = RawProperty(
        listing_key=listing_key,
        listing_id=listing_id,
        standard_status=standard_status,
        channel=Channel.REALTYFEED,
        data=data,
        crawled_at=crawled_at,
    )
    return _PropertyRow(modified_at=modified_at, property=prop)


def _get_value(record: list[str], column_index: dict[str, int], key: str) -> str:
    idx = column_index.get(key)
    if idx is None or idx >= len(record):
        return ""
    return record[idx].strip()


def _parse_timestamp(value: str) -> datetime | None:
    value = value.strip()
    if not value:
        return None

    for fmt in TIMESTAMP_FORMATS:
        try:
            parsed = datetime.strptime(value, fmt)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            continue

    logger.warning("Unsupported timestamp format: %s", value)
    return None


def _normalize_raw_json(raw: str, listing_key: str) -> dict | list | str | int | float | bool | None:
    try:
        data = json.loads(raw, parse_float=Decimal)
    except json.JSONDecodeError as exc:
        logger.warning("Invalid raw_api_data for listing %s: %s", listing_key, exc)
        return None
    return _normalize_numbers(data)


def _normalize_numbers(value: object) -> object:
    if isinstance(value, dict):
        return {key: _normalize_numbers(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_numbers(item) for item in value]
    if isinstance(value, Decimal):
        if value == value.to_integral_value():
            return int(value)
        return float(value)
    return value
