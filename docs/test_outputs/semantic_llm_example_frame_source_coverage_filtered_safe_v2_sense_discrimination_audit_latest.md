# en-es LLM Example-Frame Sense-Discrimination Audit

- Status: `review`
- Generated: `2026-04-25T00:53:04Z`
- Batch: `en-es:example-frame-composite:balanced-plus-source-coverage-filtered-safe-v2-20260425a`
- Admitted batch: `en-es:example-frame-composite:balanced-plus-source-coverage-filtered-safe-v2-20260425a:sense-admitted`

## Summary

- Input rows: `60`
- Semantic rows: `52`
- Semantic admitted rows: `31`
- Semantic rejected rows: `21`
- Non-semantic passthrough rows: `8`
- Admitted rows: `40`
- Scorers: `token_jaccard, tfidf_cosine`
- Evidence view: `all_evidence_text`
- Min intended score: `0.05`
- Min margin: `0.01`
- Rejection reasons: `{"competitor_sense_not_lower": 3, "insufficient_sense_margin": 1, "weak_intended_similarity": 17}`

## Rejected Rows

| Row | Family | Relation | Intended | Reason | Best Scorer | Intended | Competitor | Margin |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `en-es-sentence-veto-order-pedido:shadow-en-es-sentence-veto-order-ordenar-shadow-reverse-aux` | `en-es:sentence-veto:order:pedido` | `shadow_candidate` | `en-es:sentence-veto:order:ordenar:shadow` | `weak_intended_similarity` | `tfidf_cosine` | 0.034643 | 0.061999 | -0.027356 |
| `en-es-sentence-veto-report-informe:active-reverse-aux` | `en-es:sentence-veto:report:informe` | `anchor_cue` | `en-es:sentence-veto:report:informe:active` | `competitor_sense_not_lower` | `token_jaccard` | 0.076923 | 0.1 | -0.023077 |
| `en-es-sentence-veto-report-informe:shadow-en-es-sentence-veto-report-informar-shadow-reverse-aux` | `en-es:sentence-veto:report:informe` | `shadow_candidate` | `en-es:sentence-veto:report:informar:shadow` | `weak_intended_similarity` | `token_jaccard` | 0.0 | 0.0 | 0.0 |
| `en-es-sentence-veto-play-obra:llm:active:missing:v1` | `en-es:sentence-veto:play:obra` | `anchor_cue` | `en-es:sentence-veto:play:obra:active` | `competitor_sense_not_lower` | `token_jaccard` | 0.157895 | 0.166667 | -0.008772 |
| `en-es-sentence-veto-check-cheque:llm:active:missing:v1` | `en-es:sentence-veto:check:cheque` | `anchor_cue` | `en-es:sentence-veto:check:cheque:active` | `weak_intended_similarity` | `tfidf_cosine` | 0.026106 | 0.025277 | 0.000829 |
| `en-es-sentence-veto-report-informe:llm:active:missing:v1` | `en-es:sentence-veto:report:informe` | `anchor_cue` | `en-es:sentence-veto:report:informe:active` | `weak_intended_similarity` | `tfidf_cosine` | 0.029304 | 0.02933 | -2.6e-05 |
| `en-es-sentence-veto-trip-viaje:llm:active:missing:v1` | `en-es:sentence-veto:trip:viaje` | `anchor_cue` | `en-es:sentence-veto:trip:viaje:active` | `weak_intended_similarity` | `tfidf_cosine` | 0.039979 | 0.069081 | -0.029102 |
| `en-es-sentence-veto-watch-reloj:llm:active:missing:v1` | `en-es:sentence-veto:watch:reloj` | `anchor_cue` | `en-es:sentence-veto:watch:reloj:active` | `weak_intended_similarity` | `tfidf_cosine` | 0.041002 | 0.033726 | 0.007276 |
| `en-es-sentence-veto-check-cheque:llm:active:remediation-active-002:v1` | `en-es:sentence-veto:check:cheque` | `anchor_cue` | `en-es:sentence-veto:check:cheque:active` | `weak_intended_similarity` | `tfidf_cosine` | 0.026106 | 0.025277 | 0.000829 |
| `en-es-sentence-veto-order-pedido:llm:active:remediation-active-002:v1` | `en-es:sentence-veto:order:pedido` | `anchor_cue` | `en-es:sentence-veto:order:pedido:active` | `weak_intended_similarity` | `tfidf_cosine` | 0.031478 | 0.028427 | 0.003051 |
| `en-es-sentence-veto-ball-pelota:llm:shadow:en-es-sentence-veto-ball-baile-shadow:missing:v1` | `en-es:sentence-veto:ball:pelota` | `shadow_candidate` | `en-es:sentence-veto:ball:baile:shadow` | `weak_intended_similarity` | `tfidf_cosine` | 0.042816 | 0.067414 | -0.024598 |
| `en-es-sentence-veto-bank-banco:llm:active:missing:v1` | `en-es:sentence-veto:bank:banco` | `anchor_cue` | `en-es:sentence-veto:bank:banco:active` | `competitor_sense_not_lower` | `token_jaccard` | 0.052632 | 0.055556 | -0.002924 |
| `en-es-sentence-veto-bank-banco:llm:shadow:en-es-sentence-veto-bank-orilla-shadow:missing:v1` | `en-es:sentence-veto:bank:banco` | `shadow_candidate` | `en-es:sentence-veto:bank:orilla:shadow` | `weak_intended_similarity` | `tfidf_cosine` | 0.030976 | 0.027749 | 0.003227 |
| `en-es-sentence-veto-spring-primavera:llm:shadow:en-es-sentence-veto-spring-resorte-shadow:missing:v1` | `en-es:sentence-veto:spring:primavera` | `shadow_candidate` | `en-es:sentence-veto:spring:resorte:shadow` | `weak_intended_similarity` | `tfidf_cosine` | 0.032723 | 0.03612 | -0.003397 |
| `en-es-sentence-veto-seal-sello:llm:shadow:en-es-sentence-veto-seal-foca-shadow:missing:v1` | `en-es:sentence-veto:seal:sello` | `shadow_candidate` | `en-es:sentence-veto:seal:foca:shadow` | `weak_intended_similarity` | `tfidf_cosine` | 0.038948 | 0.041635 | -0.002686 |
| `en-es-sentence-veto-match-partido:llm:shadow:en-es-sentence-veto-match-cerilla-shadow:missing:v1` | `en-es:sentence-veto:match:partido` | `shadow_candidate` | `en-es:sentence-veto:match:cerilla:shadow` | `insufficient_sense_margin` | `token_jaccard` | 0.058824 | 0.055556 | 0.003268 |
| `en-es-sentence-veto-table-mesa:llm:active:missing:v1` | `en-es:sentence-veto:table:mesa` | `anchor_cue` | `en-es:sentence-veto:table:mesa:active` | `weak_intended_similarity` | `tfidf_cosine` | 0.034892 | 0.041461 | -0.006569 |
| `en-es-sentence-veto-branch-sucursal:llm:active:missing:v1` | `en-es:sentence-veto:branch:sucursal` | `anchor_cue` | `en-es:sentence-veto:branch:sucursal:active` | `weak_intended_similarity` | `tfidf_cosine` | 0.035623 | 0.035804 | -0.000181 |
| `en-es-sentence-veto-park-parque:llm:active:missing:v1` | `en-es:sentence-veto:park:parque` | `anchor_cue` | `en-es:sentence-veto:park:parque:active` | `weak_intended_similarity` | `tfidf_cosine` | 0.036207 | 0.067676 | -0.031469 |
| `en-es-sentence-veto-board-tablero:manual:shadow:en-es-sentence-veto-board-junta-shadow:leakage-safe:v1` | `en-es:sentence-veto:board:tablero` | `shadow_candidate` | `en-es:sentence-veto:board:junta:shadow` | `weak_intended_similarity` | `tfidf_cosine` | 0.040934 | 0.082322 | -0.041388 |
| `en-es-sentence-veto-plant-planta:manual:active:leakage-safe-light:v1` | `en-es:sentence-veto:plant:planta` | `anchor_cue` | `en-es:sentence-veto:plant:planta:active` | `weak_intended_similarity` | `tfidf_cosine` | 0.032435 | 0.035943 | -0.003509 |

## Recommendation

- Use the admitted batch only as an analysis artifact. Replace or quarantine rejected active/shadow rows before any promotion-candidate merge.
