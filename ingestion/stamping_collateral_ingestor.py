"""MCSS release collateral ingestion for archive-backed partition metrics."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ingestion import MetricRecord, load_records_from_json

SOURCE_SYSTEM = "mcss_stamping"
DEFAULT_ENV_VAR = "MCSS_METRICS_JSON"
DEFAULT_PROJ_ARCHIVE = "/nfs/site/disks/nwp_arc_proj_archive/"
DEFAULT_RELEASE_TEMPLATE = "$PROJ_ARCHIVE/arc/{partition}/clock_collateral/NIOA0_0P5_PRD"
RELEASE_TEMPLATE_ENV_VAR = "MCSS_RELEASE_TEMPLATE"
CLOCKS_FILE_TEMPLATE_ENV_VAR = "MCSS_CLOCKS_FILE_TEMPLATE"
CREATE_CLOCK_NAME_PATTERN = re.compile(r"\bcreate_clock\b(?P<body>[^\n;]*)", re.IGNORECASE)
NAME_OPTION_PATTERN = re.compile(r"""(?:^|\s)-name\s+(?P<name>\{[^}]+\}|"[^"]+"|'[^']+'|\S+)""")


@dataclass(frozen=True)
class CollateralSpec:
    key: str
    metric: str
    patterns: tuple[str, ...]


EXPECTED_COLLATERAL: tuple[CollateralSpec, ...] = (
    CollateralSpec(
        key="clock_definition",
        metric="mcss_clock_definition_status",
        patterns=("{partition}_clocks.tcl", "*clock_definition*.tcl", "*clock_def*.tcl", "*clocks*.tcl"),
    ),
    CollateralSpec(
        key="uncertainty",
        metric="mcss_uncertainty_status",
        patterns=("{partition}_uncertainty*.tcl", "*uncertainty*.tcl"),
    ),
    CollateralSpec(
        key="latencies",
        metric="mcss_latencies_status",
        patterns=("{partition}_latenc*.tcl", "*latenc*.tcl"),
    ),
    CollateralSpec(
        key="stampings",
        metric="mcss_stampings_status",
        patterns=("pdop_stamping.tcl", "{partition}_stamp*.tcl", "*stamp*.tcl"),
    ),
    CollateralSpec(
        key="exceptions",
        metric="mcss_exceptions_status",
        patterns=("{partition}_exception*.tcl", "{partition}_exceptions*.tcl", "*exception*.tcl"),
    ),
)


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
    """Scan per-partition MCSS release folders for required collateral coverage."""

    _validate_release_scan_root()
    collected_at = datetime.now(timezone.utc).isoformat()
    records: list[MetricRecord] = []
    for partition in partitions:
        partition_name = str(partition["partition"])
        release_dir = _release_dir_path(partition_name)
        collateral = _scan_expected_collateral(partition_name, release_dir)
        revision = _release_revision(release_dir)
        release_value = "released" if all(item["available"] for item in collateral.values()) else "not_released"

        records.append(
            _release_record(
                None,
                partition_name,
                "mcss_release_status",
                release_value,
                revision,
                collected_at,
                release_dir,
                _missing_collateral(collateral),
            )
        )
        for spec in EXPECTED_COLLATERAL:
            state = collateral[spec.key]
            records.append(
                _release_record(
                    None,
                    partition_name,
                    spec.metric,
                    "available" if state["available"] else "missing",
                    revision,
                    collected_at,
                    state["path"] or release_dir,
                    _missing_patterns(state),
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
        _partition_record("pard2d1uladda0", "mcss_release_status", "released", "mcss_r26ww17.4", collected_at),
        _partition_record("pard2d1uladda0", "mcss_clock_definition_status", "available", "mcss_r26ww17.4", collected_at),
        _partition_record("pard2d1uladda0", "mcss_uncertainty_status", "available", "mcss_r26ww17.4", collected_at),
        _partition_record("pard2d1uladda0", "mcss_latencies_status", "available", "mcss_r26ww17.4", collected_at),
        _partition_record("pard2d1uladda0", "mcss_stampings_status", "available", "mcss_r26ww17.4", collected_at),
        _partition_record("pard2d1uladda0", "mcss_exceptions_status", "available", "mcss_r26ww17.4", collected_at),
        _partition_record("paracciommu", "mcss_release_status", "not_released", "mcss_r26ww17.4", collected_at),
        _partition_record("paracciommu", "mcss_clock_definition_status", "available", "mcss_r26ww17.4", collected_at),
        _partition_record("paracciommu", "mcss_uncertainty_status", "available", "mcss_r26ww17.4", collected_at),
        _partition_record("paracciommu", "mcss_latencies_status", "missing", "mcss_r26ww17.4", collected_at),
        _partition_record("paracciommu", "mcss_stampings_status", "available", "mcss_r26ww17.4", collected_at),
        _partition_record("paracciommu", "mcss_exceptions_status", "missing", "mcss_r26ww17.4", collected_at),
    ]


def _partition_record(partition: str, metric: str, value: Any, revision: str, collected_at: str) -> MetricRecord:
    release_dir = _release_dir_path(partition)
    return {
        "milestone": "0p5",
        "deliverable": "MCSS",
        "clock": None,
        "partition": partition,
        "metric": metric,
        "value": value,
        "source": {
            "system": SOURCE_SYSTEM,
            "uri": release_dir.as_posix(),
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
    source_path: Path,
    details: dict[str, Any] | None = None,
) -> MetricRecord:
    source = {
        "system": SOURCE_SYSTEM,
        "uri": source_path.as_posix(),
        "revision": revision,
        "run_id": _run_id_from_release_path(source_path),
        "collected_at": collected_at,
    }
    if details:
        source.update(details)
    return {
        "milestone": "0p5",
        "deliverable": "MCSS",
        "clock": clock,
        "partition": partition,
        "metric": metric,
        "value": value,
        "source": source,
    }


def _release_dir_path(partition: str) -> Path:
    release_template = os.environ.get(RELEASE_TEMPLATE_ENV_VAR, DEFAULT_RELEASE_TEMPLATE).rstrip("/")
    expanded_template = expand_release_template(release_template)
    return Path(expanded_template.format(partition=partition))


def expand_release_template(release_template: str) -> str:
    archive_root = os.environ.get("PROJ_ARCHIVE", DEFAULT_PROJ_ARCHIVE).rstrip("/")
    return os.path.expandvars(
        release_template
        .replace("${PROJ_ARCHIVE}", archive_root)
        .replace("$PROJ_ARCHIVE", archive_root)
        .replace("%PROJ_ARCHIVE%", archive_root)
    )


def _validate_release_scan_root() -> None:
    release_template = os.environ.get(RELEASE_TEMPLATE_ENV_VAR, DEFAULT_RELEASE_TEMPLATE)
    if "PROJ_ARCHIVE" not in release_template:
        return

    archive_root = Path(os.environ.get("PROJ_ARCHIVE", DEFAULT_PROJ_ARCHIVE))
    if archive_root.exists():
        return

    raise RuntimeError(
        "MCSS archive root is not available: "
        f"{archive_root.as_posix()}. Run the release scan on Linux with the archive mounted, "
        "or provide pre-scanned MCSS records with --mcss-source."
    )


def _clocks_file_path(partition: str) -> Path:
    clocks_file_template = os.environ.get(CLOCKS_FILE_TEMPLATE_ENV_VAR)
    if clocks_file_template:
        return Path(clocks_file_template.format(partition=partition))
    return _release_dir_path(partition) / f"{partition}_clocks.tcl"


def _release_revision(release_path: Path) -> str:
    if not release_path.exists():
        return "missing_release_path"
    try:
        return release_path.resolve().as_posix()
    except OSError:
        return release_path.as_posix()


def _run_id_from_release_path(release_path: Path) -> str:
    parts = release_path.parts
    if "runs" in parts:
        runs_index = parts.index("runs")
        if len(parts) > runs_index + 2:
            return parts[runs_index + 2]
    return release_path.parent.name


def _scan_expected_collateral(partition: str, release_dir: Path) -> dict[str, dict[str, Any]]:
    return {
        spec.key: _scan_collateral_spec(partition, release_dir, spec)
        for spec in EXPECTED_COLLATERAL
    }


def _scan_collateral_spec(partition: str, release_dir: Path, spec: CollateralSpec) -> dict[str, Any]:
    patterns = [pattern.format(partition=partition) for pattern in spec.patterns]
    if spec.key == "clock_definition" and os.environ.get(CLOCKS_FILE_TEMPLATE_ENV_VAR):
        candidate = _clocks_file_path(partition)
        return {
            "available": candidate.is_file(),
            "path": candidate if candidate.is_file() else None,
            "patterns": [candidate.as_posix()],
        }
    for pattern in patterns:
        matches = sorted(path for path in release_dir.glob(pattern) if path.is_file())
        if matches:
            return {"available": True, "path": matches[0], "patterns": patterns}
    return {"available": False, "path": None, "patterns": patterns}


def _missing_collateral(collateral: dict[str, dict[str, Any]]) -> dict[str, Any]:
    missing = [key for key, state in collateral.items() if not state["available"]]
    return {"missing_collateral": missing} if missing else {}


def _missing_patterns(state: dict[str, Any]) -> dict[str, Any]:
    if state["available"]:
        return {}
    return {"expected_patterns": state["patterns"]}


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
