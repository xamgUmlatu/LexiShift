# en-es LLM Example-Frame Sense-Discrimination Audit

- Status: `review`
- Generated: `2026-04-27T22:24:32Z`
- Batch: `en-es:wordnet-def-ex-non-v10-wave2-draft-v1:source-admission-cycle`
- Admitted batch: `en-es:wordnet-def-ex-non-v10-wave2-draft-v1:source-admission-cycle:sense-admitted`

## Summary

- Input rows: `34`
- Semantic rows: `34`
- Semantic admitted rows: `27`
- Semantic rejected rows: `7`
- Non-semantic passthrough rows: `0`
- Admitted rows: `27`
- Scorers: `sentence_transformer_cosine`
- Evidence view: `all_evidence_text`
- Min intended score: `0.5`
- Min margin: `0.0`
- Rejection reasons: `{"competitor_sense_not_lower": 7}`

## Rejected Rows

| Row | Family | Relation | Intended | Reason | Best Scorer | Intended | Competitor | Margin |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `en-es-sentence-veto-look-aspecto:shadow-en-es-sentence-veto-look-aspecto-parecer-shadow-wordnet-definition-1` | `en-es:sentence-veto:look:aspecto` | `shadow_candidate` | `en-es:sentence-veto:look:aspecto:parecer:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.737194 | 0.812901 | -0.075707 |
| `en-es-sentence-veto-end-fin:active-wordnet-definition-1` | `en-es:sentence-veto:end:fin` | `anchor_cue` | `en-es:sentence-veto:end:fin:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.733842 | 0.777175 | -0.043333 |
| `en-es-sentence-veto-end-fin:active-wordnet-example-2` | `en-es:sentence-veto:end:fin` | `anchor_cue` | `en-es:sentence-veto:end:fin:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.698032 | 0.70462 | -0.006588 |
| `en-es-sentence-veto-end-fin:shadow-en-es-sentence-veto-end-fin-acabar-shadow-wordnet-example-2` | `en-es:sentence-veto:end:fin` | `shadow_candidate` | `en-es:sentence-veto:end:fin:acabar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.559981 | 0.560592 | -0.000611 |
| `en-es-sentence-veto-offer-oferta:shadow-en-es-sentence-veto-offer-oferta-ofrecer-shadow-wordnet-example-2` | `en-es:sentence-veto:offer:oferta` | `shadow_candidate` | `en-es:sentence-veto:offer:oferta:ofrecer:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.528855 | 0.538553 | -0.009698 |
| `en-es-sentence-veto-quiet-silencio:active-wordnet-example-2` | `en-es:sentence-veto:quiet:silencio` | `anchor_cue` | `en-es:sentence-veto:quiet:silencio:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.691358 | 0.725639 | -0.034281 |
| `en-es-sentence-veto-quiet-silencio:shadow-en-es-sentence-veto-quiet-silencio-calmar-shadow-wordnet-example-2` | `en-es:sentence-veto:quiet:silencio` | `shadow_candidate` | `en-es:sentence-veto:quiet:silencio:calmar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.653778 | 0.705952 | -0.052174 |

## Recommendation

- Use the admitted batch only as an analysis artifact. Replace or quarantine rejected active/shadow rows before any promotion-candidate merge.
