"""Citation graph analysis and Spark PageRank."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from scigraph.preprocessing.pipeline import _spark_imports, create_spark_session, preflight_environment
from scigraph.utils.config import load_config, resolve_project_path


def pagerank_base_score(vertex_count: int, damping: float) -> float:
    """Return PageRank teleport/base score per vertex."""
    if vertex_count <= 0:
        raise ValueError("vertex_count must be positive")
    return (1.0 - damping) / vertex_count


def degree_ratio(pagerank: float, in_degree: int) -> float:
    """Simple helper for identifying high PageRank relative to observed in-degree."""
    return pagerank / (in_degree + 1)


def _path(config: dict[str, Any], key: str) -> str:
    return str(resolve_project_path(config, config["paths"][key]))


def compute_degrees(vertices, full_edges, induced_edges):
    """Compute in/out degree metrics for sampled publication vertices."""
    _, F, _ = _spark_imports()
    full_out = full_edges.groupBy("paper_id").agg(F.count("*").alias("out_degree_full"))
    induced_out = induced_edges.groupBy("paper_id").agg(F.count("*").alias("out_degree_in_sample"))
    induced_in = induced_edges.groupBy("referenced_paper_id").agg(F.count("*").alias("in_degree_in_sample"))
    return (
        vertices.select("paper_id", "title", "publication_year", "cited_by_count")
        .join(full_out, on="paper_id", how="left")
        .join(induced_out, on="paper_id", how="left")
        .join(induced_in.withColumnRenamed("referenced_paper_id", "paper_id"), on="paper_id", how="left")
        .fillna(0, subset=["out_degree_full", "out_degree_in_sample", "in_degree_in_sample"])
    )


def run_pagerank(vertices, edges, config: dict[str, Any]):
    """Run iterative PageRank on a directed citation graph."""
    _, F, _ = _spark_imports()
    graph_config = config["spark"].get("graph", {})
    damping = float(graph_config.get("pagerank_damping", 0.85))
    iterations = int(graph_config.get("pagerank_iterations", 10))
    vertex_count = vertices.count()
    base = pagerank_base_score(vertex_count, damping)

    ranks = vertices.select("paper_id").withColumn("pagerank", F.lit(1.0 / vertex_count))
    out_degree = edges.groupBy("paper_id").agg(F.count("*").alias("out_degree")).cache()
    out_degree.count()

    for _ in range(iterations):
        previous_ranks = ranks
        contributions = (
            edges.join(ranks, on="paper_id", how="inner")
            .join(out_degree, on="paper_id", how="inner")
            .select(
                F.col("referenced_paper_id").alias("paper_id"),
                (F.col("pagerank") / F.col("out_degree")).alias("contribution"),
            )
        )
        dangling_mass = (
            ranks.join(out_degree, on="paper_id", how="left")
            .where("out_degree is null")
            .agg(F.sum("pagerank").alias("dangling_mass"))
            .collect()[0]["dangling_mass"]
            or 0.0
        )
        ranks = (
            vertices.select("paper_id")
            .join(contributions.groupBy("paper_id").agg(F.sum("contribution").alias("incoming")), on="paper_id", how="left")
            .fillna(0.0, subset=["incoming"])
            .withColumn(
                "pagerank",
                F.lit(base)
                + F.lit(damping) * (F.col("incoming") + F.lit(dangling_mass / vertex_count)),
            )
            .select("paper_id", "pagerank")
            .cache()
        )
        ranks.count()
        previous_ranks.unpersist()

    out_degree.unpersist()
    return ranks


def write_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    """Write graph JSON and Markdown reports."""
    json_path = resolve_project_path(config, config["paths"]["citation_graph_report_json"])
    markdown_path = resolve_project_path(config, config["paths"]["citation_graph_report_md"])
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# Citation Graph",
        "",
        f"Generated on {date.today().isoformat()}.",
        "",
        "## Summary",
        "",
        f"- Sample publication vertices: {payload['vertex_count']}",
        f"- Expanded graph vertices: {payload.get('graph_vertex_count')}",
        f"- Full outgoing citation edges: {payload['full_edge_count']}",
        f"- In-sample citation edges: {payload['in_sample_edge_count']}",
        f"- External citation edges: {payload['external_edge_count']}",
        f"- PageRank iterations: {payload['pagerank_iterations']}",
        "",
        "## Top PageRank Papers",
        "",
        "| rank | paper | in sample? | year | PageRank | in-sample in-degree | cited_by_count |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for index, row in enumerate(payload["top_pagerank"], start=1):
        title = str(row.get("title") or row["paper_id"]).replace("|", "\\|")
        lines.append(
            f"| {index} | {title} | {row.get('in_sample')} | {row.get('publication_year')} | {row['pagerank']:.8f} | {row.get('in_degree_in_sample')} | {row.get('cited_by_count')} |"
        )
    lines.extend(
        [
            "",
            "## Top Sample Papers By PageRank",
            "",
            "| rank | paper | year | PageRank | cited_by_count |",
            "| ---: | --- | ---: | ---: | ---: |",
        ]
    )
    for index, row in enumerate(payload.get("top_sample_pagerank", []), start=1):
        title = str(row.get("title") or row["paper_id"]).replace("|", "\\|")
        lines.append(
            f"| {index} | {title} | {row.get('publication_year')} | {row['pagerank']:.8f} | {row.get('cited_by_count')} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Citation count and PageRank are graph signals, not measures of scientific quality. The 1,000-record sample has no citation edges between sampled papers, so PageRank is computed on an expanded graph that includes external referenced OpenAlex IDs. Metadata such as title/year/cited_by_count is only available for sampled papers.",
        ]
    )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_citation_graph(config: dict[str, Any]) -> dict[str, Any]:
    """Run citation graph analytics and write outputs."""
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
        iterations = int(graph_config.get("pagerank_iterations", 10))
        damping = float(graph_config.get("pagerank_damping", 0.85))

        sample_vertices = spark.read.parquet(_path(config, "gold_publications")).select(
            "paper_id", "title", "publication_year", "cited_by_count"
        )
        full_edges = spark.read.parquet(_path(config, "gold_citation_edges")).dropDuplicates(
            ["paper_id", "referenced_paper_id"]
        )
        induced_edges = (
            full_edges.join(sample_vertices.select(F.col("paper_id").alias("referenced_paper_id")), on="referenced_paper_id")
            .select("paper_id", "referenced_paper_id")
            .dropDuplicates()
        )
        graph_vertices = (
            sample_vertices.select("paper_id")
            .union(full_edges.select(F.col("referenced_paper_id").alias("paper_id")))
            .distinct()
        )
        degrees = compute_degrees(sample_vertices, full_edges, induced_edges).cache()
        degrees.write.mode("overwrite").parquet(_path(config, "citation_degrees"))

        ranks = run_pagerank(graph_vertices, full_edges, config)
        pagerank = (
            ranks.join(degrees, on="paper_id", how="left")
            .withColumn("in_sample", F.col("title").isNotNull())
            .fillna(0, subset=["in_degree_in_sample", "out_degree_in_sample", "out_degree_full"])
            .withColumn("pagerank_per_in_degree", F.col("pagerank") / (F.col("in_degree_in_sample") + F.lit(1.0)))
            .orderBy(F.desc("pagerank"))
        )
        pagerank.write.mode("overwrite").parquet(_path(config, "citation_pagerank"))

        unusual = pagerank.orderBy(F.desc("pagerank_per_in_degree")).limit(top_n)
        unusual.write.mode("overwrite").parquet(_path(config, "citation_unusual_pagerank"))

        top_pagerank = [row.asDict() for row in pagerank.limit(top_n).collect()]
        top_sample_pagerank = [
            row.asDict() for row in pagerank.where("in_sample = true").limit(top_n).collect()
        ]
        top_cited = [
            row.asDict()
            for row in degrees.orderBy(F.desc("cited_by_count"), F.desc("in_degree_in_sample")).limit(top_n).collect()
        ]
        top_unusual = [row.asDict() for row in unusual.collect()]

        vertex_count = sample_vertices.count()
        graph_vertex_count = graph_vertices.count()
        full_edge_count = full_edges.count()
        in_sample_edge_count = induced_edges.count()
        payload = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "success",
            "preflight": preflight,
            "vertex_count": vertex_count,
            "graph_vertex_count": graph_vertex_count,
            "full_edge_count": full_edge_count,
            "in_sample_edge_count": in_sample_edge_count,
            "external_edge_count": full_edge_count - in_sample_edge_count,
            "pagerank_iterations": iterations,
            "pagerank_damping": damping,
            "degree_summary": {
                "max_out_degree_full": degrees.agg(F.max("out_degree_full")).collect()[0][0],
                "max_in_degree_in_sample": degrees.agg(F.max("in_degree_in_sample")).collect()[0][0],
                "papers_with_in_sample_in_degree": degrees.where("in_degree_in_sample > 0").count(),
                "papers_with_in_sample_out_degree": degrees.where("out_degree_in_sample > 0").count(),
            },
            "top_pagerank": top_pagerank,
            "top_sample_pagerank": top_sample_pagerank,
            "top_cited_by_count": top_cited,
            "high_pagerank_relative_to_indegree": top_unusual,
            "outputs": {
                key: str(resolve_project_path(config, value))
                for key, value in config["paths"].items()
                if key.startswith("citation_")
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
    payload = run_citation_graph(config)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "vertex_count": payload.get("vertex_count"),
                "full_edge_count": payload.get("full_edge_count"),
                "in_sample_edge_count": payload.get("in_sample_edge_count"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
