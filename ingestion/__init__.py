"""Data ingestion package for clock dashboard source collectors."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MetricRecord = dict[str, Any]


def load_records_from_json(path: str | Path) -> list[MetricRecord]:
	"""Load normalized metric records from a JSON file.

	The expected shape is either a list of metric records or an object with a
	top-level ``records`` list. This keeps early source adapters simple while
	the real CB2, MCSS, and run-output formats are still evolving.
	"""

	source_path = Path(path)
	payload = json.loads(source_path.read_text(encoding="utf-8"))
	if isinstance(payload, list):
		return payload
	if isinstance(payload, dict) and isinstance(payload.get("records"), list):
		return payload["records"]
	raise ValueError(f"Unsupported metric record JSON shape: {source_path}")
