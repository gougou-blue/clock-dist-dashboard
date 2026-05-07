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
    def test_cb2_checklist_status_values(self) -> None:
        metric = get_metric_definition("cb2_drc_status")
        self.assertEqual(evaluate_status(metric, "pass"), GREEN)
        self.assertEqual(evaluate_status(metric, "fail"), RED)

    def test_release_status_values(self) -> None:
        metric = get_metric_definition("mcss_release_status")
        self.assertEqual(evaluate_status(metric, "released"), GREEN)
        self.assertEqual(evaluate_status(metric, "pending"), YELLOW)
        self.assertEqual(evaluate_status(metric, "not_released"), RED)

    def test_cb2_post_push_check_status_values(self) -> None:
        metric = get_metric_definition("cb2_post_push_opens_status")
        self.assertEqual(evaluate_status(metric, "pass"), GREEN)
        self.assertEqual(evaluate_status(metric, "missing"), RED)


class AggregatorTests(unittest.TestCase):
    def test_sample_data_has_passing_and_failing_cb2_hierarchies(self) -> None:
        aggregator = MetricsAggregator()
        aggregator.update_from_records(
            combine_source_records(
                clock_repo_ingestor.sample_metrics(),
                stamping_collateral_ingestor.sample_metrics(),
                partition_run_ingestor.sample_metrics(),
            )
        )

        soc = aggregator.rollup_hierarchy_metrics("SOC")
        d2d4 = aggregator.rollup_hierarchy_metrics("D2D4")

        self.assertEqual(soc["finish_state"], "0p5 Ready")
        self.assertEqual(d2d4["finish_state"], "Blocked")

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
        self.assertIn("cb2_hierarchies", payload)
        self.assertEqual(len(payload["metadata"]["cb2_checklists"]["post_push"]), 8)
        self.assertIn(
            "cb2_post_push_crb_mismatch_status",
            {item["metric"] for item in payload["metadata"]["cb2_checklists"]["post_push"]},
        )
        self.assertGreater(payload["summary"]["open_blocker_count"], 0)
        self.assertEqual(payload["summary"]["cb2_hierarchy_count"], 7)
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
