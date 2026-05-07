"""Create UI-ready JSON payloads from evaluated dashboard metrics."""

from __future__ import annotations

from collections import Counter
from typing import Any

from core.aggregator import MetricsAggregator
from core.metrics_definitions import METRICS, MetricDefinition

CB2_CHECK_LABELS = {
    "cb2_checker_app_options_status": "Checker app options",
    "cb2_pre_req_status": "Checker prerequisites",
    "cb2_opens_status": "Opens",
    "cb2_shorts_status": "Shorts",
    "cb2_missing_shield_status": "Missing shield",
    "cb2_downgrade_quality_status": "Downgrade quality",
    "cb2_wires_on_track_status": "Wires drawn on track",
    "cb2_drc_status": "DRCs",
    "cb2_floating_vias_status": "Floating vias",
    "cb2_shielding_shorts_status": "Shielding shorts",
    "cb2_downgrade_shape_boundary_status": "Downgrade shape outside block boundary",
    "cb2_cell_to_cell_spacing_status": "Cell-to-cell spacing",
    "cb2_objects_locked_status": "Locked CB2 objects",
    "cb2_cell_overlap_status": "Overlapping CB2 cells",
    "cb2_cell_to_hip_va_spacing_status": "Spacing to other HIPs or VAs",
    "cb2_post_push_opens_status": "Opens",
    "cb2_post_push_shorts_status": "Shorts",
    "cb2_post_push_extra_objects_status": "Extra objects",
    "cb2_post_push_shield_tapping_status": "Shield tapping",
    "cb2_post_push_missing_shield_status": "Missing shield",
    "cb2_post_push_viewlogic_status": "Viewlogic check",
    "cb2_post_push_attribute_conflict_status": "Attribute conflict",
    "cb2_post_push_crb_mismatch_status": "CRB mismatch",
}


def format_for_ui(aggregator: MetricsAggregator) -> dict[str, Any]:
    """Return the full dashboard payload consumed by a static or web UI."""

    clocks = aggregator.clock_ids()
    partitions = aggregator.partition_ids()
    cb2_hierarchies = aggregator.hierarchy_ids("CB2")
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
        "cb2_hierarchies": [aggregator.rollup_hierarchy_metrics(hierarchy) for hierarchy in cb2_hierarchies],
        "clocks": [aggregator.rollup_clock_metrics(clock) for clock in clocks],
        "partitions": [aggregator.rollup_partition_metrics(partition) for partition in partitions],
        "blocking_issues": aggregator.blocking_issues(),
        "metadata": {
            "schema_version": "0.1.0",
            "cb2_checklists": _cb2_checklists(),
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
            "label": "CB2 Hierarchies",
            "value": summary.get("cb2_hierarchy_count", 0),
            "status": "Gray",
        },
        {
            "label": "MCSS Partitions",
            "value": summary.get("inventory_partition_count", summary["partition_count"]),
            "status": "Gray",
        },
        {
            "label": "CB2 Post-Push Runs",
            "value": summary.get("cb2_post_push_partition_count", 0),
            "status": "Gray",
        },
        {
            "label": "Tracked Clocks",
            "value": summary.get("inventory_clock_count", summary["clock_count"]),
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


def _cb2_checklists() -> dict[str, list[dict[str, str]]]:
    checklists: dict[str, list[dict[str, str]]] = {"pre_push": [], "post_push": []}
    for metric in METRICS:
        if metric.deliverable != "CB2" or metric.category not in {"Pre-Push", "Post-Push"}:
            continue
        checklist = "pre_push" if metric.category == "Pre-Push" else "post_push"
        checklists[checklist].append(_checklist_item(metric))
    return checklists


def _checklist_item(metric: MetricDefinition) -> dict[str, str]:
    return {
        "metric": metric.name,
        "label": CB2_CHECK_LABELS.get(metric.name, metric.name),
        "description": metric.description,
    }
