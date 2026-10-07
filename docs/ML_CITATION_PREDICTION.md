# ML Citation Prediction

Generated on 2026-10-06.

## Summary

- Status: success
- Records: 2500
- Citation threshold: 4.0
- Train rows: 1783
- Test rows: 717
- Positive labels: 634
- Negative labels: 1866
- Area under ROC: 0.9168
- Accuracy: 0.8298
- Majority baseline accuracy: 0.7464

## Confusion Matrix

| true positive | false positive | true negative | false negative |
| ---: | ---: | ---: | ---: |
| 73 | 21 | 522 | 101 |

## Feature Coefficients

| feature | coefficient |
| --- | ---: |
| publication_year_index | -0.254252 |
| reference_count | 0.023241 |
| author_count | 0.083961 |
| concept_count | 0.018127 |
| topic_count | 0.239359 |
| abstract_available_numeric | 0.000000 |

## Interpretation

This is a small supervised baseline for identifying papers in the top citation quartile within the current sample. It is not a causal model and should not be interpreted as predicting scientific quality. Recent papers have had less time to accumulate citations, so publication year can dominate this task.
