# Data Quality Report

Generated from observed raw OpenAlex records on 2026-10-05.

No records are removed or transformed by this report.

## Summary

- Records checked: 100
- Total checks: 31
- Passed checks: 24
- Warning checks: 7
- Error checks: 0
- Records with at least one reference: 62
- Records with at least one authorship: 98

## Check Results

| check | category | status | affected | % | description | examples |
| --- | --- | --- | ---: | ---: | --- | --- |
| missing_expected_fields | schema | pass | 0/17 | 0.00 | Configured fields that were not observed in any raw record. |  |
| unexpected_fields | schema | pass | 0/17 | 0.00 | Observed fields that are not declared in the acquisition config. |  |
| missing_ids | identity | pass | 0/100 | 0.00 | Records without a non-empty OpenAlex work ID. |  |
| malformed_openalex_ids | identity | pass | 0/100 | 0.00 | Non-empty work IDs that do not match the expected OpenAlex work URL pattern. |  |
| duplicate_ids | identity | pass | 0/100 | 0.00 | Records whose OpenAlex work ID appears more than once in the sample. |  |
| missing_titles | text | pass | 0/100 | 0.00 | Records missing both title and display_name. |  |
| missing_or_empty_abstract_index | text | pass | 0/100 | 0.00 | Records without an abstract inverted index. |  |
| malformed_abstract_index | text | pass | 0/100 | 0.00 | Abstract inverted indexes with unexpected token/position structure. |  |
| missing_publication_dates | temporal | pass | 0/100 | 0.00 | Records missing publication_date. |  |
| malformed_publication_dates | temporal | pass | 0/100 | 0.00 | Non-empty publication_date values that are not YYYY-MM-DD dates. |  |
| future_publication_dates | temporal | pass | 0/100 | 0.00 | Publication dates after the local run date. |  |
| publication_year_mismatch | temporal | pass | 0/100 | 0.00 | publication_year does not match the year component of publication_date. |  |
| invalid_publication_year | temporal | pass | 0/100 | 0.00 | publication_year is missing, non-integer, or outside a plausible range. |  |
| missing_authorships | authors | warn | 2/100 | 2.00 | Records with no authorship entries. | https://openalex.org/W4391329233, https://openalex.org/W4415792006 |
| malformed_authorships | authors | pass | 0/100 | 0.00 | authorships values that are not arrays. |  |
| authorship_entries_missing_author_id | authors | warn | 17/396 | 4.29 | Individual authorship entries missing nested author.id. |  |
| duplicate_author_ids_within_paper | authors | pass | 0/100 | 0.00 | Records with repeated author IDs inside one paper. |  |
| malformed_referenced_works | references | pass | 0/100 | 0.00 | referenced_works values that are not arrays. |  |
| invalid_cited_by_count | references | pass | 0/100 | 0.00 | cited_by_count values that are missing, non-integer, or negative. |  |
| empty_referenced_works | references | warn | 38/100 | 38.00 | Records with no outgoing references in OpenAlex metadata. | https://openalex.org/W7215156035, https://openalex.org/W3093665501, https://openalex.org/W4403439081, https://openalex.org/W4323355021, https://openalex.org/W7217644019 |
| duplicate_references_within_paper | references | pass | 0/100 | 0.00 | Records with repeated referenced work IDs. |  |
| self_references | references | warn | 1/100 | 1.00 | Records whose referenced_works include their own work ID. | https://openalex.org/W4392131371 |
| missing_doi | identifiers | warn | 13/100 | 13.00 | Records without DOI metadata. | https://openalex.org/W7215156035, https://openalex.org/W3093665501, https://openalex.org/W7217644019, https://openalex.org/W4287695784, https://openalex.org/W7219943880 |
| malformed_doi | identifiers | pass | 0/100 | 0.00 | Non-empty DOI values that do not match a basic DOI pattern. |  |
| missing_language | metadata | warn | 7/100 | 7.00 | Records without detected language metadata. | https://openalex.org/W7215156035, https://openalex.org/W7125700732, https://openalex.org/W7166524067, https://openalex.org/W7215934816, https://openalex.org/W7128182540 |
| malformed_primary_location | metadata | pass | 0/100 | 0.00 | primary_location values that are not objects. |  |
| malformed_locations | metadata | pass | 0/100 | 0.00 | locations values that are not arrays. |  |
| missing_primary_source | metadata | warn | 1/100 | 1.00 | Records without nested primary_location.source.id. | https://openalex.org/W4382406137 |
| malformed_open_access | metadata | pass | 0/100 | 0.00 | open_access values that are not objects. |  |
| malformed_concepts | topics | pass | 0/100 | 0.00 | concepts values that are not arrays. |  |
| malformed_topics | topics | pass | 0/100 | 0.00 | topics values that are not arrays. |  |

## Interpretation

Warnings identify data that the cleaning pipeline must handle explicitly. Errors indicate fields or structures that would break downstream assumptions if not fixed or quarantined in later Bronze/Silver/Gold processing.

Machine-readable results are saved to `reports/results/data_quality_report.json`.
