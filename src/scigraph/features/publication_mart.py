"""Integrated publication-level feature mart."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from scigraph.preprocessing.pipeline import _spark_imports, create_spark_session, preflight_environment
from scigraph.utils.config import load_config, resolve_project_path


def completeness_rate(available_count: int, total_count: int) -> float:
    """Return feature availability rate."""
    if total_count <= 0:
        return 0.0
    return available_count / total_count


def safe_average(total: float, count: int) -> float:
    """Return average with a zero-count guard."""
    if count <= 0:
        return 0.0
    return total / count


def _path(config: dict[str, Any], key: str) -> str:
    return str(resolve_project_path(config, config["paths"][key]))


def build_publication_mart(spark, config: dict[str, Any]):
    """Join publication-level outputs from prior milestones into one table."""
    _, F, _ = _spark_imports()

    publications = spark.read.parquet(_path(config, "gold_publications")).select(
        "paper_id",
        "paper_openalex_id",
        "doi",
        "title",
        "publication_date",
        "publication_year",
        "document_type",
        "language",
        "cited_by_count",
        "reference_count",
        "author_count",
        "concept_count",
        "topic_count",
        "abstract_available",
        F.size("quality_flags").alias("quality_flag_count"),
    )
    text_features = (
        spark.read.parquet(_path(config, "text_documents"))
        .select(
            "paper_id",
            F.length(F.coalesce(F.col("document_text"), F.lit(""))).alias("document_char_count"),
            F.when(
                F.length(F.trim(F.coalesce(F.col("document_text"), F.lit("")))) == 0,
                F.lit(0),
            )
            .otherwise(F.size(F.split(F.trim(F.col("document_text")), r"\s+")))
            .alias("document_word_count"),
        )
        .dropDuplicates(["paper_id"])
    )
    clusters = spark.read.parquet(_path(config, "cluster_assignments")).select("paper_id", "cluster")
    citation_degrees = spark.read.parquet(_path(config, "citation_degrees")).select(
        "paper_id", "out_degree_full", "out_degree_in_sample", "in_degree_in_sample"
    )
    ml_features = spark.read.parquet(_path(config, "ml_citation_features")).select(
        "paper_id", F.col("label").alias("high_citation_label")
    )
    ml_predictions = spark.read.parquet(_path(config, "ml_citation_predictions")).select(
        "paper_id", F.col("prediction").alias("high_citation_prediction")
    )
    ranking = spark.read.parquet(_path(config, "ranking_publications")).select(
        "paper_id", "rank", "composite_score", "citation_count_component", "recency_component"
    )
    temporal = spark.read.parquet(_path(config, "temporal_yearly_metrics")).select(
        "publication_year",
        F.col("publication_count").alias("year_publication_count"),
        F.col("citations_per_publication").alias("year_citations_per_publication"),
        "publication_count_yoy_growth",
    )

    mart = (
        publications.join(text_features, on="paper_id", how="left")
        .join(clusters, on="paper_id", how="left")
        .join(citation_degrees, on="paper_id", how="left")
        .join(ml_features, on="paper_id", how="left")
        .join(ml_predictions, on="paper_id", how="left")
        .join(ranking, on="paper_id", how="left")
        .join(temporal, on="publication_year", how="left")
        .withColumn("has_text_document", F.col("document_char_count").isNotNull())
        .withColumn("has_cluster_assignment", F.col("cluster").isNotNull())
        .withColumn("has_ml_prediction", F.col("high_citation_prediction").isNotNull())
        .withColumn("has_composite_rank", F.col("rank").isNotNull())
        .fillna(
            0,
            subset=[
                "document_char_count",
                "document_word_count",
                "out_degree_full",
                "out_degree_in_sample",
                "in_degree_in_sample",
                "quality_flag_count",
            ],
        )
    )
    return mart


def write_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    """Write feature mart JSON and Markdown reports."""
    json_path = resolve_project_path(config, config["paths"]["feature_mart_report_json"])
    markdown_path = resolve_project_path(config, config["paths"]["feature_mart_report_md"])
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# Feature Mart",
        "",
        f"Generated on {date.today().isoformat()}.",
        "",
        "## Summary",
        "",
        f"- Publication rows: {payload.get('publication_rows')}",
        f"- Feature columns: {payload.get('feature_columns')}",
        f"- Text feature availability: {payload.get('text_feature_availability'):.4f}",
        f"- Cluster availability: {payload.get('cluster_availability'):.4f}",
        f"- ML prediction availability: {payload.get('ml_prediction_availability'):.4f}",
        f"- Composite rank availability: {payload.get('ranking_availability'):.4f}",
        f"- Average document word count: {payload.get('avg_document_word_count'):.4f}",
        "",
        "## Top Composite-Ranked Rows In Mart",
        "",
        "| rank | title | year | score | cluster | high-citation label | ML prediction |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload.get("top_ranked_rows", []):
        title = str(row.get("title") or row["paper_id"]).replace("|", "\\|")
        lines.append(
            f"| {row.get('rank')} | {title} | {row.get('publication_year')} | {row.get('composite_score', 0):.6f} | {row.get('cluster')} | {row.get('high_citation_label')} | {row.get('high_citation_prediction')} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The feature mart preserves one row per sampled publication and joins signals from prior milestones for downstream inspection. Some columns are intentionally sparse: text and clustering are English-filtered, and ML predictions exist only for the held-out test split.",
        ]
    )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_feature_mart(config: dict[str, Any]) -> dict[str, Any]:
    """Build integrated publication feature mart and report coverage."""
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
        mart = build_publication_mart(spark, config).cache()
        mart.write.mode("overwrite").parquet(_path(config, "feature_publication_mart"))

        publication_rows = mart.count()
        availability = mart.agg(
            F.sum(F.col("has_text_document").cast("int")).alias("text_rows"),
            F.sum(F.col("has_cluster_assignment").cast("int")).alias("cluster_rows"),
            F.sum(F.col("has_ml_prediction").cast("int")).alias("ml_prediction_rows"),
            F.sum(F.col("has_composite_rank").cast("int")).alias("ranking_rows"),
            F.avg("document_word_count").alias("avg_document_word_count"),
        ).collect()[0]
        top_ranked_rows = [
            row.asDict()
            for row in mart.where(F.col("rank").isNotNull()).orderBy("rank").limit(10).collect()
        ]
        payload = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "success",
            "preflight": preflight,
            "publication_rows": publication_rows,
            "feature_columns": len(mart.columns),
            "text_feature_rows": int(availability["text_rows"] or 0),
            "cluster_rows": int(availability["cluster_rows"] or 0),
            "ml_prediction_rows": int(availability["ml_prediction_rows"] or 0),
            "ranking_rows": int(availability["ranking_rows"] or 0),
            "text_feature_availability": completeness_rate(int(availability["text_rows"] or 0), publication_rows),
            "cluster_availability": completeness_rate(int(availability["cluster_rows"] or 0), publication_rows),
            "ml_prediction_availability": completeness_rate(
                int(availability["ml_prediction_rows"] or 0), publication_rows
            ),
            "ranking_availability": completeness_rate(int(availability["ranking_rows"] or 0), publication_rows),
            "avg_document_word_count": float(availability["avg_document_word_count"] or 0.0),
            "top_ranked_rows": top_ranked_rows,
            "outputs": {
                key: str(resolve_project_path(config, value))
                for key, value in config["paths"].items()
                if key.startswith("feature_")
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
    payload = run_feature_mart(config)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "publication_rows": payload.get("publication_rows"),
                "feature_columns": payload.get("feature_columns"),
                "text_feature_availability": payload.get("text_feature_availability"),
                "ranking_availability": payload.get("ranking_availability"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
