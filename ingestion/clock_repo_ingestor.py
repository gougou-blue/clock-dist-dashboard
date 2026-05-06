"""CB2 collateral ingestion for global clock blockage, route, and cell metrics."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ingestion import MetricRecord, load_records_from_json

SOURCE_SYSTEM = "cb2_repo"
DEFAULT_ENV_VAR = "CB2_METRICS_JSON"


def get_latest_metrics(source_path: str | Path | None = None) -> list[MetricRecord]:
    """Return latest CB2 metric records.

    Until the real CB2 repository format is connected, this collector accepts a
    normalized JSON export path or returns a small representative sample.
    """

    resolved_path = source_path or os.environ.get(DEFAULT_ENV_VAR)
    if resolved_path:
        return _stamp_source_defaults(load_records_from_json(resolved_path))
    return sample_metrics()


def sample_metrics() -> list[MetricRecord]:
    collected_at = datetime.now(timezone.utc).isoformat()
    return [
        _record("mc_clk", "pard2d1uladda0", "blockages_drawn_pct", 100.0, "cb2_r26ww17.5", collected_at),
        _record("mc_clk", "pard2d1uladda0", "routes_completed_pct", 100.0, "cb2_r26ww17.5", collected_at),
        _record("mc_clk", "pard2d1uladda0", "cells_placed_pct", 100.0, "cb2_r26ww17.5", collected_at),
        _record("mc_clk", "pard2d1uladda0", "cb2_release_manifest_status", "released", "cb2_r26ww17.5", collected_at),
        _record("mc_clk", "pard2d1uladda0", "route_drc_count", 0, "cb2_r26ww17.5", collected_at),
        _record("mc_clk", "pard2d1uladda0", "missing_expected_routes_count", 0, "cb2_r26ww17.5", collected_at),
        _record("mc_clk", "pard2d1uladda0", "orphan_routes_count", 0, "cb2_r26ww17.5", collected_at),
        _record("mc_clk", "pard2d1uladda0", "cell_legality_violation_count", 0, "cb2_r26ww17.5", collected_at),
        _record("mc_clk", "pard2d1uladda0", "cb2_consumer_runs_behind", 0, "cb2_r26ww17.5", collected_at),
        _record("uclk_io", "paracciommu", "blockages_drawn_pct", 95.0, "cb2_r26ww17.5", collected_at),
        _record("uclk_io", "paracciommu", "routes_completed_pct", 87.5, "cb2_r26ww17.5", collected_at),
        _record("uclk_io", "paracciommu", "cells_placed_pct", 92.0, "cb2_r26ww17.5", collected_at),
        _record("uclk_io", "paracciommu", "cb2_release_manifest_status", "draft", "cb2_r26ww17.5", collected_at),
        _record("uclk_io", "paracciommu", "route_drc_count", 3, "cb2_r26ww17.5", collected_at),
        _record("uclk_io", "paracciommu", "missing_expected_routes_count", 1, "cb2_r26ww17.5", collected_at),
        _record("uclk_io", "paracciommu", "orphan_routes_count", 0, "cb2_r26ww17.5", collected_at),
        _record("uclk_io", "paracciommu", "cell_legality_violation_count", 0, "cb2_r26ww17.5", collected_at),
        _record("uclk_io", "paracciommu", "cb2_consumer_runs_behind", 1, "cb2_r26ww17.5", collected_at),
    ]


def _record(clock: str, partition: str, metric: str, value: Any, revision: str, collected_at: str) -> MetricRecord:
    return {
        "milestone": "0p5",
        "deliverable": "CB2",
        "clock": clock,
        "partition": partition,
        "metric": metric,
        "value": value,
        "source": {
            "system": SOURCE_SYSTEM,
            "uri": f"cb2/{clock}/{partition}/{metric}",
            "revision": revision,
            "run_id": "26ww17.5",
            "collected_at": collected_at,
        },
    }


def _stamp_source_defaults(records: list[MetricRecord]) -> list[MetricRecord]:
    for record in records:
        record.setdefault("deliverable", "CB2")
        record.setdefault("milestone", "0p5")
        record.setdefault("source", {})
        record["source"].setdefault("system", SOURCE_SYSTEM)
    return records
