# File-Arrival Streaming Monitor

Generated on 2026-10-06.

## Summary

- Status: empty
- Input directory: `C:\Users\tousi\Documents\ta_a5\Common\scigraph\data\streaming\file_arrivals`
- Files observed: 0
- Records observed: 0
- Missing title rate: 0.0000
- Missing author rate: 0.0000

## File Metrics

| file | records | missing titles | missing authors | year range |
| --- | ---: | ---: | ---: | --- |

## How To Use

Drop OpenAlex JSONL files into the configured input directory and rerun this command to inspect newly arrived batches. The same schema can be used with Spark Structured Streaming by replacing the bounded read with `readStream.schema(openalex_work_schema()).json(input_dir)` and writing to the configured checkpoint directory.
