# Building SciGraph: A Reproducible Literature Analytics Pipeline With Spark

Scientific literature data is rich, messy, and deeply connected. A single paper can include nested author records, journal metadata, concepts, topics, references, citation counts, abstracts, and open-access signals. SciGraph was built to turn that kind of raw metadata into something easier to inspect, analyze, search, and explain.

The project uses OpenAlex Works metadata and focuses on scalable data engineering rather than a narrow chatbot or one-off notebook. The result is a reproducible pipeline that moves from raw JSON records to Spark tables, quality reports, text analytics, graph analysis, retrieval experiments, machine learning, ranking, a feature mart, visualizations, and a guided notebook.

The completed development run uses 2,500 OpenAlex article records from publication years 2020 through 2026. A larger production acquisition is also supported through cursor-based OpenAlex paging, but the results described here come from the completed 2,500-record run.

## Why This Project Exists

Scholarly search and analysis often fail for a simple reason: the data behind the interface is not organized well enough. Before semantic search, graph ranking, or dashboards can be useful, the project needs a trustworthy data foundation.

SciGraph answers a practical question:

How far can we get by building a transparent, reproducible literature intelligence pipeline over open scholarly metadata?

The project deliberately avoids treating an LLM as the main product. Instead, it builds the pieces that make scientific literature analysis inspectable:

- Raw acquisition with source metadata
- Schema inspection and data-quality checks
- Spark Bronze, Silver, and Gold tables
- Text features from reconstructed abstracts
- Citation and author collaboration graphs
- Temporal trend analysis
- Streaming-style monitoring
- Sparse, dense, hybrid, and graph-aware retrieval comparisons
- A supervised citation-outcome baseline
- A transparent composite ranking
- A publication-level feature mart
- A visualization gallery and review notebook

## Data Source

SciGraph uses the OpenAlex Works API. The development configuration retrieves article records with abstracts, starting from 2020. OpenAlex stores many abstracts as inverted indexes rather than direct text strings, so the project reconstructs readable abstracts before text analysis.

The completed run produced:

| Metric | Value |
| --- | ---: |
| OpenAlex article records | 2,500 |
| Publication year range | 2020-2026 |
| Unique authors | 9,274 |
| Referenced works observed | 53,900 |
| Gold citation edges | 53,877 |
| Gold topic rows | 6,853 |

The sample is intentionally broad. It includes records across medicine, computer science, biology, psychology, political science, physics, engineering, chemistry, philosophy, sociology, business, and other fields. That breadth is useful for testing the pipeline, but it also creates limits for cluster interpretation.

## Pipeline Architecture

The core design follows a layered data architecture:

1. Raw OpenAlex JSONL records are preserved under `data/raw/`.
2. Spark writes a Bronze table that keeps nested metadata.
3. Silver normalizes publication-level columns and quality flags.
4. Gold creates analysis tables for publications, authors, author-publication links, citation edges, and topics.
5. Downstream modules write analysis outputs under `data/gold/`, `reports/results/`, and `docs/`.

This layout keeps the project reproducible. Each milestone writes machine-readable JSON and human-readable Markdown. The final visualization step reads those measured outputs and produces figures under `reports/figures/`.

## Data Quality Results

The data-quality stage ran 31 checks on the current sample. It found no error checks and 8 warning checks.

The warnings are normal for scholarly metadata. Some records have missing authorship arrays, missing DOI values, missing language metadata, empty reference arrays, or incomplete source information. SciGraph reports these issues without deleting records. That makes the quality layer auditable instead of silently changing the dataset.

The key outcome is simple: the sample is usable for development, but downstream analysis needs to respect known gaps.

## Spark Bronze, Silver, And Gold Outputs

The Spark pipeline successfully processed all 2,500 records.

| Table or signal | Count |
| --- | ---: |
| Bronze records | 2,500 |
| Silver publications | 2,500 |
| Gold publications | 2,500 |
| Gold authors | 9,274 |
| Gold author-publication rows | 9,337 |
| Gold citation edges | 53,877 |
| Gold topic rows | 6,853 |

This is the foundation for every later milestone. The project no longer depends on repeatedly parsing raw JSON for each experiment.

## Text Analysis And Clustering

Text analysis reconstructs paper abstracts, filters to English-language documents, tokenizes text, removes stop words and short tokens, and computes TF-IDF-style outputs.

The larger run analyzed:

- 1,793 English-language documents
- 236,607 retained tokens
- 26,728 retained vocabulary terms

The most frequent terms reflect a mixed scientific corpus rather than one field. That matters because a heterogeneous sample can make clustering harder.

K-means clustering evaluated several values of K and selected K = 5. The result is useful as an exploratory signal, but not as proof of clean research fields. The final report is careful about this point: clustering is an analysis artifact, not a validated taxonomy.

## Citation Graph Findings

The citation graph produced one of the most important negative results in the project.

The sample contains 53,877 outgoing citation edges, but the sampled publications do not cite each other inside the sample. The in-sample citation edge count is 0.

That does not mean citation analysis failed. It means the sampling strategy does not create a dense citation neighborhood. PageRank can still run on the expanded graph that includes externally referenced works, but sampled-paper PageRank is not very useful for ranking the sampled publications.

This is exactly the kind of finding a good data project should surface. The system explains what the data can support instead of overstating a graph metric.

## Author Collaboration Graph

The author collaboration graph is more informative because coauthorship information exists directly in the sampled records.

The completed run found:

- 9,274 authors
- 9,337 author-publication rows
- 1,773 multi-author publications
- 33,104 coauthor edges

Edges are undirected and weighted by shared sampled publications. The graph should not be interpreted as a complete career-level collaboration network, but it gives a useful view into observed collaboration patterns inside the sample.

## Temporal Analysis And Streaming Simulation

Temporal analysis grouped publications by year and topic. The sample spans 2020 through 2026 and produced 5,566 topic-year rows.

The newest year, 2026, has naturally low citation counts because those publications have had less time to collect citations. The project calls out this recency effect because it affects ranking and citation prediction.

The streaming milestone simulates deterministic micro-batches over the Gold publication table. In the larger run, the project replayed 2,500 records in 10 batches of 250 records and produced 0 alerts. This is not a live broker-based streaming system, but it proves that the monitoring logic works over batch-like windows.

## Retrieval Experiments

SciGraph compares several retrieval systems over the same five-query evaluation set:

- BM25 lexical retrieval
- Dense retrieval using Spark Word2Vec
- Reciprocal Rank Fusion
- Transparent reranking
- Graph-aware reranking

The evaluation uses OpenAlex topic-name matching as a proxy relevance signal, so the scores should be interpreted as approximate.

| System | Precision@10 | Recall@10 | MRR | NDCG@10 |
| --- | ---: | ---: | ---: | ---: |
| BM25 | 0.48 | 0.37 | 0.62 | 0.54 |
| Dense Word2Vec | 0.18 | 0.08 | 0.41 | 0.20 |
| Hybrid RRF | 0.36 | 0.24 | 0.73 | 0.43 |
| Hybrid plus reranker | 0.44 | 0.32 | 0.72 | 0.57 |
| Hybrid plus reranker plus graph | 0.46 | 0.37 | 0.77 | 0.62 |

The strongest NDCG@10 came from the hybrid reranked graph-aware system. BM25 remained a strong baseline, and dense Word2Vec retrieval performed worse. That is a useful result because it shows that adding a dense component does not automatically improve retrieval quality.

## Citation Prediction And Ranking

The supervised ML milestone trains a Spark logistic-regression model to predict whether a paper belongs to a high-citation group. The model uses structured features such as publication year, reference count, author count, concept count, topic count, and abstract availability.

The completed run achieved:

- AUC: 0.9174
- Accuracy: 0.8494

The model has signal, but it should not be interpreted as a measure of scientific quality. Citation outcomes are affected by field, age, visibility, and many other factors.

The ranking milestone builds a transparent composite score using normalized citation count, PageRank, recency, reference count, author count, and topic count. All 2,500 sampled publications receive a rank. Because in-sample PageRank is not informative in this sample, citation count and other structured features carry more of the ranking signal.

## Feature Mart And Review Artifacts

The integrated feature mart is one of the strongest outputs of the project. It preserves all 2,500 publication rows and joins 34 publication-level columns from earlier milestones.

Feature availability is explicit:

- Text features are available for 71.72% of rows
- Ranking features are available for 100% of rows
- The mart keeps sparse downstream signals visible instead of hiding missingness

The project also includes review-friendly artifacts:

- `docs/PROJECT_REPORT.md`
- `docs/VISUALIZATIONS.md`
- `reports/tables/milestone_summary.csv`
- `reports/tables/retrieval_ablation_summary.csv`
- `notebooks/scigraph_visual_summary.ipynb`
- `deliverables/SciGraph_Project_Presentation_v2.pptx`

## What Worked Well

Several parts of the project came together cleanly:

- Spark now runs locally with configured Java and Hadoop helper binaries.
- The pipeline writes reproducible Parquet, JSON, Markdown, CSV, and PNG artifacts.
- Text analytics and retrieval operate over reconstructed OpenAlex abstracts.
- Author collaboration analysis gives a meaningful graph signal.
- The retrieval ablation shows concrete tradeoffs between lexical, dense, hybrid, reranked, and graph-aware methods.
- The final notebook gives a simple path for reviewing the whole project.

## Current Limitations

The project is honest about its limits:

- The sample is broad and heterogeneous.
- Clusters should be treated as exploratory.
- Citation PageRank has limited value because there are no in-sample citation edges.
- Retrieval relevance uses proxy labels rather than human judgments.
- Streaming is simulated over static records.
- Dense retrieval uses a local Word2Vec model rather than a pretrained scientific embedding model.
- The production-scale acquisition is supported, but full production processing will require more time and compute.

These limitations do not weaken the project. They make the results more credible because the system states what the data can and cannot support.

## Next Steps

The most useful next extension would be a field-specific or citation-neighborhood sample. That would make citation graph analysis and clustering more meaningful.

Other strong extensions include:

- Add human relevance judgments for retrieval evaluation
- Build a FAISS or Chroma vector index over paper abstracts
- Add field-normalized citation metrics
- Convert the notebook into a lightweight dashboard
- Connect the streaming monitor to file-arrival or Structured Streaming inputs

## Final Takeaway

SciGraph is not just a set of models. It is a reproducible scientific-literature analytics system. It starts with raw OpenAlex metadata, turns it into Spark tables, measures data quality, computes text and graph features, compares retrieval systems, trains an ML baseline, ranks publications, and packages the results into reports, figures, tables, a notebook, and a presentation.

The strongest result is the system itself: a transparent pipeline that shows both what works and where the data pushes back.
