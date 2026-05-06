"""MCSS collateral ingestion for connection, relationship, and stamping metrics."""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ingestion import MetricRecord, load_records_from_json

SOURCE_SYSTEM = "mcss_stamping"
DEFAULT_ENV_VAR = "MCSS_METRICS_JSON"
DEFAULT_RELEASE_TEMPLATE = "/nfs/site/disks/nwp_clk_0002/aagoyal/nio_a0_ww17a/nio-a0-26ww17b/output/imh/imh_r2g_lite_fc/{partition}.imh_stack_r2g_fc/runs/{partition}/1276.5_dot4/release/latest/clock_collateral"
RELEASE_TEMPLATE_ENV_VAR = "MCSS_RELEASE_TEMPLATE"
CLOCKS_FILE_TEMPLATE_ENV_VAR = "MCSS_CLOCKS_FILE_TEMPLATE"
CREATE_CLOCK_NAME_PATTERN = re.compile(r"\bcreate_clock\b(?P<body>[^\n;]*)", re.IGNORECASE)
NAME_OPTION_PATTERN = re.compile(r"""(?:^|\s)-name\s+(?P<name>\{[^}]+\}|"[^"]+"|'[^']+'|\S+)""")


def get_latest_metrics(
    source_path: str | Path | None = None,
    partitions: list[dict[str, Any]] | None = None,
    scan_release_tree: bool = False,
) -> list[MetricRecord]:
    """Return latest MCSS metric records from JSON export or sample data."""

    resolved_path = source_path or os.environ.get(DEFAULT_ENV_VAR)
    if resolved_path:
        return _stamp_source_defaults(load_records_from_json(resolved_path))
    if scan_release_tree and partitions:
        return scan_release_metrics(partitions)
    return sample_metrics()


def scan_release_metrics(partitions: list[dict[str, Any]]) -> list[MetricRecord]:
    """Scan per-partition MCSS clocks files for release and clock coverage."""

    collected_at = datetime.now(timezone.utc).isoformat()
    records: list[MetricRecord] = []
    for partition in partitions:
        partition_name = str(partition["partition"])
        clocks_file = _clocks_file_path(partition_name)
        is_released = clocks_file.is_file()
        revision = _release_revision(clocks_file)
        clock_names = parse_create_clock_names(clocks_file) if is_released else []
        release_value = "released" if is_released else "not_released"
        clock_targets = clock_names or [None]

        for clock in clock_targets:
            records.append(
                _release_record(
                    clock,
                    partition_name,
                    "mcss_part1_release_status",
                    release_value,
                    revision,
                    collected_at,
                    clocks_file,
                )
            )
            records.append(
                _release_record(
                    clock,
                    partition_name,
                    "mcss_part2_release_status",
                    release_value,
                    revision,
                    collected_at,
                    clocks_file,
                )
            )
    return records


def parse_create_clock_names(clocks_file: str | Path) -> list[str]:
    """Parse clock names from create_clock commands in a released MCSS clocks file."""

    content = Path(clocks_file).read_text(encoding="utf-8", errors="ignore")
    commands = _join_tcl_continuations(_strip_tcl_comments(content))
    names = []
    for match in CREATE_CLOCK_NAME_PATTERN.finditer(commands):
        option_match = NAME_OPTION_PATTERN.search(match.group("body"))
        if option_match:
            names.append(_clean_tcl_token(option_match.group("name")))
    return sorted({name for name in names if name})


def sample_metrics() -> list[MetricRecord]:
    collected_at = datetime.now(timezone.utc).isoformat()
    return [
        _record("mc_clk", "pard2d1uladda0", "mcss_part1_completion_status", "complete", "mcss_r26ww17.4", collected_at),
        _record("mc_clk", "pard2d1uladda0", "mcss_part1_release_status", "released", "mcss_r26ww17.4", collected_at),
        _record("mc_clk", "pard2d1uladda0", "mcss_part2_completion_status", "complete", "mcss_r26ww17.4", collected_at),
        _record("mc_clk", "pard2d1uladda0", "mcss_part2_release_status", "released", "mcss_r26ww17.4", collected_at),
        _record("mc_clk", "pard2d1uladda0", "mcss_schema_validation_error_count", 0, "mcss_r26ww17.4", collected_at),
        _record("mc_clk", "pard2d1uladda0", "unresolved_clock_connection_count", 0, "mcss_r26ww17.4", collected_at),
        _record("mc_clk", "pard2d1uladda0", "invalid_clock_relationship_count", 0, "mcss_r26ww17.4", collected_at),
        _record("mc_clk", "pard2d1uladda0", "stamping_mismatch_count", 0, "mcss_r26ww17.4", collected_at),
        _record("mc_clk", "pard2d1uladda0", "mcss_consumer_runs_behind", 0, "mcss_r26ww17.4", collected_at),
        _record("uclk_io", "paracciommu", "mcss_part1_completion_status", "complete", "mcss_r26ww17.4", collected_at),
        _record("uclk_io", "paracciommu", "mcss_part1_release_status", "released", "mcss_r26ww17.4", collected_at),
        _record("uclk_io", "paracciommu", "mcss_part2_completion_status", "partial", "mcss_r26ww17.4", collected_at),
        _record("uclk_io", "paracciommu", "mcss_part2_release_status", "not_released", "mcss_r26ww17.4", collected_at),
        _record("uclk_io", "paracciommu", "mcss_schema_validation_error_count", 0, "mcss_r26ww17.4", collected_at),
        _record("uclk_io", "paracciommu", "unresolved_clock_connection_count", 2, "mcss_r26ww17.4", collected_at),
        _record("uclk_io", "paracciommu", "invalid_clock_relationship_count", 1, "mcss_r26ww17.4", collected_at),
        _record("uclk_io", "paracciommu", "stamping_mismatch_count", 1, "mcss_r26ww17.4", collected_at),
        _record("uclk_io", "paracciommu", "mcss_consumer_runs_behind", 2, "mcss_r26ww17.4", collected_at),
    ]


def _record(clock: str, partition: str, metric: str, value: Any, revision: str, collected_at: str) -> MetricRecord:
    clocks_file = _clocks_file_path(partition)
    return {
        "milestone": "0p5",
        "deliverable": "MCSS",
        "clock": clock,
        "partition": partition,
        "metric": metric,
        "value": value,
        "source": {
            "system": SOURCE_SYSTEM,
            "uri": clocks_file.as_posix(),
            "revision": revision,
            "run_id": "26ww17.5",
            "collected_at": collected_at,
        },
    }


def _release_record(
    clock: str | None,
    partition: str,
    metric: str,
    value: Any,
    revision: str,
    collected_at: str,
    clocks_file: Path,
) -> MetricRecord:
    return {
        "milestone": "0p5",
        "deliverable": "MCSS",
        "clock": clock,
        "partition": partition,
        "metric": metric,
        "value": value,
        "source": {
            "system": SOURCE_SYSTEM,
            "uri": clocks_file.as_posix(),
            "revision": revision,
            "run_id": _run_id_from_clocks_file(clocks_file),
            "collected_at": collected_at,
        },
    }


def _clocks_file_path(partition: str) -> Path:
    clocks_file_template = os.environ.get(CLOCKS_FILE_TEMPLATE_ENV_VAR)
    if clocks_file_template:
        return Path(clocks_file_template.format(partition=partition))
    release_template = os.environ.get(RELEASE_TEMPLATE_ENV_VAR, DEFAULT_RELEASE_TEMPLATE).rstrip("/")
    return Path(f"{release_template}/{{partition}}_clocks.tcl".format(partition=partition))


def _release_revision(clocks_file: Path) -> str:
    if not clocks_file.exists():
        return "missing_clocks_file"
    try:
        return clocks_file.resolve().as_posix()
    except OSError:
        return clocks_file.as_posix()


def _run_id_from_clocks_file(clocks_file: Path) -> str:
    parts = clocks_file.parts
    if "runs" in parts:
        runs_index = parts.index("runs")
        if len(parts) > runs_index + 2:
            return parts[runs_index + 2]
    return clocks_file.parent.name


def _strip_tcl_comments(content: str) -> str:
    lines = []
    for line in content.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        lines.append(line)
    return "\n".join(lines)


def _join_tcl_continuations(content: str) -> str:
    return re.sub(r"\\\s*\n\s*", " ", content)


def _clean_tcl_token(token: str) -> str:
    return token.strip().strip("{}\"'")


def _stamp_source_defaults(records: list[MetricRecord]) -> list[MetricRecord]:
    for record in records:
        record.setdefault("deliverable", "MCSS")
        record.setdefault("milestone", "0p5")
        record.setdefault("source", {})
        record["source"].setdefault("system", SOURCE_SYSTEM)
        if record.get("partition"):
            record["source"].setdefault(
                "uri",
                _clocks_file_path(record["partition"]).as_posix(),
            )
    return records
