"""Partition run ingestion for static checks and integration quality metrics."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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
    collected_at = datetime.now(timezone.utc).isoformat()
    return [
        _record("pard2d1uladda0", "no_clock_on_reg_count", 0, "partition_run_26ww17.5", collected_at),
        _record("pard2d1uladda0", "unexpected_clock_on_reg_count", 0, "partition_run_26ww17.5", collected_at),
        _record("paracciommu", "no_clock_on_reg_count", 14, "partition_run_26ww17.5", collected_at),
        _record("paracciommu", "unexpected_clock_on_reg_count", 2, "partition_run_26ww17.5", collected_at),
    ]


def _record(partition: str, metric: str, value: Any, revision: str, collected_at: str) -> MetricRecord:
    return {
        "milestone": "0p5",
        "deliverable": "MCSS",
        "clock": None,
        "partition": partition,
        "metric": metric,
        "value": value,
        "source": {
            "system": SOURCE_SYSTEM,
            "uri": f"runs/{partition}/{metric}",
            "revision": revision,
            "run_id": "26ww17.5",
            "collected_at": collected_at,
        },
    }


def _stamp_source_defaults(records: list[MetricRecord]) -> list[MetricRecord]:
    for record in records:
        record.setdefault("deliverable", "MCSS")
        record.setdefault("milestone", "0p5")
        record.setdefault("clock", None)
        record.setdefault("source", {})
        record["source"].setdefault("system", SOURCE_SYSTEM)
    return records
