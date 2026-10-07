# Streaming Simulation

Generated on 2026-10-06.

## Summary

- Status: success
- Batch size: 250
- Batch count: 10
- Records processed: 2500
- Alert count: 0
- Missing-title alert threshold: 0.0
- Missing-author alert threshold: 0.05

## Batch Metrics

| batch | records | year range | missing titles | missing authors | avg references | avg citations |
| ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 0 | 250 | 2020-2020 | 0 | 1 | 28.6120 | 19.4680 |
| 1 | 250 | 2020-2021 | 0 | 4 | 20.8600 | 9.5400 |
| 2 | 250 | 2021-2022 | 0 | 4 | 22.0800 | 9.7600 |
| 3 | 250 | 2022-2023 | 0 | 4 | 19.3320 | 4.9360 |
| 4 | 250 | 2023-2023 | 0 | 2 | 28.6960 | 10.4120 |
| 5 | 250 | 2023-2024 | 0 | 7 | 24.0320 | 4.0520 |
| 6 | 250 | 2024-2025 | 0 | 4 | 22.6720 | 2.2920 |
| 7 | 250 | 2025-2025 | 0 | 4 | 26.0360 | 1.3280 |
| 8 | 250 | 2025-2026 | 0 | 6 | 9.9800 | 0.1880 |
| 9 | 250 | 2026-2026 | 0 | 3 | 13.3000 | 0.1240 |

## Alerts

| batch | type | observed | threshold | severity |
| ---: | --- | ---: | ---: | --- |
|  | none |  |  |  |

## Interpretation

This milestone simulates streaming by replaying the fixed Gold publication table in deterministic micro-batches. It validates batch-level monitoring logic without depending on a long-running external message broker or live API stream.
