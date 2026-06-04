# en-es LLM Example-Frame Leakage Audit

- Status: `ok`
- Generated: `2026-04-26T03:21:02Z`
- Batch: `en-es:wordnet-example-frames:wordnet-source-non-v10-probe-v1-20260426a`
- Filtered batch: `en-es:wordnet-example-frames:wordnet-source-non-v10-probe-v1-20260426a:filtered`

## Summary

- Input rows: `18`
- Leakage hits: `0`
- Duplicate hits: `0`
- Rejected rows: `0`
- Kept rows: `18`
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
