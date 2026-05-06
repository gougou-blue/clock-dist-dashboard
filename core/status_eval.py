"""Shared Red/Yellow/Green/Gray status evaluation helpers."""

from __future__ import annotations

from typing import Any

from core.metrics_definitions import MetricDefinition

GREEN = "Green"
YELLOW = "Yellow"
RED = "Red"
GRAY = "Gray"

_GREEN_STATUS_VALUES = {
    "available",
    "complete",
    "completed",
    "present",
    "released",
    "pass",
    "passed",
    "true",
    "yes",
    "green",
}
_YELLOW_STATUS_VALUES = {"in_progress", "in progress", "partial", "draft", "pending", "waived", "yellow"}
_RED_STATUS_VALUES = {
    "absent",
    "missing",
    "not_started",
    "not started",
    "not_released",
    "unavailable",
    "failed",
    "fail",
    "false",
    "no",
    "red",
}


def evaluate_status(metric: MetricDefinition, value: Any) -> str:
    """Evaluate a raw metric value against its metric definition."""

    if value is None:
        return GRAY

    if metric.status_mode == "percent_complete":
        return _evaluate_percent(metric, value)
    if metric.status_mode == "zero_count":
        return _evaluate_zero_count(metric, value)
    if metric.status_mode == "release_status":
        return _evaluate_release_status(value)
    if metric.status_mode == "freshness_lag":
        return _evaluate_freshness(metric, value)
    return GRAY


def _evaluate_percent(metric: MetricDefinition, value: Any) -> str:
    numeric_value = _as_float(value)
    if numeric_value is None:
        return GRAY

    target = _as_float(metric.target_value) or 100.0
    if numeric_value >= target:
        return GREEN
    if metric.yellow_min is not None and numeric_value >= metric.yellow_min:
        return YELLOW
    return RED


def _evaluate_zero_count(metric: MetricDefinition, value: Any) -> str:
    numeric_value = _as_float(value)
    if numeric_value is None:
        return GRAY

    target = _as_float(metric.target_value) or 0.0
    if numeric_value <= target:
        return GREEN
    if metric.yellow_max is not None and numeric_value <= metric.yellow_max:
        return YELLOW
    return RED


def _evaluate_release_status(value: Any) -> str:
    if isinstance(value, bool):
        return GREEN if value else RED

    normalized = str(value).strip().lower()
    if normalized in _GREEN_STATUS_VALUES:
        return GREEN
    if normalized in _YELLOW_STATUS_VALUES:
        return YELLOW
    if normalized in _RED_STATUS_VALUES:
        return RED
    return GRAY


def _evaluate_freshness(metric: MetricDefinition, value: Any) -> str:
    numeric_value = _as_float(value)
    if numeric_value is None:
        return GRAY

    target = _as_float(metric.target_value) or 0.0
    if numeric_value <= target:
        return GREEN
    if metric.yellow_max is not None and numeric_value <= metric.yellow_max:
        return YELLOW
    return RED


def combine_statuses(statuses: list[str]) -> str:
    """Combine many metric statuses into one conservative roll-up status."""

    if not statuses:
        return GRAY
    if RED in statuses:
        return RED
    if YELLOW in statuses:
        return YELLOW
    if GRAY in statuses:
        return GRAY
    return GREEN


def finish_state(status: str) -> str:
    """Map a status color to the dashboard finish-state language."""

    if status == GREEN:
        return "0p5 Ready"
    if status == YELLOW:
        return "At Risk"
    if status == RED:
        return "Blocked"
    return "No Data"


def _as_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
