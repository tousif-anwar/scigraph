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
| 0 | 250 | 2020-2020 | 0 | 1 | 23.4400 | 13.8640 |
| 1 | 250 | 2020-2021 | 0 | 4 | 20.2600 | 12.9360 |
| 2 | 250 | 2021-2022 | 0 | 6 | 22.6120 | 8.5760 |
| 3 | 250 | 2022-2022 | 0 | 4 | 23.1760 | 9.9080 |
| 4 | 250 | 2022-2023 | 0 | 4 | 28.6840 | 6.3480 |
| 5 | 250 | 2023-2024 | 0 | 6 | 22.1000 | 2.6600 |
| 6 | 250 | 2024-2025 | 0 | 3 | 20.4400 | 2.3760 |
| 7 | 250 | 2025-2025 | 0 | 2 | 26.1680 | 1.9000 |
| 8 | 250 | 2025-2026 | 0 | 2 | 10.7800 | 0.2080 |
| 9 | 250 | 2026-2026 | 0 | 2 | 17.3000 | 0.0600 |

## Alerts

| batch | type | observed | threshold | severity |
| ---: | --- | ---: | ---: | --- |
|  | none |  |  |  |

## Interpretation

This milestone simulates streaming by replaying the fixed Gold publication table in deterministic micro-batches. It validates batch-level monitoring logic without depending on a long-running external message broker or live API stream.
