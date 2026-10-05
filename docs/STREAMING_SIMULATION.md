# Streaming Simulation

Generated on 2026-10-05.

## Summary

- Status: success
- Batch size: 100
- Batch count: 10
- Records processed: 1000
- Alert count: 0
- Missing-title alert threshold: 0.0
- Missing-author alert threshold: 0.05

## Batch Metrics

| batch | records | year range | missing titles | missing authors | avg references | avg citations |
| ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 0 | 100 | 2020-2020 | 0 | 1 | 35.1100 | 16.8800 |
| 1 | 100 | 2020-2021 | 0 | 3 | 20.0100 | 8.8600 |
| 2 | 100 | 2021-2022 | 0 | 2 | 20.4200 | 7.1000 |
| 3 | 100 | 2022-2023 | 0 | 2 | 18.4000 | 3.7400 |
| 4 | 100 | 2023-2023 | 0 | 1 | 28.6600 | 14.7800 |
| 5 | 100 | 2023-2024 | 0 | 2 | 23.7200 | 4.0600 |
| 6 | 100 | 2024-2025 | 0 | 2 | 22.6900 | 2.8500 |
| 7 | 100 | 2025-2025 | 0 | 2 | 27.5500 | 1.5900 |
| 8 | 100 | 2025-2026 | 0 | 2 | 9.9100 | 0.1800 |
| 9 | 100 | 2026-2026 | 0 | 1 | 16.8200 | 0.0900 |

## Alerts

| batch | type | observed | threshold | severity |
| ---: | --- | ---: | ---: | --- |
|  | none |  |  |  |

## Interpretation

This milestone simulates streaming by replaying the fixed Gold publication table in deterministic micro-batches. It validates batch-level monitoring logic without depending on a long-running external message broker or live API stream.
