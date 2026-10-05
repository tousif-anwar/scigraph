# Bronze/Silver/Gold Pipeline Report

Generated on 2026-10-05.

## Stage Counts

- Raw records read: 100
- Bronze records written: 100
- Silver publications written: 100
- Gold publications written: 100
- Gold authors written: 379
- Gold author-publication rows written: 379
- Gold citation edges written: 2100
- Gold topic rows written: 276

## Transform Accounting

- Records removed in Silver: 0
- Records with quality flags: 2
- Self-citations removed from Gold citation edges: 1

Quality flag counts:

```json
{
  "missing_authorships": 2
}
```

## Notes

Bronze preserves raw nested OpenAlex fields plus ingestion metadata. Silver normalizes publication-level columns and records validation flags. Gold creates publication, author, author-publication, citation-edge, and topic tables for later analysis.
