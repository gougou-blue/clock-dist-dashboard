# Global Clock Dashboard Agent Notes

Use these notes when extending the Global Clock Distribution dashboard.

- Preserve the normalized metric-record contract between ingestion and core evaluation.
- Keep source-specific parsing inside `ingestion/` modules.
- Keep thresholds, categories, and 0p5 gate participation inside `core/metrics_definitions.py`.
- Do not add manual status-entry workflows for clock owners; derive readiness from source artifacts.
- Treat completion, release, consumption, freshness, and validation as separate states.
- Prefer static JSON output first; add a service only when live querying or access control requires it.
