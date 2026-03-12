#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class CostBreakdown:
    cloud_run: float = 0.0
    cloud_sql: float = 0.0
    gcs: float = 0.0
    artifact_registry: float = 0.0
    redis: float = 0.0
    other: float = 0.0

    def total(self) -> float:
        return self.cloud_run + self.cloud_sql + self.gcs + self.artifact_registry + self.redis + self.other


def _service_bucket(service_name: str) -> str:
    normalized = service_name.strip().lower()
    if "run" in normalized:
        return "cloud_run"
    if "sql" in normalized:
        return "cloud_sql"
    if "storage" in normalized:
        return "gcs"
    if "artifact registry" in normalized or "container registry" in normalized:
        return "artifact_registry"
    if "memorystore" in normalized or "redis" in normalized:
        return "redis"
    return "other"


def _parse_csv(csv_path: Path) -> CostBreakdown:
    result = CostBreakdown()
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            service_name = str(
                row.get("service.description")
                or row.get("service")
                or row.get("Service description")
                or ""
            )
            raw_cost = row.get("cost") or row.get("Cost") or "0"
            try:
                cost = float(raw_cost)
            except ValueError:
                continue

            bucket = _service_bucket(service_name)
            setattr(result, bucket, getattr(result, bucket) + cost)
    return result


def _estimate_defaults() -> CostBreakdown:
    # Conservative PoC estimate for one developer + near-zero player load.
    return CostBreakdown(
        cloud_run=8.0,
        cloud_sql=42.0,
        gcs=4.0,
        artifact_registry=2.0,
        redis=0.0,
        other=6.0,
    )


def _status(value: float, budget: float) -> str:
    if budget <= 0:
        return "n/a"
    ratio = value / budget
    if ratio >= 1.0:
        return "OVER"
    if ratio >= 0.8:
        return "WARN"
    return "OK"


def _write_report(
    *,
    output_path: Path,
    month: str,
    project_id: str,
    source: str,
    breakdown: CostBreakdown,
    budget_total: float,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = [
        ("Cloud Run", breakdown.cloud_run),
        ("Cloud SQL", breakdown.cloud_sql),
        ("GCS", breakdown.gcs),
        ("Artifact Registry", breakdown.artifact_registry),
        ("Redis/Memorystore", breakdown.redis),
        ("Other", breakdown.other),
    ]

    lines = [
        f"# Monthly Cost Report - {month}",
        "",
        f"- Project: `{project_id}`",
        f"- Source: `{source}`",
        f"- Generated at: `{datetime.now(UTC).isoformat()}`",
        f"- Budget guardrail: `${budget_total:.2f}`",
        "",
        "| Component | Cost (USD) | Status |",
        "| --- | ---: | --- |",
    ]
    for label, value in rows:
        lines.append(f"| {label} | ${value:.2f} | {_status(value, budget_total)} |")

    total = breakdown.total()
    lines.extend(
        [
            "",
            f"- Total estimated/observed monthly cost: `${total:.2f}`",
            f"- Guardrail status: `{_status(total, budget_total)}`",
            "",
            "## Notes",
            "- Redis is expected to remain `$0.00` unless `docs/REDIS_ADOPTION_GATE.md` conditions are met.",
            "- Keep release retention at latest 3 builds to control GCS growth.",
        ]
    )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate monthly PoC cost report markdown")
    parser.add_argument("--month", required=True, help="Month key in YYYY-MM format")
    parser.add_argument("--project-id", default="ambitions-of-peace", help="GCP project id label for report")
    parser.add_argument("--billing-csv", default="", help="Optional billing export CSV path")
    parser.add_argument(
        "--output",
        required=True,
        help="Output markdown path, e.g. docs/cost-reports/2026-03-estimate.md",
    )
    parser.add_argument("--budget-total", type=float, default=80.0, help="Monthly total budget guardrail")
    args = parser.parse_args()

    if args.billing_csv:
        csv_path = Path(args.billing_csv)
        breakdown = _parse_csv(csv_path)
        source = f"billing_csv:{csv_path}"
    else:
        breakdown = _estimate_defaults()
        source = "estimate_defaults"

    _write_report(
        output_path=Path(args.output),
        month=args.month,
        project_id=args.project_id,
        source=source,
        breakdown=breakdown,
        budget_total=float(args.budget_total),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
