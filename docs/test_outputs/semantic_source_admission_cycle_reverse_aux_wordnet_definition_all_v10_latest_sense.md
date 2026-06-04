# en-es LLM Example-Frame Sense-Discrimination Audit

- Status: `review`
- Generated: `2026-04-25T01:43:28Z`
- Batch: `en-es:example-frame-composite:reverse-aux-wordnet-definition-all-v10-source-admission-latest`
- Admitted batch: `en-es:example-frame-composite:reverse-aux-wordnet-definition-all-v10-source-admission-latest:sense-admitted`

## Summary

- Input rows: `65`
- Semantic rows: `65`
- Semantic admitted rows: `64`
- Semantic rejected rows: `1`
- Non-semantic passthrough rows: `0`
- Admitted rows: `64`
- Scorers: `sentence_transformer_cosine`
- Evidence view: `all_evidence_text`
- Min intended score: `0.5`
- Min margin: `0.0`
- Rejection reasons: `{"competitor_sense_not_lower": 1}`

## Rejected Rows

| Row | Family | Relation | Intended | Reason | Best Scorer | Intended | Competitor | Margin |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `en-es-sentence-veto-report-informe:shadow-en-es-sentence-veto-report-informar-shadow-wordnet-definition-1` | `en-es:sentence-veto:report:informe` | `shadow_candidate` | `en-es:sentence-veto:report:informar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.79552 | 0.800826 | -0.005306 |

## Recommendation

- Use the admitted batch only as an analysis artifact. Replace or quarantine rejected active/shadow rows before any promotion-candidate merge.
