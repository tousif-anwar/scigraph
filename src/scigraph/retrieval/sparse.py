"""Sparse TF-IDF retrieval baseline over scientific text documents."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from scigraph.preprocessing.pipeline import _spark_imports, create_spark_session, preflight_environment
from scigraph.text.tfidf import DEFAULT_STOP_WORDS, is_valid_token, normalize_token
from scigraph.utils.config import load_config, resolve_project_path


def tokenize_query(text: str, min_length: int = 3) -> list[str]:
    """Tokenize a retrieval query using the project text-analysis rules."""
    tokens: list[str] = []
    for raw_token in text.split():
        normalized = normalize_token(raw_token)
        for token in normalized.split():
            if is_valid_token(token, min_length=min_length, stop_words=DEFAULT_STOP_WORDS):
                tokens.append(token)
    return tokens


def precision_at_k(relevant_count: int, k: int) -> float:
    """Return precision at k."""
    if k <= 0:
        raise ValueError("k must be positive")
    return relevant_count / k


def _path(config: dict[str, Any], key: str) -> str:
    return str(resolve_project_path(config, config["paths"][key]))


def _query_rows(config: dict[str, Any]) -> list[tuple[str, str, str, int]]:
    retrieval_config = config["spark"].get("retrieval", {})
    min_length = int(config["spark"].get("text", {}).get("min_token_length", 3))
    rows: list[tuple[str, str, str, int]] = []
    for query in retrieval_config.get("queries", []):
        tokens = tokenize_query(query["text"], min_length=min_length)
        for token in sorted(set(tokens)):
            rows.append((query["query_id"], query["text"], token, tokens.count(token)))
    return rows


def build_rankings(spark, config: dict[str, Any]):
    """Build sparse query-document rankings from saved document-term TF-IDF rows."""
    _, F, Window = _spark_imports()
    from pyspark.sql import Window as SparkWindow

    query_rows = _query_rows(config)
    if not query_rows:
        raise ValueError("retrieval queries produced no valid tokens")

    queries = spark.createDataFrame(query_rows, ["query_id", "query_text", "token", "query_term_frequency"])
    tfidf_terms = spark.read.parquet(_path(config, "text_tfidf_terms"))
    documents = spark.read.parquet(_path(config, "text_documents")).select(
        "paper_id", "title", "publication_year", "language"
    )
    topics = spark.read.parquet(_path(config, "gold_topics")).groupBy("paper_id").agg(
        F.collect_set("topic_name").alias("topic_names")
    )
    scored = (
        queries.join(tfidf_terms, on="token", how="inner")
        .withColumn("term_score", F.col("query_term_frequency") * F.col("tfidf"))
        .groupBy("query_id", "query_text", "paper_id")
        .agg(
            F.sum("term_score").alias("retrieval_score"),
            F.countDistinct("token").alias("matched_query_terms"),
        )
        .join(documents, on="paper_id", how="left")
        .join(topics, on="paper_id", how="left")
    )
    window = SparkWindow.partitionBy("query_id").orderBy(F.desc("retrieval_score"), "paper_id")
    return scored.withColumn("rank", F.row_number().over(window)).orderBy("query_id", "rank")


def mark_relevance(rankings, config: dict[str, Any]):
    """Mark approximate relevance using configured topic-name substrings."""
    _, F, _ = _spark_imports()
    relevance_rows = []
    for query in config["spark"].get("retrieval", {}).get("queries", []):
        for expected in query.get("expected_topic_contains", []):
            relevance_rows.append((query["query_id"], expected.lower()))
    relevance_terms = rankings.sparkSession.createDataFrame(
        relevance_rows, ["query_id", "expected_topic_substring"]
    )
    exploded = rankings.withColumn("topic_name", F.explode_outer("topic_names")).withColumn(
        "topic_name_lower", F.lower(F.col("topic_name"))
    )
    relevant = (
        exploded.join(relevance_terms, on="query_id", how="left")
        .withColumn(
            "topic_match",
            F.col("topic_name_lower").contains(F.col("expected_topic_substring")),
        )
        .groupBy("query_id", "paper_id")
        .agg(F.max(F.coalesce(F.col("topic_match").cast("int"), F.lit(0))).alias("is_relevant_int"))
        .withColumn("is_relevant", F.col("is_relevant_int") == F.lit(1))
        .select("query_id", "paper_id", "is_relevant")
    )
    return rankings.join(relevant, on=["query_id", "paper_id"], how="left").fillna(
        False, subset=["is_relevant"]
    )


def evaluate_rankings(marked_rankings, top_k: int):
    """Evaluate approximate retrieval precision by query."""
    _, F, _ = _spark_imports()
    top_results = marked_rankings.where(F.col("rank") <= F.lit(top_k))
    return (
        top_results.groupBy("query_id", "query_text")
        .agg(
            F.count("*").alias("retrieved_count"),
            F.sum(F.col("is_relevant").cast("int")).alias("relevant_retrieved_count"),
            F.avg(F.col("is_relevant").cast("int")).alias("precision_at_k"),
            F.avg("matched_query_terms").alias("avg_matched_query_terms"),
            F.max("retrieval_score").alias("top_score"),
        )
        .orderBy("query_id")
    )


def write_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    """Write retrieval JSON and Markdown reports."""
    json_path = resolve_project_path(config, config["paths"]["retrieval_report_json"])
    markdown_path = resolve_project_path(config, config["paths"]["retrieval_report_md"])
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# Retrieval",
        "",
        f"Generated on {date.today().isoformat()}.",
        "",
        "## Summary",
        "",
        f"- Queries evaluated: {payload.get('query_count')}",
        f"- Top K: {payload.get('top_k')}",
        f"- Ranking rows: {payload.get('ranking_row_count')}",
        f"- Mean precision@K: {payload.get('mean_precision_at_k'):.4f}",
        "",
        "## Query Evaluation",
        "",
        "| query | retrieved | relevant retrieved | precision@K | avg matched terms |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in payload.get("evaluation", []):
        query_text = str(row["query_text"]).replace("|", "\\|")
        lines.append(
            f"| {query_text} | {row['retrieved_count']} | {row['relevant_retrieved_count']} | {row['precision_at_k']:.4f} | {row['avg_matched_query_terms']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## Top Results",
            "",
            "| query | rank | title | score | relevant |",
            "| --- | ---: | --- | ---: | --- |",
        ]
    )
    for row in payload.get("top_results", []):
        title = str(row.get("title") or row["paper_id"]).replace("|", "\\|")
        query_text = str(row["query_text"]).replace("|", "\\|")
        lines.append(
            f"| {query_text} | {row['rank']} | {title} | {row['retrieval_score']:.4f} | {row['is_relevant']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This milestone is a sparse lexical retrieval baseline over saved TF-IDF terms. Relevance is approximated from OpenAlex topic-name substring matches, so precision values are diagnostic rather than definitive information-retrieval judgments.",
        ]
    )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_sparse_retrieval(config: dict[str, Any]) -> dict[str, Any]:
    """Run sparse retrieval and write outputs."""
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
        top_k = int(config["spark"].get("retrieval", {}).get("top_k", 10))
        rankings = build_rankings(spark, config).cache()
        marked_rankings = mark_relevance(rankings, config).cache()
        marked_rankings.write.mode("overwrite").parquet(_path(config, "retrieval_rankings"))

        evaluation = evaluate_rankings(marked_rankings, top_k).cache()
        evaluation.write.mode("overwrite").parquet(_path(config, "retrieval_evaluation"))

        evaluation_rows = [row.asDict() for row in evaluation.collect()]
        top_results = [
            row.asDict()
            for row in marked_rankings.where(F.col("rank") <= F.lit(min(top_k, 3)))
            .orderBy("query_id", "rank")
            .collect()
        ]
        mean_precision = (
            sum(row["precision_at_k"] for row in evaluation_rows) / len(evaluation_rows)
            if evaluation_rows
            else 0.0
        )
        payload = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "success",
            "preflight": preflight,
            "query_count": len(config["spark"].get("retrieval", {}).get("queries", [])),
            "top_k": top_k,
            "ranking_row_count": marked_rankings.count(),
            "mean_precision_at_k": mean_precision,
            "evaluation": evaluation_rows,
            "top_results": top_results,
            "outputs": {
                key: str(resolve_project_path(config, value))
                for key, value in config["paths"].items()
                if key.startswith("retrieval_")
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
    payload = run_sparse_retrieval(config)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "query_count": payload.get("query_count"),
                "top_k": payload.get("top_k"),
                "ranking_row_count": payload.get("ranking_row_count"),
                "mean_precision_at_k": payload.get("mean_precision_at_k"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
