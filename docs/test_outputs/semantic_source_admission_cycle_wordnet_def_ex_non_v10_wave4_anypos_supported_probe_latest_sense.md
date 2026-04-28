# en-es LLM Example-Frame Sense-Discrimination Audit

- Status: `review`
- Generated: `2026-04-28T01:17:50Z`
- Batch: `en-es-wordnet-def-ex-non-v10-wave4-anypos-supported-probe-v1-20260428a-cycle`
- Admitted batch: `en-es-wordnet-def-ex-non-v10-wave4-anypos-supported-probe-v1-20260428a-cycle:sense-admitted`

## Summary

- Input rows: `72`
- Semantic rows: `72`
- Semantic admitted rows: `51`
- Semantic rejected rows: `21`
- Non-semantic passthrough rows: `0`
- Admitted rows: `51`
- Scorers: `sentence_transformer_cosine`
- Evidence view: `all_evidence_text`
- Min intended score: `0.5`
- Min margin: `0.0`
- Rejection reasons: `{"competitor_sense_not_lower": 20, "weak_intended_similarity": 1}`

## Rejected Rows

| Row | Family | Relation | Intended | Reason | Best Scorer | Intended | Competitor | Margin |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `en-es-sentence-veto-change-cambio:active-wordnet-definition-1` | `en-es:sentence-veto:change:cambio` | `anchor_cue` | `en-es:sentence-veto:change:cambio:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.54329 | 0.552022 | -0.008732 |
| `en-es-sentence-veto-change-cambio:active-wordnet-example-2` | `en-es:sentence-veto:change:cambio` | `anchor_cue` | `en-es:sentence-veto:change:cambio:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.566423 | 0.591511 | -0.025089 |
| `en-es-sentence-veto-look-aspecto:shadow-en-es-sentence-veto-look-aspecto-parecer-shadow-wordnet-definition-1` | `en-es:sentence-veto:look:aspecto` | `shadow_candidate` | `en-es:sentence-veto:look:aspecto:parecer:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.737194 | 0.812901 | -0.075707 |
| `en-es-sentence-veto-dry-seco:active-wordnet-example-2` | `en-es:sentence-veto:dry:seco` | `anchor_cue` | `en-es:sentence-veto:dry:seco:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.695505 | 0.745873 | -0.050367 |
| `en-es-sentence-veto-fast-r-pido:shadow-en-es-sentence-veto-fast-r-pido-ayunar-shadow-wordnet-example-2` | `en-es:sentence-veto:fast:r-pido` | `shadow_candidate` | `en-es:sentence-veto:fast:r-pido:ayunar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.568678 | 0.592721 | -0.024043 |
| `en-es-sentence-veto-mean-medio:active-wordnet-example-2` | `en-es:sentence-veto:mean:medio` | `anchor_cue` | `en-es:sentence-veto:mean:medio:active` | `weak_intended_similarity` | `sentence_transformer_cosine` | 0.48154 | 0.45867 | 0.02287 |
| `en-es-sentence-veto-end-fin:active-wordnet-definition-1` | `en-es:sentence-veto:end:fin` | `anchor_cue` | `en-es:sentence-veto:end:fin:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.733842 | 0.777175 | -0.043333 |
| `en-es-sentence-veto-end-fin:active-wordnet-example-2` | `en-es:sentence-veto:end:fin` | `anchor_cue` | `en-es:sentence-veto:end:fin:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.698032 | 0.70462 | -0.006588 |
| `en-es-sentence-veto-end-fin:shadow-en-es-sentence-veto-end-fin-acabar-shadow-wordnet-example-2` | `en-es:sentence-veto:end:fin` | `shadow_candidate` | `en-es:sentence-veto:end:fin:acabar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.559981 | 0.560592 | -0.000611 |
| `en-es-sentence-veto-offer-oferta:shadow-en-es-sentence-veto-offer-oferta-ofrecer-shadow-wordnet-example-2` | `en-es:sentence-veto:offer:oferta` | `shadow_candidate` | `en-es:sentence-veto:offer:oferta:ofrecer:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.528855 | 0.538553 | -0.009698 |
| `en-es-sentence-veto-rest-reposo:active-wordnet-definition-1` | `en-es:sentence-veto:rest:reposo` | `anchor_cue` | `en-es:sentence-veto:rest:reposo:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.748443 | 0.776135 | -0.027693 |
| `en-es-sentence-veto-rest-reposo:shadow-en-es-sentence-veto-rest-reposo-descanso-shadow-wordnet-example-2` | `en-es:sentence-veto:rest:reposo` | `shadow_candidate` | `en-es:sentence-veto:rest:reposo:descanso:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.696962 | 0.698522 | -0.001561 |
| `en-es-sentence-veto-rest-reposo:shadow-en-es-sentence-veto-rest-reposo-descansar-shadow-wordnet-definition-2` | `en-es:sentence-veto:rest:reposo` | `shadow_candidate` | `en-es:sentence-veto:rest:reposo:descansar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.666285 | 0.740296 | -0.074012 |
| `en-es-sentence-veto-present-presente:shadow-en-es-sentence-veto-present-presente-actual-shadow-wordnet-example-2` | `en-es:sentence-veto:present:presente` | `shadow_candidate` | `en-es:sentence-veto:present:presente:actual:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.721731 | 0.734921 | -0.01319 |
| `en-es-sentence-veto-sign-se-al:active-wordnet-example-2` | `en-es:sentence-veto:sign:se-al` | `anchor_cue` | `en-es:sentence-veto:sign:se-al:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.621593 | 0.647799 | -0.026206 |
| `en-es-sentence-veto-sign-se-al:shadow-en-es-sentence-veto-sign-se-al-se-a-shadow-wordnet-example-2` | `en-es:sentence-veto:sign:se-al` | `shadow_candidate` | `en-es:sentence-veto:sign:se-al:se-a:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.735111 | 0.738076 | -0.002966 |
| `en-es-sentence-veto-answer-respuesta:active-wordnet-definition-1` | `en-es:sentence-veto:answer:respuesta` | `anchor_cue` | `en-es:sentence-veto:answer:respuesta:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.730008 | 0.806748 | -0.07674 |
| `en-es-sentence-veto-answer-respuesta:shadow-en-es-sentence-veto-answer-respuesta-contestaci-n-shadow-wordnet-definition-1` | `en-es:sentence-veto:answer:respuesta` | `shadow_candidate` | `en-es:sentence-veto:answer:respuesta:contestaci-n:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.777361 | 0.806748 | -0.029387 |
| `en-es-sentence-veto-answer-respuesta:shadow-en-es-sentence-veto-answer-respuesta-contestaci-n-shadow-wordnet-example-2` | `en-es:sentence-veto:answer:respuesta` | `shadow_candidate` | `en-es:sentence-veto:answer:respuesta:contestaci-n:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.564832 | 0.599216 | -0.034384 |
| `en-es-sentence-veto-quiet-silencio:active-wordnet-example-2` | `en-es:sentence-veto:quiet:silencio` | `anchor_cue` | `en-es:sentence-veto:quiet:silencio:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.691358 | 0.725639 | -0.034281 |
| `en-es-sentence-veto-quiet-silencio:shadow-en-es-sentence-veto-quiet-silencio-calmar-shadow-wordnet-example-2` | `en-es:sentence-veto:quiet:silencio` | `shadow_candidate` | `en-es:sentence-veto:quiet:silencio:calmar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.653778 | 0.705952 | -0.052174 |

## Recommendation

- Use the admitted batch only as an analysis artifact. Replace or quarantine rejected active/shadow rows before any promotion-candidate merge.
