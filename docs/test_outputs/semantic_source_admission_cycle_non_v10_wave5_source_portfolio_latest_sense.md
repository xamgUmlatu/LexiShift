# en-es LLM Example-Frame Sense-Discrimination Audit

- Status: `ok`
- Generated: `2026-04-28T22:34:17Z`
- Batch: `en-es:wordnet-source-portfolio:non-v10-wave5-anypos-v1:cycle`
- Admitted batch: `en-es:wordnet-source-portfolio:non-v10-wave5-anypos-v1:cycle:sense-admitted`

## Summary

- Input rows: `51`
- Semantic rows: `51`
- Semantic admitted rows: `51`
- Semantic rejected rows: `0`
- Non-semantic passthrough rows: `0`
- Admitted rows: `51`
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
