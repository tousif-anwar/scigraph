# SciGraph

Scalable scientific-literature intelligence using distributed text, graph, temporal, streaming, and retrieval analysis.

This repository is being built milestone by milestone for CS 660, with the initial focus on reproducible data acquisition and schema inspection. It is not a RAG application; later milestones will emphasize Spark data engineering, text analytics, graph analysis, temporal analysis, streaming, and retrieval experiments.

## Milestone Status

Milestone 1 created the repository foundation, configuration system, OpenAlex data acquisition workflow, schema inspection tooling, an initial data dictionary, and smoke tests.

Milestone 2 adds explicit data-quality checks and produces both machine-readable and human-readable reports without cleaning or dropping records.

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

During initial setup on 2026-10-05, Python was available as `python 3.14.4`. `git` and `java` were not available on PATH in this shell. PySpark is configured as a project dependency, but full Spark execution requires a compatible Java runtime.

The Milestone 1 development sample was retrieved on 2026-10-05. It contains 100 OpenAlex article records from publication years 2020-2026, with 100 unique publication IDs, 379 unique author IDs observed, 2,101 referenced works, 0 missing abstracts, 0 missing titles, 2 records with missing authorship arrays, and 0 duplicate publication IDs.

The Milestone 2 quality report ran 31 checks on the same sample. It found 0 error checks and 7 warning checks, including missing authorships, authorship entries without nested author IDs, empty reference arrays, one self-reference, missing DOIs, missing language metadata, and one missing primary source ID.

Milestone 3 adds the Spark Bronze/Silver/Gold pipeline implementation. In this environment PySpark 4.2.0 was installed successfully, but the configured `JAVA_HOME` did not contain a Java executable and `java` was not on PATH, so the Spark execution preflight wrote a blocked report instead of producing Parquet outputs.

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
