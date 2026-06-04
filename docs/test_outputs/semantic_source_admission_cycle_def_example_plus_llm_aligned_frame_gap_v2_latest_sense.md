# en-es LLM Example-Frame Sense-Discrimination Audit

- Status: `ok`
- Generated: `2026-04-28T21:09:19Z`
- Batch: `en-es:example-frame-composite:def-example-plus-llm-aligned-source-frame-gap-v2-20260429a`
- Admitted batch: `en-es:example-frame-composite:def-example-plus-llm-aligned-source-frame-gap-v2-20260429a:sense-admitted`

## Summary

- Input rows: `126`
- Semantic rows: `126`
- Semantic admitted rows: `126`
- Semantic rejected rows: `0`
- Non-semantic passthrough rows: `0`
- Admitted rows: `126`
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
