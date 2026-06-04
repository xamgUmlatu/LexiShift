# en-es LLM Example-Frame Sense-Discrimination Audit

- Status: `review`
- Generated: `2026-04-28T01:29:22Z`
- Batch: `en-es-wordnet-def-ex-non-v10-wave4-anypos-supported-probe-ranked-slate-v1-20260428a`
- Admitted batch: `en-es-wordnet-def-ex-non-v10-wave4-anypos-supported-probe-ranked-slate-v1-20260428a:sense-admitted`

## Summary

- Input rows: `72`
- Semantic rows: `72`
- Semantic admitted rows: `49`
- Semantic rejected rows: `23`
- Non-semantic passthrough rows: `0`
- Admitted rows: `49`
- Scorers: `sentence_transformer_cosine`
- Evidence view: `all_evidence_text`
- Min intended score: `0.5`
- Min margin: `0.0`
- Rejection reasons: `{"competitor_sense_not_lower": 22, "weak_intended_similarity": 1}`

## Rejected Rows

| Row | Family | Relation | Intended | Reason | Best Scorer | Intended | Competitor | Margin |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `en-es-sentence-veto-change-cambio:active-wordnet-example-2` | `en-es:sentence-veto:change:cambio` | `anchor_cue` | `en-es:sentence-veto:change:cambio:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.629348 | 0.647897 | -0.018549 |
| `en-es-sentence-veto-change-cambio:shadow-en-es-sentence-veto-change-cambio-cambiar-shadow-wordnet-definition-1` | `en-es:sentence-veto:change:cambio` | `shadow_candidate` | `en-es:sentence-veto:change:cambio:cambiar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.837962 | 0.84906 | -0.011099 |
| `en-es-sentence-veto-look-aspecto:shadow-en-es-sentence-veto-look-aspecto-parecer-shadow-wordnet-definition-1` | `en-es:sentence-veto:look:aspecto` | `shadow_candidate` | `en-es:sentence-veto:look:aspecto:parecer:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.737194 | 0.812901 | -0.075707 |
| `en-es-sentence-veto-dry-seco:active-wordnet-example-2` | `en-es:sentence-veto:dry:seco` | `anchor_cue` | `en-es:sentence-veto:dry:seco:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.695505 | 0.745873 | -0.050367 |
| `en-es-sentence-veto-use-uso:shadow-en-es-sentence-veto-use-uso-usar-shadow-wordnet-entry_sentence-2` | `en-es:sentence-veto:use:uso` | `shadow_candidate` | `en-es:sentence-veto:use:uso:usar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.617329 | 0.636762 | -0.019433 |
| `en-es-sentence-veto-fast-r-pido:shadow-en-es-sentence-veto-fast-r-pido-ayunar-shadow-wordnet-example-2` | `en-es:sentence-veto:fast:r-pido` | `shadow_candidate` | `en-es:sentence-veto:fast:r-pido:ayunar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.568678 | 0.592721 | -0.024043 |
| `en-es-sentence-veto-land-tierra:shadow-en-es-sentence-veto-land-tierra-pa-s-shadow-wordnet-example-2` | `en-es:sentence-veto:land:tierra` | `shadow_candidate` | `en-es:sentence-veto:land:tierra:pa-s:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.632322 | 0.665272 | -0.03295 |
| `en-es-sentence-veto-mean-medio:active-wordnet-example-2` | `en-es:sentence-veto:mean:medio` | `anchor_cue` | `en-es:sentence-veto:mean:medio:active` | `weak_intended_similarity` | `sentence_transformer_cosine` | 0.48154 | 0.45867 | 0.02287 |
| `en-es-sentence-veto-end-fin:shadow-en-es-sentence-veto-end-fin-acabar-shadow-wordnet-example-2` | `en-es:sentence-veto:end:fin` | `shadow_candidate` | `en-es:sentence-veto:end:fin:acabar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.559981 | 0.560592 | -0.000611 |
| `en-es-sentence-veto-offer-oferta:shadow-en-es-sentence-veto-offer-oferta-ofrecer-shadow-wordnet-example-2` | `en-es:sentence-veto:offer:oferta` | `shadow_candidate` | `en-es:sentence-veto:offer:oferta:ofrecer:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.528855 | 0.538553 | -0.009698 |
| `en-es-sentence-veto-rest-reposo:active-wordnet-definition-1` | `en-es:sentence-veto:rest:reposo` | `anchor_cue` | `en-es:sentence-veto:rest:reposo:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.557271 | 0.609924 | -0.052653 |
| `en-es-sentence-veto-rest-reposo:active-wordnet-example-2` | `en-es:sentence-veto:rest:reposo` | `anchor_cue` | `en-es:sentence-veto:rest:reposo:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.597542 | 0.623458 | -0.025915 |
| `en-es-sentence-veto-rest-reposo:shadow-en-es-sentence-veto-rest-reposo-descanso-shadow-wordnet-definition-1` | `en-es:sentence-veto:rest:reposo` | `shadow_candidate` | `en-es:sentence-veto:rest:reposo:descanso:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.553695 | 0.609924 | -0.056228 |
| `en-es-sentence-veto-rest-reposo:shadow-en-es-sentence-veto-rest-reposo-descanso-shadow-wordnet-example-2` | `en-es:sentence-veto:rest:reposo` | `shadow_candidate` | `en-es:sentence-veto:rest:reposo:descanso:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.599716 | 0.623458 | -0.023742 |
| `en-es-sentence-veto-rest-reposo:shadow-en-es-sentence-veto-rest-reposo-descansar-shadow-wordnet-definition-1` | `en-es:sentence-veto:rest:reposo` | `shadow_candidate` | `en-es:sentence-veto:rest:reposo:descansar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.737418 | 0.776283 | -0.038865 |
| `en-es-sentence-veto-rest-reposo:shadow-en-es-sentence-veto-rest-reposo-descansar-shadow-wordnet-entry_sentence-2` | `en-es:sentence-veto:rest:reposo` | `shadow_candidate` | `en-es:sentence-veto:rest:reposo:descansar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.636039 | 0.645795 | -0.009756 |
| `en-es-sentence-veto-present-presente:shadow-en-es-sentence-veto-present-presente-actual-shadow-wordnet-example-2` | `en-es:sentence-veto:present:presente` | `shadow_candidate` | `en-es:sentence-veto:present:presente:actual:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.721731 | 0.734921 | -0.01319 |
| `en-es-sentence-veto-sign-se-al:shadow-en-es-sentence-veto-sign-se-al-se-a-shadow-wordnet-example-2` | `en-es:sentence-veto:sign:se-al` | `shadow_candidate` | `en-es:sentence-veto:sign:se-al:se-a:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.735111 | 0.738076 | -0.002966 |
| `en-es-sentence-veto-answer-respuesta:active-wordnet-definition-1` | `en-es:sentence-veto:answer:respuesta` | `anchor_cue` | `en-es:sentence-veto:answer:respuesta:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.730008 | 0.806748 | -0.07674 |
| `en-es-sentence-veto-answer-respuesta:shadow-en-es-sentence-veto-answer-respuesta-contestaci-n-shadow-wordnet-definition-1` | `en-es:sentence-veto:answer:respuesta` | `shadow_candidate` | `en-es:sentence-veto:answer:respuesta:contestaci-n:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.777361 | 0.806748 | -0.029387 |
| `en-es-sentence-veto-answer-respuesta:shadow-en-es-sentence-veto-answer-respuesta-contestaci-n-shadow-wordnet-example-2` | `en-es:sentence-veto:answer:respuesta` | `shadow_candidate` | `en-es:sentence-veto:answer:respuesta:contestaci-n:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.564832 | 0.599216 | -0.034384 |
| `en-es-sentence-veto-quiet-silencio:active-wordnet-example-2` | `en-es:sentence-veto:quiet:silencio` | `anchor_cue` | `en-es:sentence-veto:quiet:silencio:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.691358 | 0.725639 | -0.034281 |
| `en-es-sentence-veto-quiet-silencio:shadow-en-es-sentence-veto-quiet-silencio-calmar-shadow-wordnet-example-2` | `en-es:sentence-veto:quiet:silencio` | `shadow_candidate` | `en-es:sentence-veto:quiet:silencio:calmar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.653778 | 0.705952 | -0.052174 |

## Recommendation

- Use the admitted batch only as an analysis artifact. Replace or quarantine rejected active/shadow rows before any promotion-candidate merge.
