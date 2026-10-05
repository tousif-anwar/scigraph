"""Author collaboration graph analysis."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from scigraph.preprocessing.pipeline import _spark_imports, create_spark_session, preflight_environment
from scigraph.utils.config import load_config, resolve_project_path


def ordered_author_pair(left_author_id: str, right_author_id: str) -> tuple[str, str]:
    """Return a deterministic undirected author-pair ordering."""
    if left_author_id == right_author_id:
        raise ValueError("author pair requires two distinct authors")
    return tuple(sorted((left_author_id, right_author_id)))


def collaboration_density(edge_count: int, author_count: int) -> float:
    """Return observed undirected edge density for an author graph."""
    if author_count < 2:
        return 0.0
    possible_edges = author_count * (author_count - 1) / 2
    return edge_count / possible_edges


def _path(config: dict[str, Any], key: str) -> str:
    return str(resolve_project_path(config, config["paths"][key]))


def build_collaboration_edges(author_publications):
    """Build weighted undirected coauthor edges from author-publication rows."""
    _, F, _ = _spark_imports()
    left = author_publications.alias("left")
    right = author_publications.alias("right")
    pairs = (
        left.join(right, on="paper_id")
        .where(F.col("left.author_id") < F.col("right.author_id"))
        .select(
            F.col("paper_id"),
            F.col("left.author_id").alias("author_id_a"),
            F.col("left.author_name").alias("author_name_a"),
            F.col("right.author_id").alias("author_id_b"),
            F.col("right.author_name").alias("author_name_b"),
        )
    )
    return (
        pairs.groupBy("author_id_a", "author_name_a", "author_id_b", "author_name_b")
        .agg(
            F.countDistinct("paper_id").alias("shared_publication_count"),
            F.collect_set("paper_id").alias("shared_publication_ids"),
        )
        .orderBy(F.desc("shared_publication_count"), "author_id_a", "author_id_b")
    )


def compute_author_metrics(author_publications, collaboration_edges):
    """Compute publication and collaboration metrics for each author."""
    _, F, _ = _spark_imports()
    paper_author_counts = author_publications.groupBy("paper_id").agg(
        F.countDistinct("author_id").alias("paper_author_count")
    )
    author_publication_metrics = (
        author_publications.join(paper_author_counts, on="paper_id", how="left")
        .groupBy("author_id", "author_name")
        .agg(
            F.countDistinct("paper_id").alias("publication_count"),
            F.sum(F.when(F.col("paper_author_count") == 1, F.lit(1)).otherwise(F.lit(0))).alias(
                "solo_publication_count"
            ),
            F.avg("author_position").alias("avg_author_position"),
        )
    )
    author_edge_rows = collaboration_edges.select(
        F.col("author_id_a").alias("author_id"),
        F.col("author_id_b").alias("collaborator_id"),
        F.col("shared_publication_count"),
    ).unionByName(
        collaboration_edges.select(
            F.col("author_id_b").alias("author_id"),
            F.col("author_id_a").alias("collaborator_id"),
            F.col("shared_publication_count"),
        )
    )
    collaboration_metrics = author_edge_rows.groupBy("author_id").agg(
        F.countDistinct("collaborator_id").alias("collaborator_count"),
        F.sum("shared_publication_count").alias("weighted_collaboration_count"),
        F.max("shared_publication_count").alias("max_shared_publications_with_one_collaborator"),
    )
    return (
        author_publication_metrics.join(collaboration_metrics, on="author_id", how="left")
        .fillna(
            0,
            subset=[
                "collaborator_count",
                "weighted_collaboration_count",
                "max_shared_publications_with_one_collaborator",
            ],
        )
        .withColumn(
            "collaborations_per_publication",
            F.col("weighted_collaboration_count") / F.col("publication_count"),
        )
        .orderBy(F.desc("collaborator_count"), F.desc("publication_count"), "author_id")
    )


def write_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    """Write author collaboration JSON and Markdown reports."""
    json_path = resolve_project_path(config, config["paths"]["author_collaboration_report_json"])
    markdown_path = resolve_project_path(config, config["paths"]["author_collaboration_report_md"])
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# Author Collaboration Graph",
        "",
        f"Generated on {date.today().isoformat()}.",
        "",
        "## Summary",
        "",
        f"- Authors: {payload.get('author_count')}",
        f"- Author-publication rows: {payload.get('author_publication_count')}",
        f"- Multi-author publications: {payload.get('multi_author_publication_count')}",
        f"- Solo-author publications: {payload.get('solo_author_publication_count')}",
        f"- Collaboration edges: {payload.get('collaboration_edge_count')}",
        f"- Graph density: {payload.get('collaboration_density'):.8f}",
        "",
        "## Top Authors By Collaborator Count",
        "",
        "| rank | author | publications | collaborators | weighted collaborations | solo publications |",
        "| ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    for index, row in enumerate(payload.get("top_authors_by_collaborators", []), start=1):
        author_name = str(row.get("author_name") or row["author_id"]).replace("|", "\\|")
        lines.append(
            f"| {index} | {author_name} | {row['publication_count']} | {row['collaborator_count']} | {row['weighted_collaboration_count']} | {row['solo_publication_count']} |"
        )
    lines.extend(
        [
            "",
            "## Strongest Collaboration Edges",
            "",
            "| rank | author A | author B | shared publications |",
            "| ---: | --- | --- | ---: |",
        ]
    )
    for index, row in enumerate(payload.get("strongest_collaboration_edges", []), start=1):
        author_a = str(row.get("author_name_a") or row["author_id_a"]).replace("|", "\\|")
        author_b = str(row.get("author_name_b") or row["author_id_b"]).replace("|", "\\|")
        lines.append(
            f"| {index} | {author_a} | {author_b} | {row['shared_publication_count']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This graph links authors who appear on the same sampled OpenAlex publication. Edge weight is the number of sampled publications shared by the same author pair. The current development sample is heterogeneous and mostly contains authors with only one sampled publication, so the graph describes observed sample collaboration rather than complete career-level collaboration networks.",
        ]
    )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_author_collaboration(config: dict[str, Any]) -> dict[str, Any]:
    """Run author collaboration graph analytics and write outputs."""
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
        graph_config = config["spark"].get("graph", {})
        top_n = int(graph_config.get("top_n", 25))

        author_publications = spark.read.parquet(_path(config, "gold_author_publications")).dropDuplicates(
            ["paper_id", "author_id"]
        )
        paper_author_counts = author_publications.groupBy("paper_id").agg(
            F.countDistinct("author_id").alias("author_count")
        )
        collaboration_edges = build_collaboration_edges(author_publications).cache()
        collaboration_edges.write.mode("overwrite").parquet(_path(config, "author_collaboration_edges"))

        author_metrics = compute_author_metrics(author_publications, collaboration_edges).cache()
        author_metrics.write.mode("overwrite").parquet(_path(config, "author_collaboration_metrics"))

        author_count = author_publications.select("author_id").distinct().count()
        author_publication_count = author_publications.count()
        publication_count = author_publications.select("paper_id").distinct().count()
        multi_author_publication_count = paper_author_counts.where("author_count > 1").count()
        solo_author_publication_count = paper_author_counts.where("author_count = 1").count()
        collaboration_edge_count = collaboration_edges.count()

        top_authors = [
            row.asDict()
            for row in author_metrics.orderBy(
                F.desc("collaborator_count"), F.desc("weighted_collaboration_count"), F.desc("publication_count")
            )
            .limit(top_n)
            .collect()
        ]
        strongest_edges = [
            row.asDict()
            for row in collaboration_edges.orderBy(
                F.desc("shared_publication_count"), "author_id_a", "author_id_b"
            )
            .limit(top_n)
            .collect()
        ]

        payload = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "success",
            "preflight": preflight,
            "author_count": author_count,
            "author_publication_count": author_publication_count,
            "publication_count": publication_count,
            "multi_author_publication_count": multi_author_publication_count,
            "solo_author_publication_count": solo_author_publication_count,
            "collaboration_edge_count": collaboration_edge_count,
            "collaboration_density": collaboration_density(collaboration_edge_count, author_count),
            "top_authors_by_collaborators": top_authors,
            "strongest_collaboration_edges": strongest_edges,
            "outputs": {
                key: str(resolve_project_path(config, value))
                for key, value in config["paths"].items()
                if key.startswith("author_collaboration_")
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
    payload = run_author_collaboration(config)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "author_count": payload.get("author_count"),
                "collaboration_edge_count": payload.get("collaboration_edge_count"),
                "multi_author_publication_count": payload.get("multi_author_publication_count"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
