# SciGraph

Scalable scientific-literature intelligence using distributed text, graph, temporal, streaming, and retrieval analysis.

This repository is being built milestone by milestone for CS 660, with the initial focus on reproducible data acquisition and schema inspection. It is not a RAG application; later milestones will emphasize Spark data engineering, text analytics, graph analysis, temporal analysis, streaming, and retrieval experiments.

## Milestone 1 Status

Milestone 1 creates the repository foundation, configuration system, OpenAlex data acquisition workflow, schema inspection tooling, an initial data dictionary, and smoke tests.

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

Run smoke tests:

```powershell
python -m pytest
```

## Configuration

Configuration lives in `configs/`. The development config controls sample size, deterministic seed, API endpoint, selected OpenAlex fields, and local artifact paths. Change `dataset.sample_size` to adjust the development subset size.

## Current Environment Notes

During initial setup on 2026-10-05, Python was available as `python 3.14.4`. `git` and `java` were not available on PATH in this shell. PySpark is configured as a project dependency, but full Spark execution will require a compatible Java runtime in later milestones.

The Milestone 1 development sample was retrieved on 2026-10-05. It contains 100 OpenAlex article records from publication years 2020-2026, with 100 unique publication IDs, 379 unique author IDs observed, 2,101 referenced works, 0 missing abstracts, 0 missing titles, 2 records with missing authorship arrays, and 0 duplicate publication IDs.

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

The acquisition script records source metadata, retrieval date, request URL, sample size, and seed in `data/raw/openalex_sample_metadata.json`. The schema inspection script writes machine-readable statistics to `reports/results/schema_summary.json` and updates `docs/DATA_DICTIONARY.md` from observed fields only.
