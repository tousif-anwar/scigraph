# Vector Index

Generated on 2026-10-06.

## Summary

- Status: success
- Backend used: sklearn_tfidf_fallback
- Documents indexed: 1777
- Vocabulary size: 20000
- Neighbors stored per query: 10

## Output Artifacts

- matrix: `C:\Users\tousi\Documents\ta_a5\Common\scigraph\data\gold\vector_index\tfidf_matrix.npz`
- vectorizer: `C:\Users\tousi\Documents\ta_a5\Common\scigraph\data\gold\vector_index\tfidf_vectorizer.pkl`
- neighbors: `C:\Users\tousi\Documents\ta_a5\Common\scigraph\data\gold\vector_index\nearest_neighbors.pkl`
- documents: `C:\Users\tousi\Documents\ta_a5\Common\scigraph\data\gold\vector_index\documents.jsonl`
- metadata: `C:\Users\tousi\Documents\ta_a5\Common\scigraph\data\gold\vector_index\metadata.json`

## Notes

The project now has a persisted nearest-neighbor index over paper title and abstract text. If Chroma or FAISS is installed later, the backend selector can be extended without changing downstream report paths; this run used the portable scikit-learn fallback available in the current environment.
