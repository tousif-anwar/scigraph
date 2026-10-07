# Scalability Benchmarks

Generated on 2026-10-06.

These are measured Spark results from the current development sample. They should not be generalized to the full OpenAlex corpus.

## Pipeline Scale Results

| records | seconds | records/sec | partitions | output bytes |
| ---: | ---: | ---: | ---: | ---: |
| 74600 | 55.2021 | 1351.3979 | 1 | 435052525 |
| 74600 | 113.859 | 655.1963 | 1 | 435052525 |
| 74600 | 121.4221 | 614.3857 | 1 | 435052525 |

## Cache Experiment

| technique | records | seconds | records/sec |
| --- | ---: | ---: | ---: |
| uncached | 74600 | 23.9509 | 3114.7055 |
| cached | 74600 | 19.4348 | 3838.4753 |

## Interpretation

The configured development benchmark uses small subsets of the currently acquired sample. Larger, course-relevant scale levels require acquiring larger samples after the Spark runtime is stable.
