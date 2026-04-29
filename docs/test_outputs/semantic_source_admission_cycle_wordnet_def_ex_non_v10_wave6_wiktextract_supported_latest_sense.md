# en-es LLM Example-Frame Sense-Discrimination Audit

- Status: `review`
- Generated: `2026-04-29T01:28:12Z`
- Batch: `en-es:wordnet-def-ex-non-v10-wave6-wiktextract-supported:source-admission-cycle-latest`
- Admitted batch: `en-es:wordnet-def-ex-non-v10-wave6-wiktextract-supported:source-admission-cycle-latest:sense-admitted`

## Summary

- Input rows: `72`
- Semantic rows: `72`
- Semantic admitted rows: `61`
- Semantic rejected rows: `11`
- Non-semantic passthrough rows: `0`
- Admitted rows: `61`
- Scorers: `sentence_transformer_cosine`
- Evidence view: `all_evidence_text`
- Min intended score: `0.5`
- Min margin: `0.0`
- Rejection reasons: `{"competitor_sense_not_lower": 11}`

## Rejected Rows

| Row | Family | Relation | Intended | Reason | Best Scorer | Intended | Competitor | Margin |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `en-es-sentence-veto-leave-permiso:active-wordnet-definition-1` | `en-es:sentence-veto:leave:permiso` | `anchor_cue` | `en-es:sentence-veto:leave:permiso:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.691471 | 0.813202 | -0.121731 |
| `en-es-sentence-veto-leave-permiso:shadow-en-es-sentence-veto-leave-permiso-excedencia-shadow-wordnet-example-2` | `en-es:sentence-veto:leave:permiso` | `shadow_candidate` | `en-es:sentence-veto:leave:permiso:excedencia:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.595441 | 0.63442 | -0.038979 |
| `en-es-sentence-veto-black-oscuro:active-wordnet-example-2` | `en-es:sentence-veto:black:oscuro` | `anchor_cue` | `en-es:sentence-veto:black:oscuro:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.589637 | 0.606172 | -0.016535 |
| `en-es-sentence-veto-low-bajo:active-wordnet-example-2` | `en-es:sentence-veto:low:bajo` | `anchor_cue` | `en-es:sentence-veto:low:bajo:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.6376 | 0.653555 | -0.015956 |
| `en-es-sentence-veto-finish-meta:active-wordnet-example-2` | `en-es:sentence-veto:finish:meta` | `anchor_cue` | `en-es:sentence-veto:finish:meta:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.588016 | 0.614828 | -0.026812 |
| `en-es-sentence-veto-throw-lanzamiento:active-wordnet-definition-2` | `en-es:sentence-veto:throw:lanzamiento` | `anchor_cue` | `en-es:sentence-veto:throw:lanzamiento:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.585689 | 0.629961 | -0.044271 |
| `en-es-sentence-veto-throw-lanzamiento:shadow-en-es-sentence-veto-throw-lanzamiento-lanzar-shadow-wordnet-example-2` | `en-es:sentence-veto:throw:lanzamiento` | `shadow_candidate` | `en-es:sentence-veto:throw:lanzamiento:lanzar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.715181 | 0.741286 | -0.026106 |
| `en-es-sentence-veto-upset-disgustado:shadow-en-es-sentence-veto-upset-disgustado-trastrocar-shadow-wordnet-example-2` | `en-es:sentence-veto:upset:disgustado` | `shadow_candidate` | `en-es:sentence-veto:upset:disgustado:trastrocar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.625647 | 0.680957 | -0.05531 |
| `en-es-sentence-veto-advance-avance:shadow-en-es-sentence-veto-advance-avance-avanzar-shadow-wordnet-definition-1` | `en-es:sentence-veto:advance:avance` | `shadow_candidate` | `en-es:sentence-veto:advance:avance:avanzar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.77269 | 0.809057 | -0.036368 |
| `en-es-sentence-veto-advance-avance:shadow-en-es-sentence-veto-advance-avance-avanzar-shadow-wordnet-entry_sentence-2` | `en-es:sentence-veto:advance:avance` | `shadow_candidate` | `en-es:sentence-veto:advance:avance:avanzar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.673688 | 0.683939 | -0.010251 |
| `en-es-sentence-veto-rank-rancio:shadow-en-es-sentence-veto-rank-rancio-fila-shadow-wordnet-example-2` | `en-es:sentence-veto:rank:rancio` | `shadow_candidate` | `en-es:sentence-veto:rank:rancio:fila:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.505396 | 0.560885 | -0.055489 |

## Recommendation

- Use the admitted batch only as an analysis artifact. Replace or quarantine rejected active/shadow rows before any promotion-candidate merge.
