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
from ingestion.stamping_collateral_ingestor import expand_release_template
from ingestion.stamping_collateral_ingestor import scan_release_metrics


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

    def test_mcss_release_scan_detects_complete_collateral_release(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            release_dir = Path(temp_dir) / "par_test" / "clock_collateral"
            release_dir.mkdir(parents=True)
            (release_dir / "par_test_clocks.tcl").write_text(
                "create_clock -name mc_clk -period 1.0 [get_ports mc_clk]\n"
                "create_clock -period 2.0 -name {uclk_io} [get_ports uclk_io]\n",
                encoding="utf-8",
            )
            for file_name in (
                "par_test_uncertainty.tcl",
                "par_test_latencies.tcl",
                "pdop_stamping.tcl",
                "par_test_exceptions.tcl",
            ):
                (release_dir / file_name).write_text("# released\n", encoding="utf-8")

            with patch.dict(
                "os.environ",
                {"MCSS_RELEASE_TEMPLATE": str(Path(temp_dir) / "{partition}" / "clock_collateral")},
            ):
                records = get_mcss_metrics(
                    partitions=[{"partition": "par_test", "active": True}],
                    scan_release_tree=True,
                )

            partition_values = {record["metric"]: record["value"] for record in records if record["clock"] is None}
            self.assertEqual(partition_values["mcss_release_status"], "released")
            self.assertEqual(partition_values["mcss_clock_definition_status"], "available")
            self.assertEqual(partition_values["mcss_uncertainty_status"], "available")
            self.assertEqual(partition_values["mcss_latencies_status"], "available")
            self.assertEqual(partition_values["mcss_stampings_status"], "available")
            self.assertEqual(partition_values["mcss_exceptions_status"], "available")
            self.assertFalse(any(record["clock"] for record in records))
            self.assertTrue(any(record["source"]["uri"].endswith("par_test_clocks.tcl") for record in records))

    def test_mcss_release_scan_uses_proj_archive_template_for_all_partitions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            archive_root = Path(temp_dir) / "archive"
            for partition in ("pard2d1chnl", "parcd2dufich0e"):
                release_dir = archive_root / "arc" / partition / "clock_collateral" / "NIOA0_0P5_PRD"
                release_dir.mkdir(parents=True)
                (release_dir / f"{partition}_clocks.tcl").write_text("# clocks\n", encoding="utf-8")
                (release_dir / f"{partition}_uncertainty.tcl").write_text("# uncertainty\n", encoding="utf-8")
                (release_dir / f"{partition}_latencies.tcl").write_text("# latencies\n", encoding="utf-8")
                (release_dir / "pdop_stamping.tcl").write_text("# stampings\n", encoding="utf-8")
                (release_dir / f"{partition}_exceptions.tcl").write_text("# exceptions\n", encoding="utf-8")

            with patch.dict("os.environ", {"PROJ_ARCHIVE": str(archive_root)}, clear=False):
                records = scan_release_metrics(
                    [
                        {"partition": "pard2d1chnl", "active": True},
                        {"partition": "parcd2dufich0e", "active": True},
                    ]
                )

            self.assertEqual(len(records), 12)
            self.assertEqual({record["partition"] for record in records}, {"pard2d1chnl", "parcd2dufich0e"})
            self.assertTrue(all(record["value"] in {"released", "available"} for record in records))
            self.assertTrue(all("NIOA0_0P5_PRD" in record["source"]["uri"] for record in records))

    def test_mcss_release_template_defaults_proj_archive_when_env_is_unset(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            expanded = expand_release_template("$PROJ_ARCHIVE/arc/{partition}/clock_collateral/NIOA0_0P5_PRD")

        self.assertEqual(
            expanded,
            "/nfs/site/disks/nwp_arc_proj_archive/arc/{partition}/clock_collateral/NIOA0_0P5_PRD",
        )

    def test_mcss_release_scan_marks_release_missing_when_any_collateral_file_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            release_dir = Path(temp_dir) / "par_test" / "clock_collateral"
            release_dir.mkdir(parents=True)
            (release_dir / "par_test_clocks.tcl").write_text(
                "create_clock -name mc_clk -period 1.0 [get_ports mc_clk]\n",
                encoding="utf-8",
            )
            for file_name in (
                "par_test_uncertainty.tcl",
                "par_test_latencies.tcl",
                "par_test_stampings.tcl",
            ):
                (release_dir / file_name).write_text("# released\n", encoding="utf-8")

            with patch.dict(
                "os.environ",
                {"MCSS_RELEASE_TEMPLATE": str(Path(temp_dir) / "{partition}" / "clock_collateral")},
            ):
                records = get_mcss_metrics(
                    partitions=[{"partition": "par_test", "active": True}],
                    scan_release_tree=True,
                )

            partition_records = {record["metric"]: record for record in records if record["clock"] is None}
            self.assertEqual(partition_records["mcss_release_status"]["value"], "not_released")
            self.assertEqual(partition_records["mcss_release_status"]["source"]["missing_collateral"], ["exceptions"])
            self.assertEqual(partition_records["mcss_exceptions_status"]["value"], "missing")


if __name__ == "__main__":
    unittest.main()
