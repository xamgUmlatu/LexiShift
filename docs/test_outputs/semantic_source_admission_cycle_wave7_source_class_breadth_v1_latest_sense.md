# en-es LLM Example-Frame Sense-Discrimination Audit

- Status: `review`
- Generated: `2026-04-30T20:46:54Z`
- Batch: `en-es:wordnet-translation-sense-source-class:non-v10-wave7-source-class-breadth-v1:cycle`
- Admitted batch: `en-es:wordnet-translation-sense-source-class:non-v10-wave7-source-class-breadth-v1:cycle:sense-admitted`

## Summary

- Input rows: `183`
- Semantic rows: `183`
- Semantic admitted rows: `153`
- Semantic rejected rows: `30`
- Non-semantic passthrough rows: `0`
- Admitted rows: `153`
- Scorers: `sentence_transformer_cosine`
- Evidence view: `all_evidence_text`
- Min intended score: `0.5`
- Min margin: `0.0`
- Rejection reasons: `{"competitor_sense_not_lower": 30}`

## Rejected Rows

| Row | Family | Relation | Intended | Reason | Best Scorer | Intended | Competitor | Margin |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `en-es-sentence-veto-gross-repulsivo:active-wordnet-example-2` | `en-es:sentence-veto:gross:repulsivo` | `anchor_cue` | `en-es:sentence-veto:gross:repulsivo:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.660856 | 0.707569 | -0.046714 |
| `en-es-sentence-veto-cast-lanzamiento:shadow-en-es-sentence-veto-cast-lanzamiento-lanzar-shadow-wordnet-example-2` | `en-es:sentence-veto:cast:lanzamiento` | `shadow_candidate` | `en-es:sentence-veto:cast:lanzamiento:lanzar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.569985 | 0.573507 | -0.003522 |
| `en-es-sentence-veto-fix-aprieto:active-wordnet-example-2` | `en-es:sentence-veto:fix:aprieto` | `anchor_cue` | `en-es:sentence-veto:fix:aprieto:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.590543 | 0.655861 | -0.065318 |
| `en-es-sentence-veto-fix-aprieto:shadow-en-es-sentence-veto-fix-aprieto-localizaci-n-shadow-wordnet-example-2` | `en-es:sentence-veto:fix:aprieto` | `shadow_candidate` | `en-es:sentence-veto:fix:aprieto:localizaci-n:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.590451 | 0.667796 | -0.077345 |
| `en-es-sentence-veto-full-lleno:active-wordnet-example-2` | `en-es:sentence-veto:full:lleno` | `anchor_cue` | `en-es:sentence-veto:full:lleno:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.615197 | 0.644977 | -0.02978 |
| `en-es-sentence-veto-even-tarde:shadow-en-es-sentence-veto-even-tarde-allanar-shadow-wordnet-example-2` | `en-es:sentence-veto:even:tarde` | `shadow_candidate` | `en-es:sentence-veto:even:tarde:allanar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.581511 | 0.589069 | -0.007558 |
| `en-es-sentence-veto-meet-adecuado:active-wordnet-example-2` | `en-es:sentence-veto:meet:adecuado` | `anchor_cue` | `en-es:sentence-veto:meet:adecuado:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.617969 | 0.654375 | -0.036406 |
| `en-es-sentence-veto-score-tantos:active-wordnet-example-2` | `en-es:sentence-veto:score:tantos` | `anchor_cue` | `en-es:sentence-veto:score:tantos:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.64186 | 0.645002 | -0.003143 |
| `en-es-sentence-veto-score-tantos:shadow-en-es-sentence-veto-score-tantos-marcador-shadow-wordnet-definition-1` | `en-es:sentence-veto:score:tantos` | `shadow_candidate` | `en-es:sentence-veto:score:tantos:marcador:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.731542 | 0.753516 | -0.021975 |
| `en-es-sentence-veto-crash-choque:shadow-en-es-sentence-veto-crash-choque-chocar-shadow-wordnet-entry_sentence-2` | `en-es:sentence-veto:crash:choque` | `shadow_candidate` | `en-es:sentence-veto:crash:choque:chocar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.609643 | 0.637073 | -0.02743 |
| `en-es-sentence-veto-fix-aprieto:active-en-es-sentence-veto-fix-aprieto-active-difficult-situation-frame-2` | `en-es:sentence-veto:fix:aprieto` | `anchor_cue` | `en-es:sentence-veto:fix:aprieto:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.737291 | 0.750976 | -0.013685 |
| `en-es-sentence-veto-fix-aprieto:active-en-es-sentence-veto-fix-aprieto-active-difficult-situation-frame-3` | `en-es:sentence-veto:fix:aprieto` | `anchor_cue` | `en-es:sentence-veto:fix:aprieto:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.69824 | 0.731177 | -0.032937 |
| `en-es-sentence-veto-full-lleno:active-en-es-sentence-veto-full-lleno-active-full-capacity-frame-3` | `en-es:sentence-veto:full:lleno` | `anchor_cue` | `en-es:sentence-veto:full:lleno:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.6105 | 0.640133 | -0.029634 |
| `en-es-sentence-veto-wrong-incorrecto:active-en-es-sentence-veto-wrong-incorrecto-active-incorrectness-frame-3` | `en-es:sentence-veto:wrong:incorrecto` | `anchor_cue` | `en-es:sentence-veto:wrong:incorrecto:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.72709 | 0.738464 | -0.011374 |
| `en-es-sentence-veto-stretch-estir-n:active-en-es-sentence-veto-stretch-estir-n-active-stretching-lengthening-frame-1` | `en-es:sentence-veto:stretch:estir-n` | `anchor_cue` | `en-es:sentence-veto:stretch:estir-n:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.718367 | 0.83868 | -0.120312 |
| `en-es-sentence-veto-stretch-estir-n:active-en-es-sentence-veto-stretch-estir-n-active-stretching-lengthening-frame-3` | `en-es:sentence-veto:stretch:estir-n` | `anchor_cue` | `en-es:sentence-veto:stretch:estir-n:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.681296 | 0.778062 | -0.096766 |
| `en-es-sentence-veto-stretch-estir-n:shadow-en-es-sentence-veto-stretch-estir-n-estirar-shadow-stretching-lengthening-frame-2` | `en-es:sentence-veto:stretch:estir-n` | `shadow_candidate` | `en-es:sentence-veto:stretch:estir-n:estirar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.830367 | 0.891423 | -0.061057 |
| `en-es-sentence-veto-score-tantos:active-en-es-sentence-veto-score-tantos-active-sports-points-scoring-frame-1` | `en-es:sentence-veto:score:tantos` | `anchor_cue` | `en-es:sentence-veto:score:tantos:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.804794 | 0.828153 | -0.023359 |
| `en-es-sentence-veto-score-tantos:active-en-es-sentence-veto-score-tantos-active-sports-points-scoring-frame-2` | `en-es:sentence-veto:score:tantos` | `anchor_cue` | `en-es:sentence-veto:score:tantos:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.787131 | 0.79698 | -0.00985 |
| `en-es-sentence-veto-score-tantos:shadow-en-es-sentence-veto-score-tantos-marcador-shadow-sports-points-scoring-frame-1` | `en-es:sentence-veto:score:tantos` | `shadow_candidate` | `en-es:sentence-veto:score:tantos:marcador:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.764403 | 0.828153 | -0.06375 |
| `en-es-sentence-veto-score-tantos:shadow-en-es-sentence-veto-score-tantos-marcador-shadow-sports-points-scoring-frame-2` | `en-es:sentence-veto:score:tantos` | `shadow_candidate` | `en-es:sentence-veto:score:tantos:marcador:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.767425 | 0.79698 | -0.029555 |
| `en-es-sentence-veto-score-tantos:shadow-en-es-sentence-veto-score-tantos-marcador-shadow-sports-points-scoring-frame-3` | `en-es:sentence-veto:score:tantos` | `shadow_candidate` | `en-es:sentence-veto:score:tantos:marcador:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.743963 | 0.74607 | -0.002108 |
| `en-es-sentence-veto-score-tantos:shadow-en-es-sentence-veto-score-tantos-anotar-shadow-sports-points-scoring-frame-3` | `en-es:sentence-veto:score:tantos` | `shadow_candidate` | `en-es:sentence-veto:score:tantos:anotar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.738158 | 0.74607 | -0.007912 |
| `en-es-sentence-veto-crash-choque:active-en-es-sentence-veto-crash-choque-active-collision-malfunction-frame-3` | `en-es:sentence-veto:crash:choque` | `anchor_cue` | `en-es:sentence-veto:crash:choque:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.620949 | 0.859113 | -0.238164 |
| `en-es-sentence-veto-crash-choque:shadow-en-es-sentence-veto-crash-choque-fallo-shadow-collision-malfunction-frame-1` | `en-es:sentence-veto:crash:choque` | `shadow_candidate` | `en-es:sentence-veto:crash:choque:fallo:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.709485 | 0.846905 | -0.13742 |
| `en-es-sentence-veto-crash-choque:shadow-en-es-sentence-veto-crash-choque-fallo-shadow-collision-malfunction-frame-2` | `en-es:sentence-veto:crash:choque` | `shadow_candidate` | `en-es:sentence-veto:crash:choque:fallo:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.706412 | 0.783711 | -0.077299 |
| `en-es-sentence-veto-crash-choque:shadow-en-es-sentence-veto-crash-choque-chocar-shadow-collision-malfunction-frame-1` | `en-es:sentence-veto:crash:choque` | `shadow_candidate` | `en-es:sentence-veto:crash:choque:chocar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.739046 | 0.846905 | -0.107859 |
| `en-es-sentence-veto-crash-choque:shadow-en-es-sentence-veto-crash-choque-chocar-shadow-collision-malfunction-frame-2` | `en-es:sentence-veto:crash:choque` | `shadow_candidate` | `en-es:sentence-veto:crash:choque:chocar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.74278 | 0.783711 | -0.040931 |
| `en-es-sentence-veto-crash-choque:shadow-en-es-sentence-veto-crash-choque-chocar-shadow-collision-malfunction-frame-3` | `en-es:sentence-veto:crash:choque` | `shadow_candidate` | `en-es:sentence-veto:crash:choque:chocar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.61608 | 0.859113 | -0.243033 |
| `en-es-sentence-veto-squeeze-crisis:shadow-en-es-sentence-veto-squeeze-crisis-apretujar-shadow-tight-physical-fit-frame-2` | `en-es:sentence-veto:squeeze:crisis` | `shadow_candidate` | `en-es:sentence-veto:squeeze:crisis:apretujar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.773612 | 0.820408 | -0.046796 |

## Recommendation

- Use the admitted batch only as an analysis artifact. Replace or quarantine rejected active/shadow rows before any promotion-candidate merge.
