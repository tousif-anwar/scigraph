# Limitations

Current Milestone 7 limitations:

- The development sample is small and is not representative of the full OpenAlex corpus.
- API sampling is deterministic for the request parameters and current OpenAlex API state, but the live corpus can change over time.
- OpenAlex abstracts are represented as `abstract_inverted_index` and may be missing.
- Data-quality checks report issues but do not clean, drop, quarantine, or repair records yet.
- Spark now runs locally using project-configured OpenJDK and Windows Hadoop helper binaries, but the benchmark was only run on the current 100-record development sample.
- The observed cache experiment is too small to generalize; cached repeated aggregation was slower because cache setup overhead dominates at this scale.
- The benchmark uses subsets of the same development sample, not independent 10K/100K/500K/1M samples yet.
- K-means clustering is exploratory only; the selected model has weak silhouette and uneven cluster sizes.
- Text analysis and clustering are currently English-filtered, while the full raw/Silver/Gold dataset still includes non-English and missing-language records.
- Stop-word filtering is project-defined and should be revisited when scaling beyond the 1,000-record development sample.
- Citation graph extraction and PageRank are implemented, but the current 1,000-record sample has 0 citation edges where both source and destination are sampled publications.
- Expanded PageRank includes externally referenced OpenAlex work IDs, but those external vertices currently lack local title, year, author, and topic metadata.
- Sampled-paper PageRank is not meaningful in the current run because sampled papers have no in-sample incoming citation edges.
- Semantic embeddings, dense retrieval, streaming, and downstream ML interpretation have not been implemented yet.
