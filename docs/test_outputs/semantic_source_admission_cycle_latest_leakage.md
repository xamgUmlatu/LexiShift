# en-es LLM Example-Frame Leakage Audit

- Status: `review`
- Generated: `2026-04-25T01:25:12Z`
- Batch: `en-es:example-frame-composite:balanced-plus-source-coverage-filtered-safe-v2-20260425a`
- Filtered batch: `en-es:example-frame-composite:balanced-plus-source-coverage-filtered-safe-v2-20260425a:filtered`

## Summary

- Input rows: `60`
- Leakage hits: `0`
- Duplicate hits: `16`
- Rejected rows: `16`
- Kept rows: `44`
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
| `en-es-sentence-veto-plant-planta:active-reverse-aux` | `en-es:sentence-veto:plant:planta` | organism capable of photosynthesis | `en-es-sentence-veto-plant-planta:active-reverse-aux` | `source_duplicate_exact_text` | 1.0 |
| `en-es-sentence-veto-drink-bebida:active-reverse-aux` | `en-es:sentence-veto:drink:bebida` | served beverage | `en-es-sentence-veto-drink-bebida:active-reverse-aux` | `source_duplicate_exact_text` | 1.0 |
| `en-es-sentence-veto-drink-bebida:shadow-en-es-sentence-veto-drink-beber-shadow-reverse-aux` | `en-es:sentence-veto:drink:bebida` | consume liquid through the mouth | `en-es-sentence-veto-drink-bebida:shadow-en-es-sentence-veto-drink-beber-shadow-reverse-aux` | `source_duplicate_exact_text` | 1.0 |
| `en-es-sentence-veto-play-obra:shadow-en-es-sentence-veto-play-jugar-shadow-reverse-aux` | `en-es:sentence-veto:play:obra` | act in a manner such that one has fun | `en-es-sentence-veto-play-obra:shadow-en-es-sentence-veto-play-jugar-shadow-reverse-aux` | `source_duplicate_exact_text` | 1.0 |
| `en-es-sentence-veto-watch-reloj:active-reverse-aux` | `en-es:sentence-veto:watch:reloj` | portable or wearable timepiece | `en-es-sentence-veto-watch-reloj:active-reverse-aux` | `source_duplicate_exact_text` | 1.0 |
| `en-es-sentence-veto-watch-reloj:shadow-en-es-sentence-veto-watch-vigilar-shadow-reverse-aux` | `en-es:sentence-veto:watch:reloj` | to attend or guard | `en-es-sentence-veto-watch-reloj:shadow-en-es-sentence-veto-watch-vigilar-shadow-reverse-aux` | `source_duplicate_exact_text` | 1.0 |
| `en-es-sentence-veto-check-cheque:active-reverse-aux` | `en-es:sentence-veto:check:cheque` | mark used as an indicator | `en-es-sentence-veto-check-cheque:active-reverse-aux` | `source_duplicate_exact_text` | 1.0 |
| `en-es-sentence-veto-order-pedido:active-reverse-aux` | `en-es:sentence-veto:order:pedido` | request for some product or service | `en-es-sentence-veto-order-pedido:active-reverse-aux` | `source_duplicate_exact_text` | 1.0 |
| `en-es-sentence-veto-order-pedido:shadow-en-es-sentence-veto-order-ordenar-shadow-reverse-aux` | `en-es:sentence-veto:order:pedido` | to set in (any) order | `en-es-sentence-veto-order-pedido:shadow-en-es-sentence-veto-order-ordenar-shadow-reverse-aux` | `source_duplicate_exact_text` | 1.0 |
| `en-es-sentence-veto-trip-viaje:active-reverse-aux` | `en-es:sentence-veto:trip:viaje` | journey | `en-es-sentence-veto-trip-viaje:active-reverse-aux` | `source_duplicate_exact_text` | 1.0 |
| `en-es-sentence-veto-trip-viaje:shadow-en-es-sentence-veto-trip-viaje-shadow-reverse-aux` | `en-es:sentence-veto:trip:viaje` | stumble or misstep | `en-es-sentence-veto-trip-viaje:shadow-en-es-sentence-veto-trip-viaje-shadow-reverse-aux` | `source_duplicate_exact_text` | 1.0 |
| `en-es-sentence-veto-report-informe:active-reverse-aux` | `en-es:sentence-veto:report:informe` | information describing events | `en-es-sentence-veto-report-informe:active-reverse-aux` | `source_duplicate_exact_text` | 1.0 |
| `en-es-sentence-veto-report-informe:shadow-en-es-sentence-veto-report-informar-shadow-reverse-aux` | `en-es:sentence-veto:report:informe` | to relate details of | `en-es-sentence-veto-report-informe:shadow-en-es-sentence-veto-report-informar-shadow-reverse-aux` | `source_duplicate_exact_text` | 1.0 |
| `en-es-sentence-veto-check-cheque:llm:active:remediation-active-002:v1` | `en-es:sentence-veto:check:cheque` | She mailed the rent check with the signed lease yesterday. | `en-es-sentence-veto-check-cheque:llm:active:missing:v1` | `source_duplicate_token_sequence_contained` | 0.8 |
| `en-es-sentence-veto-order-pedido:llm:active:remediation-active-002:v1` | `en-es:sentence-veto:order:pedido` | I placed an order for two laptops and extra chargers online. | `en-es-sentence-veto-order-pedido:llm:active:missing:v1` | `source_duplicate_token_sequence_contained` | 0.75 |
| `en-es-sentence-veto-report-informe:llm:shadow:en-es-sentence-veto-report-informar-shadow:remediation-shadow-003-004:v1` | `en-es:sentence-veto:report:informe` | Please report the delay to the manager before noon. | `en-es-sentence-veto-report-informe:llm:shadow:en-es-sentence-veto-report-informar-shadow:missing:v1` | `source_duplicate_exact_text` | 1.0 |

## Recommendation

- Use the filtered batch for downstream prototype reads, and replace the source-duplicate rows before any promotion claim.
