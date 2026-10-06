# Experiments

## Milestone 4: Preprocessing Scalability

Research question: how does the current Spark Bronze/Silver/Gold preprocessing pipeline behave as the number of records increases within the current development sample?

Hypothesis: fixed Spark startup and write overhead will dominate at tiny scales, so throughput should improve from 25 to 100 records but should not be treated as representative of large-corpus performance.

Independent variable: number of records processed.

Dependent variables: wall-clock runtime, records per second, output size, stage counts.

Controlled variables: same raw OpenAlex sample, local Spark mode, same machine, same pipeline logic, same output format.

Dataset: current 100-record OpenAlex development sample.

Baseline: end-to-end Spark pipeline at 25 records.

Method: run the Spark preprocessing pipeline for configured scales of 25, 50, and 100 records, writing isolated benchmark outputs under `experiments/scalability/runs/`.

Metric: wall-clock seconds and records per second.

Result: measured results are stored in `experiments/scalability/results/scalability_results.json` and summarized in `docs/SCALABILITY_BENCHMARKS.md`.

Interpretation: throughput improved at larger dev scales because fixed Spark overhead dominated the smallest run.

Limitations: the current sample is far too small for course-scale conclusions. Larger samples must be acquired before making claims about distributed performance.

## Milestone 5: Distributed Text Analysis and TF-IDF

Research question: what lexical signals can be extracted from scientific titles and abstracts using distributed Spark transformations?

Hypothesis: after stop-word filtering, frequent and high-TF-IDF terms should reveal coarse topical signals in the current OpenAlex sample.

Independent variable: term occurrence across documents, years, and OpenAlex topics.

Dependent variables: term frequency, document frequency, IDF, corpus TF-IDF, document-term TF-IDF rows.

Controlled variables: same 100-record OpenAlex development sample, same Silver/Gold pipeline outputs, same stop-word list, same minimum token length.

Dataset: current 100-record OpenAlex development sample.

Baseline: raw retained token counts and corpus-level term-frequency ranking.

Method: reconstruct abstracts from OpenAlex inverted indexes, join them to Silver publication records, tokenize with Spark SQL functions, filter stop words/numeric/short tokens, compute term frequency, document frequency, smoothed IDF, and TF-IDF.

Metric: token count, vocabulary size, document-term TF-IDF row count, top global/year/topic terms.

Result: after increasing the development sample to 1,000 OpenAlex records and filtering text analysis to English-language records, 738 documents were analyzed, with 99,587 retained tokens and 16,091 vocabulary terms. Top global terms include `data`, `patients`, `analysis`, `model`, `high`, and `development`.

Interpretation: the sample is heterogeneous, so the top terms reflect mixed scientific domains rather than one coherent field.

Limitations: no clustering or semantic validation yet; the dev sample is too small for stable topic conclusions.

## Milestone 6: K-means Text Clustering

Research question: can distributed K-means over TF-IDF features discover coherent groups of scientific publications?

Hypothesis: K-means may separate broad biomedical and methods/data-heavy documents, but the heterogeneous sample will likely produce weak cluster separation.

Independent variable: number of clusters K.

Dependent variables: silhouette score, training cost, cluster size distribution, representative terms, representative papers.

Controlled variables: same 1,000-record OpenAlex development sample, English-language text subset, same tokenization and stop-word filtering, same random seed.

Dataset: 738 English-language documents from the 1,000-record development sample.

Baseline: K=3.

Method: reconstruct title+abstract text, tokenize, remove stop words, hash tokens, compute IDF-weighted vectors, L2-normalize features, train K-means for K = 3, 5, and 8, and compare silhouette scores.

Metric: silhouette score with squared Euclidean distance, training cost, cluster sizes.

Result: K=3 had the best silhouette score among tested values, but the score was weak (-0.0062). Cluster sizes were 601, 2, and 135. Representative terms suggest a large general methods/data cluster and a smaller biomedical/clinical cluster, plus tiny outlier clusters.

Interpretation: K-means produced exploratory groupings but not robust scientific topic clusters. The result supports the project requirement to avoid claiming that clusters are meaningful disciplines solely from silhouette score.

Limitations: sample heterogeneity, hashed features, residual metadata/noisy records, and weak silhouette make these clusters qualitative artifacts only.

## Milestone 7: Citation Graph and PageRank

Research question: can citation edges from the OpenAlex sample identify central publications using graph degree and PageRank?

Hypothesis: citation graph centrality should differ from raw `cited_by_count`, but a random heterogeneous development sample may be too sparse internally for meaningful sample-only PageRank.

Independent variable: graph construction strategy, including sample-only citation edges versus expanded edges that include externally referenced OpenAlex work IDs.

Dependent variables: vertex count, edge count, in-degree, out-degree, PageRank score, and ratio of PageRank to in-degree.

Controlled variables: same 1,000-record OpenAlex development sample, same Spark runtime, same citation edge extraction, same PageRank iteration count and damping factor.

Dataset: 1,000 OpenAlex records and their 22,321 outgoing citation edges.

Baseline: raw citation metadata and in-sample in-degree/out-degree.

Method: build publication vertices from Gold publications, construct directed citation edges from Gold citation edges, remove self-citations during preprocessing, compute degree metrics, and run iterative Spark PageRank with dangling-mass handling on an expanded graph containing sampled publications and external referenced work IDs.

Metric: graph size, in-sample edge count, expanded edge count, PageRank rankings, and comparison with sampled-paper citation metadata.

Result: the sampled publication graph has 1,000 sampled vertices but 0 in-sample citation edges. The expanded graph has 23,177 vertices and 22,321 citation edges, all pointing from sampled publications to external referenced works.

Interpretation: this is a useful negative result for the sampling strategy. The citation extraction and PageRank implementation work, but the current sample is not citation-closed enough for meaningful sample-only graph centrality. Expanded PageRank mostly ranks external referenced work IDs that do not yet have local title/year metadata.

Limitations: PageRank values for sampled papers are tied in the current run because no sampled paper receives an in-sample citation. Future graph analysis should use a larger sample, a field/year-constrained sample, or a citation-neighborhood crawl that fetches metadata for referenced works.

## Milestone 8: Author Collaboration Graph

Research question: what coauthorship structure is visible in the current OpenAlex development sample?

Hypothesis: the author graph should expose multi-author papers and high-collaboration teams, but a heterogeneous 1,000-record sample will mostly capture one-paper collaboration snapshots rather than repeated long-term partnerships.

Independent variable: coauthorship relationships derived from Gold author-publication rows.

Dependent variables: author count, author-publication count, solo and multi-author publication counts, coauthor edge count, graph density, collaborator count per author, and shared-publication edge weight.

Controlled variables: same 1,000-record OpenAlex development sample, same Gold author-publication table, same Spark runtime, and same author ID normalization from the preprocessing pipeline.

Dataset: 3,726 author-publication rows with usable author IDs across 948 sampled publications.

Baseline: per-author publication counts without graph edges.

Method: self-join author-publication rows within each paper, keep deterministic undirected author pairs, aggregate pairs by author IDs, count shared sampled publications as edge weights, and compute author-level collaboration metrics from the weighted edge table.

Metric: number of authors, publications represented in the author graph, multi-author versus solo-author publication counts, coauthor edge count, graph density, top authors by collaborator count, and strongest coauthor edges by shared-publication count.

Result: the current run found 3,721 authors, 709 multi-author publications, 239 solo-author publications, and 11,508 undirected coauthor edges. The graph density is 0.00166275, and the strongest observed coauthor edge weight is 1 shared sampled publication.

Interpretation: the collaboration graph successfully captures observed coauthorship in the sample. High collaborator counts mostly come from large author-team papers; repeated pairwise collaboration is not visible at the current sample size.

Limitations: 52 sampled publications do not contribute to the author graph because they lack usable author IDs. The graph should not be interpreted as a complete career-level collaboration network; it only reflects coauthorship observed in the current sampled records.

## Milestone 9: Temporal Trend Analysis

Research question: what publication-year and topic-year patterns are visible in the current OpenAlex development sample?

Hypothesis: the sample should show measurable yearly publication counts and topic activity, but recent-year citation metrics will be lower because newer papers have had less time to accrue citations.

Independent variable: publication year and topic-year grouping.

Dependent variables: publication count, year-over-year publication-count growth, total and average `cited_by_count`, citations per sampled publication, average reference count, average author count, topic-year publication count, and latest-year topic growth.

Controlled variables: same 1,000-record OpenAlex development sample, same Gold publication and topic tables, same Spark runtime, and same OpenAlex-provided publication years.

Dataset: 1,000 publications with valid publication years from 2020 through 2026, plus 2,477 topic-year rows.

Baseline: raw publication counts by year.

Method: aggregate Gold publications by `publication_year`, compute citation/reference/author aggregates, use a year-ordered lag window for year-over-year growth, join Gold topics to publications, aggregate topic counts by year, and rank latest-year topics by absolute growth from the previous year.

Metric: yearly publication count, year-over-year growth, citations per publication, topic-year row count, and latest-year topic growth.

Result: the sample spans 7 publication-year buckets from 2020 to 2026. Publication counts range from 106 in 2021 to 183 in 2025. The latest year, 2026, has 149 sampled publications and 0.1611 citations per publication. The topic trend table contains 2,477 topic-year rows and 395 latest-year topic candidates.

Interpretation: temporal aggregation works and exposes both publication-year distribution and topic activity. Citation metrics decline sharply in recent years, especially 2026, which is expected from citation-window effects and should not be interpreted as lower scientific value.

Limitations: the OpenAlex API sample is not a complete yearly corpus, 2026 is still an incomplete/recent citation window, and topic growth rankings are unstable at small counts.

## Milestone 10: Streaming-Style Micro-Batch Monitoring

Research question: can the project monitor publication metadata quality and aggregate behavior in streaming-style batches?

Hypothesis: deterministic micro-batches over the current Gold publication table should produce stable batch metrics, and the existing sample should trigger no missing-title alerts because earlier quality checks found no missing titles.

Independent variable: simulated stream batch id, using 100 records per batch in the development configuration.

Dependent variables: record count, publication-year range, missing-title count/rate, missing-author count/rate, average author count, average reference count, average `cited_by_count`, and alert count.

Controlled variables: same 1,000-record OpenAlex development sample, same Gold publication table, deterministic ordering by publication year and paper ID, same alert thresholds.

Dataset: 1,000 Gold publication records replayed as 10 deterministic micro-batches.

Baseline: static Gold publication quality fields without per-batch monitoring.

Method: assign deterministic stream positions with a Spark window, divide records into 100-record micro-batches, compute per-batch aggregate metrics, and generate alert rows when missing-title or missing-author rates exceed configured thresholds.

Metric: batch count, records processed, per-batch missing-field rates, and alert count.

Result: the simulation processed 1,000 records in 10 batches of 100 records. Missing-title count was 0 in every batch. Missing-author counts ranged from 1 to 3 per batch, staying below the configured 0.05 alert threshold. Total alert count was 0.

Interpretation: the monitoring path works and produces reproducible per-batch metrics. This is a deterministic replay simulation, not a live Kafka/socket/API stream, so it validates monitoring logic rather than production streaming infrastructure.

Limitations: the simulation uses static Gold records, deterministic ordering, and local Spark execution. A future milestone should connect this monitoring logic to live or file-arrival Structured Streaming inputs if production-style streaming is required.

## Milestone 11: Sparse Retrieval Baseline

Research question: how well does a sparse lexical retrieval baseline recover topically related scientific papers from the current text corpus?

Hypothesis: TF-IDF lexical matching should work best for narrow terminology-heavy queries, such as tuberculosis, and should be weaker for broader mixed-domain queries, such as climate policy or AI in education/healthcare.

Independent variable: fixed retrieval query text.

Dependent variables: ranked result count, retrieval score, matched query-term count, topic-proxy relevance, relevant retrieved count, and precision@10.

Controlled variables: same English-filtered text documents and TF-IDF term table from Milestone 5, same tokenization and stop-word rules, same top-K cutoff, and same OpenAlex topic metadata.

Dataset: 738 English-language text documents and the saved document-term TF-IDF table.

Baseline: sparse TF-IDF score from query-token overlap with document-term TF-IDF weights.

Method: tokenize configured queries, join query terms against saved document-term TF-IDF rows, sum query-term-weighted TF-IDF scores per query and paper, rank results by score, and approximate relevance by checking whether each paper's OpenAlex topic names contain configured query-specific substrings.

Metric: precision@10 using topic-name substring matches as a proxy relevance label.

Result: five configured queries produced 372 ranked query-document rows. Mean precision@10 was 0.32. Query-level precision@10 was 0.30 for artificial intelligence/healthcare/education, 0.20 for climate change/policy/economics, 0.30 for dementia/cognitive impairment, 0.30 for digital marketing/social media, and 0.50 for tuberculosis diagnosis/treatment.

Interpretation: sparse retrieval is a useful baseline but is sensitive to exact word overlap and broad query terms. The tuberculosis query performed best because its terminology is narrow and distinctive in titles/abstracts.

Limitations: relevance labels are approximate topic-name substring matches, not human judgments. This is not semantic retrieval and not RAG; it does not use embeddings, reranking, generated answers, or citation-aware ranking.

## Milestone 12: Citation Outcome Prediction Baseline

Research question: can simple structured metadata predict whether a sampled publication belongs to the high-citation group within the current OpenAlex sample?

Hypothesis: publication year, reference count, author count, and topic/concept counts should provide some predictive signal, but recency effects and sample bias will limit interpretation.

Independent variable: publication-level metadata features.

Dependent variable: binary label indicating whether `cited_by_count` is at or above the configured high-citation quantile threshold.

Controlled variables: same 1,000-record Gold publication table, same deterministic random seed, same train/test split fraction, same logistic-regression configuration.

Dataset: 1,000 Gold publication records. The 0.75 quantile threshold was `cited_by_count >= 4`, yielding 264 positive labels and 736 negative labels because of ties at the threshold.

Baseline: majority-class accuracy from always predicting the more frequent class.

Method: build numeric features for publication year index, reference count, author count, concept count, topic count, and abstract availability; split rows into train/test sets; fit Spark ML logistic regression; evaluate area under ROC, accuracy, and confusion matrix on the test split.

Metric: area under ROC, test accuracy, majority baseline accuracy, and confusion matrix.

Result: the held-out test split contained 287 records. The model achieved area under ROC 0.8559 and accuracy 0.7735, compared with majority baseline accuracy 0.7360. The confusion matrix was 30 true positives, 6 false positives, 192 true negatives, and 59 false negatives.

Interpretation: the model has ranking signal, as shown by AUC, but the accuracy gain over the majority baseline is modest. The model is conservative about predicting high-citation papers and misses many positives. The negative coefficient for publication year is consistent with newer publications having had less time to accumulate citations.

Limitations: this is not causal and does not predict scientific quality. The target is `cited_by_count` within a small sample, citation windows are unequal across publication years, and the model does not include field-normalized citations or external metadata.

## Milestone 13: Composite Publication Ranking

Research question: can multiple existing project signals be combined into a transparent ranked list of sampled publications?

Hypothesis: citation count and reference richness will dominate the current sample because sampled-paper PageRank is tied and sparse, while recency and metadata completeness can still affect the ordering.

Independent variable: normalized scoring components and their configured weights.

Dependent variables: composite score, rank, component scores, and top-ranked publications.

Controlled variables: same 1,000-record Gold publication table, same citation PageRank output, same configured ranking weights, and same min-max normalization logic.

Dataset: 1,000 sampled publications with Gold metadata and sampled-paper citation PageRank values.

Baseline: raw `cited_by_count` sorting.

Method: join Gold publication metadata to sampled-paper PageRank, min-max normalize citation count, PageRank, publication year, reference count, author count, and topic count, then compute a weighted composite score. The development weights are 0.45 citation count, 0.15 PageRank, 0.15 recency, 0.10 reference count, 0.05 author count, and 0.10 topic count.

Metric: ranked publication count, mean composite score, maximum composite score, and inspection of the top-ranked publications.

Result: the ranking stage scored all 1,000 sampled publications. Mean composite score was 0.1861 and maximum score was 0.6401. The top-ranked paper was "The global costs of extreme weather that are attributable to climate change" with 554 cited-by count and composite score 0.6401.

Interpretation: the ranking is inspectable and reproducible, but it is not an authority metric. In the current sample, citation count and reference count drive the top ranks. PageRank contributes little because all sampled papers have tied PageRank after the citation graph milestone found no in-sample citation edges.

Limitations: weights are manually configured, components are min-max normalized within one small sample, and the score is not field-normalized or validated against human relevance judgments.

## Milestone 14: Integrated Publication Feature Mart

Research question: can outputs from the previous analysis milestones be integrated into a single publication-level dataset for downstream inspection and modeling?

Hypothesis: a one-row-per-publication feature mart should preserve all sampled publications while making feature availability explicit for English-filtered, test-split, and graph-derived signals.

Independent variable: feature source from prior milestones.

Dependent variables: publication row count, feature column count, feature availability rates, and top-ranked joined rows.

Controlled variables: same 1,000-record sample, same existing Gold outputs, same deterministic outputs from text, clustering, graph, temporal, ML, and ranking stages.

Dataset: 1,000 Gold publication records plus prior milestone outputs.

Baseline: separate Parquet outputs that require manual joins for cross-signal inspection.

Method: left-join Gold publications to text features, cluster assignments, citation degree metrics, citation-prediction labels/predictions, composite ranking scores, and yearly temporal aggregates. Preserve one row per sampled publication and add availability flags for sparse downstream features.

Metric: row preservation, number of columns, feature availability rates, and average document word count.

Result: the feature mart preserved all 1,000 sampled publication rows and produced 34 columns. Text features and cluster assignments were available for 738 publications, ML predictions for 287 held-out test rows, and composite ranking rows for all 1,000 publications. Average document word count across all publication rows was 163.8220, including zero-filled missing text rows.

Interpretation: the feature mart gives the project a single downstream table for inspection and later modeling. Sparse availability is expected because text/clustering are English-filtered and ML predictions are only produced for the held-out split.

Limitations: the mart inherits limitations from all upstream stages. It is a convenience integration layer, not a new ground-truth dataset, and some features are intentionally sparse.

## Milestones 15-18: Dense, Hybrid, Reranked, Graph-Aware Retrieval And Final Audit

Research question: do dense retrieval, hybrid retrieval, reranking, or graph-aware ranking improve over a BM25 lexical baseline on the shared scientific query set?

Hypothesis: BM25 should remain competitive on narrow terminology-heavy scientific queries; dense retrieval may help terminology mismatch but can be weaker when trained only on the small development corpus; graph-aware ranking may improve NDCG but can introduce citation/age bias.

Independent variable: retrieval system variant.

Dependent variables: precision@10, recall@10, MRR, NDCG@10, and mean latency.

Controlled variables: same 738 English text documents, same five configured queries, same OpenAlex topic-name proxy relevance labels, same top-K cutoff, and same evaluation code.

Dataset: 738 English-language title+abstract text documents.

Baseline: BM25.

Method: evaluate BM25, Spark ML Word2Vec dense retrieval, Reciprocal Rank Fusion hybrid retrieval, a transparent candidate reranker, and graph-aware score blending. Run all systems against the same query set and relevance proxy labels. Produce an ablation table, error analysis, and demo query output.

Metric: precision@10, recall@10, MRR, NDCG@10, and mean latency in seconds.

Result: BM25 reached precision@10 0.38, recall@10 0.4732, MRR 0.7667, and NDCG@10 0.6450. Dense Word2Vec retrieval was weaker, with precision@10 0.14 and NDCG@10 0.2321. Hybrid RRF alone reached precision@10 0.24 and NDCG@10 0.4177. Transparent reranking improved NDCG@10 to 0.6562. The best NDCG@10 was hybrid reranked graph-aware retrieval at 0.6609, with precision@10 0.34 and recall@10 0.4265.

Interpretation: the small local dense model did not outperform BM25. Hybrid RRF alone also did not help. Reranking and graph-aware blending improved NDCG modestly, but the gain is small and should be interpreted cautiously because relevance labels are proxy labels.

Limitations: dense retrieval uses local Spark Word2Vec rather than a large pretrained scientific sentence embedding model. Evaluation labels are OpenAlex topic-name substring proxies, not human judgments. Graph-aware ranking can favor older or more cited papers. Optional RAG was not implemented because the project focus is scalable analytics and retrieval evaluation.
