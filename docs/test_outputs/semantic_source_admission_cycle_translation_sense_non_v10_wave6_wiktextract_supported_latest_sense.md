# en-es LLM Example-Frame Sense-Discrimination Audit

- Status: `ok`
- Generated: `2026-04-30T03:34:35Z`
- Batch: `en-es:wordnet-plus-translation-sense:non-v10-wave6-wiktextract-supported-v1:cycle`
- Admitted batch: `en-es:wordnet-plus-translation-sense:non-v10-wave6-wiktextract-supported-v1:cycle:sense-admitted`

## Summary

- Input rows: `99`
- Semantic rows: `99`
- Semantic admitted rows: `99`
- Semantic rejected rows: `0`
- Non-semantic passthrough rows: `0`
- Admitted rows: `99`
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
