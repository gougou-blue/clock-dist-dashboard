"""Optional partition run ingestion for future normalized metric exports."""

from __future__ import annotations

import os
from pathlib import Path

from ingestion import MetricRecord, load_records_from_json

SOURCE_SYSTEM = "partition_runs"
DEFAULT_ENV_VAR = "PARTITION_RUN_METRICS_JSON"


def get_latest_metrics(source_path: str | Path | None = None) -> list[MetricRecord]:
    """Return latest partition-level quality records from JSON export or sample data."""

    resolved_path = source_path or os.environ.get(DEFAULT_ENV_VAR)
    if resolved_path:
        return _stamp_source_defaults(load_records_from_json(resolved_path))
    return sample_metrics()


def sample_metrics() -> list[MetricRecord]:
    return []


def _stamp_source_defaults(records: list[MetricRecord]) -> list[MetricRecord]:
    for record in records:
        record.setdefault("deliverable", "MCSS")
        record.setdefault("milestone", "0p5")
        record.setdefault("clock", None)
        record.setdefault("source", {})
        record["source"].setdefault("system", SOURCE_SYSTEM)
    return records
