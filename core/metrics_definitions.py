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
        name="cb2_checker_app_options_status",
        deliverable="CB2",
        category="Pre-Push",
        scope="hierarchy",
        description="GCXGEN checker app options are configured for the CB2 pre-push run.",
        target_value="pass",
        status_mode="release_status",
    ),
    MetricDefinition(
        name="cb2_pre_req_status",
        deliverable="CB2",
        category="Pre-Push",
        scope="hierarchy",
        description="CB2 pre-push checker prerequisites are satisfied.",
        target_value="pass",
        status_mode="release_status",
    ),
    MetricDefinition(
        name="cb2_opens_status",
        deliverable="CB2",
        category="Pre-Push",
        scope="hierarchy",
        description="No open nets are reported by the CB2 pre-push checker.",
        target_value="pass",
        status_mode="release_status",
    ),
    MetricDefinition(
        name="cb2_shorts_status",
        deliverable="CB2",
        category="Pre-Push",
        scope="hierarchy",
        description="No shorts are reported by the CB2 pre-push checker.",
        target_value="pass",
        status_mode="release_status",
    ),
    MetricDefinition(
        name="cb2_missing_shield_status",
        deliverable="CB2",
        category="Pre-Push",
        scope="hierarchy",
        description="No missing shield issues are reported for CB2 routes.",
        target_value="pass",
        status_mode="release_status",
    ),
    MetricDefinition(
        name="cb2_downgrade_quality_status",
        deliverable="CB2",
        category="Pre-Push",
        scope="hierarchy",
        description="Downgrade quality passes CB2 pre-push checks.",
        target_value="pass",
        status_mode="release_status",
    ),
    MetricDefinition(
        name="cb2_wires_on_track_status",
        deliverable="CB2",
        category="Pre-Push",
        scope="hierarchy",
        description="CB2 wires are drawn on the expected tracks.",
        target_value="pass",
        status_mode="release_status",
    ),
    MetricDefinition(
        name="cb2_drc_status",
        deliverable="CB2",
        category="Pre-Push",
        scope="hierarchy",
        description="CB2 DRC checks pass for the hierarchy.",
        target_value="pass",
        status_mode="release_status",
    ),
    MetricDefinition(
        name="cb2_floating_vias_status",
        deliverable="CB2",
        category="Pre-Push",
        scope="hierarchy",
        description="No floating vias are reported in CB2 collateral.",
        target_value="pass",
        status_mode="release_status",
    ),
    MetricDefinition(
        name="cb2_shielding_shorts_status",
        deliverable="CB2",
        category="Pre-Push",
        scope="hierarchy",
        description="No shielding shorts are reported in CB2 collateral.",
        target_value="pass",
        status_mode="release_status",
    ),
    MetricDefinition(
        name="cb2_downgrade_shape_boundary_status",
        deliverable="CB2",
        category="Pre-Push",
        scope="hierarchy",
        description="Downgrade shapes remain inside the block boundary.",
        target_value="pass",
        status_mode="release_status",
    ),
    MetricDefinition(
        name="cb2_cell_to_cell_spacing_status",
        deliverable="CB2",
        category="Pre-Push",
        scope="hierarchy",
        description="Cell-to-cell spacing passes CB2 requirements.",
        target_value="pass",
        status_mode="release_status",
    ),
    MetricDefinition(
        name="cb2_objects_locked_status",
        deliverable="CB2",
        category="Pre-Push",
        scope="hierarchy",
        description="CB2 objects are locked as expected before push.",
        target_value="pass",
        status_mode="release_status",
    ),
    MetricDefinition(
        name="cb2_cell_overlap_status",
        deliverable="CB2",
        category="Pre-Push",
        scope="hierarchy",
        description="CB2 cells do not overlap each other.",
        target_value="pass",
        status_mode="release_status",
    ),
    MetricDefinition(
        name="cb2_cell_to_hip_va_spacing_status",
        deliverable="CB2",
        category="Pre-Push",
        scope="hierarchy",
        description="Spacing between CB2 cells and other HIPs or VAs passes requirements.",
        target_value="pass",
        status_mode="release_status",
    ),
    MetricDefinition(
        name="cb2_post_push_opens_status",
        deliverable="CB2",
        category="Post-Push",
        scope="partition",
        description="No opens are reported by the CB2 post-push archive run.",
        target_value="pass",
        status_mode="release_status",
    ),
    MetricDefinition(
        name="cb2_post_push_shorts_status",
        deliverable="CB2",
        category="Post-Push",
        scope="partition",
        description="No shorts are reported by the CB2 post-push archive run.",
        target_value="pass",
        status_mode="release_status",
    ),
    MetricDefinition(
        name="cb2_post_push_extra_objects_status",
        deliverable="CB2",
        category="Post-Push",
        scope="partition",
        description="No extra CB2 objects are reported by the post-push archive run.",
        target_value="pass",
        status_mode="release_status",
    ),
    MetricDefinition(
        name="cb2_post_push_shield_tapping_status",
        deliverable="CB2",
        category="Post-Push",
        scope="partition",
        description="Shield tapping passes the CB2 post-push archive run checks.",
        target_value="pass",
        status_mode="release_status",
    ),
    MetricDefinition(
        name="cb2_post_push_missing_shield_status",
        deliverable="CB2",
        category="Post-Push",
        scope="partition",
        description="No missing shield issues are reported by the CB2 post-push archive run.",
        target_value="pass",
        status_mode="release_status",
    ),
    MetricDefinition(
        name="cb2_post_push_viewlogic_status",
        deliverable="CB2",
        category="Post-Push",
        scope="partition",
        description="Viewlogic checks pass in the CB2 post-push archive run.",
        target_value="pass",
        status_mode="release_status",
    ),
    MetricDefinition(
        name="cb2_post_push_attribute_conflict_status",
        deliverable="CB2",
        category="Post-Push",
        scope="partition",
        description="No attribute conflicts are reported by the CB2 post-push archive run.",
        target_value="pass",
        status_mode="release_status",
    ),
    MetricDefinition(
        name="cb2_post_push_crb_mismatch_status",
        deliverable="CB2",
        category="Post-Push",
        scope="partition",
        description="No CRB mismatches are reported by the CB2 post-push archive run.",
        target_value="pass",
        status_mode="release_status",
    ),
    MetricDefinition(
        name="mcss_release_status",
        deliverable="MCSS",
        category="Release",
        scope="partition",
        description="Overall MCSS release state; released only when all required collateral files are available.",
        target_value="released",
        status_mode="release_status",
    ),
    MetricDefinition(
        name="mcss_clock_definition_status",
        deliverable="MCSS",
        category="Release",
        scope="partition",
        description="Availability of the MCSS clock definition collateral for the partition.",
        target_value="available",
        status_mode="release_status",
    ),
    MetricDefinition(
        name="mcss_uncertainty_status",
        deliverable="MCSS",
        category="Release",
        scope="partition",
        description="Availability of the MCSS uncertainty collateral for the partition.",
        target_value="available",
        status_mode="release_status",
    ),
    MetricDefinition(
        name="mcss_latencies_status",
        deliverable="MCSS",
        category="Release",
        scope="partition",
        description="Availability of the MCSS latency collateral for the partition.",
        target_value="available",
        status_mode="release_status",
    ),
    MetricDefinition(
        name="mcss_stampings_status",
        deliverable="MCSS",
        category="Release",
        scope="partition",
        description="Availability of the MCSS stamping collateral for the partition.",
        target_value="available",
        status_mode="release_status",
    ),
    MetricDefinition(
        name="mcss_exceptions_status",
        deliverable="MCSS",
        category="Release",
        scope="partition",
        description="Availability of the MCSS exception collateral for the partition.",
        target_value="available",
        status_mode="release_status",
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
        "hierarchy": "implementation hierarchy for hierarchy-scoped CB2 checks, otherwise None",
        "checklist": "pre_push or post_push for CB2 checklist metrics, otherwise None",
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
