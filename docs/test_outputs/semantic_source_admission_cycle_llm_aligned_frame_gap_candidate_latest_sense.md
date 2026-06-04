# en-es LLM Example-Frame Sense-Discrimination Audit

- Status: `review`
- Generated: `2026-04-28T21:02:34Z`
- Batch: `en-es:example-frame-composite:llm-aligned-source-frame-gap-v1-20260429a`
- Admitted batch: `en-es:example-frame-composite:llm-aligned-source-frame-gap-v1-20260429a:sense-admitted`

## Summary

- Input rows: `37`
- Semantic rows: `37`
- Semantic admitted rows: `36`
- Semantic rejected rows: `1`
- Non-semantic passthrough rows: `0`
- Admitted rows: `36`
- Scorers: `sentence_transformer_cosine`
- Evidence view: `all_evidence_text`
- Min intended score: `0.5`
- Min margin: `0.0`
- Rejection reasons: `{"competitor_sense_not_lower": 1}`

## Rejected Rows

| Row | Family | Relation | Intended | Reason | Best Scorer | Intended | Competitor | Margin |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `en-es-sentence-veto-report-informe:aligned-frame:shadow-example:en-es-sentence-veto-report-informar-shadow:candidate-02` | `en-es:sentence-veto:report:informe` | `shadow_candidate` | `en-es:sentence-veto:report:informar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.532599 | 0.53292 | -0.000321 |

## Recommendation

- Use the admitted batch only as an analysis artifact. Replace or quarantine rejected active/shadow rows before any promotion-candidate merge.
