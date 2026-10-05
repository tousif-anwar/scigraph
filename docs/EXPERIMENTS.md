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
