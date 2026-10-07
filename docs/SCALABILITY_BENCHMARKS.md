# Scalability Benchmarks

Generated on 2026-10-06.

These are measured Spark results from the current development sample. They should not be generalized to the full OpenAlex corpus.

## Pipeline Scale Results

| records | seconds | records/sec | partitions | output bytes |
| ---: | ---: | ---: | ---: | ---: |
| 10000 | 133.6097 | 74.8449 | 1 | 63883301 |
| 50000 | 117.6209 | 425.0945 | 1 | 294956560 |
| 100000 | 161.2121 | 620.3008 | 1 | 575658002 |

## Cache Experiment

| technique | records | seconds | records/sec |
| --- | ---: | ---: | ---: |
| uncached | 100000 | 14.7185 | 6794.1706 |
| cached | 100000 | 5.6037 | 17845.3522 |

## Interpretation

The configured development benchmark uses small subsets of the currently acquired sample. Larger, course-relevant scale levels require acquiring larger samples after the Spark runtime is stable.
