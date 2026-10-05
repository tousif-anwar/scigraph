# Data Dictionary

Generated from observed OpenAlex sample records on 2026-10-05.

## Dataset Summary

- Records inspected: 100
- Unique publication IDs: 100
- Unique author IDs observed: 379
- Referenced works counted: 2101
- Publication-year range: [2020, 2026]
- Missing abstracts: 0
- Missing titles: 0
- Missing authors: 2
- Duplicate publication IDs: 0

## Observed Fields

| field | type | meaning | null % | example | used? | known quality issues |
| --- | --- | --- | ---: | --- | --- | --- |
| abstract_inverted_index | object (100) | OpenAlex abstract represented as an inverted index, not plaintext. | 0.00 | `{"(phosphorus": [25], "99.9%": [10], "By": [35], "HCs": [48], "These": [15], "accompanied": [2], "achieved,": [1], "activation": [23], "a...` | yes | Can be null; reconstructing text requires position ordering. |
| authorships | array (100) | Nested authorship records containing author and affiliation metadata. | 0.00 | `[{"affiliations": [{"institution_ids": ["https://openalex.org/I81605866"], "raw_affiliation_string": "R.N.E Laboratory, Multidisciplinary...` | yes | Nested structure may be empty; author identity resolution is imperfect. |
| cited_by_count | integer (100) | Number of works OpenAlex records as citing this work. | 0.00 | `8` | yes | No specific issue identified yet. |
| concepts | array (100) | Legacy OpenAlex concept tags with scores. | 0.00 | `[{"display_name": "Carbonization", "id": "https://openalex.org/C154877778", "level": 3, "score": 0.9370853900909424, "wikidata": "https:/...` | yes | Legacy field; useful for early analysis but should be interpreted carefully. |
| display_name | string (100) | OpenAlex display name for the work; often equivalent to title. | 0.00 | `"Influence of phosphorus activation and carbonization temperature on the electrochemical performance of hard carbon made from olive pomac...` | yes | May duplicate title and should not be treated as an independent text field. |
| doi | null (13), string (87) | Digital Object Identifier when available. | 13.00 | `"https://doi.org/10.1039/d5ra02547h"` | yes | May be null or inconsistently formatted. |
| id | string (100) | Stable OpenAlex work identifier. | 0.00 | `"https://openalex.org/W4411188445"` | yes | No specific issue identified yet. |
| language | null (7), string (93) | Detected language code when available. | 7.00 | `"en"` | yes | Detected language can be missing or imperfect. |
| locations | array (100) | All known source/location records for the work. | 0.00 | `[{"id": "doi:10.1039/d5ra02547h", "is_accepted": true, "is_oa": true, "is_published": true, "landing_page_url": "https://doi.org/10.1039/...` | no | Can be large and nested; not all locations have complete license/source data. |
| open_access | object (100) | Open access status metadata. | 0.00 | `{"any_repository_has_fulltext": true, "is_oa": true, "oa_status": "gold", "oa_url": "https://pubs.rsc.org/en/content/articlepdf/2025/ra/d...` | yes | Availability and license metadata may differ by location. |
| primary_location | object (100) | Primary source/location metadata for the work. | 0.00 | `{"id": "doi:10.1039/d5ra02547h", "is_accepted": true, "is_oa": true, "is_published": true, "landing_page_url": "https://doi.org/10.1039/d...` | yes | Nested venue/source metadata can be missing. |
| publication_date | string (100) | Publication date as provided by OpenAlex. | 0.00 | `"2025-01-01"` | yes | Can be null or less precise in source metadata. |
| publication_year | integer (100) | Publication year as provided by OpenAlex. | 0.00 | `2025` | yes | Should be validated for plausible range. |
| referenced_works | array (100) | OpenAlex work IDs cited by this work. | 0.00 | `["https://openalex.org/W1166011494", "https://openalex.org/W2011442509", "https://openalex.org/W2012437727", "https://openalex.org/W20298...` | yes | May be empty even for papers with bibliographies outside OpenAlex coverage. |
| title | string (100) | Publication title. | 0.00 | `"Influence of phosphorus activation and carbonization temperature on the electrochemical performance of hard carbon made from olive pomac...` | yes | May be missing, duplicated, or contain source encoding artifacts. |
| topics | array (100) | OpenAlex topic classifications when available. | 0.00 | `[{"display_name": "Advancements in Battery Materials", "domain": {"display_name": "Physical Sciences", "id": "https://openalex.org/domain...` | yes | May be absent for some records depending on OpenAlex coverage. |
| type | string (100) | OpenAlex work type, such as article. | 0.00 | `"article"` | yes | No specific issue identified yet. |

## Dataset Statistics

Machine-readable statistics are saved to `reports/results/schema_summary.json`.

Document types:

```json
{
  "article": 100
}
```

Top observed concepts:

```json
{
  "Art": 7,
  "Artificial intelligence": 10,
  "Biology": 20,
  "Business": 15,
  "Chemistry": 13,
  "Computer science": 31,
  "Economics": 11,
  "Engineering": 23,
  "Environmental science": 8,
  "Geography": 9,
  "Humanities": 9,
  "Internal medicine": 12,
  "Law": 8,
  "Materials science": 10,
  "Medicine": 33,
  "Philosophy": 7,
  "Physics": 16,
  "Political science": 13,
  "Psychology": 16,
  "Sociology": 12
}
```
