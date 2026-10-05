"""Measured Spark scalability benchmarks for the preprocessing pipeline."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from scigraph.preprocessing.pipeline import (
    build_gold,
    build_silver,
    configure_runtime_environment,
    create_spark_session,
    openalex_work_schema,
    preflight_environment,
)
from scigraph.utils.config import load_config, resolve_project_path


def _dir_size(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(file.stat().st_size for file in path.rglob("*") if file.is_file())


def _file_size(path: Path) -> int:
    return path.stat().st_size if path.exists() else 0


def _benchmark_config(config: dict[str, Any], run_dir: Path, scale: int) -> dict[str, Any]:
    bench_config = json.loads(json.dumps(config))
    scale_dir = run_dir / f"scale_{scale}"
    bench_config["paths"]["bronze_works"] = str(scale_dir / "bronze")
    bench_config["paths"]["silver_publications"] = str(scale_dir / "silver_publications")
    bench_config["paths"]["gold_publications"] = str(scale_dir / "gold_publications")
    bench_config["paths"]["gold_authors"] = str(scale_dir / "gold_authors")
    bench_config["paths"]["gold_author_publications"] = str(scale_dir / "gold_author_publications")
    bench_config["paths"]["gold_citation_edges"] = str(scale_dir / "gold_citation_edges")
    bench_config["paths"]["gold_topics"] = str(scale_dir / "gold_topics")
    return bench_config


def _make_bronze(raw_df, config: dict[str, Any], scale: int):
    _, F, _ = __import__("scigraph.preprocessing.pipeline", fromlist=["_spark_imports"])._spark_imports()
    return (
        raw_df.limit(scale)
        .withColumn("_bronze_ingested_at_utc", F.current_timestamp())
        .withColumn("_source_dataset", F.lit(config["dataset"]["name"]))
        .withColumn("_source_license", F.lit(config["dataset"]["license"]))
    )


def run_pipeline_scale_benchmark(spark, config: dict[str, Any], run_dir: Path) -> list[dict[str, Any]]:
    """Run measured end-to-end preprocessing benchmarks for configured record scales."""
    raw_path = resolve_project_path(config, config["paths"]["raw_sample_jsonl"])
    raw_df = spark.read.schema(openalex_work_schema()).json(str(raw_path))
    available_records = raw_df.count()
    input_size_bytes = _file_size(raw_path)

    rows: list[dict[str, Any]] = []
    for requested_scale in config["spark"].get("benchmark_scale_records", [available_records]):
        scale = min(int(requested_scale), available_records)
        bench_config = _benchmark_config(config, run_dir, scale)
        scale_dir = run_dir / f"scale_{scale}"
        if scale_dir.exists():
            shutil.rmtree(scale_dir)
        scale_dir.mkdir(parents=True, exist_ok=True)

        start = time.perf_counter()
        bronze_df = _make_bronze(raw_df, config, scale)
        bronze_partitions = bronze_df.rdd.getNumPartitions()
        bronze_path = Path(bench_config["paths"]["bronze_works"])
        bronze_df.write.mode("overwrite").parquet(str(bronze_path))
        bronze_count = bronze_df.count()

        silver_df = build_silver(bronze_df, bench_config)
        silver_count = silver_df.count()
        gold_outputs = build_gold(silver_df, bench_config)
        gold_counts = {name: df.count() for name, df in gold_outputs.items()}
        duration_seconds = round(time.perf_counter() - start, 4)

        output_size_bytes = sum(_dir_size(Path(path)) for key, path in bench_config["paths"].items() if key.startswith(("bronze_", "silver_", "gold_")))
        rows.append(
            {
                "experiment": "pipeline_scale",
                "requested_records": int(requested_scale),
                "records": scale,
                "available_records": available_records,
                "duration_seconds": duration_seconds,
                "records_per_second": round(scale / duration_seconds, 4) if duration_seconds else None,
                "input_size_bytes": input_size_bytes,
                "output_size_bytes": output_size_bytes,
                "bronze_partitions": bronze_partitions,
                "bronze_records": bronze_count,
                "silver_records": silver_count,
                "gold_publications": gold_counts["gold_publications"],
                "gold_authors": gold_counts["gold_authors"],
                "gold_author_publications": gold_counts["gold_author_publications"],
                "gold_citation_edges": gold_counts["gold_citation_edges"],
                "gold_topics": gold_counts["gold_topics"],
            }
        )
    return rows


def run_cache_benchmark(spark, config: dict[str, Any]) -> list[dict[str, Any]]:
    """Compare repeated uncached vs cached aggregation on the current raw sample."""
    raw_path = resolve_project_path(config, config["paths"]["raw_sample_jsonl"])
    raw_df = spark.read.schema(openalex_work_schema()).json(str(raw_path))
    scale = raw_df.count()
    _, F, _ = __import__("scigraph.preprocessing.pipeline", fromlist=["_spark_imports"])._spark_imports()
    aggregation = raw_df.groupBy("publication_year").agg(F.count("*").alias("documents"))

    start = time.perf_counter()
    aggregation.count()
    aggregation.count()
    uncached_seconds = round(time.perf_counter() - start, 4)

    cached = aggregation.cache()
    start = time.perf_counter()
    cached.count()
    cached.count()
    cached_seconds = round(time.perf_counter() - start, 4)
    cached.unpersist()

    return [
        {
            "experiment": "cache_repeated_aggregation",
            "technique": "uncached",
            "records": scale,
            "duration_seconds": uncached_seconds,
            "records_per_second": round(scale / uncached_seconds, 4) if uncached_seconds else None,
        },
        {
            "experiment": "cache_repeated_aggregation",
            "technique": "cached",
            "records": scale,
            "duration_seconds": cached_seconds,
            "records_per_second": round(scale / cached_seconds, 4) if cached_seconds else None,
        },
    ]


def write_results(config: dict[str, Any], payload: dict[str, Any]) -> None:
    json_path = resolve_project_path(config, config["paths"]["scalability_results_json"])
    csv_path = resolve_project_path(config, config["paths"]["scalability_results_csv"])
    report_path = resolve_project_path(config, config["paths"]["scalability_report_md"])
    json_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    pipeline_rows = payload["pipeline_scale_results"]
    if pipeline_rows:
        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(pipeline_rows[0].keys()))
            writer.writeheader()
            writer.writerows(pipeline_rows)

    lines = [
        "# Scalability Benchmarks",
        "",
        f"Generated on {date.today().isoformat()}.",
        "",
        "These are measured Spark results from the current development sample. They should not be generalized to the full OpenAlex corpus.",
        "",
        "## Pipeline Scale Results",
        "",
        "| records | seconds | records/sec | partitions | output bytes |",
        "| ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in pipeline_rows:
        lines.append(
            f"| {row['records']} | {row['duration_seconds']} | {row['records_per_second']} | {row['bronze_partitions']} | {row['output_size_bytes']} |"
        )
    lines.extend(["", "## Cache Experiment", "", "| technique | records | seconds | records/sec |", "| --- | ---: | ---: | ---: |"])
    for row in payload["cache_results"]:
        lines.append(
            f"| {row['technique']} | {row['records']} | {row['duration_seconds']} | {row['records_per_second']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The configured development benchmark uses small subsets of the currently acquired sample. Larger, course-relevant scale levels require acquiring larger samples after the Spark runtime is stable.",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_benchmarks(config: dict[str, Any]) -> dict[str, Any]:
    configure_runtime_environment(config)
    preflight = preflight_environment(config)
    if not preflight["ok"]:
        payload = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "blocked",
            "preflight": preflight,
            "pipeline_scale_results": [],
            "cache_results": [],
        }
        write_results(config, payload)
        return payload

    run_dir = resolve_project_path(
        config,
        Path(config["paths"]["scalability_runs_dir"]) / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
    )
    spark = create_spark_session(config)
    try:
        pipeline_results = run_pipeline_scale_benchmark(spark, config, run_dir)
        cache_results = run_cache_benchmark(spark, config)
        payload = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "success",
            "preflight": preflight,
            "run_dir": str(run_dir),
            "pipeline_scale_results": pipeline_results,
            "cache_results": cache_results,
        }
        write_results(config, payload)
        return payload
    finally:
        spark.stop()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/dev.yaml")
    args = parser.parse_args()
    config = load_config(Path(args.config))
    payload = run_benchmarks(config)
    print(json.dumps({"status": payload["status"], "pipeline_runs": len(payload["pipeline_scale_results"])}, indent=2))


if __name__ == "__main__":
    main()
