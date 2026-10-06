# Architecture

Milestones 1 through 3 establish the project skeleton, data acquisition path, schema inspection, raw data-quality reporting, and Spark Bronze/Silver/Gold pipeline implementation.

```text
OpenAlex Works API
  -> raw JSONL sample in data/raw/
  -> schema inspection
  -> reports/results/schema_summary.json
  -> docs/DATA_DICTIONARY.md
  -> data-quality checks
  -> reports/results/data_quality_report.json
  -> docs/DATA_QUALITY_REPORT.md
  -> Spark Bronze table: data/bronze/openalex_works/
  -> Spark Silver table: data/silver/publications/
  -> Spark Gold tables:
       data/gold/publications/
       data/gold/authors/
       data/gold/author_publications/
       data/gold/citation_edges/
       data/gold/topics/
```

Later milestones will add scalability benchmarks, text analytics, graph analytics, temporal analysis, streaming, and retrieval.

Milestone 4 adds measured preprocessing benchmarks under `experiments/scalability/` and documents the local Windows Spark runtime requirements.

Milestone 5 adds distributed text analytics outputs under `data/gold/text_*`, with reports in `reports/results/text_analysis_report.json` and `docs/TEXT_ANALYSIS.md`.

Milestone 6 adds K-means clustering outputs under `data/gold/cluster_*`, with reports in `reports/results/clustering_report.json` and `docs/CLUSTERING.md`.

Milestone 7 adds citation graph analytics. Gold citation edges feed degree computation and iterative Spark PageRank, with outputs under:

```text
data/gold/citation_degrees/
data/gold/citation_pagerank/
data/gold/citation_unusual_pagerank/
reports/results/citation_graph_report.json
docs/CITATION_GRAPH.md
```

The current PageRank job runs on an expanded graph containing sampled publications plus externally referenced OpenAlex work IDs, because the 1,000-record sample has no citation edges between sampled publications.

Milestone 8 adds author collaboration graph analytics. Gold author-publication rows feed an undirected weighted coauthor graph, with outputs under:

```text
data/gold/author_collaboration_edges/
data/gold/author_collaboration_metrics/
reports/results/author_collaboration_report.json
docs/AUTHOR_COLLABORATION_GRAPH.md
```

Collaboration edge weight is the number of sampled publications shared by an author pair. Author metrics combine publication counts, solo-publication counts, collaborator counts, and weighted collaboration counts.

Milestone 9 adds temporal trend analysis. Gold publications and topics feed yearly publication/citation aggregates and topic-year trend tables, with outputs under:

```text
data/gold/temporal_yearly_metrics/
data/gold/temporal_topic_trends/
data/gold/temporal_emerging_topics/
reports/results/temporal_analysis_report.json
docs/TEMPORAL_ANALYSIS.md
```

Temporal outputs are descriptive aggregates over the current sample. They are not full-corpus time-series estimates.

Milestone 10 adds deterministic streaming-style micro-batch monitoring. Gold publications are replayed in fixed-size batches to produce monitoring metrics and alert outputs under:

```text
data/gold/streaming_batch_metrics/
data/gold/streaming_alerts/
reports/results/streaming_simulation_report.json
docs/STREAMING_SIMULATION.md
```

This stage validates batch-level monitoring logic without requiring an external broker or long-running streaming service.

Milestone 11 adds sparse retrieval experiments. Saved text documents, document-term TF-IDF rows, and Gold topics feed query-document rankings and approximate topic-proxy evaluation outputs under:

```text
data/gold/retrieval_rankings/
data/gold/retrieval_evaluation/
reports/results/retrieval_report.json
docs/RETRIEVAL.md
```

The retrieval stage is a lexical baseline. It does not perform semantic embedding search or generated-answer RAG.

Milestone 12 adds a supervised citation-outcome baseline. Gold publications feed Spark ML feature assembly, logistic-regression training, held-out prediction, and evaluation outputs under:

```text
data/gold/ml_citation_features/
data/gold/ml_citation_predictions/
reports/results/ml_citation_prediction_report.json
docs/ML_CITATION_PREDICTION.md
```

This stage is a diagnostic ML baseline for citation-count labels within the current sample, not a causal model of scientific quality.
