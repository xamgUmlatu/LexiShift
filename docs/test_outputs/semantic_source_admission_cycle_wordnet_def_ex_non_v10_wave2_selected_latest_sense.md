# en-es LLM Example-Frame Sense-Discrimination Audit

- Status: `review`
- Generated: `2026-04-27T22:53:31Z`
- Batch: `en-es:wordnet-def-ex-non-v10-wave2-selected-v1:source-admission-cycle`
- Admitted batch: `en-es:wordnet-def-ex-non-v10-wave2-selected-v1:source-admission-cycle:sense-admitted`

## Summary

- Input rows: `38`
- Semantic rows: `38`
- Semantic admitted rows: `30`
- Semantic rejected rows: `8`
- Non-semantic passthrough rows: `0`
- Admitted rows: `30`
- Scorers: `sentence_transformer_cosine`
- Evidence view: `all_evidence_text`
- Min intended score: `0.5`
- Min margin: `0.0`
- Rejection reasons: `{"competitor_sense_not_lower": 8}`

## Rejected Rows

| Row | Family | Relation | Intended | Reason | Best Scorer | Intended | Competitor | Margin |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `en-es-sentence-veto-look-aspecto:shadow-en-es-sentence-veto-look-aspecto-parecer-shadow-wordnet-definition-1` | `en-es:sentence-veto:look:aspecto` | `shadow_candidate` | `en-es:sentence-veto:look:aspecto:parecer:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.737194 | 0.812901 | -0.075707 |
| `en-es-sentence-veto-offer-oferta:shadow-en-es-sentence-veto-offer-oferta-ofrecer-shadow-wordnet-example-2` | `en-es:sentence-veto:offer:oferta` | `shadow_candidate` | `en-es:sentence-veto:offer:oferta:ofrecer:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.528855 | 0.538553 | -0.009698 |
| `en-es-sentence-veto-rest-reposo:shadow-en-es-sentence-veto-rest-reposo-descansar-shadow-wordnet-definition-2` | `en-es:sentence-veto:rest:reposo` | `shadow_candidate` | `en-es:sentence-veto:rest:reposo:descansar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.666285 | 0.683478 | -0.017193 |
| `en-es-sentence-veto-sign-se-al:active-wordnet-example-2` | `en-es:sentence-veto:sign:se-al` | `anchor_cue` | `en-es:sentence-veto:sign:se-al:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.621593 | 0.647799 | -0.026206 |
| `en-es-sentence-veto-sign-se-al:shadow-en-es-sentence-veto-sign-se-al-se-a-shadow-wordnet-example-2` | `en-es:sentence-veto:sign:se-al` | `shadow_candidate` | `en-es:sentence-veto:sign:se-al:se-a:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.735111 | 0.738076 | -0.002966 |
| `en-es-sentence-veto-answer-respuesta:active-wordnet-definition-1` | `en-es:sentence-veto:answer:respuesta` | `anchor_cue` | `en-es:sentence-veto:answer:respuesta:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.730008 | 0.806748 | -0.07674 |
| `en-es-sentence-veto-answer-respuesta:shadow-en-es-sentence-veto-answer-respuesta-contestaci-n-shadow-wordnet-definition-1` | `en-es:sentence-veto:answer:respuesta` | `shadow_candidate` | `en-es:sentence-veto:answer:respuesta:contestaci-n:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.777361 | 0.806748 | -0.029387 |
| `en-es-sentence-veto-answer-respuesta:shadow-en-es-sentence-veto-answer-respuesta-contestaci-n-shadow-wordnet-example-2` | `en-es:sentence-veto:answer:respuesta` | `shadow_candidate` | `en-es:sentence-veto:answer:respuesta:contestaci-n:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.564832 | 0.599216 | -0.034384 |

## Recommendation

- Use the admitted batch only as an analysis artifact. Replace or quarantine rejected active/shadow rows before any promotion-candidate merge.
