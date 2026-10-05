# Bronze/Silver/Gold Pipeline Report

Generated on 2026-10-05.

Status: blocked

## Runtime Blocker

Spark pipeline was not executed because the local Spark runtime preflight failed.

## Preflight Checks

| check | status | details |
| --- | --- | --- |
| pyspark_import | pass | 4.2.0 |
| java_executable | fail | No Java executable found on PATH or under JAVA_HOME/bin. |

## Planned Outputs

When Spark can run, this pipeline writes Bronze, Silver, and Gold Parquet datasets using the paths configured in `configs/dev.yaml`.
