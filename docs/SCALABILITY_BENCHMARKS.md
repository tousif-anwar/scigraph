# Scalability Benchmarks

Generated on 2026-10-05.

These are measured Spark results from the current development sample. They should not be generalized to the full OpenAlex corpus.

## Pipeline Scale Results

| records | seconds | records/sec | partitions | output bytes |
| ---: | ---: | ---: | ---: | ---: |
| 25 | 6.0581 | 4.1267 | 1 | 156678 |
| 50 | 3.3908 | 14.7458 | 1 | 256866 |
| 100 | 3.3065 | 30.2435 | 1 | 465010 |

## Cache Experiment

| technique | records | seconds | records/sec |
| --- | ---: | ---: | ---: |
| uncached | 100 | 0.3157 | 316.7564 |
| cached | 100 | 2.0605 | 48.5319 |

## Interpretation

The configured development benchmark uses small subsets of the currently acquired sample. Larger, course-relevant scale levels require acquiring larger samples after the Spark runtime is stable.

At this tiny scale, caching was slower because materializing the cache costs more than recomputing the small aggregation. This is a measured result, not a general conclusion about caching on large Spark workloads.

## Runtime Notes

Spark used PySpark 4.2.0, OpenJDK `C:/Users/tousi/.jdks/openjdk-23.0.2`, and project-local Hadoop Windows helper binaries in `tools/hadoop/bin`.
