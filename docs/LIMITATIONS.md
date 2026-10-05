# Limitations

Current Milestone 5 limitations:

- The development sample is small and is not representative of the full OpenAlex corpus.
- API sampling is deterministic for the request parameters and current OpenAlex API state, but the live corpus can change over time.
- OpenAlex abstracts are represented as `abstract_inverted_index` and may be missing.
- Data-quality checks report issues but do not clean, drop, quarantine, or repair records yet.
- Spark now runs locally using project-configured OpenJDK and Windows Hadoop helper binaries, but the benchmark was only run on the current 100-record development sample.
- The observed cache experiment is too small to generalize; cached repeated aggregation was slower because cache setup overhead dominates at this scale.
- The benchmark uses subsets of the same development sample, not independent 10K/100K/500K/1M samples yet.
- Text analysis is lexical only; no K-means clustering, semantic embeddings, dense retrieval, graph analysis, streaming, or ML interpretation has been implemented yet.
- Stop-word filtering is project-defined and should be revisited when scaling beyond the 100-record development sample.
