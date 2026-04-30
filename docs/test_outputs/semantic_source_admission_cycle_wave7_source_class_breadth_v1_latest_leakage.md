# en-es LLM Example-Frame Leakage Audit

- Status: `review`
- Generated: `2026-04-30T18:06:24Z`
- Batch: `en-es:wave7-source-class-breadth-v1:evidence-composite`
- Filtered batch: `en-es:wave7-source-class-breadth-v1:evidence-composite:filtered`

## Summary

- Input rows: `180`
- Leakage hits: `0`
- Duplicate hits: `4`
- Rejected rows: `4`
- Kept rows: `176`
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
| `en-es-sentence-veto-cast-lanzamiento:active-wordnet-definition-2` | `en-es:sentence-veto:cast:lanzamiento` | the act of throwing a fishing line out over the water by means of a rod and reel | `en-es-sentence-veto-cast-lanzamiento:active-wordnet-definition-1` | `source_duplicate_token_sequence_contained` | 0.2667 |
| `en-es-sentence-veto-score-tantos:shadow-en-es-sentence-veto-score-tantos-anotar-shadow-translation-sense-1` | `en-es:sentence-veto:score:tantos` | score verb sense: to earn points in a game | `en-es-sentence-veto-score-tantos:shadow-en-es-sentence-veto-score-tantos-anotar-shadow-wordnet-definition-1` | `source_duplicate_token_sequence_contained` | 0.4 |
| `en-es-sentence-veto-crash-choque:shadow-en-es-sentence-veto-crash-choque-chocar-shadow-translation-sense-1` | `en-es:sentence-veto:crash:choque` | crash verb sense: to collide, fall or come down violently | `en-es-sentence-veto-crash-choque:shadow-en-es-sentence-veto-crash-choque-chocar-shadow-wordnet-definition-1` | `source_duplicate_token_sequence_contained` | 0.5 |
| `en-es-sentence-veto-fix-aprieto:active-en-es-sentence-veto-fix-aprieto-active-difficulty-constraint-frame-1` | `en-es:sentence-veto:fix:aprieto` | a difficult situation or dilemma | `en-es-sentence-veto-fix-aprieto:active-en-es-sentence-veto-fix-aprieto-active-translation-sense-1` | `source_duplicate_token_sequence_contained` | 0.625 |

## Recommendation

- Use the filtered batch for downstream prototype reads, and replace the source-duplicate rows before any promotion claim.
