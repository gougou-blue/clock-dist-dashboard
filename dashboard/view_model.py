"""Create UI-ready JSON payloads from evaluated dashboard metrics."""

from __future__ import annotations

from collections import Counter
from typing import Any

from core.aggregator import MetricsAggregator


def format_for_ui(aggregator: MetricsAggregator) -> dict[str, Any]:
    """Return the full dashboard payload consumed by a static or web UI."""

    clocks = aggregator.clock_ids()
    partitions = aggregator.partition_ids()
    pairs = sorted(
        {
            (record["clock"], record["partition"])
            for record in aggregator.records
            if record.get("clock") and record.get("partition")
        }
    )

    summary = aggregator.program_summary()
    pair_rollups = [aggregator.rollup_clock_partition(clock, partition) for clock, partition in pairs]

    return {
        "summary": summary,
        "cards": _summary_cards(summary),
        "clocks": [aggregator.rollup_clock_metrics(clock) for clock in clocks],
        "partitions": [aggregator.rollup_partition_metrics(partition) for partition in partitions],
        "clock_partition_matrix": pair_rollups,
        "blocking_issues": aggregator.blocking_issues(),
        "metadata": {
            "schema_version": "0.1.0",
            "clock_inventory": list(aggregator.clock_inventory.values()),
            "partition_inventory": list(aggregator.partition_inventory.values()),
            "subfc_summary": _subfc_summary(aggregator.partition_inventory.values()),
            "intended_consumers": ["partition owners", "technical leads", "managers"],
            "source_policy": "Derived from repositories, release manifests, run logs, and static checks; no manual clock-owner status entry.",
        },
    }


def _summary_cards(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "label": "0p5 Ready Pairs",
            "value": f"{summary['ready_clock_partition_pairs']}/{summary['clock_partition_pair_count']}",
            "status": "Green" if summary["open_blocker_count"] == 0 else "Red",
        },
        {
            "label": "Ready Percent",
            "value": f"{summary['ready_clock_partition_pct']}%",
            "status": summary.get("finish_state", "No Data"),
        },
        {
            "label": "Tracked Clocks",
            "value": summary.get("inventory_clock_count", summary["clock_count"]),
            "status": "Gray",
        },
        {
            "label": "Tracked Partitions",
            "value": summary.get("inventory_partition_count", summary["partition_count"]),
            "status": "Gray",
        },
        {
            "label": "Open Blockers",
            "value": summary["open_blocker_count"],
            "status": "Green" if summary["open_blocker_count"] == 0 else "Red",
        },
    ]


def _subfc_summary(partitions: Any) -> list[dict[str, Any]]:
    counts = Counter(partition.get("subfc", "unknown") for partition in partitions)
    return [
        {"subfc": subfc, "partition_count": count}
        for subfc, count in sorted(counts.items())
    ]
