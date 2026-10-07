# Advanced Retrieval And Ablation

Generated on 2026-10-06.

## Summary

- Documents: 1793
- Queries: 5
- Top K: 10
- Dense model: Spark ML Word2Vec (32 dimensions)

## Ablation Results

| system | precision@K | recall@K | MRR | NDCG@K | mean latency seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| bm25 | 0.4800 | 0.3654 | 0.6167 | 0.5351 | 0.0380 |
| dense | 0.1800 | 0.0787 | 0.4074 | 0.2011 | 16.5668 |
| graph_alpha_0 | 0.4400 | 0.3154 | 0.7167 | 0.5747 | 0.0000 |
| graph_alpha_0.25 | 0.4000 | 0.3086 | 0.7333 | 0.5532 | 0.0000 |
| graph_alpha_0.5 | 0.4200 | 0.3586 | 0.7667 | 0.5815 | 0.0000 |
| hybrid_reranked | 0.4400 | 0.3154 | 0.7167 | 0.5747 | 0.0010 |
| hybrid_reranked_graph | 0.4600 | 0.3654 | 0.7667 | 0.6188 | 0.0000 |
| hybrid_rrf | 0.3600 | 0.2429 | 0.7333 | 0.4285 | 0.0000 |

## Interpretation

BM25 is the lexical baseline. Dense retrieval uses Spark ML Word2Vec trained locally on the development corpus. Hybrid retrieval uses reciprocal rank fusion. Reranking is a transparent second-stage score over the hybrid candidates. Graph-aware ranking blends reranked retrieval scores with the composite publication score. Metrics use the same topic-name proxy relevance labels as the sparse retrieval milestone.
