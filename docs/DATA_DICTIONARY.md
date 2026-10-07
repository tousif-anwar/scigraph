# Data Dictionary

Generated from observed OpenAlex sample records on 2026-10-06.

## Dataset Summary

- Records inspected: 74600
- Unique publication IDs: 74600
- Unique author IDs observed: 371312
- Referenced works counted: 6985577
- Publication-year range: [2010, 2026]
- Missing abstracts: 0
- Missing titles: 4
- Missing authors: 170
- Duplicate publication IDs: 0

## Observed Fields

| field | type | meaning | null % | example | used? | known quality issues |
| --- | --- | --- | ---: | --- | --- | --- |
| abstract_inverted_index | object (74600) | OpenAlex abstract represented as an inverted index, not plaintext. | 0.00 | `{"(LHD).": [16], "(neutrons": [34], "10%": [79], "2017,": [54], "CCD": [146], "Device": [15], "FY": [53], "For": [86], "Helical": [14], "...` | yes | Can be null; reconstructing text requires position ordering. |
| authorships | array (74600) | Nested authorship records containing author and affiliation metadata. | 0.00 | `[{"affiliations": [{"institution_ids": ["https://openalex.org/I199525922", "https://openalex.org/I4210108322"], "raw_affiliation_string":...` | yes | Nested structure may be empty; author identity resolution is imperfect. |
| cited_by_count | integer (74600) | Number of works OpenAlex records as citing this work. | 0.00 | `801217` | yes | No specific issue identified yet. |
| concepts | array (74600) | Legacy OpenAlex concept tags with scores. | 0.00 | `[{"display_name": "Radiation", "id": "https://openalex.org/C153385146", "level": 2, "score": 0.7057818174362183, "wikidata": "https://www...` | yes | Legacy field; useful for early analysis but should be interpreted carefully. |
| display_name | string (74600) | OpenAlex display name for the work; often equivalent to title. | 0.00 | `"Radiation Resistant Camera System for Monitoring Deuterium Plasma Discharges in the Large Helical Device"` | yes | May duplicate title and should not be treated as an independent text field. |
| doi | null (1484), string (73116) | Digital Object Identifier when available. | 1.99 | `"https://doi.org/10.1585/pfr.15.2402039"` | yes | May be null or inconsistently formatted. |
| id | string (74600) | Stable OpenAlex work identifier. | 0.00 | `"https://openalex.org/W3038568908"` | yes | No specific issue identified yet. |
| language | null (3), string (74597) | Detected language code when available. | 0.00 | `"en"` | yes | Detected language can be missing or imperfect. |
| locations | array (74600) | All known source/location records for the work. | 0.00 | `[{"id": "doi:10.1585/pfr.15.2402039", "is_accepted": true, "is_oa": true, "is_published": true, "landing_page_url": "https://doi.org/10.1...` | no | Can be large and nested; not all locations have complete license/source data. |
| open_access | object (74600) | Open access status metadata. | 0.00 | `{"any_repository_has_fulltext": true, "is_oa": true, "oa_status": "diamond", "oa_url": "https://www.jstage.jst.go.jp/article/pfr/15/0/15_...` | yes | Availability and license metadata may differ by location. |
| primary_location | object (74600) | Primary source/location metadata for the work. | 0.00 | `{"id": "doi:10.1585/pfr.15.2402039", "is_accepted": true, "is_oa": true, "is_published": true, "landing_page_url": "https://doi.org/10.15...` | yes | Nested venue/source metadata can be missing. |
| publication_date | string (74600) | Publication date as provided by OpenAlex. | 0.00 | `"2020-06-08"` | yes | Can be null or less precise in source metadata. |
| publication_year | integer (74600) | Publication year as provided by OpenAlex. | 0.00 | `2020` | yes | Should be validated for plausible range. |
| referenced_works | array (74600) | OpenAlex work IDs cited by this work. | 0.00 | `["https://openalex.org/W2069091362", "https://openalex.org/W2151240562", "https://openalex.org/W2527753843", "https://openalex.org/W25906...` | yes | May be empty even for papers with bibliographies outside OpenAlex coverage. |
| title | string (74600) | Publication title. | 0.00 | `"Radiation Resistant Camera System for Monitoring Deuterium Plasma Discharges in the Large Helical Device"` | yes | May be missing, duplicated, or contain source encoding artifacts. |
| topics | array (74600) | OpenAlex topic classifications when available. | 0.00 | `[{"display_name": "Magnetic confinement fusion research", "domain": {"display_name": "Physical Sciences", "id": "https://openalex.org/dom...` | yes | May be absent for some records depending on OpenAlex coverage. |
| type | string (74600) | OpenAlex work type, such as article. | 0.00 | `"article"` | yes | No specific issue identified yet. |

## Dataset Statistics

Machine-readable statistics are saved to `reports/results/schema_summary.json`.

Document types:

```json
{
  "article": 74600
}
```

Top observed concepts:

```json
{
  "Artificial intelligence": 8697,
  "Biochemistry": 9737,
  "Biology": 28206,
  "Chemistry": 17233,
  "Computer science": 23592,
  "Economics": 7541,
  "Engineering": 14159,
  "Gene": 9948,
  "Genetics": 10629,
  "Internal medicine": 14970,
  "Materials science": 13494,
  "Mathematics": 9735,
  "Medicine": 27666,
  "Nanotechnology": 9057,
  "Organic chemistry": 8755,
  "Pathology": 8269,
  "Physics": 15333,
  "Political science": 7371,
  "Psychology": 9431,
  "Quantum mechanics": 7478
}
```
