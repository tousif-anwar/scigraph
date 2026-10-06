"""Generate project visualizations from measured SciGraph report artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt

from scigraph.utils.config import load_config, resolve_project_path


FIGURE_NAMES = [
    "dataset_publications_by_year.png",
    "data_quality_checks.png",
    "pipeline_stage_counts.png",
    "text_top_terms.png",
    "clustering_results.png",
    "citation_graph_summary.png",
    "author_collaboration_summary.png",
    "temporal_yearly_metrics.png",
    "streaming_batch_metrics.png",
    "retrieval_ablation.png",
    "ml_citation_prediction.png",
    "ranking_top_publications.png",
    "feature_mart_availability.png",
]


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON report."""
    return json.loads(path.read_text(encoding="utf-8"))


def save_bar(path: Path, title: str, labels: list[str], values: list[float], ylabel: str) -> None:
    """Save a basic labeled bar chart."""
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.bar(labels, values, color="#4C78A8")
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=35)
    ax.grid(axis="y", alpha=0.25)
    for index, value in enumerate(values):
        ax.text(index, value, f"{value:g}", ha="center", va="bottom", fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def generate_figures(config: dict[str, Any]) -> list[Path]:
    """Generate all static project figures and return written paths."""
    root = resolve_project_path(config, ".")
    results = root / "reports" / "results"
    figures = root / "reports" / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    schema = load_json(results / "schema_summary.json")
    stats = schema["dataset_statistics"]
    years = sorted(stats["documents_per_year"].keys())
    save_bar(
        figures / "dataset_publications_by_year.png",
        "OpenAlex Sample Publications By Year",
        years,
        [stats["documents_per_year"][year] for year in years],
        "Publications",
    )
    written.append(figures / "dataset_publications_by_year.png")

    quality = load_json(results / "data_quality_report.json")["summary"]
    save_bar(
        figures / "data_quality_checks.png",
        "Data Quality Check Outcomes",
        ["Passed", "Warnings", "Errors"],
        [quality["passed_checks"], quality["warning_checks"], quality["error_checks"]],
        "Checks",
    )
    written.append(figures / "data_quality_checks.png")

    pipeline_counts = load_json(results / "bronze_silver_gold_report.json")["stage_counts"]
    pipeline_keys = [
        "raw_records",
        "bronze_records",
        "silver_publications",
        "gold_publications",
        "gold_authors",
        "gold_author_publications",
        "gold_citation_edges",
        "gold_topics",
    ]
    save_bar(
        figures / "pipeline_stage_counts.png",
        "Bronze/Silver/Gold Pipeline Output Counts",
        [key.replace("_", " ") for key in pipeline_keys],
        [pipeline_counts[key] for key in pipeline_keys],
        "Rows",
    )
    written.append(figures / "pipeline_stage_counts.png")

    text = load_json(results / "text_analysis_report.json")
    terms = text["top_global_terms"][:12]
    save_bar(
        figures / "text_top_terms.png",
        "Top Global Text Terms",
        [row["token"] for row in terms],
        [row["term_frequency"] for row in terms],
        "Term frequency",
    )
    written.append(figures / "text_top_terms.png")

    clustering = load_json(results / "clustering_report.json")
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    k_results = clustering["k_results"]
    axes[0].plot([row["k"] for row in k_results], [row["silhouette"] for row in k_results], marker="o")
    axes[0].set_title("K-means Silhouette By K")
    axes[0].set_xlabel("K")
    axes[0].set_ylabel("Silhouette")
    axes[0].grid(alpha=0.25)
    cluster_sizes = clustering["cluster_sizes"]
    axes[1].bar([str(key) for key in cluster_sizes.keys()], list(cluster_sizes.values()), color="#59A14F")
    axes[1].set_title("Selected K=3 Cluster Sizes")
    axes[1].set_xlabel("Cluster")
    axes[1].set_ylabel("Documents")
    axes[1].grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(figures / "clustering_results.png", dpi=160)
    plt.close(fig)
    written.append(figures / "clustering_results.png")

    citation = load_json(results / "citation_graph_report.json")
    save_bar(
        figures / "citation_graph_summary.png",
        "Citation Graph Summary",
        ["Sample vertices", "Expanded vertices", "Outgoing edges", "In-sample edges"],
        [
            citation["vertex_count"],
            citation["graph_vertex_count"],
            citation["full_edge_count"],
            citation["in_sample_edge_count"],
        ],
        "Count",
    )
    written.append(figures / "citation_graph_summary.png")

    author = load_json(results / "author_collaboration_report.json")
    save_bar(
        figures / "author_collaboration_summary.png",
        "Author Collaboration Graph Summary",
        ["Authors", "Author-pub rows", "Multi-author pubs", "Solo pubs", "Edges"],
        [
            author["author_count"],
            author["author_publication_count"],
            author["multi_author_publication_count"],
            author["solo_author_publication_count"],
            author["collaboration_edge_count"],
        ],
        "Count",
    )
    written.append(figures / "author_collaboration_summary.png")

    temporal = load_json(results / "temporal_analysis_report.json")
    yearly = temporal["yearly_metrics"]
    fig, ax1 = plt.subplots(figsize=(10, 5.5))
    ax1.bar([row["publication_year"] for row in yearly], [row["publication_count"] for row in yearly], color="#4C78A8")
    ax1.set_title("Publication Volume And Citation Rate By Year")
    ax1.set_xlabel("Publication year")
    ax1.set_ylabel("Publications")
    ax2 = ax1.twinx()
    ax2.plot(
        [row["publication_year"] for row in yearly],
        [row["citations_per_publication"] for row in yearly],
        color="#F58518",
        marker="o",
    )
    ax2.set_ylabel("Citations per publication")
    ax1.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(figures / "temporal_yearly_metrics.png", dpi=160)
    plt.close(fig)
    written.append(figures / "temporal_yearly_metrics.png")

    streaming = load_json(results / "streaming_simulation_report.json")
    batches = streaming["batch_metrics"]
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.plot([row["batch_id"] for row in batches], [row["missing_author_count"] for row in batches], marker="o", label="Missing authors")
    ax.plot([row["batch_id"] for row in batches], [row["missing_title_count"] for row in batches], marker="o", label="Missing titles")
    ax.set_title("Streaming Simulation Missing Metadata By Batch")
    ax.set_xlabel("Batch ID")
    ax.set_ylabel("Records")
    ax.legend()
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(figures / "streaming_batch_metrics.png", dpi=160)
    plt.close(fig)
    written.append(figures / "streaming_batch_metrics.png")

    advanced = load_json(results / "advanced_retrieval_results.json")
    systems = advanced["systems"]
    fig, ax = plt.subplots(figsize=(11, 5.5))
    x = range(len(systems))
    ax.bar([i - 0.2 for i in x], [row["precision_at_k"] for row in systems], width=0.4, label="Precision@10")
    ax.bar([i + 0.2 for i in x], [row["ndcg_at_k"] for row in systems], width=0.4, label="NDCG@10")
    ax.set_title("Retrieval Ablation Quality")
    ax.set_ylabel("Score")
    ax.set_xticks(list(x))
    ax.set_xticklabels([row["system"] for row in systems], rotation=35, ha="right")
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(figures / "retrieval_ablation.png", dpi=160)
    plt.close(fig)
    written.append(figures / "retrieval_ablation.png")

    ml = load_json(results / "ml_citation_prediction_report.json")
    matrix = ml["confusion_matrix"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    image = axes[0].imshow([[matrix["tn"], matrix["fp"]], [matrix["fn"], matrix["tp"]]], cmap="Blues")
    axes[0].set_title("Citation Prediction Confusion Matrix")
    axes[0].set_xticks([0, 1], ["Pred 0", "Pred 1"])
    axes[0].set_yticks([0, 1], ["True 0", "True 1"])
    for row_index, row in enumerate([[matrix["tn"], matrix["fp"]], [matrix["fn"], matrix["tp"]]]):
        for col_index, value in enumerate(row):
            axes[0].text(col_index, row_index, str(value), ha="center", va="center")
    fig.colorbar(image, ax=axes[0], fraction=0.046, pad=0.04)
    coeffs = ml["feature_coefficients"]
    axes[1].barh([row["feature"] for row in coeffs], [row["coefficient"] for row in coeffs], color="#E45756")
    axes[1].set_title("Logistic Regression Coefficients")
    axes[1].set_xlabel("Coefficient")
    axes[1].grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(figures / "ml_citation_prediction.png", dpi=160)
    plt.close(fig)
    written.append(figures / "ml_citation_prediction.png")

    ranking = load_json(results / "ranking_report.json")
    top_ranked = ranking["top_ranked_publications"][:10]
    fig, ax = plt.subplots(figsize=(10, 6))
    labels = [f"#{row['rank']} {row['title'][:35]}" for row in reversed(top_ranked)]
    ax.barh(labels, [row["composite_score"] for row in reversed(top_ranked)], color="#72B7B2")
    ax.set_title("Top Composite-Ranked Publications")
    ax.set_xlabel("Composite score")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(figures / "ranking_top_publications.png", dpi=160)
    plt.close(fig)
    written.append(figures / "ranking_top_publications.png")

    mart = load_json(results / "feature_mart_report.json")
    save_bar(
        figures / "feature_mart_availability.png",
        "Feature Mart Availability",
        ["Text", "Cluster", "ML prediction", "Ranking"],
        [
            mart["text_feature_availability"],
            mart["cluster_availability"],
            mart["ml_prediction_availability"],
            mart["ranking_availability"],
        ],
        "Availability rate",
    )
    written.append(figures / "feature_mart_availability.png")

    return written


def write_gallery(config: dict[str, Any], figures: list[Path]) -> Path:
    """Write a Markdown gallery for generated figures."""
    root = resolve_project_path(config, ".")
    gallery = root / "docs" / "VISUALIZATIONS.md"
    lines = [
        "# Visualizations",
        "",
        "Generated from measured SciGraph JSON/Parquet-derived report artifacts. No data in these charts is invented.",
        "",
    ]
    captions = {
        "dataset_publications_by_year.png": "Publication counts by year in the OpenAlex development sample.",
        "data_quality_checks.png": "Pass/warning/error counts from the data-quality checks.",
        "pipeline_stage_counts.png": "Rows written by Bronze, Silver, and Gold pipeline stages.",
        "text_top_terms.png": "Most frequent retained text terms after filtering.",
        "clustering_results.png": "K-means silhouette results and selected cluster sizes.",
        "citation_graph_summary.png": "Citation graph vertex and edge counts.",
        "author_collaboration_summary.png": "Author collaboration graph size and publication counts.",
        "temporal_yearly_metrics.png": "Publication counts and citation rates by year.",
        "streaming_batch_metrics.png": "Missing metadata counts in simulated streaming batches.",
        "retrieval_ablation.png": "Retrieval system precision and NDCG comparison.",
        "ml_citation_prediction.png": "Citation prediction confusion matrix and feature coefficients.",
        "ranking_top_publications.png": "Top publications by composite ranking score.",
        "feature_mart_availability.png": "Availability rates for integrated feature mart signals.",
    }
    for figure in figures:
        relative = Path("..") / "reports" / "figures" / figure.name
        lines.extend([f"## {figure.stem.replace('_', ' ').title()}", "", captions.get(figure.name, ""), "", f"![{figure.stem}]({relative.as_posix()})", ""])
    gallery.write_text("\n".join(lines), encoding="utf-8")
    return gallery


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/dev.yaml")
    args = parser.parse_args()
    config = load_config(Path(args.config))
    figures = generate_figures(config)
    gallery = write_gallery(config, figures)
    print(json.dumps({"figure_count": len(figures), "gallery": str(gallery)}, indent=2))


if __name__ == "__main__":
    main()
