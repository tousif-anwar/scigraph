# Architecture

Milestones 1 and 2 establish the project skeleton, data acquisition path, schema inspection, and raw data-quality reporting.

```text
OpenAlex Works API
  -> raw JSONL sample in data/raw/
  -> schema inspection
  -> reports/results/schema_summary.json
  -> docs/DATA_DICTIONARY.md
  -> data-quality checks
  -> reports/results/data_quality_report.json
  -> docs/DATA_QUALITY_REPORT.md
```

Later milestones will add Spark Bronze/Silver/Gold processing, scalability benchmarks, text analytics, graph analytics, temporal analysis, streaming, and retrieval.
