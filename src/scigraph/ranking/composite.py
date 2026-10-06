"""Transparent multi-signal publication ranking."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from scigraph.preprocessing.pipeline import _spark_imports, create_spark_session, preflight_environment
from scigraph.utils.config import load_config, resolve_project_path


DEFAULT_WEIGHTS = {
    "citation_count": 0.45,
    "pagerank": 0.15,
    "recency": 0.15,
    "reference_count": 0.10,
    "author_count": 0.05,
    "topic_count": 0.10,
}


def weighted_score(components: dict[str, float], weights: dict[str, float]) -> float:
    """Return a weighted score from normalized components."""
    return sum(components.get(name, 0.0) * weight for name, weight in weights.items())


def safe_minmax(value: float, minimum: float, maximum: float) -> float:
    """Return min-max normalized value, guarding constant ranges."""
    if maximum <= minimum:
        return 0.0
    return (value - minimum) / (maximum - minimum)


def _path(config: dict[str, Any], key: str) -> str:
    return str(resolve_project_path(config, config["paths"][key]))


def _weights(config: dict[str, Any]) -> dict[str, float]:
    configured = config["spark"].get("ranking", {}).get("weights", {})
    weights = {**DEFAULT_WEIGHTS, **configured}
    total = sum(weights.values())
    if total <= 0:
        raise ValueError("ranking weights must sum to a positive value")
    return {name: float(weight) / total for name, weight in weights.items()}


def add_minmax_component(df, source_col: str, output_col: str):
    """Add a min-max normalized component column."""
    _, F, _ = _spark_imports()
    stats = df.agg(F.min(source_col).alias("minimum"), F.max(source_col).alias("maximum")).collect()[0]
    minimum = float(stats["minimum"] or 0.0)
    maximum = float(stats["maximum"] or 0.0)
    if maximum <= minimum:
        return df.withColumn(output_col, F.lit(0.0))
    return df.withColumn(output_col, (F.col(source_col) - F.lit(minimum)) / F.lit(maximum - minimum))


def build_ranking_table(spark, config: dict[str, Any]):
    """Build composite publication ranking rows."""
    _, F, Window = _spark_imports()
    from pyspark.sql import Window as SparkWindow

    weights = _weights(config)
    publications = spark.read.parquet(_path(config, "gold_publications")).select(
        "paper_id",
        "title",
        "publication_year",
        "cited_by_count",
        "reference_count",
        "author_count",
        "topic_count",
        "concept_count",
    )
    pagerank = spark.read.parquet(_path(config, "citation_pagerank")).where("in_sample = true").select(
        "paper_id", "pagerank"
    )
    base = (
        publications.join(pagerank, on="paper_id", how="left")
        .fillna(0.0, subset=["pagerank"])
        .fillna(
            0,
            subset=[
                "cited_by_count",
                "reference_count",
                "author_count",
                "topic_count",
                "concept_count",
                "publication_year",
            ],
        )
    )
    scored = base
    for source_col, output_col in [
        ("cited_by_count", "citation_count_component"),
        ("pagerank", "pagerank_component"),
        ("publication_year", "recency_component"),
        ("reference_count", "reference_count_component"),
        ("author_count", "author_count_component"),
        ("topic_count", "topic_count_component"),
    ]:
        scored = add_minmax_component(scored, source_col, output_col)

    scored = scored.withColumn(
        "composite_score",
        F.lit(weights["citation_count"]) * F.col("citation_count_component")
        + F.lit(weights["pagerank"]) * F.col("pagerank_component")
        + F.lit(weights["recency"]) * F.col("recency_component")
        + F.lit(weights["reference_count"]) * F.col("reference_count_component")
        + F.lit(weights["author_count"]) * F.col("author_count_component")
        + F.lit(weights["topic_count"]) * F.col("topic_count_component"),
    )
    window = SparkWindow.orderBy(F.desc("composite_score"), F.desc("cited_by_count"), "paper_id")
    return scored.withColumn("rank", F.row_number().over(window)).orderBy("rank")


def write_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    """Write ranking JSON and Markdown reports."""
    json_path = resolve_project_path(config, config["paths"]["ranking_report_json"])
    markdown_path = resolve_project_path(config, config["paths"]["ranking_report_md"])
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# Composite Ranking",
        "",
        f"Generated on {date.today().isoformat()}.",
        "",
        "## Summary",
        "",
        f"- Ranked publications: {payload.get('ranked_publication_count')}",
        f"- Top N reported: {payload.get('top_n')}",
        f"- Mean composite score: {payload.get('mean_composite_score'):.6f}",
        "",
        "## Weights",
        "",
        "| component | weight |",
        "| --- | ---: |",
    ]
    for name, weight in payload.get("weights", {}).items():
        lines.append(f"| {name} | {weight:.4f} |")
    lines.extend(
        [
            "",
            "## Top Ranked Publications",
            "",
            "| rank | title | year | score | cited_by_count | references | authors | topics |",
            "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in payload.get("top_ranked_publications", []):
        title = str(row.get("title") or row["paper_id"]).replace("|", "\\|")
        lines.append(
            f"| {row['rank']} | {title} | {row['publication_year']} | {row['composite_score']:.6f} | {row['cited_by_count']} | {row['reference_count']} | {row['author_count']} | {row['topic_count']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This ranking is a transparent weighted baseline, not an authority score or measure of scientific quality. In the current sample, sampled-paper PageRank contributes little because Milestone 7 found no citation edges among sampled papers.",
        ]
    )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_composite_ranking(config: dict[str, Any]) -> dict[str, Any]:
    """Run composite ranking and write outputs."""
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
        top_n = int(config["spark"].get("ranking", {}).get("top_n", 25))
        weights = _weights(config)
        ranking = build_ranking_table(spark, config).cache()
        ranking.write.mode("overwrite").parquet(_path(config, "ranking_publications"))

        top_ranked = [row.asDict() for row in ranking.limit(top_n).collect()]
        payload = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "success",
            "preflight": preflight,
            "ranked_publication_count": ranking.count(),
            "top_n": top_n,
            "weights": weights,
            "mean_composite_score": ranking.agg(F.avg("composite_score")).collect()[0][0],
            "max_composite_score": ranking.agg(F.max("composite_score")).collect()[0][0],
            "top_ranked_publications": top_ranked,
            "outputs": {
                key: str(resolve_project_path(config, value))
                for key, value in config["paths"].items()
                if key.startswith("ranking_")
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
    payload = run_composite_ranking(config)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "ranked_publication_count": payload.get("ranked_publication_count"),
                "top_n": payload.get("top_n"),
                "mean_composite_score": payload.get("mean_composite_score"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
