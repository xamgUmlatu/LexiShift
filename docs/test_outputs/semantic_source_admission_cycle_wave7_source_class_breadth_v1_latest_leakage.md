# en-es LLM Example-Frame Leakage Audit

- Status: `review`
- Generated: `2026-04-30T20:46:54Z`
- Batch: `en-es:wave7-source-class-breadth-v1:evidence-composite`
- Filtered batch: `en-es:wave7-source-class-breadth-v1:evidence-composite:filtered`

## Summary

- Input rows: `195`
- Leakage hits: `0`
- Duplicate hits: `12`
- Rejected rows: `12`
- Kept rows: `183`
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
| `en-es-sentence-veto-gross-repulsivo:shadow-en-es-sentence-veto-gross-repulsivo-gruesa-shadow-quantity-dozen-count-frame-1` | `en-es:sentence-veto:gross:repulsivo` | twelve dozen | `en-es-sentence-veto-gross-repulsivo:shadow-en-es-sentence-veto-gross-repulsivo-gruesa-shadow-wordnet-definition-1` | `source_duplicate_exact_text` | 1.0 |
| `en-es-sentence-veto-cast-lanzamiento:shadow-en-es-sentence-veto-cast-lanzamiento-molde-shadow-moulded-object-frame-1` | `en-es:sentence-veto:cast:lanzamiento` | object made in a mould | `en-es-sentence-veto-cast-lanzamiento:shadow-en-es-sentence-veto-cast-lanzamiento-molde-shadow-translation-sense-1` | `source_duplicate_token_sequence_contained` | 0.625 |
| `en-es-sentence-veto-fix-aprieto:active-en-es-sentence-veto-fix-aprieto-active-difficult-situation-frame-1` | `en-es:sentence-veto:fix:aprieto` | a difficult situation or dilemma | `en-es-sentence-veto-fix-aprieto:active-en-es-sentence-veto-fix-aprieto-active-translation-sense-1` | `source_duplicate_token_sequence_contained` | 0.625 |
| `en-es-sentence-veto-full-lleno:active-en-es-sentence-veto-full-lleno-active-full-capacity-frame-2` | `en-es:sentence-veto:full:lleno` | containing the maximum possible amount | `en-es-sentence-veto-full-lleno:active-en-es-sentence-veto-full-lleno-active-translation-sense-1` | `source_duplicate_token_sequence_contained` | 0.625 |
| `en-es-sentence-veto-even-tarde:active-en-es-sentence-veto-even-tarde-active-evening-time-frame-1` | `en-es:sentence-veto:even:tarde` | evening or latter part of the day | `en-es-sentence-veto-even-tarde:active-wordnet-definition-1` | `source_duplicate_token_sequence_contained` | 0.3333 |
| `en-es-sentence-veto-meet-adecuado:shadow-en-es-sentence-veto-meet-adecuado-encontrar-shadow-meeting-encounter-frame-1` | `en-es:sentence-veto:meet:adecuado` | come together | `en-es-sentence-veto-meet-adecuado:shadow-en-es-sentence-veto-meet-adecuado-encontrar-shadow-wordnet-definition-1` | `source_duplicate_exact_text` | 1.0 |
| `en-es-sentence-veto-meet-adecuado:shadow-en-es-sentence-veto-meet-adecuado-encontrar-shadow-meeting-encounter-frame-3` | `en-es:sentence-veto:meet:adecuado` | come face to face | `en-es-sentence-veto-meet-adecuado:shadow-en-es-sentence-veto-meet-adecuado-encontrar-shadow-translation-sense-1` | `source_duplicate_token_sequence_contained` | 0.3 |
| `en-es-sentence-veto-squeeze-crisis:shadow-en-es-sentence-veto-squeeze-crisis-apretujar-shadow-tight-physical-fit-frame-1` | `en-es:sentence-veto:squeeze:crisis` | fit into a tight place | `en-es-sentence-veto-squeeze-crisis:shadow-en-es-sentence-veto-squeeze-crisis-apretujar-shadow-translation-sense-1` | `source_duplicate_token_sequence_contained` | 0.5556 |
| `en-es-sentence-veto-squeeze-crisis:shadow-en-es-sentence-veto-squeeze-crisis-apretujar-shadow-tight-physical-fit-frame-3` | `en-es:sentence-veto:squeeze:crisis` | squeezed into a tight space | `en-es-sentence-veto-squeeze-crisis:shadow-en-es-sentence-veto-squeeze-crisis-apretujar-shadow-wordnet-definition-1` | `source_duplicate_token_sequence_contained` | 0.5 |

## Recommendation

- Use the filtered batch for downstream prototype reads, and replace the source-duplicate rows before any promotion claim.
