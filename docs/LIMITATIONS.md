# Limitations

Current Milestone 3 limitations:

- The development sample is small and is not representative of the full OpenAlex corpus.
- API sampling is deterministic for the request parameters and current OpenAlex API state, but the live corpus can change over time.
- OpenAlex abstracts are represented as `abstract_inverted_index` and may be missing.
- Data-quality checks report issues but do not clean, drop, quarantine, or repair records yet.
- The Spark Bronze/Silver/Gold pipeline is implemented, but full execution is blocked in this environment until a valid Java executable is installed and available on PATH or under `JAVA_HOME/bin`.
- PySpark 4.2.0 is installed in the current interpreter; Java is the remaining local runtime blocker observed during Milestone 3.
- No cleaning, graph analysis, text modeling, retrieval, streaming, or ML has been implemented yet.
