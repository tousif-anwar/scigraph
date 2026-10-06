# SciGraph

Scalable scientific-literature intelligence using distributed text, graph, temporal, streaming, and retrieval analysis.

This repository is being built milestone by milestone for CS 660, with the initial focus on reproducible data acquisition and schema inspection. It is not a RAG application; later milestones will emphasize Spark data engineering, text analytics, graph analysis, temporal analysis, streaming, and retrieval experiments.

## Milestone Status

Milestone 1 created the repository foundation, configuration system, OpenAlex data acquisition workflow, schema inspection tooling, an initial data dictionary, and smoke tests.

Milestone 2 adds explicit data-quality checks and produces both machine-readable and human-readable reports without cleaning or dropping records.

Milestones 3 through 13 add the local Spark Bronze/Silver/Gold pipeline, scalability benchmarking, distributed TF-IDF text analysis, K-means clustering, citation graph analytics, author collaboration graph analytics, temporal trend analysis, streaming-style micro-batch monitoring, sparse retrieval experiments, a supervised citation-outcome baseline, and a transparent composite publication ranking.

## Dataset

The project uses [OpenAlex Works](https://help.openalex.org/api/) metadata. OpenAlex describes its API as a REST API over works, authors, sources, institutions, topics, and related entities, and states that its data is CC0. Work records may include `abstract_inverted_index`; OpenAlex documents that plaintext abstracts are not shipped directly and must be reconstructed from this inverted index when available.

The default development sample is intentionally small and configurable. Raw API responses are preserved under `data/raw/` and should not be modified.

## Quick Start

From this directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e . --no-deps
```

Acquire the development sample:

```powershell
python -m scigraph.ingestion.acquire_openalex --config configs/dev.yaml
```

Inspect the sample schema and regenerate the data dictionary:

```powershell
python -m scigraph.ingestion.inspect_schema --config configs/dev.yaml
```

Generate the data-quality report:

```powershell
python -m scigraph.preprocessing.quality --config configs/dev.yaml
```

Run the Spark Bronze/Silver/Gold pipeline:

```powershell
python -m scigraph.preprocessing.pipeline --config configs/dev.yaml
```

This command requires PySpark and a working Java runtime. If either is missing, it writes a blocked pipeline report instead of silently pretending the Spark stages ran.

Run smoke tests:

```powershell
python -m pytest
```

## Configuration

Configuration lives in `configs/`. The development config controls sample size, deterministic seed, API endpoint, selected OpenAlex fields, and local artifact paths. Change `dataset.sample_size` to adjust the development subset size.

## Current Environment Notes

During initial setup on 2026-10-05, Python was available as `python 3.14.4`. Java and Git were initially not available on PATH in this shell. Later milestones configured Spark to use the existing OpenJDK at `C:/Users/tousi/.jdks/openjdk-23.0.2`, added project-local Hadoop Windows helper binaries under `tools/hadoop/bin`, and added `C:\Program Files\Git\cmd` plus `C:\Windows\System32` to the user PATH so Git is available in new terminals.

The Milestone 1 development sample was retrieved on 2026-10-05. It contains 100 OpenAlex article records from publication years 2020-2026, with 100 unique publication IDs, 379 unique author IDs observed, 2,101 referenced works, 0 missing abstracts, 0 missing titles, 2 records with missing authorship arrays, and 0 duplicate publication IDs.

The Milestone 2 quality report ran 31 checks on the same sample. It found 0 error checks and 7 warning checks, including missing authorships, authorship entries without nested author IDs, empty reference arrays, one self-reference, missing DOIs, missing language metadata, and one missing primary source ID.

Milestone 3 adds the Spark Bronze/Silver/Gold pipeline implementation. In this environment PySpark 4.2.0 was installed successfully, but the configured `JAVA_HOME` did not contain a Java executable and `java` was not on PATH, so the Spark execution preflight wrote a blocked report instead of producing Parquet outputs.

Milestone 4 repaired the local Spark runtime by configuring the project to use the existing OpenJDK at `C:/Users/tousi/.jdks/openjdk-23.0.2` and project-local Hadoop Windows helper binaries under `tools/hadoop/bin`. Spark now writes Parquet locally. The dev benchmark measured 25, 50, and 100 record pipeline runs; the 100-record run completed in 3.3065 seconds at 30.2435 records/second.

Milestone 5 adds distributed text analytics over titles and reconstructed abstracts. After increasing the dev corpus to 1,000 OpenAlex records, the English-filtered text run analyzed 738 documents, retained 99,587 tokens, produced a 16,091-term vocabulary, and wrote document-term TF-IDF outputs.

Milestone 6 adds K-means text clustering over normalized TF-IDF features. It evaluated K = 3, 5, and 8 on the 738 English-language documents and selected K = 3 by silhouette, but the silhouette scores were weak and cluster balance remained uneven, so the clusters are treated as exploratory rather than validated research fields.

Milestone 7 adds citation graph analytics and iterative Spark PageRank. The 1,000-record sample produced 22,321 outgoing citation edges and 23,177 expanded graph vertices after including externally referenced OpenAlex work IDs. However, none of the sampled publications cite another sampled publication, so the in-sample citation edge count is 0. PageRank is therefore computed on the expanded citation graph, and sampled-paper PageRank values are tied/uninformative in the current sample.

Milestone 8 adds an undirected weighted author collaboration graph. The current sample contains 3,721 authors with usable author IDs, 3,726 author-publication rows across 948 publications, 709 multi-author publications, 239 solo-author publications, and 11,508 observed coauthor edges. Edge weights count shared sampled publications; in this heterogeneous development sample, the strongest observed edge weight is 1.

Milestone 9 adds temporal trend analysis. The 1,000-record sample spans publication years 2020-2026, with 7 yearly buckets, 2,477 topic-year rows, and 395 latest-year topic candidates. The latest sampled year is 2026; citation counts for recent publications are low because they have had less time to accumulate citations.

Milestone 10 adds deterministic streaming-style micro-batch monitoring over the Gold publication table. The current run replayed 1,000 records in 10 batches of 100 records, computed per-batch quality and citation/reference metrics, and produced 0 alerts using a missing-title threshold of 0.0 and a missing-author threshold of 0.05.

Milestone 11 adds a sparse TF-IDF retrieval baseline over the saved English-language text documents. Five fixed scientific queries produced 372 ranked query-document rows. Using OpenAlex topic-name substring matches as a rough relevance proxy, mean precision@10 was 0.32; the strongest query was tuberculosis diagnosis/treatment at precision@10 = 0.50.

Milestone 12 adds a Spark ML logistic-regression baseline for predicting whether a sampled paper is in the high-citation group. The high-citation threshold was `cited_by_count >= 4`, producing 264 positive labels and 736 negative labels. On the held-out test split, the model reached area under ROC 0.8559 and accuracy 0.7735, compared with a majority-class baseline accuracy of 0.7360.

Milestone 13 adds a transparent composite publication ranking. It ranked all 1,000 sampled publications using normalized citation count, citation PageRank, recency, reference count, author count, and topic count. The mean composite score was 0.1861 and the maximum score was 0.6401. In this sample, PageRank contributes little because sampled-paper PageRank is constant after Milestone 7's zero in-sample citation-edge result.

## Repository Layout

```text
scigraph/
├── configs/
├── data/
│   ├── raw/
│   ├── bronze/
│   ├── silver/
│   └── gold/
├── docs/
├── experiments/
├── notebooks/
├── reports/
├── src/scigraph/
└── tests/
```

## Reproducibility

The acquisition script records source metadata, retrieval date, request URL, sample size, and seed in `data/raw/openalex_sample_metadata.json`. The schema inspection script writes machine-readable statistics to `reports/results/schema_summary.json` and updates `docs/DATA_DICTIONARY.md` from observed fields only. The quality script writes `reports/results/data_quality_report.json` and `docs/DATA_QUALITY_REPORT.md`. The Spark pipeline writes `reports/results/bronze_silver_gold_report.json` and `docs/BRONZE_SILVER_GOLD_PIPELINE.md`.

Scalability benchmarks write `experiments/scalability/results/scalability_results.json`, `experiments/scalability/results/scalability_results.csv`, and `docs/SCALABILITY_BENCHMARKS.md`.

Text analysis writes `reports/results/text_analysis_report.json`, `docs/TEXT_ANALYSIS.md`, and Parquet outputs under `data/gold/text_*`.

Clustering writes `reports/results/clustering_report.json`, `docs/CLUSTERING.md`, and Parquet outputs under `data/gold/cluster_*`.

Citation graph analysis writes `reports/results/citation_graph_report.json`, `docs/CITATION_GRAPH.md`, and Parquet outputs under `data/gold/citation_*`.

Author collaboration analysis writes `reports/results/author_collaboration_report.json`, `docs/AUTHOR_COLLABORATION_GRAPH.md`, and Parquet outputs under `data/gold/author_collaboration_*`.

Temporal analysis writes `reports/results/temporal_analysis_report.json`, `docs/TEMPORAL_ANALYSIS.md`, and Parquet outputs under `data/gold/temporal_*`.

Streaming simulation writes `reports/results/streaming_simulation_report.json`, `docs/STREAMING_SIMULATION.md`, and Parquet outputs under `data/gold/streaming_*`.

Sparse retrieval writes `reports/results/retrieval_report.json`, `docs/RETRIEVAL.md`, and Parquet outputs under `data/gold/retrieval_*`.

Citation prediction writes `reports/results/ml_citation_prediction_report.json`, `docs/ML_CITATION_PREDICTION.md`, and Parquet outputs under `data/gold/ml_citation_*`.

Composite ranking writes `reports/results/ranking_report.json`, `docs/RANKING.md`, and Parquet outputs under `data/gold/ranking_*`.
