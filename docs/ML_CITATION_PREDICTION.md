# ML Citation Prediction

Generated on 2026-10-06.

## Summary

- Status: success
- Records: 2500
- Citation threshold: 4.0
- Train rows: 1783
- Test rows: 717
- Positive labels: 663
- Negative labels: 1837
- Area under ROC: 0.9174
- Accuracy: 0.8494
- Majority baseline accuracy: 0.7348

## Confusion Matrix

| true positive | false positive | true negative | false negative |
| ---: | ---: | ---: | ---: |
| 84 | 10 | 525 | 98 |

## Feature Coefficients

| feature | coefficient |
| --- | ---: |
| publication_year_index | -0.294224 |
| reference_count | 0.020846 |
| author_count | 0.083332 |
| concept_count | 0.015755 |
| topic_count | 0.250930 |
| abstract_available_numeric | 0.000000 |

## Interpretation

This is a small supervised baseline for identifying papers in the top citation quartile within the current sample. It is not a causal model and should not be interpreted as predicting scientific quality. Recent papers have had less time to accumulate citations, so publication year can dominate this task.
