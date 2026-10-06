# Data Dictionary

Generated from observed OpenAlex sample records on 2026-10-06.

## Dataset Summary

- Records inspected: 2500
- Unique publication IDs: 2500
- Unique author IDs observed: 9274
- Referenced works counted: 53900
- Publication-year range: [2020, 2026]
- Missing abstracts: 0
- Missing titles: 0
- Missing authors: 39
- Duplicate publication IDs: 0

## Observed Fields

| field | type | meaning | null % | example | used? | known quality issues |
| --- | --- | --- | ---: | --- | --- | --- |
| abstract_inverted_index | object (2500) | OpenAlex abstract represented as an inverted index, not plaintext. | 0.00 | `{"(phosphorus": [25], "99.9%": [10], "By": [35], "HCs": [48], "These": [15], "accompanied": [2], "achieved,": [1], "activation": [23], "a...` | yes | Can be null; reconstructing text requires position ordering. |
| authorships | array (2500) | Nested authorship records containing author and affiliation metadata. | 0.00 | `[{"affiliations": [{"institution_ids": ["https://openalex.org/I81605866"], "raw_affiliation_string": "R.N.E Laboratory, Multidisciplinary...` | yes | Nested structure may be empty; author identity resolution is imperfect. |
| cited_by_count | integer (2500) | Number of works OpenAlex records as citing this work. | 0.00 | `8` | yes | No specific issue identified yet. |
| concepts | array (2500) | Legacy OpenAlex concept tags with scores. | 0.00 | `[{"display_name": "Carbonization", "id": "https://openalex.org/C154877778", "level": 3, "score": 0.9370853900909424, "wikidata": "https:/...` | yes | Legacy field; useful for early analysis but should be interpreted carefully. |
| display_name | string (2500) | OpenAlex display name for the work; often equivalent to title. | 0.00 | `"Influence of phosphorus activation and carbonization temperature on the electrochemical performance of hard carbon made from olive pomac...` | yes | May duplicate title and should not be treated as an independent text field. |
| doi | null (238), string (2262) | Digital Object Identifier when available. | 9.52 | `"https://doi.org/10.1039/d5ra02547h"` | yes | May be null or inconsistently formatted. |
| id | string (2500) | Stable OpenAlex work identifier. | 0.00 | `"https://openalex.org/W4411188445"` | yes | No specific issue identified yet. |
| language | null (215), string (2285) | Detected language code when available. | 8.60 | `"en"` | yes | Detected language can be missing or imperfect. |
| locations | array (2500) | All known source/location records for the work. | 0.00 | `[{"id": "doi:10.1039/d5ra02547h", "is_accepted": true, "is_oa": true, "is_published": true, "landing_page_url": "https://doi.org/10.1039/...` | no | Can be large and nested; not all locations have complete license/source data. |
| open_access | object (2500) | Open access status metadata. | 0.00 | `{"any_repository_has_fulltext": true, "is_oa": true, "oa_status": "gold", "oa_url": "https://pubs.rsc.org/en/content/articlepdf/2025/ra/d...` | yes | Availability and license metadata may differ by location. |
| primary_location | object (2500) | Primary source/location metadata for the work. | 0.00 | `{"id": "doi:10.1039/d5ra02547h", "is_accepted": true, "is_oa": true, "is_published": true, "landing_page_url": "https://doi.org/10.1039/d...` | yes | Nested venue/source metadata can be missing. |
| publication_date | string (2500) | Publication date as provided by OpenAlex. | 0.00 | `"2025-01-01"` | yes | Can be null or less precise in source metadata. |
| publication_year | integer (2500) | Publication year as provided by OpenAlex. | 0.00 | `2025` | yes | Should be validated for plausible range. |
| referenced_works | array (2500) | OpenAlex work IDs cited by this work. | 0.00 | `["https://openalex.org/W1166011494", "https://openalex.org/W2011442509", "https://openalex.org/W2012437727", "https://openalex.org/W20298...` | yes | May be empty even for papers with bibliographies outside OpenAlex coverage. |
| title | string (2500) | Publication title. | 0.00 | `"Influence of phosphorus activation and carbonization temperature on the electrochemical performance of hard carbon made from olive pomac...` | yes | May be missing, duplicated, or contain source encoding artifacts. |
| topics | array (2500) | OpenAlex topic classifications when available. | 0.00 | `[{"display_name": "Advancements in Battery Materials", "domain": {"display_name": "Physical Sciences", "id": "https://openalex.org/domain...` | yes | May be absent for some records depending on OpenAlex coverage. |
| type | string (2500) | OpenAlex work type, such as article. | 0.00 | `"article"` | yes | No specific issue identified yet. |

## Dataset Statistics

Machine-readable statistics are saved to `reports/results/schema_summary.json`.

Document types:

```json
{
  "article": 2500
}
```

Top observed concepts:

```json
{
  "Art": 203,
  "Artificial intelligence": 209,
  "Biology": 463,
  "Business": 281,
  "Chemistry": 312,
  "Computer science": 679,
  "Economics": 209,
  "Engineering": 315,
  "Geography": 216,
  "Humanities": 261,
  "Internal medicine": 291,
  "Law": 203,
  "Materials science": 214,
  "Mathematics": 262,
  "Medicine": 767,
  "Philosophy": 311,
  "Physics": 360,
  "Political science": 406,
  "Psychology": 422,
  "Sociology": 320
}
```
