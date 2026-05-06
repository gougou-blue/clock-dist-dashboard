"""Canonical metric definitions for the Global Clock Distribution dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MetricDefinition:
    """Defines one normalized progress, quality, release, or freshness metric."""

    name: str
    deliverable: str
    category: str
    scope: str
    description: str
    target_value: float | bool | str | None = None
    status_mode: str = "informational"
    yellow_min: float | None = None
    yellow_max: float | None = None
    required_for_0p5: bool = True


METRICS: list[MetricDefinition] = [
    MetricDefinition(
        name="blockages_drawn_pct",
        deliverable="CB2",
        category="Progress",
        scope="clock_partition",
        description="Percent of planned global clock blockages drawn for the clock in a partition.",
        target_value=100.0,
        status_mode="percent_complete",
        yellow_min=90.0,
    ),
    MetricDefinition(
        name="routes_completed_pct",
        deliverable="CB2",
        category="Progress",
        scope="clock_partition",
        description="Percent of expected global trunk routes completed for the clock in a partition.",
        target_value=100.0,
        status_mode="percent_complete",
        yellow_min=90.0,
    ),
    MetricDefinition(
        name="cells_placed_pct",
        deliverable="CB2",
        category="Progress",
        scope="clock_partition",
        description="Percent of required anchor, repeater, tap, or PDOP cells placed legally.",
        target_value=100.0,
        status_mode="percent_complete",
        yellow_min=90.0,
    ),
    MetricDefinition(
        name="cb2_release_manifest_status",
        deliverable="CB2",
        category="Release",
        scope="clock_partition",
        description="Whether CB2 collateral is officially released for 0p5 consumption.",
        target_value=True,
        status_mode="release_status",
    ),
    MetricDefinition(
        name="route_drc_count",
        deliverable="CB2",
        category="Quality",
        scope="clock_partition",
        description="Open DRC violations attributed to global clock routes.",
        target_value=0.0,
        status_mode="zero_count",
        yellow_max=2.0,
    ),
    MetricDefinition(
        name="missing_expected_routes_count",
        deliverable="CB2",
        category="Quality",
        scope="clock_partition",
        description="Expected global route segments absent from delivered collateral.",
        target_value=0.0,
        status_mode="zero_count",
    ),
    MetricDefinition(
        name="orphan_routes_count",
        deliverable="CB2",
        category="Quality",
        scope="clock_partition",
        description="Clock route shapes not tied to expected topology or release inventory.",
        target_value=0.0,
        status_mode="zero_count",
    ),
    MetricDefinition(
        name="cell_legality_violation_count",
        deliverable="CB2",
        category="Quality",
        scope="clock_partition",
        description="Required clock cells placed in illegal or unusable locations.",
        target_value=0.0,
        status_mode="zero_count",
    ),
    MetricDefinition(
        name="cb2_consumer_runs_behind",
        deliverable="CB2",
        category="Freshness",
        scope="clock_partition",
        description="How many accepted source revisions the partition consumer lags behind CB2 release.",
        target_value=0.0,
        status_mode="freshness_lag",
        yellow_max=1.0,
    ),
    MetricDefinition(
        name="mcss_part1_completion_status",
        deliverable="MCSS",
        category="Progress",
        scope="clock_partition",
        description="Completion state of MCSS Part 1 clock connection definition.",
        target_value="complete",
        status_mode="release_status",
    ),
    MetricDefinition(
        name="mcss_part1_release_status",
        deliverable="MCSS",
        category="Release",
        scope="clock_partition",
        description="Official release state of MCSS Part 1 for partition consumption.",
        target_value="released",
        status_mode="release_status",
    ),
    MetricDefinition(
        name="mcss_part2_completion_status",
        deliverable="MCSS",
        category="Progress",
        scope="clock_partition",
        description="Completion state of MCSS Part 2 relationship and stamping definition.",
        target_value="complete",
        status_mode="release_status",
    ),
    MetricDefinition(
        name="mcss_part2_release_status",
        deliverable="MCSS",
        category="Release",
        scope="clock_partition",
        description="Official release state of MCSS Part 2 for partition consumption.",
        target_value="released",
        status_mode="release_status",
    ),
    MetricDefinition(
        name="mcss_schema_validation_error_count",
        deliverable="MCSS",
        category="Quality",
        scope="clock_partition",
        description="Schema or structural validation errors found in MCSS collateral.",
        target_value=0.0,
        status_mode="zero_count",
    ),
    MetricDefinition(
        name="unresolved_clock_connection_count",
        deliverable="MCSS",
        category="Quality",
        scope="clock_partition",
        description="Required clock connections missing from MCSS definitions.",
        target_value=0.0,
        status_mode="zero_count",
    ),
    MetricDefinition(
        name="invalid_clock_relationship_count",
        deliverable="MCSS",
        category="Quality",
        scope="clock_partition",
        description="Invalid generated, muxed, divided, or gated clock relationships.",
        target_value=0.0,
        status_mode="zero_count",
    ),
    MetricDefinition(
        name="stamping_mismatch_count",
        deliverable="MCSS",
        category="Quality",
        scope="clock_partition",
        description="Mismatches between stamped MCSS data and expected partition clock topology.",
        target_value=0.0,
        status_mode="zero_count",
        yellow_max=1.0,
    ),
    MetricDefinition(
        name="no_clock_on_reg_count",
        deliverable="MCSS",
        category="Quality",
        scope="partition",
        description="Registers with no resolved clock in static partition checks.",
        target_value=0.0,
        status_mode="zero_count",
    ),
    MetricDefinition(
        name="unexpected_clock_on_reg_count",
        deliverable="MCSS",
        category="Quality",
        scope="partition",
        description="Registers receiving an unexpected clock after stamping or integration.",
        target_value=0.0,
        status_mode="zero_count",
    ),
    MetricDefinition(
        name="mcss_consumer_runs_behind",
        deliverable="MCSS",
        category="Freshness",
        scope="clock_partition",
        description="How many accepted source revisions the partition consumer lags behind MCSS release.",
        target_value=0.0,
        status_mode="freshness_lag",
        yellow_max=1.0,
    ),
]

METRICS_BY_NAME: dict[str, MetricDefinition] = {metric.name: metric for metric in METRICS}


def get_metric_definition(name: str) -> MetricDefinition:
    """Return the definition for a metric name, raising a useful error if unknown."""

    try:
        return METRICS_BY_NAME[name]
    except KeyError as exc:
        raise KeyError(f"Unknown metric: {name}") from exc


def metric_names(required_only: bool = False) -> list[str]:
    """Return all metric names, optionally limited to 0p5 gate metrics."""

    return [metric.name for metric in METRICS if metric.required_for_0p5 or not required_only]


def expected_record_fields() -> dict[str, Any]:
    """Document the normalized record shape used between ingestion and core layers."""

    return {
        "milestone": "0p5",
        "deliverable": "CB2 or MCSS",
        "clock": "clock identifier or None for partition-only metrics",
        "partition": "partition identifier",
        "metric": "metric name from METRICS",
        "value": "numeric, bool, or status string",
        "source": {
            "system": "source system name",
            "uri": "source path or API endpoint",
            "revision": "source revision or release label",
            "run_id": "partition or collection run id",
            "collected_at": "ISO-8601 timestamp",
        },
    }
