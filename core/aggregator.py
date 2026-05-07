"""Aggregate normalized clock distribution metrics into dashboard-ready rollups."""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Iterable

from core.metrics_definitions import METRICS, MetricDefinition, get_metric_definition
from core.status_eval import combine_statuses, evaluate_status, finish_state

MetricRecord = dict[str, Any]


class MetricsAggregator:
    """Stores latest metric values and computes clock, partition, and program readiness."""

    def __init__(
        self,
        milestone: str = "0p5",
        partition_inventory: Iterable[dict[str, Any]] | None = None,
        clock_inventory: Iterable[dict[str, Any]] | None = None,
    ) -> None:
        self.milestone = milestone
        self.records: list[MetricRecord] = []
        self._records_by_key: dict[tuple[str | None, str | None, str | None, str], MetricRecord] = {}
        self.partition_inventory: dict[str, dict[str, Any]] = {}
        self.clock_inventory: dict[str, dict[str, Any]] = {}
        self.set_partition_inventory(partition_inventory or [])
        self.set_clock_inventory(clock_inventory or [])

    def set_partition_inventory(self, partition_inventory: Iterable[dict[str, Any]]) -> None:
        """Register authoritative partition metadata for dashboard coverage."""

        self.partition_inventory = {
            str(partition["partition"]): deepcopy(partition)
            for partition in partition_inventory
            if partition.get("partition") and partition.get("active", True)
        }

    def set_clock_inventory(self, clock_inventory: Iterable[dict[str, Any]]) -> None:
        """Register authoritative clock domain metadata for dashboard coverage."""

        self.clock_inventory = {
            str(clock["clock"]): deepcopy(clock)
            for clock in clock_inventory
            if clock.get("clock") and clock.get("active", True)
        }

    def clock_ids(self) -> list[str]:
        """Return the union of inventoried clocks and clocks with metric records."""

        record_clocks = {record["clock"] for record in self.records if record.get("clock")}
        return sorted(set(self.clock_inventory) | record_clocks)

    def partition_ids(self) -> list[str]:
        """Return the union of inventoried partitions and partitions with metric records."""

        record_partitions = {record["partition"] for record in self.records if record.get("partition")}
        return sorted(set(self.partition_inventory) | record_partitions)

    def hierarchy_ids(self, deliverable: str | None = None) -> list[str]:
        """Return hierarchy IDs with metric records, optionally scoped by deliverable."""

        return sorted(
            {
                str(record["hierarchy"])
                for record in self.records
                if record.get("hierarchy") and (deliverable is None or record.get("deliverable") == deliverable)
            }
        )

    def update_from_records(self, records: Iterable[MetricRecord]) -> None:
        """Merge normalized records into the current snapshot."""

        for raw_record in records:
            record = self._normalize_record(raw_record)
            key = (record.get("clock"), record.get("partition"), record.get("hierarchy"), record["metric"])
            self._records_by_key[key] = record
        self.records = list(self._records_by_key.values())

    def update_from_ingestion(self, records: Iterable[MetricRecord]) -> None:
        """Compatibility wrapper for ingestion collectors."""

        self.update_from_records(records)

    def rollup_clock_metrics(self, clock: str) -> dict[str, Any]:
        """Return evaluated metrics and readiness for one clock across all partitions."""

        matching = [record for record in self.records if record.get("clock") == clock]
        return self._build_rollup(
            entity_type="clock",
            entity_id=clock,
            records=matching,
            metadata=self.clock_inventory.get(clock, {}),
        )

    def rollup_partition_metrics(self, partition: str) -> dict[str, Any]:
        """Return evaluated metrics and readiness for one partition across all clocks."""

        matching = [record for record in self.records if record.get("partition") == partition]
        return self._build_rollup(
            entity_type="partition",
            entity_id=partition,
            records=matching,
            metadata=self.partition_inventory.get(partition, {}),
        )

    def rollup_hierarchy_metrics(self, hierarchy: str) -> dict[str, Any]:
        """Return evaluated metrics and readiness for one implementation hierarchy."""

        matching = [record for record in self.records if record.get("hierarchy") == hierarchy]
        return self._build_rollup(entity_type="hierarchy", entity_id=hierarchy, records=matching)

    def rollup_clock_partition(self, clock: str, partition: str) -> dict[str, Any]:
        """Return evaluated metrics and readiness for a single clock-partition pair."""

        matching = [
            record
            for record in self.records
            if record.get("partition") == partition and record.get("clock") in {clock, None}
        ]
        return self._build_rollup(entity_type="clock_partition", entity_id=f"{clock}::{partition}", records=matching)

    def program_summary(self) -> dict[str, Any]:
        """Compute top-level counts and status distribution for manager summary cards."""

        clocks = self.clock_ids()
        partitions = self.partition_ids()
        pairs = sorted(
            {
                (record["clock"], record["partition"])
                for record in self.records
                if record.get("clock") and record.get("partition")
            }
        )

        pair_rollups = [self.rollup_clock_partition(clock, partition) for clock, partition in pairs]
        status_counts = defaultdict(int)
        required_records = [record for record in self.evaluated_records() if get_metric_definition(record["metric"]).required_for_0p5]
        for record in required_records:
            status_counts[record["status"]] += 1

        blockers = self.blocking_issues()
        ready_pairs = sum(1 for rollup in pair_rollups if rollup["status"] == "Green")
        total_pairs = len(pair_rollups)
        finish_status = combine_statuses([record["status"] for record in required_records])

        return {
            "milestone": self.milestone,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "clock_count": len(clocks),
            "inventory_clock_count": len(self.clock_inventory),
            "partition_count": len(partitions),
            "inventory_partition_count": len(self.partition_inventory),
            "cb2_hierarchy_count": len(self.hierarchy_ids("CB2")),
            "cb2_post_push_partition_count": len(
                {
                    record.get("partition")
                    for record in self.records
                    if record.get("deliverable") == "CB2" and record.get("checklist") == "post_push" and record.get("partition")
                }
            ),
            "clock_partition_pair_count": total_pairs,
            "ready_clock_partition_pairs": ready_pairs,
            "ready_clock_partition_pct": round((ready_pairs / total_pairs) * 100, 1) if total_pairs else 0.0,
            "status_counts": dict(status_counts),
            "open_blocker_count": len(blockers),
            "finish_state": finish_state(finish_status),
        }

    def blocking_issues(self) -> list[MetricRecord]:
        """Return evaluated records that are currently Red, with provenance preserved."""

        issues = []
        for record in self.evaluated_records():
            if record["status"] == "Red":
                issues.append(record)
        return sorted(
            issues,
            key=lambda item: (item.get("hierarchy") or "", item.get("partition") or "", item.get("clock") or "", item["metric"]),
        )

    def evaluated_records(self) -> list[MetricRecord]:
        """Return every raw record with metric definition details and evaluated status."""

        evaluated = []
        for record in self.records:
            metric = get_metric_definition(record["metric"])
            evaluated_record = deepcopy(record)
            evaluated_record.update(
                {
                    "deliverable": metric.deliverable,
                    "category": metric.category,
                    "description": metric.description,
                    "target": metric.target_value,
                    "status": evaluate_status(metric, record.get("value")),
                }
            )
            evaluated.append(evaluated_record)
        return evaluated

    def _build_rollup(
        self,
        entity_type: str,
        entity_id: str,
        records: list[MetricRecord],
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        evaluated = []
        statuses = []
        by_deliverable: dict[str, list[str]] = defaultdict(list)
        by_category: dict[str, list[str]] = defaultdict(list)

        for record in records:
            metric = get_metric_definition(record["metric"])
            status = evaluate_status(metric, record.get("value"))
            evaluated_record = deepcopy(record)
            evaluated_record.update(
                {
                    "deliverable": metric.deliverable,
                    "category": metric.category,
                    "description": metric.description,
                    "target": metric.target_value,
                    "status": status,
                }
            )
            evaluated.append(evaluated_record)
            if metric.required_for_0p5:
                statuses.append(status)
                by_deliverable[metric.deliverable].append(status)
                by_category[metric.category].append(status)

        overall_status = combine_statuses(statuses)
        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "metadata": metadata or {},
            "status": overall_status,
            "finish_state": finish_state(overall_status),
            "deliverables": {
                deliverable: {
                    "status": combine_statuses(deliverable_statuses),
                    "finish_state": finish_state(combine_statuses(deliverable_statuses)),
                }
                for deliverable, deliverable_statuses in sorted(by_deliverable.items())
            },
            "categories": {
                category: {
                    "status": combine_statuses(category_statuses),
                    "finish_state": finish_state(combine_statuses(category_statuses)),
                }
                for category, category_statuses in sorted(by_category.items())
            },
            "metrics": sorted(evaluated, key=lambda item: (item["deliverable"], item["category"], item["metric"])),
        }

    def _normalize_record(self, record: MetricRecord) -> MetricRecord:
        metric: MetricDefinition = get_metric_definition(record["metric"])
        normalized = deepcopy(record)
        normalized.setdefault("milestone", self.milestone)
        normalized.setdefault("deliverable", metric.deliverable)
        normalized.setdefault("clock", None)
        normalized.setdefault("partition", None)
        normalized.setdefault("hierarchy", None)
        normalized.setdefault("checklist", None)
        normalized.setdefault("source", {})
        normalized["source"].setdefault("system", "unknown")
        normalized["source"].setdefault("uri", None)
        normalized["source"].setdefault("revision", None)
        normalized["source"].setdefault("run_id", None)
        normalized["source"].setdefault("collected_at", datetime.now(timezone.utc).isoformat())
        return normalized


def combine_source_records(*record_groups: Iterable[MetricRecord]) -> list[MetricRecord]:
    """Flatten source record groups from multiple ingestors into one list."""

    combined: list[MetricRecord] = []
    for group in record_groups:
        combined.extend(group)
    return combined
