# en-es LLM Example-Frame Sense-Discrimination Audit

- Status: `ok`
- Generated: `2026-04-26T03:25:23Z`
- Batch: `en-es:source-admission-cycle:wordnet-def-source-non-v10-probe-v1-20260426a`
- Admitted batch: `en-es:source-admission-cycle:wordnet-def-source-non-v10-probe-v1-20260426a:sense-admitted`

## Summary

- Input rows: `18`
- Semantic rows: `18`
- Semantic admitted rows: `18`
- Semantic rejected rows: `0`
- Non-semantic passthrough rows: `0`
- Admitted rows: `18`
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
