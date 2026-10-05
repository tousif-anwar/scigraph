"""Deterministic micro-batch simulation over Gold publication records."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from scigraph.preprocessing.pipeline import _spark_imports, create_spark_session, preflight_environment
from scigraph.utils.config import load_config, resolve_project_path


def batch_id_for_position(position: int, batch_size: int) -> int:
    """Return zero-based batch id for a one-based stream position."""
    if position <= 0:
        raise ValueError("position must be one-based and positive")
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    return (position - 1) // batch_size


def alert_triggered(rate: float, threshold: float) -> bool:
    """Return whether an observed rate crosses an alert threshold."""
    return rate > threshold


def _path(config: dict[str, Any], key: str) -> str:
    return str(resolve_project_path(config, config["paths"][key]))


def assign_micro_batches(publications, batch_size: int):
    """Assign deterministic micro-batch ids to publication records."""
    _, F, _ = _spark_imports()
    from pyspark.sql import Window

    window = Window.orderBy("publication_year", "paper_id")
    return (
        publications.withColumn("stream_position", F.row_number().over(window))
        .withColumn("batch_id", ((F.col("stream_position") - F.lit(1)) / F.lit(batch_size)).cast("int"))
        .withColumn("simulated_event_time", F.to_timestamp(F.concat_ws("-", F.col("publication_year"), F.lit("01"), F.lit("01"))))
    )


def compute_batch_metrics(batched_publications):
    """Compute per-batch monitoring metrics."""
    _, F, _ = _spark_imports()
    return (
        batched_publications.groupBy("batch_id")
        .agg(
            F.min("stream_position").alias("first_stream_position"),
            F.max("stream_position").alias("last_stream_position"),
            F.countDistinct("paper_id").alias("record_count"),
            F.min("publication_year").alias("min_publication_year"),
            F.max("publication_year").alias("max_publication_year"),
            F.sum(F.when(F.col("title").isNull() | (F.trim(F.col("title")) == ""), F.lit(1)).otherwise(F.lit(0))).alias(
                "missing_title_count"
            ),
            F.sum(F.when(F.col("author_count") <= 0, F.lit(1)).otherwise(F.lit(0))).alias(
                "missing_author_count"
            ),
            F.avg("author_count").alias("avg_author_count"),
            F.avg("reference_count").alias("avg_reference_count"),
            F.avg("cited_by_count").alias("avg_cited_by_count"),
        )
        .withColumn("missing_title_rate", F.col("missing_title_count") / F.col("record_count"))
        .withColumn("missing_author_rate", F.col("missing_author_count") / F.col("record_count"))
        .orderBy("batch_id")
    )


def build_alerts(batch_metrics, missing_title_threshold: float, missing_author_threshold: float):
    """Create monitoring alerts from batch metrics."""
    _, F, _ = _spark_imports()
    title_alerts = batch_metrics.where(F.col("missing_title_rate") > F.lit(missing_title_threshold)).select(
        "batch_id",
        F.lit("missing_title_rate").alias("alert_type"),
        F.col("missing_title_rate").alias("observed_value"),
        F.lit(missing_title_threshold).alias("threshold"),
        F.lit("critical").alias("severity"),
    )
    author_alerts = batch_metrics.where(F.col("missing_author_rate") > F.lit(missing_author_threshold)).select(
        "batch_id",
        F.lit("missing_author_rate").alias("alert_type"),
        F.col("missing_author_rate").alias("observed_value"),
        F.lit(missing_author_threshold).alias("threshold"),
        F.lit("warning").alias("severity"),
    )
    return title_alerts.unionByName(author_alerts).orderBy("batch_id", "alert_type")


def write_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    """Write streaming simulation JSON and Markdown reports."""
    json_path = resolve_project_path(config, config["paths"]["streaming_report_json"])
    markdown_path = resolve_project_path(config, config["paths"]["streaming_report_md"])
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# Streaming Simulation",
        "",
        f"Generated on {date.today().isoformat()}.",
        "",
        "## Summary",
        "",
        f"- Status: {payload.get('status')}",
        f"- Batch size: {payload.get('batch_size')}",
        f"- Batch count: {payload.get('batch_count')}",
        f"- Records processed: {payload.get('records_processed')}",
        f"- Alert count: {payload.get('alert_count')}",
        f"- Missing-title alert threshold: {payload.get('missing_title_threshold')}",
        f"- Missing-author alert threshold: {payload.get('missing_author_threshold')}",
        "",
        "## Batch Metrics",
        "",
        "| batch | records | year range | missing titles | missing authors | avg references | avg citations |",
        "| ---: | ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in payload.get("batch_metrics", []):
        lines.append(
            f"| {row['batch_id']} | {row['record_count']} | {row['min_publication_year']}-{row['max_publication_year']} | {row['missing_title_count']} | {row['missing_author_count']} | {row.get('avg_reference_count', 0):.4f} | {row.get('avg_cited_by_count', 0):.4f} |"
        )
    lines.extend(
        [
            "",
            "## Alerts",
            "",
            "| batch | type | observed | threshold | severity |",
            "| ---: | --- | ---: | ---: | --- |",
        ]
    )
    alerts = payload.get("alerts", [])
    if alerts:
        for row in alerts:
            lines.append(
                f"| {row['batch_id']} | {row['alert_type']} | {row['observed_value']:.4f} | {row['threshold']:.4f} | {row['severity']} |"
            )
    else:
        lines.append("|  | none |  |  |  |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This milestone simulates streaming by replaying the fixed Gold publication table in deterministic micro-batches. It validates batch-level monitoring logic without depending on a long-running external message broker or live API stream.",
        ]
    )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_streaming_simulation(config: dict[str, Any]) -> dict[str, Any]:
    """Run deterministic micro-batch monitoring over Gold publications."""
    preflight = preflight_environment(config)
    if not preflight["ok"]:
        payload = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "blocked",
            "preflight": preflight,
        }
        write_report(config, payload)
        return payload

    spark = create_spark_session(config)
    try:
        streaming_config = config["spark"].get("streaming", {})
        batch_size = int(streaming_config.get("batch_size", 100))
        missing_title_threshold = float(streaming_config.get("alert_missing_title_rate", 0.0))
        missing_author_threshold = float(streaming_config.get("alert_missing_author_rate", 0.05))

        publications = spark.read.parquet(_path(config, "gold_publications"))
        batched = assign_micro_batches(publications, batch_size).cache()
        batch_metrics = compute_batch_metrics(batched).cache()
        batch_metrics.write.mode("overwrite").parquet(_path(config, "streaming_batch_metrics"))

        alerts = build_alerts(batch_metrics, missing_title_threshold, missing_author_threshold).cache()
        alerts.write.mode("overwrite").parquet(_path(config, "streaming_alerts"))

        batch_rows = [row.asDict() for row in batch_metrics.collect()]
        alert_rows = [row.asDict() for row in alerts.collect()]
        payload = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "success",
            "preflight": preflight,
            "batch_size": batch_size,
            "batch_count": len(batch_rows),
            "records_processed": sum(row["record_count"] for row in batch_rows),
            "alert_count": len(alert_rows),
            "missing_title_threshold": missing_title_threshold,
            "missing_author_threshold": missing_author_threshold,
            "batch_metrics": batch_rows,
            "alerts": alert_rows,
            "outputs": {
                key: str(resolve_project_path(config, value))
                for key, value in config["paths"].items()
                if key.startswith("streaming_")
            },
        }
        write_report(config, payload)
        return payload
    finally:
        spark.stop()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/dev.yaml")
    args = parser.parse_args()
    config = load_config(Path(args.config))
    payload = run_streaming_simulation(config)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "batch_size": payload.get("batch_size"),
                "batch_count": payload.get("batch_count"),
                "records_processed": payload.get("records_processed"),
                "alert_count": payload.get("alert_count"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
