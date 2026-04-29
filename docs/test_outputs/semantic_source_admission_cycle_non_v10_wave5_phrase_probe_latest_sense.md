# en-es LLM Example-Frame Sense-Discrimination Audit

- Status: `ok`
- Generated: `2026-04-29T00:12:29Z`
- Batch: `en-es:wordnet-source-portfolio:non-v10-wave5-phrase-probe-cycle`
- Admitted batch: `en-es:wordnet-source-portfolio:non-v10-wave5-phrase-probe-cycle:sense-admitted`

## Summary

- Input rows: `58`
- Semantic rows: `51`
- Semantic admitted rows: `51`
- Semantic rejected rows: `0`
- Non-semantic passthrough rows: `7`
- Admitted rows: `58`
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
