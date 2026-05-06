from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ingestion import load_records_from_json
from ingestion.clock_inventory_ingestor import get_clock_inventory
from ingestion.clock_repo_ingestor import get_latest_metrics as get_cb2_metrics
from ingestion.partition_inventory_ingestor import get_partition_inventory
from ingestion.stamping_collateral_ingestor import get_latest_metrics as get_mcss_metrics


class IngestionTests(unittest.TestCase):
    def test_load_records_from_top_level_list(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "metrics.json"
            source.write_text(
                json.dumps(
                    [
                        {
                            "metric": "routes_completed_pct",
                            "clock": "clk_test",
                            "partition": "partition_test",
                            "value": 100.0,
                        }
                    ]
                ),
                encoding="utf-8",
            )

            records = load_records_from_json(source)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["metric"], "routes_completed_pct")

    def test_load_records_from_records_object(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "metrics.json"
            source.write_text(
                json.dumps(
                    {
                        "records": [
                            {
                                "metric": "blockages_drawn_pct",
                                "clock": "clk_test",
                                "partition": "partition_test",
                                "value": 90.0,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            records = load_records_from_json(source)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["value"], 90.0)

    def test_cb2_ingestor_stamps_source_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "cb2.json"
            source.write_text(
                json.dumps(
                    [
                        {
                            "metric": "routes_completed_pct",
                            "clock": "clk_test",
                            "partition": "partition_test",
                            "value": 100.0,
                        }
                    ]
                ),
                encoding="utf-8",
            )

            records = get_cb2_metrics(source)

        self.assertEqual(records[0]["deliverable"], "CB2")
        self.assertEqual(records[0]["source"]["system"], "cb2_repo")

    def test_nwpnio_partition_inventory_loads_and_normalizes_names(self) -> None:
        inventory = get_partition_inventory()

        self.assertEqual(inventory["program"], "NWPNIO")
        self.assertEqual(len(inventory["active_partitions"]), 196)
        partition_names = {partition["partition"] for partition in inventory["active_partitions"]}
        self.assertIn("paracciommu", partition_names)
        self.assertIn("parscfubruiodatatype2", partition_names)
        self.assertIn("parcabpwba", partition_names)
        self.assertEqual(len(inventory["normalization_warnings"]), 3)

    def test_nwpnio_clock_inventory_loads_clock_domains(self) -> None:
        inventory = get_clock_inventory()

        self.assertEqual(inventory["program"], "NWPNIO")
        self.assertEqual(len(inventory["active_clocks"]), 52)
        clock_names = {clock["clock"] for clock in inventory["active_clocks"]}
        self.assertIn("mc_2x_clk", clock_names)
        self.assertIn("bclk1_pn", clock_names)
        self.assertIn("grs_ana_xtalclk", clock_names)

    def test_mcss_release_scan_detects_part1_and_part2_from_clocks_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            release_dir = Path(temp_dir) / "par_test" / "clock_collateral"
            release_dir.mkdir(parents=True)
            (release_dir / "par_test_clocks.tcl").write_text(
                "create_clock -name mc_clk -period 1.0 [get_ports mc_clk]\n"
                "create_clock -period 2.0 -name {uclk_io} [get_ports uclk_io]\n",
                encoding="utf-8",
            )

            with patch.dict(
                "os.environ",
                {"MCSS_RELEASE_TEMPLATE": str(Path(temp_dir) / "{partition}" / "clock_collateral")},
            ):
                records = get_mcss_metrics(
                    partitions=[{"partition": "par_test", "active": True}],
                    scan_release_tree=True,
                )

            values = {(record["clock"], record["metric"]): record["value"] for record in records}
            self.assertEqual(values[("mc_clk", "mcss_part1_release_status")], "released")
            self.assertEqual(values[("mc_clk", "mcss_part2_release_status")], "released")
            self.assertEqual(values[("uclk_io", "mcss_part1_release_status")], "released")
            self.assertEqual(values[("uclk_io", "mcss_part2_release_status")], "released")
            self.assertTrue(all(record["source"]["uri"].endswith("par_test_clocks.tcl") for record in records))


if __name__ == "__main__":
    unittest.main()
