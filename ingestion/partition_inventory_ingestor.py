"""Partition inventory ingestion for NWPNIO dashboard coverage."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

PartitionInventory = dict[str, Any]

DEFAULT_ENV_VAR = "PARTITION_INVENTORY_JSON"
DEFAULT_INVENTORY_PATH = Path("data/nwpnio_partition_inventory.json")
_SPREADSHEET_MARKER = re.compile(r"\s+\*+$")


def get_partition_inventory(source_path: str | Path | None = None) -> PartitionInventory:
    """Load and normalize the active partition inventory."""

    resolved_path = Path(source_path or os.environ.get(DEFAULT_ENV_VAR) or DEFAULT_INVENTORY_PATH)
    payload = json.loads(resolved_path.read_text(encoding="utf-8"))
    partitions = [_normalize_partition(raw_partition) for raw_partition in payload.get("partitions", [])]
    return {
        "program": payload.get("program", "unknown"),
        "milestone": payload.get("milestone", "0p5"),
        "source_path": str(resolved_path),
        "partitions": partitions,
        "active_partitions": [partition for partition in partitions if partition.get("active", True)],
        "normalization_warnings": [
            warning
            for partition in partitions
            for warning in partition.get("normalization_warnings", [])
        ],
    }


def _normalize_partition(raw_partition: dict[str, Any]) -> dict[str, Any]:
    raw_name = str(raw_partition.get("partition", ""))
    stripped_name = raw_name.strip()
    canonical_name = _SPREADSHEET_MARKER.sub("", stripped_name)
    warnings = []

    if raw_name != stripped_name:
        warnings.append(
            {
                "partition": canonical_name,
                "raw_partition": raw_name,
                "issue": "trimmed_leading_or_trailing_whitespace",
            }
        )
    if stripped_name != canonical_name:
        warnings.append(
            {
                "partition": canonical_name,
                "raw_partition": raw_name,
                "issue": "removed_trailing_spreadsheet_marker",
            }
        )

    normalized = dict(raw_partition)
    normalized["partition"] = canonical_name
    normalized["raw_partition"] = raw_name
    normalized["subfc"] = str(raw_partition.get("subfc", "unknown")).strip() or "unknown"
    normalized["active"] = bool(raw_partition.get("active", True))
    normalized["normalization_warnings"] = warnings
    return normalized
