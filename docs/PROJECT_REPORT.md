# SciGraph Project Report

Generated on 2026-10-06.

## Executive Summary

SciGraph is a milestone-built scientific literature analytics project over OpenAlex Works metadata. The project is not a RAG application. It implements a reproducible Spark-based data pipeline and a set of distributed analytics experiments covering data quality, text analysis, clustering, citation graphs, author collaboration graphs, temporal trends, streaming-style monitoring, sparse retrieval, supervised ML, composite ranking, and an integrated publication feature mart.

The current development run uses 2,500 OpenAlex article records from publication years 2020-2026. Raw data is preserved, Silver and Gold analysis tables are produced as Parquet, each analytic stage writes machine-readable JSON plus human-readable Markdown reports, and the final visualization gallery includes 13 generated figures. The project currently has 57 passing tests.

Key measured outputs:

| Area | Result |
| --- | --- |
| Raw sample | 2,500 OpenAlex article records |
| Publication year range | 2020-2026 |
| Unique publications | 2,500 |
| Unique authors | 9,008 |
| Referenced works observed | 53,740 before self-citation removal |
| Gold citation edges | 53,704 |
| Text documents analyzed | 1,777 English-language documents |
| Text vocabulary | 26,884 retained terms |
| Clustering | K=3 selected, exploratory only |
| Citation graph | 2,500 sampled vertices, 53,704 edges, 1 in-sample citation edge |
| Author collaboration graph | 9,008 authors, 31,499 coauthor edges |
| Temporal analysis | 7 yearly buckets, 5,977 topic-year rows |
| Streaming simulation | 10 micro-batches, 2,500 records processed, 0 alerts |
| Retrieval ablation | BM25 precision@10 = 0.48; best NDCG@10 = 0.6188 with hybrid reranked graph-aware retrieval |
| Citation prediction | AUC = 0.9168, accuracy = 0.8298 |
| Composite ranking | 2,500 ranked publications, mean score = 0.1880 |
| Feature mart | 2,500 rows, 34 columns |
| Vector index | 1,777 documents, 20,000-vector vocabulary |
| Field-normalized citations | 2,500 rows, 166 field/year groups |
| Visualizations | 13 PNG figures generated from measured JSON/Parquet-derived reports |

## Project Objective

The project objective is to build scalable scientific literature intelligence over open scholarly metadata. The implemented system answers questions such as:

- What fields and quality issues exist in the raw literature metadata?
- Can nested OpenAlex data be normalized into analysis-ready Spark tables?
- What terms, topics, and clusters appear in the current corpus?
- What citation and collaboration graph signals are observable?
- How do publication and topic patterns vary over time?
- Can the project monitor incoming records in batch-like streaming windows?
- How well does sparse lexical retrieval work as a baseline?
- Can structured metadata predict high-citation labels within the sample?
- Can multiple signals be integrated into a single publication-level feature mart?

## Data Source

The project uses OpenAlex Works metadata. The development configuration retrieves article records with abstracts from 2020 onward. OpenAlex represents abstracts as `abstract_inverted_index`, so the project reconstructs plaintext abstracts during text processing rather than expecting raw abstract strings.

Current sample statistics:

| Metric | Value |
| --- | ---: |
| Records | 2,500 |
| Unique publications | 2,500 |
| Unique authors | 9,008 |
| Missing titles | 0 |
| Missing abstracts | 0 |
| Missing authorship arrays | 34 |
| Duplicate publication IDs | 0 |
| Publication year range | 2020-2026 |
| Document type | 2,500 articles |

Top broad concepts in the sample include Medicine, Computer science, Biology, Psychology, Political science, Physics, Engineering, Chemistry, Philosophy, Sociology, and Business. This confirms that the development sample is heterogeneous rather than field-specific.

## Environment and Runtime Work

The project was developed in a local Windows environment with Python 3.14.4 and PySpark 4.2.0. Early Spark execution was blocked because Java was not available on PATH. The project was repaired by configuring Spark to use:

- Existing OpenJDK: `C:/Users/tousi/.jdks/openjdk-23.0.2`
- Project-local Hadoop Windows helper binaries: `tools/hadoop/bin/winutils.exe` and `tools/hadoop/bin/hadoop.dll`

Git was also not initially reachable from this shell. The PATH was repaired by adding:

- `C:\Program Files\Git\cmd`
- `C:\Windows\System32`

After this repair, Git was verified as `git version 2.45.1.windows.1`.

## Architecture

The project follows a layered data layout:

```text
OpenAlex Works API
  -> raw JSONL sample in data/raw/
  -> schema inspection and data-quality reports
  -> Spark Bronze table
  -> Spark Silver publication table
  -> Spark Gold analysis tables
  -> text, graph, temporal, streaming, retrieval, ML, ranking, and feature-mart outputs
```

Core Gold tables:

| Table | Purpose |
| --- | --- |
| `data/gold/publications/` | One row per publication |
| `data/gold/authors/` | Deduplicated authors |
| `data/gold/author_publications/` | Authorship bridge table |
| `data/gold/citation_edges/` | Directed publication-to-reference edges |
| `data/gold/topics/` | Publication-topic rows |

Downstream outputs are stored under `data/gold/*` and documented in `docs/*.md`.

## Milestone Results

### Milestone 1: Repository, Acquisition, and Schema Inspection

Implemented:

- Repository skeleton.
- Configuration loading.
- OpenAlex API acquisition.
- Raw sample metadata capture.
- Schema inspection.
- Initial data dictionary.

Result:

- Current development sample contains 2,500 OpenAlex article records.
- Publication years span 2020-2026.
- All sampled records have publication IDs and titles.
- Raw data is preserved under `data/raw/`.

Main outputs:

- `data/raw/openalex_works_sample.jsonl`
- `data/raw/openalex_sample_metadata.json`
- `reports/results/schema_summary.json`
- `docs/DATA_DICTIONARY.md`

### Milestone 2: Data Quality

Implemented:

- Rule-based data quality checks over the raw sample.
- JSON and Markdown quality reports.
- Warning/error distinction without dropping records.

Result:

| Metric | Value |
| --- | ---: |
| Records checked | 2,500 |
| Total checks | 31 |
| Passed checks | 23 |
| Warning checks | 8 |
| Error checks | 0 |
| Records with any author | 2,466 |
| Records with any reference | 1,450 |

Interpretation:

The sample is usable for development. There are warnings around authorships, references, DOIs, language metadata, and source IDs, but no blocking quality errors.

Main outputs:

- `reports/results/data_quality_report.json`
- `docs/DATA_QUALITY_REPORT.md`

### Milestone 3: Bronze, Silver, and Gold Spark Pipeline

Implemented:

- Spark Bronze/Silver/Gold transformation pipeline.
- Explicit OpenAlex schema.
- Runtime preflight checks for PySpark, Java, and Windows Hadoop helpers.
- Gold tables for publications, authors, author-publication rows, citation edges, and topics.

Result:

| Stage | Rows |
| --- | ---: |
| Raw records | 2,500 |
| Bronze records | 2,500 |
| Silver publications | 2,500 |
| Gold publications | 2,500 |
| Gold authors | 9,008 |
| Gold author-publication rows | 9,058 |
| Gold citation edges | 53,704 |
| Gold topic rows | 7,443 |

Interpretation:

The Spark pipeline now runs locally and writes Parquet outputs. It removes self-citations from Gold citation edges and keeps quality flags available in publication rows.

Main outputs:

- `data/bronze/openalex_works/`
- `data/silver/publications/`
- `data/gold/publications/`
- `data/gold/authors/`
- `data/gold/author_publications/`
- `data/gold/citation_edges/`
- `data/gold/topics/`
- `reports/results/bronze_silver_gold_report.json`

### Milestone 4: Scalability Benchmarking

Implemented:

- Local Spark scalability benchmark runner.
- Isolated benchmark output directories.
- Runtime and throughput reporting.

Result:

- Benchmarked local Spark pipeline at development scales.
- The 100-record benchmark completed in 3.3065 seconds at 30.2435 records/second.
- Later configuration expanded benchmark scales to 500, 1,000, and 2,500 records.

Interpretation:

Tiny local runs are dominated by Spark startup and write overhead. The benchmark is useful for reproducibility and local runtime validation, not for large-corpus performance claims.

Main outputs:

- `experiments/scalability/results/scalability_results.json`
- `experiments/scalability/results/scalability_results.csv`
- `docs/SCALABILITY_BENCHMARKS.md`

### Milestone 5: Text Analysis and TF-IDF

Implemented:

- Abstract reconstruction from OpenAlex inverted indexes.
- English-filtered text document table.
- Tokenization, stop-word filtering, term frequency, document frequency, IDF, and TF-IDF.
- Global, yearly, and topic-level term outputs.

Result:

| Metric | Value |
| --- | ---: |
| Documents analyzed | 1,777 |
| Tokens retained | 236,429 |
| Vocabulary size | 26,884 |
| Document-term TF-IDF rows | Generated under `data/gold/text_tfidf_terms/` |

Top global terms include `data`, `patients`, `analysis`, `model`, `high`, and `development`.

Interpretation:

The text sample is broad and heterogeneous. Term statistics expose useful lexical signals, but top terms reflect mixed scientific domains rather than one coherent research area.

Main outputs:

- `data/gold/text_documents/`
- `data/gold/text_terms_global/`
- `data/gold/text_terms_by_year/`
- `data/gold/text_terms_by_topic/`
- `data/gold/text_tfidf_terms/`
- `reports/results/text_analysis_report.json`
- `docs/TEXT_ANALYSIS.md`

### Milestone 6: K-means Text Clustering

Implemented:

- Distributed K-means clustering over normalized TF-IDF features.
- Evaluation for K = 3, 5, and 8.
- Cluster terms and representative papers.

Result:

| Metric | Value |
| --- | ---: |
| Documents clustered | 1,777 |
| Selected K | 3 |
| K=3 silhouette | approximately -0.0062 |
| Cluster sizes | 267, 1,505, 5 |

Interpretation:

The clustering is exploratory only. Weak/negative silhouette scores and uneven cluster sizes mean the clusters should not be presented as validated scientific fields.

Main outputs:

- `data/gold/cluster_assignments/`
- `data/gold/cluster_terms/`
- `data/gold/cluster_representative_papers/`
- `reports/results/clustering_report.json`
- `docs/CLUSTERING.md`

### Milestone 7: Citation Graph and PageRank

Implemented:

- Citation degree metrics.
- Expanded citation graph including externally referenced OpenAlex work IDs.
- Iterative Spark PageRank with dangling-mass handling.
- PageRank and unusual PageRank-relative-to-degree outputs.

Result:

| Metric | Value |
| --- | ---: |
| Sample publication vertices | 2,500 |
| Expanded graph vertices | 55,704 |
| Full outgoing citation edges | 53,704 |
| In-sample citation edges | 1 |
| External citation edges | 53,703 |
| PageRank iterations | 10 |

Interpretation:

This milestone produced an important sampling result: only one sampled publication cites another sampled publication. PageRank can be computed on the expanded graph, but sampled-paper PageRank remains weak for ranking sampled papers in the current sample.

Main outputs:

- `data/gold/citation_degrees/`
- `data/gold/citation_pagerank/`
- `data/gold/citation_unusual_pagerank/`
- `reports/results/citation_graph_report.json`
- `docs/CITATION_GRAPH.md`

### Milestone 8: Author Collaboration Graph

Implemented:

- Undirected weighted coauthor graph.
- Edge weights as shared sampled publications.
- Author-level publication and collaborator metrics.

Result:

| Metric | Value |
| --- | ---: |
| Authors | 9,008 |
| Author-publication rows | 9,020 |
| Publications represented | 2,367 |
| Multi-author publications | 1,729 |
| Solo-author publications | 638 |
| Collaboration edges | 31,499 |
| Strongest observed edge weight | 1 |

Interpretation:

The author collaboration graph captures observed sample coauthorship. Most pairwise collaborations occur only once in this sample, so this is not a complete career-level collaboration network.

Main outputs:

- `data/gold/author_collaboration_edges/`
- `data/gold/author_collaboration_metrics/`
- `reports/results/author_collaboration_report.json`
- `docs/AUTHOR_COLLABORATION_GRAPH.md`

### Milestone 9: Temporal Trend Analysis

Implemented:

- Yearly publication and citation aggregates.
- Topic-year trend table.
- Latest-year topic growth candidates.

Result:

| Metric | Value |
| --- | ---: |
| Publication year range | 2020-2026 |
| Publications with valid years | 2,500 |
| Year buckets | 7 |
| Topic-year rows | 5,977 |
| Largest sampled year | 2025 with 423 publications |

Interpretation:

Temporal aggregation works and exposes publication-year and topic-year patterns. Citation counts are much lower for recent papers, especially 2026, because newer papers have had less time to collect citations.

Main outputs:

- `data/gold/temporal_yearly_metrics/`
- `data/gold/temporal_topic_trends/`
- `data/gold/temporal_emerging_topics/`
- `reports/results/temporal_analysis_report.json`
- `docs/TEMPORAL_ANALYSIS.md`

### Milestone 10: Streaming-Style Micro-Batch Monitoring

Implemented:

- Deterministic replay of Gold publication rows as micro-batches.
- Per-batch monitoring metrics.
- Missing-title and missing-author alert generation.

Result:

| Metric | Value |
| --- | ---: |
| Batch size | 250 |
| Batch count | 10 |
| Records processed | 2,500 |
| Alert count | 0 |
| Missing-title threshold | 0.0 |
| Missing-author threshold | 0.05 |

Interpretation:

The monitoring logic works and produces stable per-batch metrics. This is a deterministic replay simulation, not a production live stream with event-time disorder, retry handling, checkpoint recovery, or broker integration.

Main outputs:

- `data/gold/streaming_batch_metrics/`
- `data/gold/streaming_alerts/`
- `reports/results/streaming_simulation_report.json`
- `docs/STREAMING_SIMULATION.md`

### Milestone 11: Sparse Retrieval Baseline

Implemented:

- Fixed scientific query set.
- Sparse TF-IDF query-document scoring.
- Approximate topic-label relevance evaluation.

Result:

| Query | Precision@10 |
| --- | ---: |
| Artificial intelligence healthcare education | See `docs/RETRIEVAL.md` |
| Climate change policy economics | See `docs/RETRIEVAL.md` |
| Dementia cognitive impairment | See `docs/RETRIEVAL.md` |
| Digital marketing social media | See `docs/RETRIEVAL.md` |
| Tuberculosis diagnosis treatment | See `docs/RETRIEVAL.md` |
| Mean precision@10 | 0.38 |

Other metrics:

- Queries evaluated: 5
- Top K: 10
- Ranking rows: 886

Interpretation:

Sparse retrieval is a useful lexical baseline. It performs better on narrow, distinctive terminology such as tuberculosis and worse on broader terms such as climate and policy. Relevance labels are approximate topic-name substring matches, not human judgments.

Main outputs:

- `data/gold/retrieval_rankings/`
- `data/gold/retrieval_evaluation/`
- `reports/results/retrieval_report.json`
- `docs/RETRIEVAL.md`

### Milestone 12: Citation Outcome Prediction

Implemented:

- Spark ML feature assembly.
- Logistic regression baseline.
- Held-out train/test evaluation.
- Confusion matrix and coefficient report.

Features:

- Publication year index
- Reference count
- Author count
- Concept count
- Topic count
- Abstract availability

Result:

| Metric | Value |
| --- | ---: |
| Records | 2,500 |
| High-citation threshold | `cited_by_count >= 4` |
| Positive labels | 634 |
| Negative labels | 1,866 |
| Train rows | 1,783 |
| Test rows | 717 |
| Area under ROC | 0.9168 |
| Accuracy | 0.8298 |
| Majority baseline accuracy | 0.7464 |
| True positives | 73 |
| False positives | 21 |
| True negatives | 522 |
| False negatives | 101 |

Interpretation:

The model has useful ranking signal, but the accuracy improvement over the majority baseline is modest. It is conservative and misses many high-citation positives. The negative publication-year coefficient is consistent with recency effects: newer papers have had less time to accumulate citations.

Main outputs:

- `data/gold/ml_citation_features/`
- `data/gold/ml_citation_predictions/`
- `reports/results/ml_citation_prediction_report.json`
- `docs/ML_CITATION_PREDICTION.md`

### Milestone 13: Composite Publication Ranking

Implemented:

- Transparent weighted ranking of publications.
- Min-max normalized component scores.
- Weighted combination of citation count, PageRank, recency, reference count, author count, and topic count.

Weights:

| Component | Weight |
| --- | ---: |
| Citation count | 0.45 |
| PageRank | 0.15 |
| Recency | 0.15 |
| Reference count | 0.10 |
| Author count | 0.05 |
| Topic count | 0.10 |

Result:

| Metric | Value |
| --- | ---: |
| Ranked publications | 2,500 |
| Top N reported | 25 |
| Mean composite score | 0.1880 |
| Maximum composite score | 0.6327 |

Top-ranked paper:

- "The Pantheon+ Analysis: The Full Data Set and Light-curve Release"
- Publication year: 2022
- `cited_by_count`: 945
- Composite score: 0.6327

Interpretation:

The ranking is inspectable and reproducible, but not an authority score. Citation count and reference count dominate the top results. PageRank contributes little because sampled-paper PageRank is tied in the current sample.

Main outputs:

- `data/gold/ranking_publications/`
- `reports/results/ranking_report.json`
- `docs/RANKING.md`

### Milestone 14: Integrated Publication Feature Mart

Implemented:

- One-row-per-publication feature mart.
- Left joins from Gold publications to text, clustering, graph, temporal, ML, and ranking outputs.
- Feature availability flags.

Result:

| Metric | Value |
| --- | ---: |
| Publication rows | 2,500 |
| Feature columns | 34 |
| Text feature rows | 1,777 |
| Cluster rows | 1,777 |
| ML prediction rows | 717 |
| Ranking rows | 2,500 |
| Text feature availability | 0.7108 |
| Cluster availability | 0.7108 |
| ML prediction availability | 0.2868 |
| Ranking availability | 1.0000 |
| Average document word count | 155.1912 |

Interpretation:

The feature mart gives the project a single downstream table for inspection and later modeling. Sparse availability is expected because text and clustering are English-filtered, while ML predictions exist only for the held-out test split.

Main outputs:

- `data/gold/feature_publication_mart/`
- `reports/results/feature_mart_report.json`
- `docs/FEATURE_MART.md`

### Milestones 15-18: Advanced Retrieval, Ablation, Error Analysis, Demo, And Final Audit

Implemented:

- BM25 lexical retrieval baseline.
- Spark ML Word2Vec dense retrieval.
- Reciprocal Rank Fusion hybrid retrieval.
- Transparent second-stage reranking.
- Graph-aware ranking that blends retrieval and composite publication scores.
- Shared ablation table over the same query set.
- Error analysis.
- Demo query artifact for `retrieval augmented generation for clinical decision support`.
- Final report and reproducibility audit.

Result:

| System | Precision@10 | Recall@10 | MRR | NDCG@10 | Mean latency seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| BM25 | 0.4800 | 0.3120 | 0.8667 | 0.6203 | 0.0626 |
| Dense Word2Vec | 0.2800 | 0.1664 | 0.6400 | 0.3284 | 17.7123 |
| Hybrid RRF | 0.4400 | 0.3062 | 0.7667 | 0.5010 | 0.0000 |
| Hybrid + reranker | 0.4400 | 0.2696 | 0.9000 | 0.5918 | 0.0015 |
| Hybrid + reranker + graph | 0.4400 | 0.2696 | 0.9000 | 0.5918 | 0.0000 |

Interpretation:

BM25 remained a strong baseline. Dense retrieval with a small locally trained Word2Vec model was substantially weaker and slower. Hybrid RRF alone did not improve quality. Transparent reranking improved NDCG, and graph-aware blending produced the best NDCG@10, but the gain was modest. These results are useful because they show that additional components do not automatically improve retrieval quality.

Optional RAG was not implemented. This is intentional: the assignment warned not to add an LLM merely to make the project appear more AI-focused, and the retrieval/analytics system already supports the core course objectives.

Main outputs:

- `reports/results/advanced_retrieval_results.json`
- `reports/results/demo_results.json`
- `docs/ADVANCED_RETRIEVAL.md`
- `docs/ERROR_ANALYSIS.md`
- `docs/DEMO.md`

### Extension Pass: Vector Index, Normalized Citations, File Arrival, Dashboard

Implemented:

- A vector-style nearest-neighbor index over paper titles and reconstructed abstracts.
- Field/year-normalized citation features using OpenAlex topic fields and publication year.
- A file-arrival monitor directory for incoming OpenAlex JSONL files.
- A lightweight static HTML dashboard generated from measured reports and figures.

Result:

| Artifact | Result |
| --- | ---: |
| Vector-index backend | scikit-learn TF-IDF fallback |
| Vector-index documents | 1,777 |
| Vector-index vocabulary | 20,000 |
| Field-normalized citation rows | 2,500 |
| Topic fields | 25 |
| Field/year groups | 166 |
| File-arrival input files | 0 |
| Dashboard | `docs/dashboard/index.html` |

Interpretation:

The extension pass adds practical next-layer artifacts without changing the project's non-RAG scope. FAISS or Chroma can be installed later and wired behind the same vector-index output contract; the current fallback is portable and reproducible in this local environment. The file-arrival monitor is ready for dropped JSONL batches and documents the Structured Streaming path.

Main outputs:

- `data/gold/vector_index/`
- `data/gold/citation_field_normalized/`
- `data/streaming/file_arrivals/`
- `reports/results/vector_index_report.json`
- `reports/results/citation_field_normalized_report.json`
- `reports/results/streaming_file_arrival_report.json`
- `docs/VECTOR_INDEX.md`
- `docs/FIELD_NORMALIZED_CITATIONS.md`
- `docs/STREAMING_FILE_ARRIVAL.md`
- `docs/dashboard/index.html`

### Final Visualization Layer

Implemented:

- Static figure generation from measured report JSON outputs.
- A Markdown visualization gallery covering dataset, quality, pipeline, text, clustering, graph, temporal, streaming, retrieval, ML, ranking, and feature mart results.
- Focused tests for the visualization module.

Result:

| Metric | Value |
| --- | ---: |
| Figures generated | 13 |
| Gallery file | `docs/VISUALIZATIONS.md` |
| Figure directory | `reports/figures/` |

Main outputs:

- `docs/VISUALIZATIONS.md`
- `notebooks/scigraph_visual_summary.ipynb`
- `reports/tables/milestone_summary.csv`
- `reports/tables/retrieval_ablation_summary.csv`
- `reports/figures/dataset_publications_by_year.png`
- `reports/figures/data_quality_checks.png`
- `reports/figures/pipeline_stage_counts.png`
- `reports/figures/text_top_terms.png`
- `reports/figures/clustering_results.png`
- `reports/figures/citation_graph_summary.png`
- `reports/figures/author_collaboration_summary.png`
- `reports/figures/temporal_yearly_metrics.png`
- `reports/figures/streaming_batch_metrics.png`
- `reports/figures/retrieval_ablation.png`
- `reports/figures/ml_citation_prediction.png`
- `reports/figures/ranking_top_publications.png`
- `reports/figures/feature_mart_availability.png`

## Key Findings

1. The current sample is broad and heterogeneous.
   The sample spans many fields and concepts, so text and clustering outputs should be interpreted as mixed-corpus exploratory artifacts.

2. Spark execution is working locally.
   Java and Hadoop helper issues were repaired, and Spark now writes Bronze, Silver, Gold, and downstream Parquet outputs.

3. Text analytics are productive but English-filtered.
   Text analysis and clustering cover 1,777 of 2,500 publications. This is intentional but means text-derived outputs are sparse in full publication-level tables.

4. K-means clustering is weak.
   The selected K=3 model has weak/negative silhouette and uneven clusters. It should not be used as proof of meaningful research-field discovery.

5. The citation graph exposed a sampling limitation.
   There are 53,704 outgoing citation edges, but only 1 in-sample citation edge. PageRank is computable on an expanded graph but remains weak for ranking sampled papers.

6. Author collaboration captures coauthorship snapshots.
   The graph has 31,499 coauthor edges. Edge weights are sample-local and should not be treated as complete career-level collaboration history.

7. Recency strongly affects citations.
   Recent years, especially 2026, show low citations per publication. Citation-based ranking and prediction should not be interpreted as scientific quality.

8. BM25 remained the strongest simple retrieval baseline.
   Dense Word2Vec retrieval underperformed BM25 on the shared proxy relevance evaluation, and hybrid RRF alone did not help.

9. Reranking and graph-aware ranking helped modestly.
   The best NDCG@10 came from hybrid reranking plus graph-aware blending, but the gain over BM25 was small.

10. Supervised ML has signal but modest practical improvement.
   The citation prediction model achieved AUC 0.9168 on the refreshed development run, but it should still be treated as an exploratory baseline.

11. The feature mart is the best current downstream artifact.
   It integrates 34 publication-level columns for all 2,500 rows and makes sparse feature availability explicit.

12. The visualization gallery makes the full pipeline inspectable.
   The figures are regenerated from measured report outputs rather than hand-entered values.

13. The extension pass adds the requested production-facing artifacts.
   The project now includes a vector-style abstract index over 1,777 documents, field/year-normalized citation metrics for 2,500 publications, a file-arrival monitor, and a lightweight static dashboard.

## Reproducibility

From the project directory:

```powershell
python -m scigraph.ingestion.acquire_openalex --config configs/dev.yaml
python -m scigraph.ingestion.inspect_schema --config configs/dev.yaml
python -m scigraph.preprocessing.quality --config configs/dev.yaml
python -m scigraph.preprocessing.pipeline --config configs/dev.yaml
python -m scigraph.text.tfidf --config configs/dev.yaml
python -m scigraph.text.clustering --config configs/dev.yaml
python -m scigraph.graph.citation_graph --config configs/dev.yaml
python -m scigraph.graph.author_collaboration --config configs/dev.yaml
python -m scigraph.temporal.trends --config configs/dev.yaml
python -m scigraph.streaming.microbatch --config configs/dev.yaml
python -m scigraph.retrieval.sparse --config configs/dev.yaml
python -m scigraph.retrieval.advanced --config configs/dev.yaml
python -m scigraph.evaluation.citation_prediction --config configs/dev.yaml
python -m scigraph.ranking.composite --config configs/dev.yaml
python -m scigraph.features.publication_mart --config configs/dev.yaml
python -m scigraph.evaluation.field_normalized_citations --config configs/dev.yaml
python -m scigraph.retrieval.vector_index --config configs/dev.yaml
python -m scigraph.streaming.file_arrival --config configs/dev.yaml
python -m scigraph.visualization.figures --config configs/dev.yaml
python -m scigraph.dashboard.static --config configs/dev.yaml
python -m pytest
```

Latest verification:

- `.\scripts\run_pipeline.ps1 -Config configs\dev.yaml` completed on 2026-10-06 in 13 minutes 26 seconds.
- `python -m pytest` passed with 57 tests.

## Current Limitations

- The development sample is small and is not representative of the full OpenAlex corpus.
- OpenAlex API sampling can change as the live corpus changes.
- The sample is heterogeneous, which weakens clustering and topic interpretation.
- Text analysis and clustering are English-filtered.
- Data-quality checks report issues but do not clean, repair, or quarantine records.
- Citation PageRank is only weakly useful for sampled-paper ranking because the sample has 1 internal citation edge.
- Author collaboration is sample-local and does not represent complete career-level collaboration histories.
- Temporal citation metrics are affected by recency and unequal citation windows.
- Streaming is covered by deterministic micro-batch replay and a bounded file-arrival monitor, not a live broker-based streaming system.
- Retrieval evaluation uses approximate topic-name relevance labels, not human judgments.
- Dense retrieval uses a local Word2Vec model rather than a large pretrained scientific embedding model.
- Optional RAG is not implemented; the project remains focused on scalable analytics and retrieval evaluation.
- Citation prediction is not causal and does not predict scientific quality.
- Composite ranking uses manual weights and sample-local normalization.
- The vector index uses the portable scikit-learn TF-IDF fallback in this environment because FAISS and Chroma are not installed.
- The feature mart inherits all upstream limitations.

## Recommended Next Steps

1. Acquire a larger and more coherent sample.
   A field-constrained or citation-neighborhood crawl would improve citation graph and clustering validity.

2. Add citation-neighborhood expansion.
   Fetch metadata for referenced works so PageRank nodes have title/year/topic metadata.

3. Replace the fallback vector backend with Chroma or FAISS.
   The index contract is in place; installing one of those backends would make the retrieval layer closer to a production vector database.

4. Improve clustering.
   Try field-specific subsets, larger samples, better text filtering, and possibly embeddings once the non-LLM baseline is complete.

5. Add human or semi-structured relevance judgments for retrieval.
   Current retrieval evaluation uses approximate OpenAlex topic-name matching.

6. Promote file-arrival monitoring to a long-running Structured Streaming job.
   The configured input and checkpoint paths are in place; a long-running stream would test checkpointing, event-time behavior, late data, and recovery.

7. Add human relevance judgments for retrieval and rerun the ablation.
   This would make BM25/dense/hybrid/reranker conclusions much stronger.

8. Add dashboard filtering and drill-down.
   The current dashboard is static HTML generated from measured reports; interactive filtering would make it easier to inspect fields, years, and retrieval systems.

## Final Status

The project now contains a complete, reproducible, multi-stage scientific literature analytics pipeline over a 2,500-record OpenAlex development sample. It includes data engineering, data quality, text analytics, graph analytics, temporal analysis, monitoring, retrieval, machine learning, ranking, integrated feature production, vector indexing, field-normalized citation metrics, a file-arrival monitor, and a final dashboard plus visualization gallery.

The strongest current deliverable is not any single model score. It is the full reproducible pipeline and the honest documentation of what the sample can and cannot support.
