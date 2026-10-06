"""Advanced retrieval experiments: BM25, dense, hybrid, reranking, and graph-aware ranking."""

from __future__ import annotations

import argparse
import json
import math
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from scigraph.preprocessing.pipeline import create_spark_session, preflight_environment
from scigraph.text.tfidf import DEFAULT_STOP_WORDS, is_valid_token, normalize_token
from scigraph.utils.config import load_config, resolve_project_path


@dataclass
class RetrievalDocument:
    paper_id: str
    title: str
    year: int | None
    text: str
    tokens: list[str]
    topic_names: list[str]
    cited_by_count: int
    composite_score: float
    pagerank: float


def tokenize_text(text: str, min_length: int = 3) -> list[str]:
    """Tokenize text with the project text rules."""
    tokens: list[str] = []
    for raw_token in text.split():
        for token in normalize_token(raw_token).split():
            if is_valid_token(token, min_length=min_length, stop_words=DEFAULT_STOP_WORDS):
                tokens.append(token)
    return tokens


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Compute cosine similarity for dense vectors."""
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot / (left_norm * right_norm)


def reciprocal_rank(rank: int, k: int = 60) -> float:
    """Return reciprocal-rank fusion contribution."""
    if rank <= 0:
        raise ValueError("rank must be positive")
    return 1.0 / (k + rank)


def dcg(relevance: list[int]) -> float:
    """Return discounted cumulative gain for binary relevance."""
    return sum((2**rel - 1) / math.log2(index + 2) for index, rel in enumerate(relevance))


def ndcg_at_k(relevance: list[int], k: int) -> float:
    """Return normalized discounted cumulative gain at K."""
    observed = relevance[:k]
    ideal = sorted(relevance, reverse=True)[:k]
    ideal_dcg = dcg(ideal)
    if ideal_dcg == 0.0:
        return 0.0
    return dcg(observed) / ideal_dcg


def average_precision_at_k(relevance: list[int], k: int) -> float:
    """Return average precision at K for binary relevance."""
    hits = 0
    precision_sum = 0.0
    for index, rel in enumerate(relevance[:k], start=1):
        if rel:
            hits += 1
            precision_sum += hits / index
    return precision_sum / hits if hits else 0.0


def _path(config: dict[str, Any], key: str) -> str:
    return str(resolve_project_path(config, config["paths"][key]))


def _queries(config: dict[str, Any]) -> list[dict[str, Any]]:
    return config["spark"].get("retrieval", {}).get("queries", [])


def _advanced_config(config: dict[str, Any]) -> dict[str, Any]:
    return config["spark"].get("advanced_retrieval", {})


def load_documents(spark, config: dict[str, Any]) -> list[RetrievalDocument]:
    """Load manageable English text documents and metadata for retrieval evaluation."""
    from pyspark.sql import functions as F

    text_documents = spark.read.parquet(_path(config, "text_documents")).select(
        "paper_id", "title", "publication_year", "document_text"
    )
    topics = spark.read.parquet(_path(config, "gold_topics")).groupBy("paper_id").agg(
        F.collect_set("topic_name").alias("topic_names")
    )
    ranking = spark.read.parquet(_path(config, "ranking_publications")).select(
        "paper_id", "cited_by_count", "composite_score", "pagerank"
    )
    rows = (
        text_documents.join(topics, on="paper_id", how="left")
        .join(ranking, on="paper_id", how="left")
        .fillna(0, subset=["cited_by_count"])
        .fillna(0.0, subset=["composite_score", "pagerank"])
        .collect()
    )
    min_length = int(config["spark"].get("text", {}).get("min_token_length", 3))
    documents: list[RetrievalDocument] = []
    for row in rows:
        text = row["document_text"] or ""
        documents.append(
            RetrievalDocument(
                paper_id=row["paper_id"],
                title=row["title"] or row["paper_id"],
                year=row["publication_year"],
                text=text,
                tokens=tokenize_text(text, min_length=min_length),
                topic_names=list(row["topic_names"] or []),
                cited_by_count=int(row["cited_by_count"] or 0),
                composite_score=float(row["composite_score"] or 0.0),
                pagerank=float(row["pagerank"] or 0.0),
            )
        )
    return documents


def relevant_document_ids(documents: list[RetrievalDocument], query: dict[str, Any]) -> set[str]:
    """Approximate relevance using configured topic-name substring labels."""
    expected = [term.lower() for term in query.get("expected_topic_contains", [])]
    relevant: set[str] = set()
    for document in documents:
        topic_text = " | ".join(document.topic_names).lower()
        if any(term in topic_text for term in expected):
            relevant.add(document.paper_id)
    return relevant


def bm25_rank(documents: list[RetrievalDocument], query_tokens: list[str], k1: float = 1.5, b: float = 0.75):
    """Rank documents with BM25."""
    doc_count = len(documents)
    doc_lengths = {doc.paper_id: len(doc.tokens) for doc in documents}
    avgdl = sum(doc_lengths.values()) / doc_count if doc_count else 0.0
    document_frequency: Counter[str] = Counter()
    term_counts: dict[str, Counter[str]] = {}
    for doc in documents:
        counts = Counter(doc.tokens)
        term_counts[doc.paper_id] = counts
        for token in counts:
            document_frequency[token] += 1

    query_terms = Counter(query_tokens)
    rows = []
    for doc in documents:
        score = 0.0
        counts = term_counts[doc.paper_id]
        for token, query_weight in query_terms.items():
            if token not in counts:
                continue
            df = document_frequency[token]
            idf = math.log(1 + (doc_count - df + 0.5) / (df + 0.5))
            tf = counts[token]
            denom = tf + k1 * (1 - b + b * doc_lengths[doc.paper_id] / avgdl) if avgdl else 1.0
            score += query_weight * idf * (tf * (k1 + 1)) / denom
        if score > 0:
            rows.append({"paper_id": doc.paper_id, "score": score})
    return sorted(rows, key=lambda row: (-row["score"], row["paper_id"]))


def train_word2vec_embeddings(spark, documents: list[RetrievalDocument], config: dict[str, Any]):
    """Train Spark Word2Vec document embeddings and return model plus document vectors."""
    from pyspark.ml.feature import Word2Vec

    adv = _advanced_config(config)
    rows = [(doc.paper_id, doc.tokens) for doc in documents]
    frame = spark.createDataFrame(rows, ["paper_id", "tokens"])
    model = Word2Vec(
        vectorSize=int(adv.get("dense_vector_size", 32)),
        minCount=int(adv.get("dense_min_count", 1)),
        maxIter=int(adv.get("dense_max_iter", 5)),
        inputCol="tokens",
        outputCol="vector",
        seed=int(config["spark"].get("ml", {}).get("seed", 660)),
    ).fit(frame)
    vectors = {
        row["paper_id"]: [float(value) for value in row["vector"]]
        for row in model.transform(frame).select("paper_id", "vector").collect()
    }
    return model, vectors


def dense_rank_with_spark(spark, model, documents: list[RetrievalDocument], vectors: dict[str, list[float]], query_tokens: list[str]):
    """Rank documents with Word2Vec cosine similarity."""
    query_frame = spark.createDataFrame([("query", query_tokens)], ["paper_id", "tokens"])
    query_vector = [float(value) for value in model.transform(query_frame).collect()[0]["vector"]]
    rows = []
    for doc in documents:
        score = cosine_similarity(query_vector, vectors.get(doc.paper_id, []))
        if score > 0:
            rows.append({"paper_id": doc.paper_id, "score": score})
    return sorted(rows, key=lambda row: (-row["score"], row["paper_id"]))


def rrf_fuse(rankings: list[list[dict[str, Any]]], k: int = 60):
    """Fuse rankings with reciprocal rank fusion."""
    scores: defaultdict[str, float] = defaultdict(float)
    for ranking in rankings:
        for rank, row in enumerate(ranking, start=1):
            scores[row["paper_id"]] += reciprocal_rank(rank, k)
    return [
        {"paper_id": paper_id, "score": score}
        for paper_id, score in sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    ]


def rerank_candidates(
    candidates: list[dict[str, Any]],
    documents_by_id: dict[str, RetrievalDocument],
    query_tokens: list[str],
    candidate_k: int,
):
    """Transparent second-stage reranker using coverage, recency, and citation metadata."""
    query_set = set(query_tokens)
    rows = []
    for rank, row in enumerate(candidates[:candidate_k], start=1):
        doc = documents_by_id[row["paper_id"]]
        coverage = len(query_set.intersection(doc.tokens)) / max(len(query_set), 1)
        title_coverage = len(query_set.intersection(tokenize_text(doc.title))) / max(len(query_set), 1)
        rerank_score = row["score"] + 0.10 * coverage + 0.05 * title_coverage + 0.05 * doc.composite_score
        rows.append({"paper_id": doc.paper_id, "score": rerank_score, "first_stage_rank": rank})
    return sorted(rows, key=lambda item: (-item["score"], item["paper_id"]))


def graph_aware_rank(candidates: list[dict[str, Any]], documents_by_id: dict[str, RetrievalDocument], alpha: float):
    """Blend retrieval score with graph/composite score."""
    if not candidates:
        return []
    max_score = max(row["score"] for row in candidates) or 1.0
    rows = []
    for row in candidates:
        doc = documents_by_id[row["paper_id"]]
        normalized_retrieval = row["score"] / max_score
        score = (1 - alpha) * normalized_retrieval + alpha * doc.composite_score
        rows.append({"paper_id": row["paper_id"], "score": score})
    return sorted(rows, key=lambda item: (-item["score"], item["paper_id"]))


def evaluate_ranking(ranking: list[dict[str, Any]], relevant_ids: set[str], top_k: int) -> dict[str, float]:
    """Evaluate one query ranking."""
    ranked_ids = [row["paper_id"] for row in ranking]
    top_ids = ranked_ids[:top_k]
    relevance = [1 if paper_id in relevant_ids else 0 for paper_id in ranked_ids]
    relevant_at_k = sum(1 for paper_id in top_ids if paper_id in relevant_ids)
    first_relevant_rank = next((index for index, rel in enumerate(relevance, start=1) if rel), None)
    return {
        "precision_at_k": relevant_at_k / top_k if top_k else 0.0,
        "recall_at_k": relevant_at_k / len(relevant_ids) if relevant_ids else 0.0,
        "mrr": 1 / first_relevant_rank if first_relevant_rank else 0.0,
        "ndcg_at_k": ndcg_at_k(relevance, top_k),
        "average_precision_at_k": average_precision_at_k(relevance, top_k),
    }


def run_advanced_retrieval(config: dict[str, Any]) -> dict[str, Any]:
    """Run all retrieval systems and write reports."""
    preflight = preflight_environment(config)
    if not preflight["ok"]:
        return {"status": "blocked", "preflight": preflight}

    spark = create_spark_session(config)
    try:
        adv = _advanced_config(config)
        top_k = int(adv.get("top_k", 10))
        candidate_k = int(adv.get("candidate_k", 50))
        rrf_k = int(adv.get("rrf_k", 60))
        graph_alphas = [float(value) for value in adv.get("graph_alphas", [0.0, 0.25, 0.5])]
        documents = load_documents(spark, config)
        documents_by_id = {doc.paper_id: doc for doc in documents}
        word2vec_model, dense_vectors = train_word2vec_embeddings(spark, documents, config)

        system_metrics: defaultdict[str, list[dict[str, float]]] = defaultdict(list)
        per_query: list[dict[str, Any]] = []
        top_results: dict[str, list[dict[str, Any]]] = {}
        graph_alpha_metrics: defaultdict[str, list[dict[str, float]]] = defaultdict(list)

        for query in _queries(config):
            query_tokens = tokenize_text(query["text"])
            relevant_ids = relevant_document_ids(documents, query)

            timings: dict[str, float] = {}
            start = time.perf_counter()
            bm25 = bm25_rank(documents, query_tokens)
            timings["bm25"] = time.perf_counter() - start

            start = time.perf_counter()
            dense = dense_rank_with_spark(spark, word2vec_model, documents, dense_vectors, query_tokens)
            timings["dense"] = time.perf_counter() - start

            start = time.perf_counter()
            hybrid = rrf_fuse([bm25, dense], rrf_k)
            timings["hybrid"] = time.perf_counter() - start

            start = time.perf_counter()
            reranked = rerank_candidates(hybrid, documents_by_id, query_tokens, candidate_k)
            timings["hybrid_reranked"] = time.perf_counter() - start

            systems = {
                "bm25": bm25,
                "dense": dense,
                "hybrid_rrf": hybrid,
                "hybrid_reranked": reranked,
            }
            best_graph = None
            for alpha in graph_alphas:
                graph_ranked = graph_aware_rank(reranked, documents_by_id, alpha)
                name = f"graph_alpha_{alpha:g}"
                systems[name] = graph_ranked
                metrics = evaluate_ranking(graph_ranked, relevant_ids, top_k)
                graph_alpha_metrics[name].append(metrics)
                if best_graph is None or metrics["ndcg_at_k"] > best_graph[1]["ndcg_at_k"]:
                    best_graph = (name, metrics, graph_ranked)
            if best_graph:
                systems["hybrid_reranked_graph"] = best_graph[2]

            query_result = {
                "query_id": query["query_id"],
                "query_text": query["text"],
                "relevant_document_count": len(relevant_ids),
                "latencies_seconds": timings,
                "systems": {},
            }
            for name, ranking in systems.items():
                metrics = evaluate_ranking(ranking, relevant_ids, top_k)
                system_metrics[name].append(metrics | {"latency_seconds": timings.get(name, 0.0)})
                query_result["systems"][name] = metrics
            per_query.append(query_result)

            if query["query_id"] == _queries(config)[0]["query_id"]:
                top_results = {
                    name: [
                        {
                            "rank": index,
                            "paper_id": row["paper_id"],
                            "title": documents_by_id[row["paper_id"]].title,
                            "year": documents_by_id[row["paper_id"]].year,
                            "score": row["score"],
                            "relevant": row["paper_id"] in relevant_ids,
                        }
                        for index, row in enumerate(ranking[:top_k], start=1)
                    ]
                    for name, ranking in systems.items()
                    if name in {"bm25", "dense", "hybrid_rrf", "hybrid_reranked", "hybrid_reranked_graph"}
                }

        ablation = []
        for name, metrics_rows in system_metrics.items():
            if not metrics_rows:
                continue
            ablation.append(
                {
                    "system": name,
                    "precision_at_k": sum(row["precision_at_k"] for row in metrics_rows) / len(metrics_rows),
                    "recall_at_k": sum(row["recall_at_k"] for row in metrics_rows) / len(metrics_rows),
                    "mrr": sum(row["mrr"] for row in metrics_rows) / len(metrics_rows),
                    "ndcg_at_k": sum(row["ndcg_at_k"] for row in metrics_rows) / len(metrics_rows),
                    "mean_latency_seconds": sum(row.get("latency_seconds", 0.0) for row in metrics_rows)
                    / len(metrics_rows),
                }
            )
        ablation = sorted(ablation, key=lambda row: row["system"])

        demo_query = adv.get("demo_query", "retrieval augmented generation for clinical decision support")
        demo_tokens = tokenize_text(demo_query)
        demo_bm25 = bm25_rank(documents, demo_tokens)
        demo_dense = dense_rank_with_spark(spark, word2vec_model, documents, dense_vectors, demo_tokens)
        demo_hybrid = rrf_fuse([demo_bm25, demo_dense], rrf_k)
        demo_reranked = rerank_candidates(demo_hybrid, documents_by_id, demo_tokens, candidate_k)
        demo_results = [
            {
                "rank": index,
                "paper_id": row["paper_id"],
                "title": documents_by_id[row["paper_id"]].title,
                "year": documents_by_id[row["paper_id"]].year,
                "score": row["score"],
                "cited_by_count": documents_by_id[row["paper_id"]].cited_by_count,
                "pagerank": documents_by_id[row["paper_id"]].pagerank,
                "abstract_excerpt": documents_by_id[row["paper_id"]].text[:300],
            }
            for index, row in enumerate(demo_reranked[:top_k], start=1)
        ]

        payload = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "success",
            "document_count": len(documents),
            "query_count": len(_queries(config)),
            "top_k": top_k,
            "candidate_k": candidate_k,
            "systems": ablation,
            "per_query": per_query,
            "top_results_for_first_query": top_results,
            "demo_query": demo_query,
            "demo_results": demo_results,
            "dense_model": {
                "model": "Spark ML Word2Vec",
                "vector_size": int(adv.get("dense_vector_size", 32)),
                "max_iter": int(adv.get("dense_max_iter", 5)),
                "min_count": int(adv.get("dense_min_count", 1)),
            },
        }
        write_outputs(config, payload)
        return payload
    finally:
        spark.stop()


def write_outputs(config: dict[str, Any], payload: dict[str, Any]) -> None:
    """Write JSON, Markdown report, demo, and error analysis artifacts."""
    results_path = resolve_project_path(config, config["paths"]["advanced_retrieval_results_json"])
    report_path = resolve_project_path(config, config["paths"]["advanced_retrieval_report_md"])
    error_path = resolve_project_path(config, config["paths"]["error_analysis_md"])
    demo_json_path = resolve_project_path(config, config["paths"]["demo_results_json"])
    demo_md_path = resolve_project_path(config, config["paths"]["demo_report_md"])
    for path in [results_path, report_path, error_path, demo_json_path, demo_md_path]:
        path.parent.mkdir(parents=True, exist_ok=True)

    results_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    demo_json_path.write_text(
        json.dumps(
            {"query": payload["demo_query"], "results": payload["demo_results"]},
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    report_lines = [
        "# Advanced Retrieval And Ablation",
        "",
        f"Generated on {date.today().isoformat()}.",
        "",
        "## Summary",
        "",
        f"- Documents: {payload['document_count']}",
        f"- Queries: {payload['query_count']}",
        f"- Top K: {payload['top_k']}",
        f"- Dense model: {payload['dense_model']['model']} ({payload['dense_model']['vector_size']} dimensions)",
        "",
        "## Ablation Results",
        "",
        "| system | precision@K | recall@K | MRR | NDCG@K | mean latency seconds |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["systems"]:
        report_lines.append(
            f"| {row['system']} | {row['precision_at_k']:.4f} | {row['recall_at_k']:.4f} | {row['mrr']:.4f} | {row['ndcg_at_k']:.4f} | {row['mean_latency_seconds']:.4f} |"
        )
    report_lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "BM25 is the lexical baseline. Dense retrieval uses Spark ML Word2Vec trained locally on the development corpus. Hybrid retrieval uses reciprocal rank fusion. Reranking is a transparent second-stage score over the hybrid candidates. Graph-aware ranking blends reranked retrieval scores with the composite publication score. Metrics use the same topic-name proxy relevance labels as the sparse retrieval milestone.",
        ]
    )
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    error_lines = [
        "# Retrieval Error Analysis",
        "",
        f"Generated on {date.today().isoformat()}.",
        "",
        "## Method",
        "",
        "Errors were inspected using the shared query set and OpenAlex topic-name proxy relevance labels. This is not a substitute for human relevance judgments, but it gives reproducible failure categories for the final report.",
        "",
        "## Observed Failure Categories",
        "",
        "- Terminology mismatch: lexical retrieval misses documents that use related but different wording.",
        "- Broad query ambiguity: terms such as policy, education, and healthcare match many fields.",
        "- Metadata-label mismatch: a retrieved document can appear relevant by title but not match the configured topic-name proxy.",
        "- Dense-vector drift: Word2Vec similarities can favor documents with generally similar vocabulary rather than precise topical relevance.",
        "- Older-paper and citation bias: graph-aware ranking can favor papers with stronger citation/composite metadata, which may disadvantage newer papers.",
        "",
        "## Per-Query Notes",
        "",
    ]
    for query in payload["per_query"]:
        best_system = max(query["systems"].items(), key=lambda item: item[1]["ndcg_at_k"])
        error_lines.append(
            f"- `{query['query_text']}`: best NDCG@K system was `{best_system[0]}` with NDCG@K {best_system[1]['ndcg_at_k']:.4f}; relevant proxy documents available: {query['relevant_document_count']}."
        )
    error_path.write_text("\n".join(error_lines) + "\n", encoding="utf-8")

    demo_lines = [
        "# Retrieval Demo",
        "",
        f"Generated on {date.today().isoformat()}.",
        "",
        f"Query: `{payload['demo_query']}`",
        "",
        "| rank | title | year | score | cited_by_count | pagerank |",
        "| ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["demo_results"]:
        title = str(row["title"]).replace("|", "\\|")
        demo_lines.append(
            f"| {row['rank']} | {title} | {row['year']} | {row['score']:.6f} | {row['cited_by_count']} | {row['pagerank']:.8f} |"
        )
    demo_lines.extend(["", "The demo uses the hybrid + transparent reranker pipeline."])
    demo_md_path.write_text("\n".join(demo_lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/dev.yaml")
    args = parser.parse_args()
    payload = run_advanced_retrieval(load_config(Path(args.config)))
    print(
        json.dumps(
            {
                "status": payload["status"],
                "document_count": payload.get("document_count"),
                "query_count": payload.get("query_count"),
                "systems": [row["system"] for row in payload.get("systems", [])],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
