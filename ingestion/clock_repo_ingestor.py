"""CB2 collateral ingestion for global clock blockage, route, and cell metrics."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ingestion import MetricRecord, load_records_from_json

SOURCE_SYSTEM = "cb2_repo"
DEFAULT_ENV_VAR = "CB2_METRICS_JSON"
CB2_HIERARCHIES = ("SOC", "MEMTOP", "UIOA", "UIOE", "D2D1", "D2D4", "C2C")
PRE_PUSH_CHECKS = (
    "cb2_checker_app_options_status",
    "cb2_pre_req_status",
    "cb2_opens_status",
    "cb2_shorts_status",
    "cb2_missing_shield_status",
    "cb2_downgrade_quality_status",
    "cb2_wires_on_track_status",
    "cb2_drc_status",
    "cb2_floating_vias_status",
    "cb2_shielding_shorts_status",
    "cb2_downgrade_shape_boundary_status",
    "cb2_cell_to_cell_spacing_status",
    "cb2_objects_locked_status",
    "cb2_cell_overlap_status",
    "cb2_cell_to_hip_va_spacing_status",
)


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
    records = []
    failing_checks = {
        "D2D4": {"cb2_drc_status", "cb2_floating_vias_status"},
        "C2C": {"cb2_missing_shield_status"},
    }
    for hierarchy in CB2_HIERARCHIES:
        for metric in PRE_PUSH_CHECKS:
            value = "fail" if metric in failing_checks.get(hierarchy, set()) else "pass"
            records.append(_record(hierarchy, metric, value, "cb2_r26ww17.5", collected_at))
    return records


def _record(hierarchy: str, metric: str, value: Any, revision: str, collected_at: str) -> MetricRecord:
    return {
        "milestone": "0p5",
        "deliverable": "CB2",
        "clock": None,
        "partition": None,
        "hierarchy": hierarchy,
        "checklist": "pre_push",
        "metric": metric,
        "value": value,
        "source": {
            "system": SOURCE_SYSTEM,
            "uri": f"cb2/{hierarchy}/pre_push/{metric}",
            "revision": revision,
            "run_id": "26ww17.5",
            "collected_at": collected_at,
        },
    }


def _stamp_source_defaults(records: list[MetricRecord]) -> list[MetricRecord]:
    for record in records:
        record.setdefault("deliverable", "CB2")
        record.setdefault("milestone", "0p5")
        record.setdefault("clock", None)
        record.setdefault("partition", None)
        record.setdefault("checklist", "pre_push")
        record.setdefault("source", {})
        record["source"].setdefault("system", SOURCE_SYSTEM)
    return records
