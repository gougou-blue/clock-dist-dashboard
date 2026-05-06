#!/usr/bin/env python3
"""Inspect MCSS archive collateral filenames and missing dashboard metrics."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from ingestion.partition_inventory_ingestor import get_partition_inventory
from ingestion.stamping_collateral_ingestor import DEFAULT_RELEASE_TEMPLATE, EXPECTED_COLLATERAL


def release_dir(partition: str, release_template: str) -> Path:
    return Path(os.path.expandvars(release_template).format(partition=partition))


def load_payload(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def missing_by_metric(payload: dict[str, Any] | None) -> dict[str, list[str]]:
    missing: dict[str, list[str]] = defaultdict(list)
    if not payload:
        return missing
    for issue in payload.get("blocking_issues", []):
        if issue.get("deliverable") == "MCSS":
            missing[issue["metric"]].append(issue.get("partition") or "-")
    return {metric: sorted(partitions) for metric, partitions in missing.items()}


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect MCSS archive collateral coverage and filenames.")
    parser.add_argument("--payload", default="public/data/latest.json", help="Dashboard payload JSON to inspect for missing metrics.")
    parser.add_argument("--inventory-source", default=None, help="Partition inventory JSON path.")
    parser.add_argument("--release-template", default=os.environ.get("MCSS_RELEASE_TEMPLATE", DEFAULT_RELEASE_TEMPLATE))
    parser.add_argument("--limit", type=int, default=30, help="Maximum filenames or partitions to print per section.")
    args = parser.parse_args()

    inventory = get_partition_inventory(args.inventory_source)["active_partitions"]
    partitions = [str(partition["partition"]) for partition in inventory]
    payload = load_payload(Path(args.payload))
    missing = missing_by_metric(payload)

    existing_dirs: list[Path] = []
    missing_dirs: list[str] = []
    file_counts: Counter[str] = Counter()
    example_paths: dict[str, str] = {}

    for partition in partitions:
        directory = release_dir(partition, args.release_template)
        if not directory.is_dir():
            missing_dirs.append(partition)
            continue
        existing_dirs.append(directory)
        for path in directory.iterdir():
            if path.is_file():
                file_counts[path.name] += 1
                example_paths.setdefault(path.name, path.as_posix())

    print(f"Partitions in inventory: {len(partitions)}")
    print(f"Existing release dirs: {len(existing_dirs)}")
    print(f"Missing release dirs: {len(missing_dirs)}")
    if missing_dirs:
        print("Missing release dir partitions:")
        print("  " + ", ".join(missing_dirs[: args.limit]))
        if len(missing_dirs) > args.limit:
            print(f"  ... {len(missing_dirs) - args.limit} more")
    print()

    print("Top archive filenames:")
    for name, count in file_counts.most_common(args.limit):
        print(f"  {count:4d}  {name}")
        print(f"        {example_paths[name]}")
    print()

    print("Configured collateral patterns:")
    for spec in EXPECTED_COLLATERAL:
        print(f"  {spec.key}: {', '.join(spec.patterns)}")
    print()

    if missing:
        print("Missing MCSS metrics from payload:")
        for metric, metric_partitions in sorted(missing.items()):
            print(f"  {metric}: {len(metric_partitions)}")
            print("    " + ", ".join(metric_partitions[: args.limit]))
            if len(metric_partitions) > args.limit:
                print(f"    ... {len(metric_partitions) - args.limit} more")


if __name__ == "__main__":
    main()
