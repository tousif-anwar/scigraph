# Data Quality Report

Generated from observed raw OpenAlex records on 2026-10-06.

No records are removed or transformed by this report.

## Summary

- Records checked: 100000
- Total checks: 31
- Passed checks: 22
- Warning checks: 9
- Error checks: 0
- Records with at least one reference: 97835
- Records with at least one authorship: 99826

## Check Results

| check | category | status | affected | % | description | examples |
| --- | --- | --- | ---: | ---: | --- | --- |
| missing_expected_fields | schema | pass | 0/17 | 0.00 | Configured fields that were not observed in any raw record. |  |
| unexpected_fields | schema | pass | 0/17 | 0.00 | Observed fields that are not declared in the acquisition config. |  |
| missing_ids | identity | pass | 0/100000 | 0.00 | Records without a non-empty OpenAlex work ID. |  |
| malformed_openalex_ids | identity | pass | 0/100000 | 0.00 | Non-empty work IDs that do not match the expected OpenAlex work URL pattern. |  |
| duplicate_ids | identity | pass | 0/100000 | 0.00 | Records whose OpenAlex work ID appears more than once in the sample. |  |
| missing_titles | text | warn | 5/100000 | 0.01 | Records missing both title and display_name. | https://openalex.org/W2150865801, https://openalex.org/W1518641734, https://openalex.org/W2397770138, https://openalex.org/W2402962589, https://openalex.org/W2611715903 |
| missing_or_empty_abstract_index | text | pass | 0/100000 | 0.00 | Records without an abstract inverted index. |  |
| malformed_abstract_index | text | pass | 0/100000 | 0.00 | Abstract inverted indexes with unexpected token/position structure. |  |
| missing_publication_dates | temporal | pass | 0/100000 | 0.00 | Records missing publication_date. |  |
| malformed_publication_dates | temporal | pass | 0/100000 | 0.00 | Non-empty publication_date values that are not YYYY-MM-DD dates. |  |
| future_publication_dates | temporal | pass | 0/100000 | 0.00 | Publication dates after the local run date. |  |
| publication_year_mismatch | temporal | pass | 0/100000 | 0.00 | publication_year does not match the year component of publication_date. |  |
| invalid_publication_year | temporal | pass | 0/100000 | 0.00 | publication_year is missing, non-integer, or outside a plausible range. |  |
| missing_authorships | authors | warn | 174/100000 | 0.17 | Records with no authorship entries. | https://openalex.org/W4292528167, https://openalex.org/W2801085490, https://openalex.org/W2018838463, https://openalex.org/W3216401400, https://openalex.org/W4245784696 |
| malformed_authorships | authors | pass | 0/100000 | 0.00 | authorships values that are not arrays. |  |
| authorship_entries_missing_author_id | authors | warn | 38209/862246 | 4.43 | Individual authorship entries missing nested author.id. |  |
| duplicate_author_ids_within_paper | authors | warn | 713/100000 | 0.71 | Records with repeated author IDs inside one paper. | https://openalex.org/W2104549677, https://openalex.org/W2133416234, https://openalex.org/W3193598686, https://openalex.org/W3003217347, https://openalex.org/W2125826054 |
| malformed_referenced_works | references | pass | 0/100000 | 0.00 | referenced_works values that are not arrays. |  |
| invalid_cited_by_count | references | pass | 0/100000 | 0.00 | cited_by_count values that are missing, non-integer, or negative. |  |
| empty_referenced_works | references | warn | 2165/100000 | 2.17 | Records with no outgoing references in OpenAlex metadata. | https://openalex.org/W4385245566, https://openalex.org/W2964121744, https://openalex.org/W1849190772, https://openalex.org/W4292528167, https://openalex.org/W4392145873 |
| duplicate_references_within_paper | references | pass | 0/100000 | 0.00 | Records with repeated referenced work IDs. |  |
| self_references | references | warn | 1991/100000 | 1.99 | Records whose referenced_works include their own work ID. | https://openalex.org/W2092157292, https://openalex.org/W639708223, https://openalex.org/W3177828909, https://openalex.org/W2018289835, https://openalex.org/W2034285706 |
| missing_doi | identifiers | warn | 1891/100000 | 1.89 | Records without DOI metadata. | https://openalex.org/W1849190772, https://openalex.org/W2095705004, https://openalex.org/W3106250896, https://openalex.org/W2047735993, https://openalex.org/W3099878876 |
| malformed_doi | identifiers | pass | 0/100000 | 0.00 | Non-empty DOI values that do not match a basic DOI pattern. |  |
| missing_language | metadata | warn | 3/100000 | 0.00 | Records without detected language metadata. | https://openalex.org/W2963730812, https://openalex.org/W4206212643, https://openalex.org/W7126028315 |
| malformed_primary_location | metadata | pass | 0/100000 | 0.00 | primary_location values that are not objects. |  |
| malformed_locations | metadata | pass | 0/100000 | 0.00 | locations values that are not arrays. |  |
| missing_primary_source | metadata | warn | 1274/100000 | 1.27 | Records without nested primary_location.source.id. | https://openalex.org/W1849190772, https://openalex.org/W2095705004, https://openalex.org/W3106250896, https://openalex.org/W3118608800, https://openalex.org/W2047735993 |
| malformed_open_access | metadata | pass | 0/100000 | 0.00 | open_access values that are not objects. |  |
| malformed_concepts | topics | pass | 0/100000 | 0.00 | concepts values that are not arrays. |  |
| malformed_topics | topics | pass | 0/100000 | 0.00 | topics values that are not arrays. |  |

## Interpretation

Warnings identify data that the cleaning pipeline must handle explicitly. Errors indicate fields or structures that would break downstream assumptions if not fixed or quarantined in later Bronze/Silver/Gold processing.

Machine-readable results are saved to `reports/results/data_quality_report.json`.
