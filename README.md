# Global Clock Distribution Dashboard

Initial scaffold for a 0p5 progress and quality dashboard covering CB2 collateral and MCSS release collateral readiness.

The dashboard is designed to derive status from repositories, release manifests, partition run logs, and static checks. It should not depend on manual status entry by clock owners.

## What It Tracks

The initial NWPNIO partition inventory is stored in `data/nwpnio_partition_inventory.json` and currently contains 196 active partitions grouped by `subfc`.
The initial NWPNIO clock inventory is stored in `data/nwpnio_clock_inventory.json` and currently contains 52 active clock domains.
The initial MCSS archive directory pattern is `$PROJ_ARCHIVE/arc/{partition}/clock_collateral/NIOA0_0P5_PRD/`, with `PROJ_ARCHIVE=/nfs/site/disks/nwp_arc_proj_archive/` for the current NWPNIO archive.

CB2 metrics include:

- Blockages drawn percentage
- Routes completed percentage
- Cells placed percentage
- CB2 release manifest status
- Route DRC count
- Missing expected routes
- Orphan routes
- Cell legality violations
- Consumer freshness lag

MCSS metrics include:

- Overall MCSS release status, green only when all required collateral files are present
- Clock definition collateral availability
- Uncertainty collateral availability
- Xvoltage collateral availability
- CDC collateral availability
- Latencies collateral availability
- Stampings collateral availability
- Exceptions collateral availability

## Repository Layout

```text
.github/
  agents/global_clock_dashboard_agent.md
  workflows/clock_metrics_pipeline.yml
ingestion/
  clock_repo_ingestor.py
  stamping_collateral_ingestor.py
  partition_run_ingestor.py
core/
  metrics_definitions.py
  status_eval.py
  aggregator.py
dashboard/
  view_model.py
  main.py
tests/
  test_metrics.py
  test_ingestion.py
```

## Run Locally

The project currently uses only the Python standard library.

```powershell
python -m unittest discover -s tests
python -m dashboard.main --scan-mcss-release-tree --output public/data/latest.json
```

In VS Code, you can also run the `Build Clock Dashboard Data` build task to regenerate the same payload.

## View the Dashboard

Generate the payload and serve the static UI:

```powershell
python -m dashboard.main --scan-mcss-release-tree --output public/data/latest.json
python -m http.server 8000 --directory public
```

Then open `http://localhost:8000/`.

The command writes a static dashboard payload to `public/data/latest.json` using representative sample data. Real source data can be passed later as normalized JSON exports:

```powershell
python -m dashboard.main `
  --cb2-source path/to/cb2_metrics.json `
  --mcss-source path/to/mcss_metrics.json `
  --partition-source path/to/partition_metrics.json `
  --inventory-source data/nwpnio_partition_inventory.json `
  --clock-inventory-source data/nwpnio_clock_inventory.json `
  --scan-mcss-release-tree `
  --output public/data/latest.json
```

Each JSON source may be either a list of records or an object with a top-level `records` list.
The inventory source uses a top-level `partitions` list with `partition`, `subfc`, and `active` fields.
The clock inventory source uses a top-level `clocks` list with `clock`, optional `display_name`, and `active` fields.
Set `PROJ_ARCHIVE` to `/nfs/site/disks/nwp_arc_proj_archive/`, or set `MCSS_RELEASE_TEMPLATE` to override the default MCSS release directory pattern. `MCSS_CLOCKS_FILE_TEMPLATE` can override only the full clocks Tcl file pattern. Templates must include `{partition}` where the partition name belongs.

When `--scan-mcss-release-tree` is set, the MCSS ingestor checks each active partition release folder for the expected collateral files and emits partition-level release availability records.

The MCSS release scan sources data from each partition archive clock collateral directory, for example:

```text
$PROJ_ARCHIVE/arc/pard2d1chnl/clock_collateral/NIOA0_0P5_PRD/
```

For each active partition, the default release directory template is:

```text
$PROJ_ARCHIVE/arc/{partition}/clock_collateral/NIOA0_0P5_PRD
```

MCSS release is marked `released` only when all required collateral types are found in that directory: clock definition, uncertainty, xvoltage, cdc, latencies, stampings, and exceptions. The scanner accepts known shared filenames such as `pdop_stamping.tcl`, looks for partition-prefixed files such as `{partition}_clocks.tcl`, `{partition}_uncertainty*.tcl`, `{partition}_xvoltage*.tcl`, `{partition}_cdc*.tcl`, `{partition}_latenc*.tcl`, `{partition}_stamp*.tcl`, and `{partition}_exception*.tcl`, and then uses broader fallback globs for each collateral type.

## Normalized Metric Record

```json
{
  "milestone": "0p5",
  "deliverable": "CB2",
  "clock": "clk_core",
  "partition": "partition_a",
  "metric": "routes_completed_pct",
  "value": 100.0,
  "source": {
    "system": "cb2_repo",
    "uri": "cb2/clk_core/partition_a/routes_completed_pct",
    "revision": "cb2_r26ww17.5",
    "run_id": "26ww17.5",
    "collected_at": "2026-05-04T10:30:00Z"
  }
}
```

## Finish-State Model

The dashboard separates file existence from readiness:

```text
Exists -> Complete -> Released -> Consumed -> Validated -> 0p5 Ready
```

A clock-partition pair is 0p5 ready only when required CB2 and MCSS metrics are green. Yellow means at risk. Red means blocked. Gray means no data or not applicable.
