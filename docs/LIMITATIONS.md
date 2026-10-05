# Limitations

Current Milestone 11 limitations:

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
- Author collaboration graph extraction is implemented, but it includes only publications with usable author IDs.
- Author collaboration edge weights are based only on shared sampled publications; the strongest observed edge weight is currently 1, so repeated long-term collaborations are not visible yet.
- High collaborator counts can come from one large author-team paper and should not be interpreted as broad career-level centrality without a larger or field-specific sample.
- Temporal analysis is implemented, but yearly publication counts reflect the current OpenAlex API sample, not the full yearly OpenAlex corpus.
- Recent-year citation metrics, especially 2026, are affected by citation-window delay and should not be interpreted as scientific impact.
- Latest-year topic growth rankings are unstable because many topic counts are small.
- Streaming-style monitoring is implemented as deterministic micro-batch replay over static Gold records, not as a live external message-broker stream.
- The streaming simulation uses local Spark and deterministic ordering by publication year and paper ID, so it validates monitoring behavior but not event-time disorder, retries, checkpoint recovery, or production backpressure.
- Sparse retrieval is implemented, but relevance is measured with OpenAlex topic-name substring proxies rather than human relevance judgments.
- Retrieval is lexical TF-IDF only; semantic embeddings, dense retrieval, reranking, RAG, live streaming infrastructure, and downstream ML interpretation have not been implemented yet.
