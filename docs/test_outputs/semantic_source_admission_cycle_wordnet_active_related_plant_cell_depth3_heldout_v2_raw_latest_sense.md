# en-es LLM Example-Frame Sense-Discrimination Audit

- Status: `review`
- Generated: `2026-04-25T05:28:03Z`
- Batch: `en-es:example-frame-composite:reverse-aux-wordnet-wiktextract-wordnet-active-related-plant-cell-depth3-heldout-v2-raw-v1`
- Admitted batch: `en-es:example-frame-composite:reverse-aux-wordnet-wiktextract-wordnet-active-related-plant-cell-depth3-heldout-v2-raw-v1:sense-admitted`

## Summary

- Input rows: `136`
- Semantic rows: `136`
- Semantic admitted rows: `133`
- Semantic rejected rows: `3`
- Non-semantic passthrough rows: `0`
- Admitted rows: `133`
- Scorers: `sentence_transformer_cosine`
- Evidence view: `all_evidence_text`
- Min intended score: `0.5`
- Min margin: `0.0`
- Rejection reasons: `{"competitor_sense_not_lower": 3}`

## Rejected Rows

| Row | Family | Relation | Intended | Reason | Best Scorer | Intended | Competitor | Margin |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `en-es-sentence-veto-cell-celula:active-wordnet-definition-2` | `en-es:sentence-veto:cell:celula` | `anchor_cue` | `en-es:sentence-veto:cell:celula:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.667993 | 0.691692 | -0.0237 |
| `en-es-sentence-veto-cell-celula:active-wordnet-definition-3` | `en-es:sentence-veto:cell:celula` | `anchor_cue` | `en-es:sentence-veto:cell:celula:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.623825 | 0.706228 | -0.082404 |
| `en-es-sentence-veto-cell-celula:shadow-en-es-sentence-veto-cell-celda-shadow-wordnet-example-3` | `en-es:sentence-veto:cell:celula` | `shadow_candidate` | `en-es:sentence-veto:cell:celda:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.577662 | 0.785997 | -0.208335 |

## Recommendation

- Use the admitted batch only as an analysis artifact. Replace or quarantine rejected active/shadow rows before any promotion-candidate merge.
