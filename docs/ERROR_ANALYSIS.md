# Retrieval Error Analysis

Generated on 2026-10-06.

## Method

Errors were inspected using the shared query set and OpenAlex topic-name proxy relevance labels. This is not a substitute for human relevance judgments, but it gives reproducible failure categories for the final report.

## Observed Failure Categories

- Terminology mismatch: lexical retrieval misses documents that use related but different wording.
- Broad query ambiguity: terms such as policy, education, and healthcare match many fields.
- Metadata-label mismatch: a retrieved document can appear relevant by title but not match the configured topic-name proxy.
- Dense-vector drift: Word2Vec similarities can favor documents with generally similar vocabulary rather than precise topical relevance.
- Older-paper and citation bias: graph-aware ranking can favor papers with stronger citation/composite metadata, which may disadvantage newer papers.

## Per-Query Notes

- `artificial intelligence healthcare education`: best NDCG@K system was `hybrid_reranked` with NDCG@K 0.5484; relevant proxy documents available: 31.
- `climate change policy economics`: best NDCG@K system was `hybrid_reranked` with NDCG@K 0.5856; relevant proxy documents available: 23.
- `tuberculosis diagnosis treatment`: best NDCG@K system was `bm25` with NDCG@K 0.8922; relevant proxy documents available: 6.
- `digital marketing social media`: best NDCG@K system was `bm25` with NDCG@K 0.5816; relevant proxy documents available: 9.
- `dementia cognitive impairment`: best NDCG@K system was `hybrid_reranked` with NDCG@K 0.9218; relevant proxy documents available: 4.
