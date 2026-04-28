# en-es LLM Example-Frame Sense-Discrimination Audit

- Status: `review`
- Generated: `2026-04-25T01:42:40Z`
- Batch: `en-es:example-frame-composite:reverse-aux-wordnet-def-example-all-v10-source-admission-latest`
- Admitted batch: `en-es:example-frame-composite:reverse-aux-wordnet-def-example-all-v10-source-admission-latest:sense-admitted`

## Summary

- Input rows: `93`
- Semantic rows: `93`
- Semantic admitted rows: `87`
- Semantic rejected rows: `6`
- Non-semantic passthrough rows: `0`
- Admitted rows: `87`
- Scorers: `sentence_transformer_cosine`
- Evidence view: `all_evidence_text`
- Min intended score: `0.5`
- Min margin: `0.0`
- Rejection reasons: `{"competitor_sense_not_lower": 6}`

## Rejected Rows

| Row | Family | Relation | Intended | Reason | Best Scorer | Intended | Competitor | Margin |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `en-es-sentence-veto-cell-celula:active-wordnet-definition-2` | `en-es:sentence-veto:cell:celula` | `anchor_cue` | `en-es:sentence-veto:cell:celula:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.667993 | 0.691692 | -0.0237 |
| `en-es-sentence-veto-drink-bebida:active-wordnet-example-2` | `en-es:sentence-veto:drink:bebida` | `anchor_cue` | `en-es:sentence-veto:drink:bebida:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.76509 | 0.784039 | -0.018948 |
| `en-es-sentence-veto-drink-bebida:shadow-en-es-sentence-veto-drink-beber-shadow-wordnet-example-2` | `en-es:sentence-veto:drink:bebida` | `shadow_candidate` | `en-es:sentence-veto:drink:beber:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.662433 | 0.694093 | -0.03166 |
| `en-es-sentence-veto-play-obra:shadow-en-es-sentence-veto-play-jugar-shadow-wordnet-example-2` | `en-es:sentence-veto:play:obra` | `shadow_candidate` | `en-es:sentence-veto:play:jugar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.526126 | 0.536965 | -0.01084 |
| `en-es-sentence-veto-report-informe:shadow-en-es-sentence-veto-report-informar-shadow-wordnet-definition-1` | `en-es:sentence-veto:report:informe` | `shadow_candidate` | `en-es:sentence-veto:report:informar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.79552 | 0.800826 | -0.005306 |
| `en-es-sentence-veto-report-informe:shadow-en-es-sentence-veto-report-informar-shadow-wordnet-example-2` | `en-es:sentence-veto:report:informe` | `shadow_candidate` | `en-es:sentence-veto:report:informar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.524467 | 0.607957 | -0.08349 |

## Recommendation

- Use the admitted batch only as an analysis artifact. Replace or quarantine rejected active/shadow rows before any promotion-candidate merge.
