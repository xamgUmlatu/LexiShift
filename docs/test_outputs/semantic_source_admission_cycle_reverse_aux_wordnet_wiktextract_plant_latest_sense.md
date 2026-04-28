# en-es LLM Example-Frame Sense-Discrimination Audit

- Status: `ok`
- Generated: `2026-04-25T02:09:18Z`
- Batch: `en-es:example-frame-composite:reverse-aux-wordnet-wiktextract-plant-v10-source-admission-latest`
- Admitted batch: `en-es:example-frame-composite:reverse-aux-wordnet-wiktextract-plant-v10-source-admission-latest:sense-admitted`

## Summary

- Input rows: `67`
- Semantic rows: `67`
- Semantic admitted rows: `67`
- Semantic rejected rows: `0`
- Non-semantic passthrough rows: `0`
- Admitted rows: `67`
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
