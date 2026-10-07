# Bronze/Silver/Gold Pipeline Report

Generated on 2026-10-06.

## Stage Counts

- Raw records read: 100000
- Bronze records written: 100000
- Silver publications written: 100000
- Gold publications written: 100000
- Gold authors written: 464323
- Gold author-publication rows written: 824037
- Gold citation edges written: 9111549
- Gold topic rows written: 300000

## Transform Accounting

- Records removed in Silver: 0
- Records with quality flags: 179
- Self-citations removed from Gold citation edges: 1991

Quality flag counts:

```json
{
  "missing_authorships": 174,
  "missing_title": 5
}
```

## Notes

Bronze preserves raw nested OpenAlex fields plus ingestion metadata. Silver normalizes publication-level columns and records validation flags. Gold creates publication, author, author-publication, citation-edge, and topic tables for later analysis.
