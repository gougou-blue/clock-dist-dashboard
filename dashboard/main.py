"""Command-line orchestration for the Global Clock Distribution dashboard."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from core.aggregator import MetricsAggregator, combine_source_records
from dashboard.view_model import format_for_ui
from ingestion import (
    clock_inventory_ingestor,
    clock_repo_ingestor,
    partition_inventory_ingestor,
    partition_run_ingestor,
    stamping_collateral_ingestor,
)


def refresh_data(
    cb2_source: str | None = None,
    mcss_source: str | None = None,
    partition_source: str | None = None,
    inventory_source: str | None = None,
    clock_inventory_source: str | None = None,
    scan_mcss_release_tree: bool = False,
) -> MetricsAggregator:
    """Fetch latest records from all configured sources and update the aggregator."""

    cb2_records = clock_repo_ingestor.get_latest_metrics(cb2_source)
    inventory = partition_inventory_ingestor.get_partition_inventory(inventory_source)
    clock_inventory = clock_inventory_ingestor.get_clock_inventory(clock_inventory_source)
    mcss_records = stamping_collateral_ingestor.get_latest_metrics(
        mcss_source,
        partitions=inventory["active_partitions"],
        scan_release_tree=scan_mcss_release_tree,
    )
    partition_records = partition_run_ingestor.get_latest_metrics(partition_source)

    aggregator = MetricsAggregator(
        milestone="0p5",
        partition_inventory=inventory["active_partitions"],
        clock_inventory=clock_inventory["active_clocks"],
    )
    aggregator.update_from_ingestion(combine_source_records(cb2_records, mcss_records, partition_records))
    return aggregator


def write_dashboard_payload(payload: dict, output_path: str | Path) -> Path:
    """Write dashboard JSON and return the resolved output path."""

    resolved = Path(output_path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return resolved


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Global Clock Distribution dashboard data.")
    parser.add_argument("--cb2-source", help="Optional normalized CB2 metric JSON export.")
    parser.add_argument("--mcss-source", help="Optional normalized MCSS metric JSON export.")
    parser.add_argument("--partition-source", help="Optional normalized partition run metric JSON export.")
    parser.add_argument("--inventory-source", help="Optional partition inventory JSON export.")
    parser.add_argument("--clock-inventory-source", help="Optional clock inventory JSON export.")
    parser.add_argument(
        "--scan-mcss-release-tree",
        action="store_true",
        help="Derive MCSS release and collateral availability from per-partition release folders.",
    )
    parser.add_argument("--output", default="public/data/latest.json", help="Output JSON path.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        aggregator = refresh_data(
            cb2_source=args.cb2_source,
            mcss_source=args.mcss_source,
            partition_source=args.partition_source,
            inventory_source=args.inventory_source,
            clock_inventory_source=args.clock_inventory_source,
            scan_mcss_release_tree=args.scan_mcss_release_tree,
        )
    except RuntimeError as error:
        raise SystemExit(str(error)) from error
    payload = format_for_ui(aggregator)
    output_path = write_dashboard_payload(payload, args.output)
    print(f"Wrote dashboard payload: {output_path}")
    print(f"0p5 finish state: {payload['summary']['finish_state']}")
    print(f"Open blockers: {payload['summary']['open_blocker_count']}")


if __name__ == "__main__":
    main()
