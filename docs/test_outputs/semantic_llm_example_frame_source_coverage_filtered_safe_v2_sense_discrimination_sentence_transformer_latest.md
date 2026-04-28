# en-es LLM Example-Frame Sense-Discrimination Audit

- Status: `review`
- Generated: `2026-04-25T00:53:22Z`
- Batch: `en-es:example-frame-composite:balanced-plus-source-coverage-filtered-safe-v2-20260425a`
- Admitted batch: `en-es:example-frame-composite:balanced-plus-source-coverage-filtered-safe-v2-20260425a:sense-admitted`

## Summary

- Input rows: `60`
- Semantic rows: `52`
- Semantic admitted rows: `48`
- Semantic rejected rows: `4`
- Non-semantic passthrough rows: `8`
- Admitted rows: `56`
- Scorers: `sentence_transformer_cosine`
- Evidence view: `all_evidence_text`
- Min intended score: `0.5`
- Min margin: `0.01`
- Rejection reasons: `{"competitor_sense_not_lower": 2, "insufficient_sense_margin": 2}`

## Rejected Rows

| Row | Family | Relation | Intended | Reason | Best Scorer | Intended | Competitor | Margin |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `en-es-sentence-veto-check-cheque:active-reverse-aux` | `en-es:sentence-veto:check:cheque` | `anchor_cue` | `en-es:sentence-veto:check:cheque:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.645188 | 0.653943 | -0.008755 |
| `en-es-sentence-veto-order-pedido:shadow-en-es-sentence-veto-order-ordenar-shadow-reverse-aux` | `en-es:sentence-veto:order:pedido` | `shadow_candidate` | `en-es:sentence-veto:order:ordenar:shadow` | `insufficient_sense_margin` | `sentence_transformer_cosine` | 0.776653 | 0.772987 | 0.003666 |
| `en-es-sentence-veto-report-informe:active-reverse-aux` | `en-es:sentence-veto:report:informe` | `anchor_cue` | `en-es:sentence-veto:report:informe:active` | `insufficient_sense_margin` | `sentence_transformer_cosine` | 0.734216 | 0.725876 | 0.00834 |
| `en-es-sentence-veto-report-informe:shadow-en-es-sentence-veto-report-informar-shadow-reverse-aux` | `en-es:sentence-veto:report:informe` | `shadow_candidate` | `en-es:sentence-veto:report:informar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.714239 | 0.739001 | -0.024762 |

## Recommendation

- Use the admitted batch only as an analysis artifact. Replace or quarantine rejected active/shadow rows before any promotion-candidate merge.
