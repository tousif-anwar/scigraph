# Bronze/Silver/Gold Pipeline Report

Generated on 2026-10-05.

## Stage Counts

- Raw records read: 1000
- Bronze records written: 1000
- Silver publications written: 1000
- Gold publications written: 1000
- Gold authors written: 3721
- Gold author-publication rows written: 3742
- Gold citation edges written: 22321
- Gold topic rows written: 2736

## Transform Accounting

- Records removed in Silver: 0
- Records with quality flags: 18
- Self-citations removed from Gold citation edges: 8

Quality flag counts:

```json
{
  "missing_authorships": 18
}
```

## Notes

Bronze preserves raw nested OpenAlex fields plus ingestion metadata. Silver normalizes publication-level columns and records validation flags. Gold creates publication, author, author-publication, citation-edge, and topic tables for later analysis.
