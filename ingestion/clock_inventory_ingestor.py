"""Clock domain inventory ingestion for NWPNIO dashboard coverage."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

ClockInventory = dict[str, Any]

DEFAULT_ENV_VAR = "CLOCK_INVENTORY_JSON"
DEFAULT_INVENTORY_PATH = Path("data/nwpnio_clock_inventory.json")


def get_clock_inventory(source_path: str | Path | None = None) -> ClockInventory:
    """Load and normalize the active clock domain inventory."""

    resolved_path = Path(source_path or os.environ.get(DEFAULT_ENV_VAR) or DEFAULT_INVENTORY_PATH)
    payload = json.loads(resolved_path.read_text(encoding="utf-8"))
    clocks = [_normalize_clock(raw_clock) for raw_clock in payload.get("clocks", [])]
    return {
        "program": payload.get("program", "unknown"),
        "milestone": payload.get("milestone", "0p5"),
        "source_path": str(resolved_path),
        "clocks": clocks,
        "active_clocks": [clock for clock in clocks if clock.get("active", True)],
    }


def _normalize_clock(raw_clock: dict[str, Any]) -> dict[str, Any]:
    canonical_name = str(raw_clock.get("clock", "")).strip()
    display_name = str(raw_clock.get("display_name", canonical_name)).strip() or canonical_name
    normalized = dict(raw_clock)
    normalized["clock"] = canonical_name
    normalized["display_name"] = display_name
    normalized["active"] = bool(raw_clock.get("active", True))
    return normalized
