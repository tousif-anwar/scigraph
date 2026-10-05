# K-means Text Clustering

Generated on 2026-10-05.

## Summary

- Documents clustered: 738
- K values evaluated: [3, 5, 8]
- Selected K: 3

## K Evaluation

| k | silhouette | training cost | cluster sizes |
| ---: | ---: | ---: | --- |
| 3 | -0.0062 | 717.4361 | {0: 601, 1: 2, 2: 135} |
| 5 | -0.0175 | 717.6205 | {0: 2, 1: 2, 2: 730, 3: 2, 4: 2} |
| 8 | -0.0134 | 712.2744 | {0: 2, 1: 1, 2: 6, 3: 47, 4: 28, 5: 10, 6: 642, 7: 2} |

## Interpretation

Silhouette is used as a diagnostic, not proof that clusters are scientific disciplines. Representative terms and papers require qualitative review before interpretation.

The best tested K still has weak separation and uneven cluster sizes. This is a negative-but-useful result: K-means on the current heterogeneous OpenAlex sample should be treated as exploratory, not as a reliable discipline discovery method.
