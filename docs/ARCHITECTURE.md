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
