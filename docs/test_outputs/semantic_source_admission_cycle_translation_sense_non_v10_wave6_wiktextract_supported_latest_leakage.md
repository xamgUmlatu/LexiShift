# en-es LLM Example-Frame Leakage Audit

- Status: `ok`
- Generated: `2026-04-30T03:34:35Z`
- Batch: `en-es:translation-sense-evidence:translation-sense-non-v10-wave6-wiktextract-supported-v1-latest`
- Filtered batch: `en-es:translation-sense-evidence:translation-sense-non-v10-wave6-wiktextract-supported-v1-latest:filtered`

## Summary

- Input rows: `38`
- Leakage hits: `0`
- Duplicate hits: `0`
- Rejected rows: `0`
- Kept rows: `38`
- Jaccard threshold: `0.75`
- Duplicate jaccard threshold: `0.92`
- Min contained tokens: `5`
- Min duplicate tokens: `4`

## Leakage Rows

| Row | Family | Evidence | Matched Case | Reason | Jaccard |
| --- | --- | --- | --- | --- | ---: |
| `none` | `n/a` | n/a | `n/a` | `n/a` | 0 |

## Duplicate Rows

| Row | Family | Evidence | Matched Row | Reason | Jaccard |
| --- | --- | --- | --- | --- | ---: |
| `none` | `n/a` | n/a | `n/a` | `n/a` | 0 |

## Recommendation

- No benchmark-near-copy or source-duplicate rows were found; the batch can advance to the next admission gate.
