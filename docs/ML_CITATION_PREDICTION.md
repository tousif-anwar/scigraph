# ML Citation Prediction

Generated on 2026-10-05.

## Summary

- Status: success
- Records: 1000
- Citation threshold: 4.0
- Train rows: 713
- Test rows: 287
- Positive labels: 264
- Negative labels: 736
- Area under ROC: 0.8559
- Accuracy: 0.7735
- Majority baseline accuracy: 0.7360

## Confusion Matrix

| true positive | false positive | true negative | false negative |
| ---: | ---: | ---: | ---: |
| 30 | 6 | 192 | 59 |

## Feature Coefficients

| feature | coefficient |
| --- | ---: |
| publication_year_index | -0.268415 |
| reference_count | 0.023072 |
| author_count | 0.078583 |
| concept_count | 0.014098 |
| topic_count | 0.258860 |
| abstract_available_numeric | 0.000000 |

## Interpretation

This is a small supervised baseline for identifying papers in the top citation quartile within the current sample. It is not a causal model and should not be interpreted as predicting scientific quality. Recent papers have had less time to accumulate citations, so publication year can dominate this task.
