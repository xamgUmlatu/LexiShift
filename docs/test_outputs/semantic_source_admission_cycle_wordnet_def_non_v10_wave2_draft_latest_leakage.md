# en-es LLM Example-Frame Leakage Audit

- Status: `ok`
- Generated: `2026-04-27T22:25:03Z`
- Batch: `en-es:wordnet-example-frames:wordnet-def-non-v10-wave2-draft-v1-20260428a`
- Filtered batch: `en-es:wordnet-example-frames:wordnet-def-non-v10-wave2-draft-v1-20260428a:filtered`

## Summary

- Input rows: `17`
- Leakage hits: `0`
- Duplicate hits: `0`
- Rejected rows: `0`
- Kept rows: `17`
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
