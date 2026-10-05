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
