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

Result: 100 documents analyzed, 13,024 retained tokens, 5,209 vocabulary terms, and 8,766 document-term TF-IDF rows. Top global terms include `data`, `model`, `patients`, `time`, `analysis`, and `cancer`.

Interpretation: the sample is heterogeneous, so the top terms reflect mixed scientific domains rather than one coherent field.

Limitations: no clustering or semantic validation yet; the dev sample is too small for stable topic conclusions.
