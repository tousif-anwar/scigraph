"""File-arrival ingestion monitor for OpenAlex JSONL drops."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from scigraph.preprocessing.pipeline import (
    _spark_imports,
    create_spark_session,
    openalex_work_schema,
    preflight_environment,
)
from scigraph.utils.config import load_config, resolve_project_path


def missing_rate(missing_count: int, total_count: int) -> float:
    """Return missing-value rate with a zero-count guard."""
    if total_count <= 0:
        return 0.0
    return missing_count / total_count


def _path(config: dict[str, Any], key: str) -> Path:
    return resolve_project_path(config, config["paths"][key])


def write_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    """Write file-arrival monitor JSON and Markdown reports."""
    json_path = _path(config, "file_arrival_report_json")
    markdown_path = _path(config, "file_arrival_report_md")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# File-Arrival Streaming Monitor",
        "",
        f"Generated on {date.today().isoformat()}.",
        "",
        "## Summary",
        "",
        f"- Status: {payload.get('status')}",
        f"- Input directory: `{payload.get('input_dir')}`",
        f"- Files observed: {payload.get('file_count')}",
        f"- Records observed: {payload.get('record_count')}",
        f"- Missing title rate: {payload.get('missing_title_rate', 0.0):.4f}",
        f"- Missing author rate: {payload.get('missing_author_rate', 0.0):.4f}",
        "",
        "## File Metrics",
        "",
        "| file | records | missing titles | missing authors | year range |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for row in payload.get("files", []):
        lines.append(
            f"| `{row['file_name']}` | {row['record_count']} | {row['missing_title_count']} | {row['missing_author_count']} | {row.get('min_publication_year')} - {row.get('max_publication_year')} |"
        )
    lines.extend(
        [
            "",
            "## How To Use",
            "",
            "Drop OpenAlex JSONL files into the configured input directory and rerun this command to inspect newly arrived batches. The same schema can be used with Spark Structured Streaming by replacing the bounded read with `readStream.schema(openalex_work_schema()).json(input_dir)` and writing to the configured checkpoint directory.",
        ]
    )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_file_arrival_monitor(config: dict[str, Any]) -> dict[str, Any]:
    """Run a bounded Structured-Streaming-compatible file-arrival monitor."""
    input_dir = _path(config, "file_arrival_input_dir")
    checkpoint_dir = _path(config, "file_arrival_checkpoint_dir")
    input_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    preflight = preflight_environment(config)
    if not preflight["ok"]:
        payload = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "blocked",
            "preflight": preflight,
            "input_dir": str(input_dir),
            "checkpoint_dir": str(checkpoint_dir),
            "file_count": 0,
            "record_count": 0,
        }
        write_report(config, payload)
        return payload

    files = sorted(path for path in input_dir.glob("*.jsonl") if path.is_file())
    if not files:
        payload = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "empty",
            "preflight": preflight,
            "input_dir": str(input_dir),
            "checkpoint_dir": str(checkpoint_dir),
            "file_count": 0,
            "record_count": 0,
            "missing_title_rate": 0.0,
            "missing_author_rate": 0.0,
            "files": [],
        }
        write_report(config, payload)
        return payload

    spark = create_spark_session(config)
    try:
        _, F, _ = _spark_imports()
        frame = spark.read.schema(openalex_work_schema()).json(str(input_dir / "*.jsonl"))
        monitored = frame.withColumn("_input_file", F.input_file_name()).withColumn(
            "_missing_author", F.size(F.coalesce(F.col("authorships"), F.array())) == 0
        )
        file_metrics = (
            monitored.groupBy("_input_file")
            .agg(
                F.count("*").alias("record_count"),
                F.sum(F.when(F.col("title").isNull() | (F.trim(F.col("title")) == ""), 1).otherwise(0)).alias("missing_title_count"),
                F.sum(F.col("_missing_author").cast("int")).alias("missing_author_count"),
                F.min("publication_year").alias("min_publication_year"),
                F.max("publication_year").alias("max_publication_year"),
            )
            .orderBy("_input_file")
        )
        file_rows = []
        for row in file_metrics.collect():
            item = row.asDict()
            item["file_name"] = Path(item.pop("_input_file")).name
            file_rows.append(item)
        record_count = sum(int(row["record_count"]) for row in file_rows)
        missing_title_count = sum(int(row["missing_title_count"] or 0) for row in file_rows)
        missing_author_count = sum(int(row["missing_author_count"] or 0) for row in file_rows)
        payload = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "success",
            "preflight": preflight,
            "input_dir": str(input_dir),
            "checkpoint_dir": str(checkpoint_dir),
            "file_count": len(file_rows),
            "record_count": record_count,
            "missing_title_rate": missing_rate(missing_title_count, record_count),
            "missing_author_rate": missing_rate(missing_author_count, record_count),
            "files": file_rows,
        }
        write_report(config, payload)
        return payload
    finally:
        spark.stop()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/dev.yaml")
    args = parser.parse_args()
    payload = run_file_arrival_monitor(load_config(Path(args.config)))
    print(
        json.dumps(
            {
                "status": payload["status"],
                "file_count": payload.get("file_count"),
                "record_count": payload.get("record_count"),
                "missing_title_rate": payload.get("missing_title_rate"),
                "missing_author_rate": payload.get("missing_author_rate"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
