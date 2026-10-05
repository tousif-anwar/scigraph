# Limitations

Current Milestone 1 limitations:

- The development sample is small and is not representative of the full OpenAlex corpus.
- API sampling is deterministic for the request parameters and current OpenAlex API state, but the live corpus can change over time.
- OpenAlex abstracts are represented as `abstract_inverted_index` and may be missing.
- Full Spark execution requires a compatible Java runtime; Java was not available on PATH during initial setup.
- No cleaning, graph analysis, text modeling, retrieval, streaming, or ML has been implemented yet.
