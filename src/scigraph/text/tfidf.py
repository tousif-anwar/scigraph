"""Spark text analytics and TF-IDF term statistics."""

from __future__ import annotations

import argparse
import json
import math
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from scigraph.preprocessing.pipeline import _spark_imports, create_spark_session, preflight_environment
from scigraph.utils.config import load_config, resolve_project_path


DEFAULT_STOP_WORDS = {
    "able",
    "about",
    "above",
    "across",
    "after",
    "against",
    "almost",
    "alone",
    "along",
    "already",
    "all",
    "also",
    "although",
    "always",
    "another",
    "any",
    "are",
    "around",
    "been",
    "before",
    "being",
    "below",
    "among",
    "based",
    "because",
    "become",
    "becomes",
    "becoming",
    "between",
    "beyond",
    "both",
    "but",
    "can",
    "cannot",
    "could",
    "could",
    "during",
    "each",
    "either",
    "else",
    "first",
    "for",
    "from",
    "had",
    "has",
    "have",
    "having",
    "how",
    "however",
    "into",
    "its",
    "may",
    "might",
    "more",
    "most",
    "not",
    "other",
    "our",
    "out",
    "over",
    "paper",
    "per",
    "research",
    "results",
    "same",
    "should",
    "show",
    "shown",
    "study",
    "such",
    "than",
    "that",
    "the",
    "their",
    "then",
    "there",
    "these",
    "this",
    "those",
    "through",
    "thus",
    "too",
    "under",
    "use",
    "used",
    "using",
    "via",
    "was",
    "well",
    "were",
    "when",
    "where",
    "whether",
    "which",
    "while",
    "who",
    "whose",
    "with",
    "within",
    "without",
    "would",
    "and",
}


def normalize_token(token: str) -> str:
    """Normalize a single token for deterministic unit tests."""
    normalized = "".join(character.lower() if character.isalnum() else " " for character in token)
    return " ".join(normalized.split())


def is_valid_token(token: str, min_length: int = 3, stop_words: set[str] | None = None) -> bool:
    """Return whether a token should be kept for term statistics."""
    stop_words = stop_words or DEFAULT_STOP_WORDS
    return len(token) >= min_length and not token.isnumeric() and token not in stop_words


def idf(document_count: int, document_frequency: int) -> float:
    """Compute smoothed IDF."""
    return math.log((document_count + 1) / (document_frequency + 1)) + 1


def _path(config: dict[str, Any], key: str) -> str:
    return str(resolve_project_path(config, config["paths"][key]))


def reconstruct_abstracts(bronze_df):
    """Reconstruct OpenAlex abstract text from inverted-index maps using Spark expressions."""
    _, F, _ = _spark_imports()
    positions = (
        bronze_df.select(
            F.col("id").alias("paper_id"),
            F.explode(F.map_entries("abstract_inverted_index")).alias("entry"),
        )
        .select(
            "paper_id",
            F.col("entry.key").alias("token"),
            F.explode(F.col("entry.value")).alias("position"),
        )
        .where(F.col("position").isNotNull())
    )
    ordered = positions.groupBy("paper_id").agg(
        F.sort_array(F.collect_list(F.struct("position", "token"))).alias("ordered_tokens")
    )
    return ordered.select(
        "paper_id",
        F.array_join(F.transform("ordered_tokens", lambda item: item["token"]), " ").alias("abstract"),
    )


def build_text_documents(spark, config: dict[str, Any]):
    """Build analysis-ready text documents from Silver publications plus Bronze abstracts."""
    _, F, _ = _spark_imports()
    silver = spark.read.parquet(_path(config, "silver_publications"))
    bronze = spark.read.parquet(_path(config, "bronze_works"))
    abstracts = reconstruct_abstracts(bronze)
    documents = (
        silver.join(abstracts, on="paper_id", how="left")
        .withColumn(
            "document_text",
            F.trim(F.concat_ws(" ", F.coalesce(F.col("title"), F.lit("")), F.coalesce(F.col("abstract"), F.lit("")))),
        )
        .select(
            "paper_id",
            "paper_openalex_id",
            "title",
            "publication_year",
            "document_type",
            "language",
            "abstract_available",
            "document_text",
        )
    )
    documents.write.mode("overwrite").parquet(_path(config, "text_documents"))
    return documents


def tokenize_documents(documents, config: dict[str, Any]):
    """Tokenize documents with Spark SQL functions."""
    _, F, _ = _spark_imports()
    min_length = int(config["spark"].get("text", {}).get("min_token_length", 3))
    stop_words = list(DEFAULT_STOP_WORDS)
    tokens = (
        documents.select(
            "paper_id",
            "publication_year",
            F.explode(
                F.split(F.regexp_replace(F.lower(F.coalesce(F.col("document_text"), F.lit(""))), r"[^a-z0-9]+", " "), r"\s+")
            ).alias("token"),
        )
        .where(F.length("token") >= min_length)
        .where(~F.col("token").isin(stop_words))
        .where(~F.col("token").rlike(r"^[0-9]+$"))
    )
    return tokens


def compute_term_statistics(tokens, documents, config: dict[str, Any]) -> dict[str, Any]:
    """Compute term frequency, document frequency, and TF-IDF outputs."""
    _, F, _ = _spark_imports()
    top_n = int(config["spark"].get("text", {}).get("top_n_terms", 25))
    document_count = documents.count()

    term_frequency = tokens.groupBy("token").agg(F.count("*").alias("term_frequency"))
    doc_frequency = tokens.select("paper_id", "token").distinct().groupBy("token").agg(
        F.count("*").alias("document_frequency")
    )
    global_terms = (
        term_frequency.join(doc_frequency, on="token")
        .withColumn(
            "idf",
            F.log((F.lit(document_count) + F.lit(1.0)) / (F.col("document_frequency") + F.lit(1.0)))
            + F.lit(1.0),
        )
        .withColumn("corpus_tfidf", F.col("term_frequency") * F.col("idf"))
        .orderBy(F.desc("term_frequency"), "token")
    )
    global_terms.write.mode("overwrite").parquet(_path(config, "text_terms_global"))

    terms_by_year = (
        tokens.groupBy("publication_year", "token")
        .agg(F.count("*").alias("term_frequency"))
        .orderBy("publication_year", F.desc("term_frequency"), "token")
    )
    terms_by_year.write.mode("overwrite").parquet(_path(config, "text_terms_by_year"))

    gold_topics = spark_read_topics(tokens, config)
    terms_by_topic = (
        tokens.join(gold_topics, on="paper_id", how="inner")
        .groupBy("topic_name", "token")
        .agg(F.count("*").alias("term_frequency"))
        .orderBy("topic_name", F.desc("term_frequency"), "token")
    )
    terms_by_topic.write.mode("overwrite").parquet(_path(config, "text_terms_by_topic"))

    tfidf_terms = (
        tokens.groupBy("paper_id", "token")
        .agg(F.count("*").alias("term_frequency"))
        .join(doc_frequency, on="token")
        .withColumn(
            "idf",
            F.log((F.lit(document_count) + F.lit(1.0)) / (F.col("document_frequency") + F.lit(1.0)))
            + F.lit(1.0),
        )
        .withColumn("tfidf", F.col("term_frequency") * F.col("idf"))
    )
    tfidf_terms.write.mode("overwrite").parquet(_path(config, "text_tfidf_terms"))

    return {
        "document_count": document_count,
        "token_count": tokens.count(),
        "vocabulary_size": global_terms.count(),
        "top_global_terms": [row.asDict() for row in global_terms.limit(top_n).collect()],
        "top_year_terms": [row.asDict() for row in terms_by_year.limit(top_n).collect()],
        "top_topic_terms": [row.asDict() for row in terms_by_topic.limit(top_n).collect()],
        "tfidf_rows": tfidf_terms.count(),
    }


def spark_read_topics(tokens, config: dict[str, Any]):
    """Read topic rows with only fields needed for term-by-topic analysis."""
    spark = tokens.sparkSession
    return spark.read.parquet(_path(config, "gold_topics")).select("paper_id", "topic_name").where(
        "topic_name is not null"
    )


def write_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    """Write JSON and Markdown reports for text analytics."""
    json_path = resolve_project_path(config, config["paths"]["text_report_json"])
    markdown_path = resolve_project_path(config, config["paths"]["text_report_md"])
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# Text Analysis",
        "",
        f"Generated on {date.today().isoformat()}.",
        "",
        "## Summary",
        "",
        f"- Documents analyzed: {payload['document_count']}",
        f"- Tokens retained: {payload['token_count']}",
        f"- Vocabulary size: {payload['vocabulary_size']}",
        f"- Document-term TF-IDF rows: {payload['tfidf_rows']}",
        "",
        "## Top Global Terms",
        "",
        "| term | term frequency | document frequency | idf | corpus tf-idf |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["top_global_terms"]:
        lines.append(
            f"| {row['token']} | {row['term_frequency']} | {row['document_frequency']} | {row['idf']:.4f} | {row['corpus_tfidf']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "This milestone computes distributed token, term-frequency, document-frequency, and TF-IDF statistics. K-means clustering and qualitative cluster inspection are intentionally left for Milestone 6.",
        ]
    )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_text_analysis(config: dict[str, Any]) -> dict[str, Any]:
    """Run distributed text analysis and write artifacts."""
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
        documents = build_text_documents(spark, config)
        tokens = tokenize_documents(documents, config)
        stats = compute_term_statistics(tokens, documents, config)
        payload = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "success",
            "preflight": preflight,
            **stats,
            "outputs": {
                key: str(resolve_project_path(config, value))
                for key, value in config["paths"].items()
                if key.startswith("text_")
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
    payload = run_text_analysis(config)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "document_count": payload.get("document_count"),
                "token_count": payload.get("token_count"),
                "vocabulary_size": payload.get("vocabulary_size"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
