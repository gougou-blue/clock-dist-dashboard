from __future__ import annotations

import unittest

from core.aggregator import MetricsAggregator, combine_source_records
from core.metrics_definitions import get_metric_definition
from core.status_eval import GREEN, RED, YELLOW, evaluate_status
from dashboard.view_model import format_for_ui
from ingestion import clock_repo_ingestor, partition_run_ingestor, stamping_collateral_ingestor
from ingestion.clock_inventory_ingestor import get_clock_inventory
from ingestion.partition_inventory_ingestor import get_partition_inventory


class StatusEvaluationTests(unittest.TestCase):
    def test_percent_complete_thresholds(self) -> None:
        metric = get_metric_definition("routes_completed_pct")
        self.assertEqual(evaluate_status(metric, 100.0), GREEN)
        self.assertEqual(evaluate_status(metric, 95.0), YELLOW)
        self.assertEqual(evaluate_status(metric, 60.0), RED)

    def test_zero_count_thresholds(self) -> None:
        metric = get_metric_definition("route_drc_count")
        self.assertEqual(evaluate_status(metric, 0), GREEN)
        self.assertEqual(evaluate_status(metric, 2), YELLOW)
        self.assertEqual(evaluate_status(metric, 3), RED)

    def test_release_status_values(self) -> None:
        metric = get_metric_definition("mcss_release_status")
        self.assertEqual(evaluate_status(metric, "released"), GREEN)
        self.assertEqual(evaluate_status(metric, "pending"), YELLOW)
        self.assertEqual(evaluate_status(metric, "not_released"), RED)


class AggregatorTests(unittest.TestCase):
    def test_sample_data_has_ready_and_blocked_pairs(self) -> None:
        aggregator = MetricsAggregator()
        aggregator.update_from_records(
            combine_source_records(
                clock_repo_ingestor.sample_metrics(),
                stamping_collateral_ingestor.sample_metrics(),
                partition_run_ingestor.sample_metrics(),
            )
        )

        ready_pair = aggregator.rollup_clock_partition("mc_clk", "pard2d1uladda0")
        blocked_pair = aggregator.rollup_clock_partition("uclk_io", "paracciommu")

        self.assertEqual(ready_pair["finish_state"], "0p5 Ready")
        self.assertEqual(blocked_pair["finish_state"], "Blocked")

    def test_view_model_contains_summary_cards_and_blockers(self) -> None:
        aggregator = MetricsAggregator()
        aggregator.update_from_records(
            combine_source_records(
                clock_repo_ingestor.sample_metrics(),
                stamping_collateral_ingestor.sample_metrics(),
                partition_run_ingestor.sample_metrics(),
            )
        )

        payload = format_for_ui(aggregator)

        self.assertIn("summary", payload)
        self.assertIn("cards", payload)
        self.assertGreater(payload["summary"]["open_blocker_count"], 0)
        self.assertEqual(payload["summary"]["clock_count"], 2)
        self.assertEqual(payload["summary"]["partition_count"], 2)

    def test_clock_inventory_is_included_without_metric_records(self) -> None:
        inventory = get_clock_inventory()
        aggregator = MetricsAggregator(clock_inventory=inventory["active_clocks"])

        payload = format_for_ui(aggregator)

        self.assertEqual(payload["summary"]["inventory_clock_count"], 52)
        self.assertEqual(payload["summary"]["clock_count"], 52)
        self.assertEqual(len(payload["clocks"]), 52)
        self.assertEqual(payload["clocks"][0]["finish_state"], "No Data")

    def test_inventory_partitions_are_included_without_metric_records(self) -> None:
        inventory = get_partition_inventory()
        aggregator = MetricsAggregator(partition_inventory=inventory["active_partitions"])

        payload = format_for_ui(aggregator)

        self.assertEqual(payload["summary"]["inventory_partition_count"], 196)
        self.assertEqual(payload["summary"]["partition_count"], 196)
        self.assertEqual(len(payload["partitions"]), 196)
        self.assertEqual(payload["partitions"][0]["finish_state"], "No Data")


if __name__ == "__main__":
    unittest.main()
