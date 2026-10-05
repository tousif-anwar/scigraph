"""Spark K-means clustering over scientific document text."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from scigraph.preprocessing.pipeline import _spark_imports, create_spark_session, preflight_environment
from scigraph.text.tfidf import DEFAULT_STOP_WORDS
from scigraph.utils.config import load_config, resolve_project_path


def choose_best_k(results: list[dict[str, Any]]) -> int:
    """Choose the K with the highest silhouette score."""
    if not results:
        raise ValueError("Cannot choose K without results.")
    return max(results, key=lambda row: row["silhouette"])["k"]


def cluster_size_distribution(assignments: list[int]) -> dict[int, int]:
    """Return a deterministic cluster-size distribution for tests."""
    distribution: dict[int, int] = {}
    for cluster in assignments:
        distribution[cluster] = distribution.get(cluster, 0) + 1
    return dict(sorted(distribution.items()))


def _path(config: dict[str, Any], key: str) -> str:
    return str(resolve_project_path(config, config["paths"][key]))


def _clustering_config(config: dict[str, Any]) -> dict[str, Any]:
    return config["spark"].get("clustering", {})


def prepare_features(documents, config: dict[str, Any]):
    """Tokenize documents and create IDF-weighted sparse feature vectors."""
    _, _, _ = _spark_imports()
    from pyspark.ml.feature import HashingTF, IDF, Normalizer, RegexTokenizer, StopWordsRemover

    cluster_config = _clustering_config(config)
    tokenizer = RegexTokenizer(
        inputCol="document_text",
        outputCol="raw_tokens",
        pattern="[^A-Za-z0-9]+",
        minTokenLength=int(cluster_config.get("min_token_length", 3)),
        toLowercase=True,
    )
    remover = StopWordsRemover(
        inputCol="raw_tokens",
        outputCol="tokens",
        stopWords=sorted(DEFAULT_STOP_WORDS),
        caseSensitive=False,
    )
    hashing_tf = HashingTF(
        inputCol="tokens",
        outputCol="tf_features",
        numFeatures=int(cluster_config.get("num_features", 4096)),
    )
    idf = IDF(inputCol="tf_features", outputCol="idf_features")
    normalizer = Normalizer(inputCol="idf_features", outputCol="features", p=2.0)

    tokenized = remover.transform(tokenizer.transform(documents))
    featurized = hashing_tf.transform(tokenized)
    idf_model = idf.fit(featurized)
    normalized = normalizer.transform(idf_model.transform(featurized))
    return normalized.select(
        "paper_id",
        "title",
        "language",
        "publication_year",
        "document_text",
        "tokens",
        "features",
    )


def evaluate_k_values(features, config: dict[str, Any]) -> tuple[list[dict[str, Any]], Any]:
    """Fit K-means for configured K values and return metrics plus best prediction frame."""
    from pyspark.ml.clustering import KMeans
    from pyspark.ml.evaluation import ClusteringEvaluator

    cluster_config = _clustering_config(config)
    evaluator = ClusteringEvaluator(featuresCol="features", predictionCol="cluster")
    rows: list[dict[str, Any]] = []
    best_predictions = None
    best_silhouette = None

    for k in [int(value) for value in cluster_config.get("k_values", [3, 5, 8])]:
        model = KMeans(
            k=k,
            seed=int(cluster_config.get("seed", 660)),
            maxIter=int(cluster_config.get("max_iter", 20)),
            featuresCol="features",
            predictionCol="cluster",
        ).fit(features)
        predictions = model.transform(features)
        silhouette = float(evaluator.evaluate(predictions))
        sizes = {
            int(row["cluster"]): int(row["count"])
            for row in predictions.groupBy("cluster").count().orderBy("cluster").collect()
        }
        rows.append(
            {
                "k": k,
                "silhouette": silhouette,
                "training_cost": float(model.summary.trainingCost),
                "cluster_sizes": sizes,
            }
        )
        if best_silhouette is None or silhouette > best_silhouette:
            best_silhouette = silhouette
            best_predictions = predictions

    return rows, best_predictions


def summarize_clusters(predictions, config: dict[str, Any]) -> dict[str, Any]:
    """Write cluster assignments, representative terms, and representative papers."""
    _, F, _ = _spark_imports()
    cluster_config = _clustering_config(config)
    top_terms_per_cluster = int(cluster_config.get("top_terms_per_cluster", 12))
    representative_count = int(cluster_config.get("representative_papers_per_cluster", 5))

    assignments = predictions.select(
        "paper_id",
        "title",
        "publication_year",
        F.col("cluster").cast("int").alias("cluster"),
    )
    assignments.write.mode("overwrite").parquet(_path(config, "cluster_assignments"))

    exploded_tokens = predictions.select("cluster", F.explode("tokens").alias("token")).where(
        (F.length("token") >= int(cluster_config.get("min_token_length", 3)))
        & (~F.col("token").isin(list(DEFAULT_STOP_WORDS)))
        & (~F.col("token").rlike(r"^[0-9]+$"))
    )
    token_counts = exploded_tokens.groupBy("cluster", "token").agg(F.count("*").alias("term_frequency"))
    window = __import__("pyspark.sql.window", fromlist=["Window"]).Window.partitionBy("cluster").orderBy(
        F.desc("term_frequency"), "token"
    )
    cluster_terms = (
        token_counts.withColumn("rank", F.row_number().over(window))
        .where(F.col("rank") <= top_terms_per_cluster)
        .orderBy("cluster", "rank")
    )
    cluster_terms.write.mode("overwrite").parquet(_path(config, "cluster_terms"))

    paper_window = __import__("pyspark.sql.window", fromlist=["Window"]).Window.partitionBy("cluster").orderBy(
        "publication_year", "title"
    )
    representative_papers = (
        assignments.withColumn("rank", F.row_number().over(paper_window))
        .where(F.col("rank") <= representative_count)
        .orderBy("cluster", "rank")
    )
    representative_papers.write.mode("overwrite").parquet(_path(config, "cluster_representative_papers"))

    return {
        "cluster_terms": [row.asDict() for row in cluster_terms.collect()],
        "representative_papers": [row.asDict() for row in representative_papers.collect()],
        "cluster_sizes": {
            int(row["cluster"]): int(row["count"])
            for row in assignments.groupBy("cluster").count().orderBy("cluster").collect()
        },
    }


def write_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    """Write clustering JSON and Markdown reports."""
    json_path = resolve_project_path(config, config["paths"]["cluster_report_json"])
    markdown_path = resolve_project_path(config, config["paths"]["cluster_report_md"])
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# K-means Text Clustering",
        "",
        f"Generated on {date.today().isoformat()}.",
        "",
        "## Summary",
        "",
        f"- Documents clustered: {payload.get('document_count')}",
        f"- K values evaluated: {payload.get('k_values')}",
        f"- Selected K: {payload.get('selected_k')}",
        "",
        "## K Evaluation",
        "",
        "| k | silhouette | training cost | cluster sizes |",
        "| ---: | ---: | ---: | --- |",
    ]
    for row in payload.get("k_results", []):
        lines.append(
            f"| {row['k']} | {row['silhouette']:.4f} | {row['training_cost']:.4f} | {row['cluster_sizes']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Silhouette is used as a diagnostic, not proof that clusters are scientific disciplines. Representative terms and papers require qualitative review before interpretation.",
        ]
    )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_clustering(config: dict[str, Any]) -> dict[str, Any]:
    """Run Spark K-means text clustering."""
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
        documents = spark.read.parquet(_path(config, "text_documents")).where("document_text is not null")
        language = _clustering_config(config).get("language")
        if language:
            documents = documents.where(f"language = '{language}'")
        features = prepare_features(documents, config).cache()
        document_count = features.count()
        k_results, best_predictions = evaluate_k_values(features, config)
        selected_k = choose_best_k(k_results)
        cluster_summary = summarize_clusters(best_predictions, config)
        payload = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "success",
            "preflight": preflight,
            "document_count": document_count,
            "k_values": [row["k"] for row in k_results],
            "selected_k": selected_k,
            "k_results": k_results,
            **cluster_summary,
            "outputs": {
                key: str(resolve_project_path(config, value))
                for key, value in config["paths"].items()
                if key.startswith("cluster_")
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
    payload = run_clustering(config)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "document_count": payload.get("document_count"),
                "selected_k": payload.get("selected_k"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
