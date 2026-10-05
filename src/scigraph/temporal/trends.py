"""Temporal trend analysis for OpenAlex publication metadata."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from scigraph.preprocessing.pipeline import _spark_imports, create_spark_session, preflight_environment
from scigraph.utils.config import load_config, resolve_project_path


def year_over_year_growth(current_count: int, previous_count: int | None) -> float | None:
    """Return proportional year-over-year growth, or None when no baseline exists."""
    if previous_count is None or previous_count == 0:
        return None
    return (current_count - previous_count) / previous_count


def citation_rate(total_citations: int, publication_count: int) -> float:
    """Return citations per sampled publication for an aggregate group."""
    if publication_count <= 0:
        return 0.0
    return total_citations / publication_count


def _path(config: dict[str, Any], key: str) -> str:
    return str(resolve_project_path(config, config["paths"][key]))


def build_yearly_metrics(publications):
    """Build publication and citation aggregates by publication year."""
    _, F, _ = _spark_imports()
    from pyspark.sql import Window
    yearly = (
        publications.where("publication_year is not null")
        .groupBy("publication_year")
        .agg(
            F.countDistinct("paper_id").alias("publication_count"),
            F.sum(F.coalesce(F.col("cited_by_count"), F.lit(0))).alias("total_cited_by_count"),
            F.avg("cited_by_count").alias("avg_cited_by_count"),
            F.avg("reference_count").alias("avg_reference_count"),
            F.avg("author_count").alias("avg_author_count"),
            F.sum(F.when(F.col("abstract_available"), F.lit(1)).otherwise(F.lit(0))).alias(
                "abstract_available_count"
            ),
        )
        .withColumn(
            "citations_per_publication",
            F.col("total_cited_by_count") / F.col("publication_count"),
        )
    )
    window = Window.orderBy("publication_year")
    return (
        yearly.withColumn("previous_year_publication_count", F.lag("publication_count").over(window))
        .withColumn(
            "publication_count_yoy_growth",
            F.when(
                F.col("previous_year_publication_count").isNull()
                | (F.col("previous_year_publication_count") == 0),
                F.lit(None).cast("double"),
            ).otherwise(
                (F.col("publication_count") - F.col("previous_year_publication_count"))
                / F.col("previous_year_publication_count")
            ),
        )
        .orderBy("publication_year")
    )


def build_topic_trends(publications, topics):
    """Build topic-year publication counts and citation aggregates."""
    _, F, _ = _spark_imports()
    from pyspark.sql import Window
    topic_publications = topics.join(
        publications.select("paper_id", "publication_year", "cited_by_count"),
        on="paper_id",
        how="inner",
    ).where("publication_year is not null and topic_id is not null")
    topic_year = (
        topic_publications.groupBy(
            "publication_year", "topic_id", "topic_name", "topic_domain", "topic_field", "topic_subfield"
        )
        .agg(
            F.countDistinct("paper_id").alias("publication_count"),
            F.sum(F.coalesce(F.col("cited_by_count"), F.lit(0))).alias("total_cited_by_count"),
            F.avg("cited_by_count").alias("avg_cited_by_count"),
        )
        .withColumn(
            "citations_per_publication",
            F.col("total_cited_by_count") / F.col("publication_count"),
        )
    )
    window = Window.partitionBy("publication_year").orderBy(F.desc("publication_count"), "topic_name")
    return topic_year.withColumn("topic_rank_in_year", F.row_number().over(window)).orderBy(
        "publication_year", "topic_rank_in_year"
    )


def build_emerging_topics(topic_trends, latest_year: int):
    """Rank topics by latest-year growth within the sampled data."""
    _, F, _ = _spark_imports()
    previous_year = latest_year - 1
    by_topic = topic_trends.groupBy("topic_id", "topic_name", "topic_domain", "topic_field", "topic_subfield").agg(
        F.min("publication_year").alias("first_year"),
        F.max("publication_year").alias("last_year"),
        F.countDistinct("publication_year").alias("active_year_count"),
        F.sum("publication_count").alias("total_publication_count"),
        F.sum(F.when(F.col("publication_year") == latest_year, F.col("publication_count")).otherwise(F.lit(0))).alias(
            "latest_year_publication_count"
        ),
        F.sum(
            F.when(F.col("publication_year") == previous_year, F.col("publication_count")).otherwise(F.lit(0))
        ).alias("previous_year_publication_count"),
        F.sum(F.when(F.col("publication_year") == latest_year, F.col("total_cited_by_count")).otherwise(F.lit(0))).alias(
            "latest_year_cited_by_count"
        ),
    )
    return (
        by_topic.withColumn(
            "absolute_growth",
            F.col("latest_year_publication_count") - F.col("previous_year_publication_count"),
        )
        .withColumn(
            "growth_ratio",
            F.when(F.col("previous_year_publication_count") == 0, F.lit(None).cast("double")).otherwise(
                F.col("absolute_growth") / F.col("previous_year_publication_count")
            ),
        )
        .where("latest_year_publication_count > 0")
        .orderBy(F.desc("absolute_growth"), F.desc("latest_year_publication_count"), "topic_name")
    )


def write_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    """Write temporal JSON and Markdown reports."""
    json_path = resolve_project_path(config, config["paths"]["temporal_report_json"])
    markdown_path = resolve_project_path(config, config["paths"]["temporal_report_md"])
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# Temporal Analysis",
        "",
        f"Generated on {date.today().isoformat()}.",
        "",
        "## Summary",
        "",
        f"- Publication year range: {payload.get('min_publication_year')} - {payload.get('max_publication_year')}",
        f"- Publications with valid years: {payload.get('publications_with_year')}",
        f"- Year buckets: {payload.get('year_bucket_count')}",
        f"- Topic-year rows: {payload.get('topic_year_row_count')}",
        f"- Latest sampled year: {payload.get('latest_year')}",
        "",
        "## Yearly Metrics",
        "",
        "| year | publications | YoY growth | avg cited_by_count | citations/publication | avg authors |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload.get("yearly_metrics", []):
        growth = row.get("publication_count_yoy_growth")
        growth_text = "" if growth is None else f"{growth:.4f}"
        lines.append(
            f"| {row['publication_year']} | {row['publication_count']} | {growth_text} | {row.get('avg_cited_by_count', 0):.4f} | {row.get('citations_per_publication', 0):.4f} | {row.get('avg_author_count', 0):.4f} |"
        )
    lines.extend(
        [
            "",
            "## Top Latest-Year Topics",
            "",
            "| rank | topic | latest-year publications | previous-year publications | absolute growth | growth ratio |",
            "| ---: | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for index, row in enumerate(payload.get("top_emerging_topics", []), start=1):
        topic = str(row.get("topic_name") or row["topic_id"]).replace("|", "\\|")
        ratio = row.get("growth_ratio")
        ratio_text = "" if ratio is None else f"{ratio:.4f}"
        lines.append(
            f"| {index} | {topic} | {row['latest_year_publication_count']} | {row['previous_year_publication_count']} | {row['absolute_growth']} | {ratio_text} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Temporal aggregates describe the sampled records by publication year, not the full OpenAlex corpus. The latest-year topic list is a within-sample signal and can be unstable when the newest year is incomplete or sparsely represented.",
        ]
    )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_temporal_analysis(config: dict[str, Any]) -> dict[str, Any]:
    """Run temporal trend analysis and write outputs."""
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
        top_n = int(config["spark"].get("graph", {}).get("top_n", 25))

        publications = spark.read.parquet(_path(config, "gold_publications"))
        topics = spark.read.parquet(_path(config, "gold_topics"))

        yearly_metrics = build_yearly_metrics(publications).cache()
        yearly_metrics.write.mode("overwrite").parquet(_path(config, "temporal_yearly_metrics"))

        topic_trends = build_topic_trends(publications, topics).cache()
        topic_trends.write.mode("overwrite").parquet(_path(config, "temporal_topic_trends"))

        year_bounds = publications.agg(
            F.min("publication_year").alias("min_year"),
            F.max("publication_year").alias("max_year"),
            F.count(F.col("publication_year")).alias("publications_with_year"),
        ).collect()[0]
        latest_year = int(year_bounds["max_year"])

        emerging_topics = build_emerging_topics(topic_trends, latest_year).cache()
        emerging_topics.write.mode("overwrite").parquet(_path(config, "temporal_emerging_topics"))

        yearly_rows = [row.asDict() for row in yearly_metrics.collect()]
        top_emerging_topics = [row.asDict() for row in emerging_topics.limit(top_n).collect()]
        top_latest_year_topics = [
            row.asDict()
            for row in topic_trends.where(F.col("publication_year") == latest_year)
            .orderBy(F.desc("publication_count"), "topic_name")
            .limit(top_n)
            .collect()
        ]

        payload = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "success",
            "preflight": preflight,
            "min_publication_year": int(year_bounds["min_year"]),
            "max_publication_year": latest_year,
            "latest_year": latest_year,
            "publications_with_year": int(year_bounds["publications_with_year"]),
            "year_bucket_count": yearly_metrics.count(),
            "topic_year_row_count": topic_trends.count(),
            "emerging_topic_count": emerging_topics.count(),
            "yearly_metrics": yearly_rows,
            "top_emerging_topics": top_emerging_topics,
            "top_latest_year_topics": top_latest_year_topics,
            "outputs": {
                key: str(resolve_project_path(config, value))
                for key, value in config["paths"].items()
                if key.startswith("temporal_")
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
    payload = run_temporal_analysis(config)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "min_publication_year": payload.get("min_publication_year"),
                "max_publication_year": payload.get("max_publication_year"),
                "year_bucket_count": payload.get("year_bucket_count"),
                "topic_year_row_count": payload.get("topic_year_row_count"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
