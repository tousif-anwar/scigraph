# Advanced Retrieval And Ablation

Generated on 2026-10-06.

## Summary

- Documents: 1777
- Queries: 5
- Top K: 10
- Dense model: Spark ML Word2Vec (32 dimensions)

## Ablation Results

| system | precision@K | recall@K | MRR | NDCG@K | mean latency seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| bm25 | 0.4800 | 0.3120 | 0.8667 | 0.6203 | 0.0626 |
| dense | 0.2800 | 0.1664 | 0.6400 | 0.3284 | 17.7123 |
| graph_alpha_0 | 0.4400 | 0.2696 | 0.9000 | 0.5918 | 0.0000 |
| graph_alpha_0.25 | 0.4400 | 0.2696 | 0.9000 | 0.5918 | 0.0000 |
| graph_alpha_0.5 | 0.4400 | 0.2696 | 0.9000 | 0.5918 | 0.0000 |
| hybrid_reranked | 0.4400 | 0.2696 | 0.9000 | 0.5918 | 0.0015 |
| hybrid_reranked_graph | 0.4400 | 0.2696 | 0.9000 | 0.5918 | 0.0000 |
| hybrid_rrf | 0.4400 | 0.3062 | 0.7667 | 0.5010 | 0.0000 |

## Interpretation

BM25 is the lexical baseline. Dense retrieval uses Spark ML Word2Vec trained locally on the development corpus. Hybrid retrieval uses reciprocal rank fusion. Reranking is a transparent second-stage score over the hybrid candidates. Graph-aware ranking blends reranked retrieval scores with the composite publication score. Metrics use the same topic-name proxy relevance labels as the sparse retrieval milestone.
