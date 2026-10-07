"""Field/year-normalized citation metrics."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from scigraph.preprocessing.pipeline import _spark_imports, create_spark_session, preflight_environment
from scigraph.utils.config import load_config, resolve_project_path


def citation_age(publication_year: int, current_year: int) -> int:
    """Return citation age in years with a minimum age of one."""
    return max(1, current_year - publication_year + 1)


def z_score(value: float, mean: float, stddev: float) -> float:
    """Return a guarded z-score."""
    if stddev <= 0:
        return 0.0
    return (value - mean) / stddev


def _path(config: dict[str, Any], key: str) -> str:
    return str(resolve_project_path(config, config["paths"][key]))


def build_field_normalized_metrics(spark, config: dict[str, Any]):
    """Build publication-level citation metrics normalized by topic field and year."""
    _, F, Window = _spark_imports()
    from pyspark.sql import Window as SparkWindow

    publications = spark.read.parquet(_path(config, "gold_publications")).select(
        "paper_id", "title", "publication_year", "cited_by_count", "document_type", "language"
    )
    topics = spark.read.parquet(_path(config, "gold_topics")).select(
        "paper_id", "topic_field", "topic_name"
    )
    topic_window = SparkWindow.partitionBy("paper_id").orderBy(
        F.col("topic_field").asc_nulls_last(), F.col("topic_name").asc_nulls_last()
    )
    primary_topic = (
        topics.withColumn("topic_rank", F.row_number().over(topic_window))
        .where(F.col("topic_rank") == 1)
        .select(
            "paper_id",
            F.coalesce(F.col("topic_field"), F.lit("Unknown")).alias("primary_topic_field"),
            F.coalesce(F.col("topic_name"), F.lit("Unknown")).alias("primary_topic_name"),
        )
    )
    current_year = date.today().year
    enriched = (
        publications.join(primary_topic, on="paper_id", how="left")
        .fillna({"primary_topic_field": "Unknown", "primary_topic_name": "Unknown", "cited_by_count": 0})
        .withColumn(
            "citation_age_years",
            F.greatest(F.lit(1), F.lit(current_year) - F.col("publication_year") + F.lit(1)),
        )
        .withColumn("citations_per_year", F.col("cited_by_count") / F.col("citation_age_years"))
    )
    stats = enriched.groupBy("primary_topic_field", "publication_year").agg(
        F.count("*").alias("field_year_publication_count"),
        F.avg("cited_by_count").alias("field_year_mean_citations"),
        F.stddev_pop("cited_by_count").alias("field_year_stddev_citations"),
    )
    percentile_window = SparkWindow.partitionBy("primary_topic_field", "publication_year").orderBy(
        F.col("cited_by_count"), F.col("paper_id")
    )
    return (
        enriched.join(stats, on=["primary_topic_field", "publication_year"], how="left")
        .withColumn(
            "field_year_citation_zscore",
            F.when(F.col("field_year_stddev_citations") > 0, (F.col("cited_by_count") - F.col("field_year_mean_citations")) / F.col("field_year_stddev_citations")).otherwise(F.lit(0.0)),
        )
        .withColumn("field_year_citation_percentile", F.percent_rank().over(percentile_window))
        .orderBy(F.desc("field_year_citation_zscore"), F.desc("cited_by_count"), "paper_id")
    )


def write_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    """Write field-normalized citation JSON and Markdown reports."""
    json_path = resolve_project_path(config, config["paths"]["citation_field_report_json"])
    markdown_path = resolve_project_path(config, config["paths"]["citation_field_report_md"])
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# Field-Normalized Citations",
        "",
        f"Generated on {date.today().isoformat()}.",
        "",
        "## Summary",
        "",
        f"- Publication rows: {payload.get('publication_rows')}",
        f"- Topic fields: {payload.get('field_count')}",
        f"- Field/year groups: {payload.get('field_year_group_count')}",
        f"- Mean citations per year: {payload.get('mean_citations_per_year'):.4f}",
        "",
        "## Top Field-Normalized Papers",
        "",
        "| z-score | percentile | citations | field | year | title |",
        "| ---: | ---: | ---: | --- | ---: | --- |",
    ]
    for row in payload.get("top_publications", []):
        title = str(row.get("title") or row["paper_id"]).replace("|", "\\|")
        lines.append(
            f"| {row['field_year_citation_zscore']:.4f} | {row['field_year_citation_percentile']:.4f} | {row['cited_by_count']} | {row['primary_topic_field']} | {row['publication_year']} | {title} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Raw citations are hard to compare across fields and publication years. These features compare each paper against papers in the same OpenAlex topic field and publication year, adding citation-age, per-year citation rate, field/year z-score, and field/year percentile columns.",
        ]
    )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_field_normalized_citations(config: dict[str, Any]) -> dict[str, Any]:
    """Build and persist field-normalized citation metrics."""
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
        _, F, _ = _spark_imports()
        metrics = build_field_normalized_metrics(spark, config).cache()
        metrics.write.mode("overwrite").parquet(_path(config, "citation_field_normalized"))
        aggregate = metrics.agg(
            F.count("*").alias("publication_rows"),
            F.countDistinct("primary_topic_field").alias("field_count"),
            F.countDistinct("primary_topic_field", "publication_year").alias("field_year_group_count"),
            F.avg("citations_per_year").alias("mean_citations_per_year"),
        ).collect()[0]
        top_publications = [
            row.asDict()
            for row in metrics.orderBy(F.desc("field_year_citation_zscore"), F.desc("cited_by_count")).limit(10).collect()
        ]
        payload = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "success",
            "preflight": preflight,
            "publication_rows": int(aggregate["publication_rows"] or 0),
            "field_count": int(aggregate["field_count"] or 0),
            "field_year_group_count": int(aggregate["field_year_group_count"] or 0),
            "mean_citations_per_year": float(aggregate["mean_citations_per_year"] or 0.0),
            "top_publications": top_publications,
            "outputs": {
                "citation_field_normalized": _path(config, "citation_field_normalized"),
                "citation_field_report_json": _path(config, "citation_field_report_json"),
                "citation_field_report_md": _path(config, "citation_field_report_md"),
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
    payload = run_field_normalized_citations(load_config(Path(args.config)))
    print(
        json.dumps(
            {
                "status": payload["status"],
                "publication_rows": payload.get("publication_rows"),
                "field_count": payload.get("field_count"),
                "field_year_group_count": payload.get("field_year_group_count"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
