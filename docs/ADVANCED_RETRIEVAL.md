# Advanced Retrieval And Ablation

Generated on 2026-10-06.

## Summary

- Documents: 738
- Queries: 5
- Top K: 10
- Dense model: Spark ML Word2Vec (32 dimensions)

## Ablation Results

| system | precision@K | recall@K | MRR | NDCG@K | mean latency seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| bm25 | 0.3800 | 0.4732 | 0.7667 | 0.6450 | 0.0156 |
| dense | 0.1400 | 0.1738 | 0.5833 | 0.2321 | 16.8594 |
| graph_alpha_0 | 0.3200 | 0.3932 | 0.9000 | 0.6562 | 0.0000 |
| graph_alpha_0.25 | 0.3200 | 0.3932 | 0.9000 | 0.6416 | 0.0000 |
| graph_alpha_0.5 | 0.3400 | 0.4265 | 0.9000 | 0.6263 | 0.0000 |
| hybrid_reranked | 0.3200 | 0.3932 | 0.9000 | 0.6562 | 0.0010 |
| hybrid_reranked_graph | 0.3400 | 0.4265 | 0.9000 | 0.6609 | 0.0000 |
| hybrid_rrf | 0.2400 | 0.3359 | 0.8500 | 0.4177 | 0.0000 |

## Interpretation

BM25 is the lexical baseline. Dense retrieval uses Spark ML Word2Vec trained locally on the development corpus. Hybrid retrieval uses reciprocal rank fusion. Reranking is a transparent second-stage score over the hybrid candidates. Graph-aware ranking blends reranked retrieval scores with the composite publication score. Metrics use the same topic-name proxy relevance labels as the sparse retrieval milestone.
