# en-es LLM Example-Frame Leakage Audit

- Status: `review`
- Generated: `2026-04-25T03:13:04Z`
- Batch: `en-es:wordnet-example-frames:wordnet-plant-active-related-heldout-v1-20260425a`
- Filtered batch: `en-es:wordnet-example-frames:wordnet-plant-active-related-heldout-v1-20260425a:filtered`

## Summary

- Input rows: `14`
- Leakage hits: `0`
- Duplicate hits: `2`
- Rejected rows: `2`
- Kept rows: `12`
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
| `en-es-sentence-veto-plant-planta:active-wordnet-definition-1` | `en-es:sentence-veto:plant:planta` | (botany) a living organism lacking the power of locomotion | `en-es-sentence-veto-plant-planta:active-wordnet-definition-1` | `source_duplicate_exact_text` | 1.0 |
| `en-es-sentence-veto-plant-planta:shadow-en-es-sentence-veto-plant-fabrica-shadow-wordnet-example-2` | `en-es:sentence-veto:plant:planta` | they built a large plant to manufacture automobiles | `en-es-sentence-veto-plant-planta:shadow-en-es-sentence-veto-plant-fabrica-shadow-wordnet-example-1` | `source_duplicate_exact_text` | 1.0 |

## Recommendation

- Use the filtered batch for downstream prototype reads, and replace the source-duplicate rows before any promotion claim.
