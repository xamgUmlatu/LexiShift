# en-es LLM Example-Frame Sense-Discrimination Audit

- Status: `ok`
- Generated: `2026-04-30T18:16:15Z`
- Batch: `en-es:wave7-source-class-breadth-v1:phrase-control-triage:cycle`
- Admitted batch: `en-es:wave7-source-class-breadth-v1:phrase-control-triage:cycle:sense-admitted`

## Summary

- Input rows: `307`
- Semantic rows: `134`
- Semantic admitted rows: `134`
- Semantic rejected rows: `0`
- Non-semantic passthrough rows: `173`
- Admitted rows: `307`
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
