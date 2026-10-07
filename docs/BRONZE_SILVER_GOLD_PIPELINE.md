# Bronze/Silver/Gold Pipeline Report

Generated on 2026-10-06.

## Stage Counts

- Raw records read: 74600
- Bronze records written: 74600
- Silver publications written: 74600
- Gold publications written: 74600
- Gold authors written: 371312
- Gold author-publication rows written: 633746
- Gold citation edges written: 6983986
- Gold topic rows written: 220275

## Transform Accounting

- Records removed in Silver: 0
- Records with quality flags: 174
- Self-citations removed from Gold citation edges: 1591

Quality flag counts:

```json
{
  "missing_authorships": 170,
  "missing_title": 4
}
```

## Notes

Bronze preserves raw nested OpenAlex fields plus ingestion metadata. Silver normalizes publication-level columns and records validation flags. Gold creates publication, author, author-publication, citation-edge, and topic tables for later analysis.
