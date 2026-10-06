# Scalability Benchmarks

Generated on 2026-10-06.

These are measured Spark results from the current development sample. They should not be generalized to the full OpenAlex corpus.

## Pipeline Scale Results

| records | seconds | records/sec | partitions | output bytes |
| ---: | ---: | ---: | ---: | ---: |
| 500 | 8.7962 | 56.8427 | 1 | 1877571 |
| 1000 | 5.5265 | 180.9463 | 1 | 3657777 |
| 2500 | 5.5565 | 449.9235 | 1 | 8558948 |

## Cache Experiment

| technique | records | seconds | records/sec |
| --- | ---: | ---: | ---: |
| uncached | 2500 | 0.4806 | 5201.831 |
| cached | 2500 | 0.5512 | 4535.5588 |

## Interpretation

The configured development benchmark uses small subsets of the currently acquired sample. Larger, course-relevant scale levels require acquiring larger samples after the Spark runtime is stable.
