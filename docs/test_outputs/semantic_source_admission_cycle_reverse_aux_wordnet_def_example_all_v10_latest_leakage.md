# en-es LLM Example-Frame Leakage Audit

- Status: `review`
- Generated: `2026-04-25T01:42:40Z`
- Batch: `en-es:wordnet-example-frames:wordnet-definition-example-frames-all-v10-20260425a`
- Filtered batch: `en-es:wordnet-example-frames:wordnet-definition-example-frames-all-v10-20260425a:filtered`

## Summary

- Input rows: `62`
- Leakage hits: `0`
- Duplicate hits: `1`
- Rejected rows: `1`
- Kept rows: `61`
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
| `en-es-sentence-veto-table-mesa:shadow-en-es-sentence-veto-table-tabla-shadow-wordnet-definition-1` | `en-es:sentence-veto:table:mesa` | a set of data arranged in rows and columns | `en-es-sentence-veto-table-mesa:shadow-en-es-sentence-veto-table-tabla-shadow-reverse-aux` | `source_duplicate_token_sequence_contained` | 0.6 |

## Recommendation

- Use the filtered batch for downstream prototype reads, and replace the source-duplicate rows before any promotion claim.
