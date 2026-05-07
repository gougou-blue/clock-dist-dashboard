#!/usr/bin/env python3
"""Print a compact status summary for a generated dashboard payload."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def iter_unique_entity_metrics(payload: dict[str, Any]) -> list[dict[str, Any]]:
    metrics_by_key: dict[tuple[str | None, str | None, str], dict[str, Any]] = {}
    for section in ("partitions", "clocks", "cb2_hierarchies"):
        for rollup in payload.get(section, []):
            for metric in rollup.get("metrics", []):
                key = (metric.get("clock"), metric.get("partition"), metric.get("hierarchy"), metric.get("metric"))
                metrics_by_key[key] = metric
    return list(metrics_by_key.values())


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize dashboard payload statuses.")
    parser.add_argument("payload", nargs="?", default="public/data/latest.json", help="Dashboard payload JSON path.")
    args = parser.parse_args()

    payload_path = Path(args.payload)
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    metrics = iter_unique_entity_metrics(payload)
    red_metrics = payload.get("blocking_issues", [])

    print(f"Payload: {payload_path}")
    print(f"Finish state: {payload['summary']['finish_state']}")
    print(f"Open blockers: {payload['summary']['open_blocker_count']}")
    print()

    print("Statuses by deliverable:")
    for (deliverable, status), count in sorted(Counter((m.get("deliverable"), m.get("status")) for m in metrics).items()):
        print(f"  {deliverable or 'unknown'} / {status or 'unknown'}: {count}")
    print()

    print("Red blockers by metric:")
    for (deliverable, metric), count in sorted(Counter((m.get("deliverable"), m.get("metric")) for m in red_metrics).items()):
        print(f"  {deliverable or 'unknown'} / {metric or 'unknown'}: {count}")

    print()
    print("MCSS release availability:")
    release_counts = Counter(
        (m.get("status"), m.get("value"))
        for m in metrics
        if m.get("metric") == "mcss_release_status"
    )
    for (status, value), count in sorted(release_counts.items()):
        print(f"  {status or 'unknown'} / {value or 'unknown'}: {count}")


if __name__ == "__main__":
    main()
