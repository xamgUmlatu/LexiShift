# en-es LLM Example-Frame Sense-Discrimination Audit

- Status: `ok`
- Generated: `2026-04-25T04:49:21Z`
- Batch: `en-es:example-frame-composite:reverse-aux-wordnet-wiktextract-wordnet-active-related-plant-heldout-clean-v1`
- Admitted batch: `en-es:example-frame-composite:reverse-aux-wordnet-wiktextract-wordnet-active-related-plant-heldout-clean-v1:sense-admitted`

## Summary

- Input rows: `79`
- Semantic rows: `79`
- Semantic admitted rows: `79`
- Semantic rejected rows: `0`
- Non-semantic passthrough rows: `0`
- Admitted rows: `79`
- Scorers: `sentence_transformer_cosine`
- Evidence view: `all_evidence_text`
- Min intended score: `0.5`
- Min margin: `0.0`
- Rejection reasons: `{}`

## Rejected Rows

| Row | Family | Relation | Intended | Reason | Best Scorer | Intended | Competitor | Margin |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `none` | `n/a` | `n/a` | `n/a` | `n/a` | `n/a` | 0 | 0 | 0 |

## Recommendation

- All active/shadow rows pass sense-discrimination admission; use the admitted batch for merge and downstream ablation.
