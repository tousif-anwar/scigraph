# Bronze/Silver/Gold Pipeline Report

Generated on 2026-10-06.

## Stage Counts

- Raw records read: 2500
- Bronze records written: 2500
- Silver publications written: 2500
- Gold publications written: 2500
- Gold authors written: 9274
- Gold author-publication rows written: 9337
- Gold citation edges written: 53877
- Gold topic rows written: 6853

## Transform Accounting

- Records removed in Silver: 0
- Records with quality flags: 39
- Self-citations removed from Gold citation edges: 23

Quality flag counts:

```json
{
  "missing_authorships": 39
}
```

## Notes

Bronze preserves raw nested OpenAlex fields plus ingestion metadata. Silver normalizes publication-level columns and records validation flags. Gold creates publication, author, author-publication, citation-edge, and topic tables for later analysis.
