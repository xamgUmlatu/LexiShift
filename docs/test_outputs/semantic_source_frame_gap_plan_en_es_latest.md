# en-es Source Frame Gap Plan

- Status: `ready`
- Generated: `2026-04-28T20:55:59Z`
- Dataset: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v10.json`
- Alignment audit: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/semantic_source_row_alignment_audit_en_es_latest.json`
- Candidate source id: `llm_aligned_sentence_frame_rows`
- Prompt version: `aligned-sentence-frame-v1`
- Selected model: `gpt-5.4-mini`
- Temperature: `0.2`
- Leakage policy: `prompts_use_sense_labels_and_glosses_only; do_not_include_sentence_veto_case_sentences`
- Sense slots: `38`
- Missing selector-ready slots: `23`
- Planned candidate requests: `97`
- Estimated prompt tokens: `30792`

## Recommendation

Plan 97 no-spend candidate requests covering 23 missing active/shadow selector slots. Execute these only through the existing leakage audit and source-admission cycle, then rerun the context-conditioned matrix before any runtime claim.

## Gap Summary

| Target | Slots | Missing Slots | Candidate Requests |
| --- | ---: | ---: | ---: |
| active_example | 19 | 10 | 42 |
| shadow_example | 19 | 13 | 55 |

## Missing Slots By Family

| Family | Missing Active | Missing Shadows | Candidate Requests |
| --- | ---: | ---: | ---: |
| en-es:sentence-veto:board:tablero | 1 | 1 | 10 |
| en-es:sentence-veto:cell:celula | 1 | 1 | 10 |
| en-es:sentence-veto:file:archivo | 1 | 1 | 10 |
| en-es:sentence-veto:match:partido | 1 | 1 | 10 |
| en-es:sentence-veto:seal:sello | 1 | 1 | 10 |
| en-es:sentence-veto:drink:bebida | 1 | 1 | 6 |
| en-es:sentence-veto:play:obra | 1 | 1 | 6 |
| en-es:sentence-veto:report:informe | 1 | 1 | 6 |
| en-es:sentence-veto:watch:reloj | 1 | 1 | 6 |
| en-es:sentence-veto:ball:pelota | 0 | 1 | 5 |
| en-es:sentence-veto:branch:sucursal | 0 | 1 | 5 |
| en-es:sentence-veto:plant:planta | 1 | 0 | 5 |
| en-es:sentence-veto:spring:primavera | 0 | 1 | 5 |
| en-es:sentence-veto:trip:viaje | 0 | 1 | 3 |

## Request Rows

| Request | Target | Family | Candidate Sense | Attempt | Prompt Tokens Est. |
| --- | --- | --- | --- | ---: | ---: |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-ball-pelota:en-es-sentence-veto-ball-baile-shadow:candidate-01 | shadow_example | en-es:sentence-veto:ball:pelota | en-es:sentence-veto:ball:baile:shadow | 1 | 319 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-ball-pelota:en-es-sentence-veto-ball-baile-shadow:candidate-02 | shadow_example | en-es:sentence-veto:ball:pelota | en-es:sentence-veto:ball:baile:shadow | 2 | 319 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-ball-pelota:en-es-sentence-veto-ball-baile-shadow:candidate-03 | shadow_example | en-es:sentence-veto:ball:pelota | en-es:sentence-veto:ball:baile:shadow | 3 | 319 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-ball-pelota:en-es-sentence-veto-ball-baile-shadow:candidate-04 | shadow_example | en-es:sentence-veto:ball:pelota | en-es:sentence-veto:ball:baile:shadow | 4 | 319 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-ball-pelota:en-es-sentence-veto-ball-baile-shadow:candidate-05 | shadow_example | en-es:sentence-veto:ball:pelota | en-es:sentence-veto:ball:baile:shadow | 5 | 319 |
| en-es:source-frame-gap:active_example:en-es-sentence-veto-plant-planta:en-es-sentence-veto-plant-planta-active:candidate-01 | active_example | en-es:sentence-veto:plant:planta | en-es:sentence-veto:plant:planta:active | 1 | 319 |
| en-es:source-frame-gap:active_example:en-es-sentence-veto-plant-planta:en-es-sentence-veto-plant-planta-active:candidate-02 | active_example | en-es:sentence-veto:plant:planta | en-es:sentence-veto:plant:planta:active | 2 | 319 |
| en-es:source-frame-gap:active_example:en-es-sentence-veto-plant-planta:en-es-sentence-veto-plant-planta-active:candidate-03 | active_example | en-es:sentence-veto:plant:planta | en-es:sentence-veto:plant:planta:active | 3 | 319 |
| en-es:source-frame-gap:active_example:en-es-sentence-veto-plant-planta:en-es-sentence-veto-plant-planta-active:candidate-04 | active_example | en-es:sentence-veto:plant:planta | en-es:sentence-veto:plant:planta:active | 4 | 319 |
| en-es:source-frame-gap:active_example:en-es-sentence-veto-plant-planta:en-es-sentence-veto-plant-planta-active:candidate-05 | active_example | en-es:sentence-veto:plant:planta | en-es:sentence-veto:plant:planta:active | 5 | 319 |
| en-es:source-frame-gap:active_example:en-es-sentence-veto-cell-celula:en-es-sentence-veto-cell-celula-active:candidate-01 | active_example | en-es:sentence-veto:cell:celula | en-es:sentence-veto:cell:celula:active | 1 | 313 |
| en-es:source-frame-gap:active_example:en-es-sentence-veto-cell-celula:en-es-sentence-veto-cell-celula-active:candidate-02 | active_example | en-es:sentence-veto:cell:celula | en-es:sentence-veto:cell:celula:active | 2 | 313 |
| en-es:source-frame-gap:active_example:en-es-sentence-veto-cell-celula:en-es-sentence-veto-cell-celula-active:candidate-03 | active_example | en-es:sentence-veto:cell:celula | en-es:sentence-veto:cell:celula:active | 3 | 313 |
| en-es:source-frame-gap:active_example:en-es-sentence-veto-cell-celula:en-es-sentence-veto-cell-celula-active:candidate-04 | active_example | en-es:sentence-veto:cell:celula | en-es:sentence-veto:cell:celula:active | 4 | 313 |
| en-es:source-frame-gap:active_example:en-es-sentence-veto-cell-celula:en-es-sentence-veto-cell-celula-active:candidate-05 | active_example | en-es:sentence-veto:cell:celula | en-es:sentence-veto:cell:celula:active | 5 | 313 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-cell-celula:en-es-sentence-veto-cell-celda-shadow:candidate-01 | shadow_example | en-es:sentence-veto:cell:celula | en-es:sentence-veto:cell:celda:shadow | 1 | 308 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-cell-celula:en-es-sentence-veto-cell-celda-shadow:candidate-02 | shadow_example | en-es:sentence-veto:cell:celula | en-es:sentence-veto:cell:celda:shadow | 2 | 308 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-cell-celula:en-es-sentence-veto-cell-celda-shadow:candidate-03 | shadow_example | en-es:sentence-veto:cell:celula | en-es:sentence-veto:cell:celda:shadow | 3 | 308 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-cell-celula:en-es-sentence-veto-cell-celda-shadow:candidate-04 | shadow_example | en-es:sentence-veto:cell:celula | en-es:sentence-veto:cell:celda:shadow | 4 | 308 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-cell-celula:en-es-sentence-veto-cell-celda-shadow:candidate-05 | shadow_example | en-es:sentence-veto:cell:celula | en-es:sentence-veto:cell:celda:shadow | 5 | 308 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-spring-primavera:en-es-sentence-veto-spring-resorte-shadow:candidate-01 | shadow_example | en-es:sentence-veto:spring:primavera | en-es:sentence-veto:spring:resorte:shadow | 1 | 322 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-spring-primavera:en-es-sentence-veto-spring-resorte-shadow:candidate-02 | shadow_example | en-es:sentence-veto:spring:primavera | en-es:sentence-veto:spring:resorte:shadow | 2 | 322 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-spring-primavera:en-es-sentence-veto-spring-resorte-shadow:candidate-03 | shadow_example | en-es:sentence-veto:spring:primavera | en-es:sentence-veto:spring:resorte:shadow | 3 | 322 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-spring-primavera:en-es-sentence-veto-spring-resorte-shadow:candidate-04 | shadow_example | en-es:sentence-veto:spring:primavera | en-es:sentence-veto:spring:resorte:shadow | 4 | 322 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-spring-primavera:en-es-sentence-veto-spring-resorte-shadow:candidate-05 | shadow_example | en-es:sentence-veto:spring:primavera | en-es:sentence-veto:spring:resorte:shadow | 5 | 322 |
| en-es:source-frame-gap:active_example:en-es-sentence-veto-seal-sello:en-es-sentence-veto-seal-sello-active:candidate-01 | active_example | en-es:sentence-veto:seal:sello | en-es:sentence-veto:seal:sello:active | 1 | 313 |
| en-es:source-frame-gap:active_example:en-es-sentence-veto-seal-sello:en-es-sentence-veto-seal-sello-active:candidate-02 | active_example | en-es:sentence-veto:seal:sello | en-es:sentence-veto:seal:sello:active | 2 | 313 |
| en-es:source-frame-gap:active_example:en-es-sentence-veto-seal-sello:en-es-sentence-veto-seal-sello-active:candidate-03 | active_example | en-es:sentence-veto:seal:sello | en-es:sentence-veto:seal:sello:active | 3 | 313 |
| en-es:source-frame-gap:active_example:en-es-sentence-veto-seal-sello:en-es-sentence-veto-seal-sello-active:candidate-04 | active_example | en-es:sentence-veto:seal:sello | en-es:sentence-veto:seal:sello:active | 4 | 313 |
| en-es:source-frame-gap:active_example:en-es-sentence-veto-seal-sello:en-es-sentence-veto-seal-sello-active:candidate-05 | active_example | en-es:sentence-veto:seal:sello | en-es:sentence-veto:seal:sello:active | 5 | 313 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-seal-sello:en-es-sentence-veto-seal-foca-shadow:candidate-01 | shadow_example | en-es:sentence-veto:seal:sello | en-es:sentence-veto:seal:foca:shadow | 1 | 309 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-seal-sello:en-es-sentence-veto-seal-foca-shadow:candidate-02 | shadow_example | en-es:sentence-veto:seal:sello | en-es:sentence-veto:seal:foca:shadow | 2 | 309 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-seal-sello:en-es-sentence-veto-seal-foca-shadow:candidate-03 | shadow_example | en-es:sentence-veto:seal:sello | en-es:sentence-veto:seal:foca:shadow | 3 | 309 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-seal-sello:en-es-sentence-veto-seal-foca-shadow:candidate-04 | shadow_example | en-es:sentence-veto:seal:sello | en-es:sentence-veto:seal:foca:shadow | 4 | 309 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-seal-sello:en-es-sentence-veto-seal-foca-shadow:candidate-05 | shadow_example | en-es:sentence-veto:seal:sello | en-es:sentence-veto:seal:foca:shadow | 5 | 309 |
| en-es:source-frame-gap:active_example:en-es-sentence-veto-file-archivo:en-es-sentence-veto-file-archivo-active:candidate-01 | active_example | en-es:sentence-veto:file:archivo | en-es:sentence-veto:file:archivo:active | 1 | 311 |
| en-es:source-frame-gap:active_example:en-es-sentence-veto-file-archivo:en-es-sentence-veto-file-archivo-active:candidate-02 | active_example | en-es:sentence-veto:file:archivo | en-es:sentence-veto:file:archivo:active | 2 | 311 |
| en-es:source-frame-gap:active_example:en-es-sentence-veto-file-archivo:en-es-sentence-veto-file-archivo-active:candidate-03 | active_example | en-es:sentence-veto:file:archivo | en-es:sentence-veto:file:archivo:active | 3 | 311 |
| en-es:source-frame-gap:active_example:en-es-sentence-veto-file-archivo:en-es-sentence-veto-file-archivo-active:candidate-04 | active_example | en-es:sentence-veto:file:archivo | en-es:sentence-veto:file:archivo:active | 4 | 311 |
| en-es:source-frame-gap:active_example:en-es-sentence-veto-file-archivo:en-es-sentence-veto-file-archivo-active:candidate-05 | active_example | en-es:sentence-veto:file:archivo | en-es:sentence-veto:file:archivo:active | 5 | 311 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-file-archivo:en-es-sentence-veto-file-lima-shadow:candidate-01 | shadow_example | en-es:sentence-veto:file:archivo | en-es:sentence-veto:file:lima:shadow | 1 | 315 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-file-archivo:en-es-sentence-veto-file-lima-shadow:candidate-02 | shadow_example | en-es:sentence-veto:file:archivo | en-es:sentence-veto:file:lima:shadow | 2 | 315 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-file-archivo:en-es-sentence-veto-file-lima-shadow:candidate-03 | shadow_example | en-es:sentence-veto:file:archivo | en-es:sentence-veto:file:lima:shadow | 3 | 315 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-file-archivo:en-es-sentence-veto-file-lima-shadow:candidate-04 | shadow_example | en-es:sentence-veto:file:archivo | en-es:sentence-veto:file:lima:shadow | 4 | 315 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-file-archivo:en-es-sentence-veto-file-lima-shadow:candidate-05 | shadow_example | en-es:sentence-veto:file:archivo | en-es:sentence-veto:file:lima:shadow | 5 | 315 |
| en-es:source-frame-gap:active_example:en-es-sentence-veto-match-partido:en-es-sentence-veto-match-partido-active:candidate-01 | active_example | en-es:sentence-veto:match:partido | en-es:sentence-veto:match:partido:active | 1 | 316 |
| en-es:source-frame-gap:active_example:en-es-sentence-veto-match-partido:en-es-sentence-veto-match-partido-active:candidate-02 | active_example | en-es:sentence-veto:match:partido | en-es:sentence-veto:match:partido:active | 2 | 316 |
| en-es:source-frame-gap:active_example:en-es-sentence-veto-match-partido:en-es-sentence-veto-match-partido-active:candidate-03 | active_example | en-es:sentence-veto:match:partido | en-es:sentence-veto:match:partido:active | 3 | 316 |
| en-es:source-frame-gap:active_example:en-es-sentence-veto-match-partido:en-es-sentence-veto-match-partido-active:candidate-04 | active_example | en-es:sentence-veto:match:partido | en-es:sentence-veto:match:partido:active | 4 | 316 |
| en-es:source-frame-gap:active_example:en-es-sentence-veto-match-partido:en-es-sentence-veto-match-partido-active:candidate-05 | active_example | en-es:sentence-veto:match:partido | en-es:sentence-veto:match:partido:active | 5 | 316 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-match-partido:en-es-sentence-veto-match-cerilla-shadow:candidate-01 | shadow_example | en-es:sentence-veto:match:partido | en-es:sentence-veto:match:cerilla:shadow | 1 | 312 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-match-partido:en-es-sentence-veto-match-cerilla-shadow:candidate-02 | shadow_example | en-es:sentence-veto:match:partido | en-es:sentence-veto:match:cerilla:shadow | 2 | 312 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-match-partido:en-es-sentence-veto-match-cerilla-shadow:candidate-03 | shadow_example | en-es:sentence-veto:match:partido | en-es:sentence-veto:match:cerilla:shadow | 3 | 312 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-match-partido:en-es-sentence-veto-match-cerilla-shadow:candidate-04 | shadow_example | en-es:sentence-veto:match:partido | en-es:sentence-veto:match:cerilla:shadow | 4 | 312 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-match-partido:en-es-sentence-veto-match-cerilla-shadow:candidate-05 | shadow_example | en-es:sentence-veto:match:partido | en-es:sentence-veto:match:cerilla:shadow | 5 | 312 |
| en-es:source-frame-gap:active_example:en-es-sentence-veto-board-tablero:en-es-sentence-veto-board-tablero-active:candidate-01 | active_example | en-es:sentence-veto:board:tablero | en-es:sentence-veto:board:tablero:active | 1 | 327 |
| en-es:source-frame-gap:active_example:en-es-sentence-veto-board-tablero:en-es-sentence-veto-board-tablero-active:candidate-02 | active_example | en-es:sentence-veto:board:tablero | en-es:sentence-veto:board:tablero:active | 2 | 327 |
| en-es:source-frame-gap:active_example:en-es-sentence-veto-board-tablero:en-es-sentence-veto-board-tablero-active:candidate-03 | active_example | en-es:sentence-veto:board:tablero | en-es:sentence-veto:board:tablero:active | 3 | 327 |
| en-es:source-frame-gap:active_example:en-es-sentence-veto-board-tablero:en-es-sentence-veto-board-tablero-active:candidate-04 | active_example | en-es:sentence-veto:board:tablero | en-es:sentence-veto:board:tablero:active | 4 | 327 |
| en-es:source-frame-gap:active_example:en-es-sentence-veto-board-tablero:en-es-sentence-veto-board-tablero-active:candidate-05 | active_example | en-es:sentence-veto:board:tablero | en-es:sentence-veto:board:tablero:active | 5 | 327 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-board-tablero:en-es-sentence-veto-board-junta-shadow:candidate-01 | shadow_example | en-es:sentence-veto:board:tablero | en-es:sentence-veto:board:junta:shadow | 1 | 330 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-board-tablero:en-es-sentence-veto-board-junta-shadow:candidate-02 | shadow_example | en-es:sentence-veto:board:tablero | en-es:sentence-veto:board:junta:shadow | 2 | 330 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-board-tablero:en-es-sentence-veto-board-junta-shadow:candidate-03 | shadow_example | en-es:sentence-veto:board:tablero | en-es:sentence-veto:board:junta:shadow | 3 | 330 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-board-tablero:en-es-sentence-veto-board-junta-shadow:candidate-04 | shadow_example | en-es:sentence-veto:board:tablero | en-es:sentence-veto:board:junta:shadow | 4 | 330 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-board-tablero:en-es-sentence-veto-board-junta-shadow:candidate-05 | shadow_example | en-es:sentence-veto:board:tablero | en-es:sentence-veto:board:junta:shadow | 5 | 330 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-branch-sucursal:en-es-sentence-veto-branch-rama-shadow:candidate-01 | shadow_example | en-es:sentence-veto:branch:sucursal | en-es:sentence-veto:branch:rama:shadow | 1 | 314 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-branch-sucursal:en-es-sentence-veto-branch-rama-shadow:candidate-02 | shadow_example | en-es:sentence-veto:branch:sucursal | en-es:sentence-veto:branch:rama:shadow | 2 | 314 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-branch-sucursal:en-es-sentence-veto-branch-rama-shadow:candidate-03 | shadow_example | en-es:sentence-veto:branch:sucursal | en-es:sentence-veto:branch:rama:shadow | 3 | 314 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-branch-sucursal:en-es-sentence-veto-branch-rama-shadow:candidate-04 | shadow_example | en-es:sentence-veto:branch:sucursal | en-es:sentence-veto:branch:rama:shadow | 4 | 314 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-branch-sucursal:en-es-sentence-veto-branch-rama-shadow:candidate-05 | shadow_example | en-es:sentence-veto:branch:sucursal | en-es:sentence-veto:branch:rama:shadow | 5 | 314 |
| en-es:source-frame-gap:active_example:en-es-sentence-veto-drink-bebida:en-es-sentence-veto-drink-bebida-active:candidate-01 | active_example | en-es:sentence-veto:drink:bebida | en-es:sentence-veto:drink:bebida:active | 1 | 313 |
| en-es:source-frame-gap:active_example:en-es-sentence-veto-drink-bebida:en-es-sentence-veto-drink-bebida-active:candidate-02 | active_example | en-es:sentence-veto:drink:bebida | en-es:sentence-veto:drink:bebida:active | 2 | 313 |
| en-es:source-frame-gap:active_example:en-es-sentence-veto-drink-bebida:en-es-sentence-veto-drink-bebida-active:candidate-03 | active_example | en-es:sentence-veto:drink:bebida | en-es:sentence-veto:drink:bebida:active | 3 | 313 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-drink-bebida:en-es-sentence-veto-drink-beber-shadow:candidate-01 | shadow_example | en-es:sentence-veto:drink:bebida | en-es:sentence-veto:drink:beber:shadow | 1 | 313 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-drink-bebida:en-es-sentence-veto-drink-beber-shadow:candidate-02 | shadow_example | en-es:sentence-veto:drink:bebida | en-es:sentence-veto:drink:beber:shadow | 2 | 313 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-drink-bebida:en-es-sentence-veto-drink-beber-shadow:candidate-03 | shadow_example | en-es:sentence-veto:drink:bebida | en-es:sentence-veto:drink:beber:shadow | 3 | 313 |
| en-es:source-frame-gap:active_example:en-es-sentence-veto-play-obra:en-es-sentence-veto-play-obra-active:candidate-01 | active_example | en-es:sentence-veto:play:obra | en-es:sentence-veto:play:obra:active | 1 | 314 |
| en-es:source-frame-gap:active_example:en-es-sentence-veto-play-obra:en-es-sentence-veto-play-obra-active:candidate-02 | active_example | en-es:sentence-veto:play:obra | en-es:sentence-veto:play:obra:active | 2 | 314 |
| en-es:source-frame-gap:active_example:en-es-sentence-veto-play-obra:en-es-sentence-veto-play-obra-active:candidate-03 | active_example | en-es:sentence-veto:play:obra | en-es:sentence-veto:play:obra:active | 3 | 314 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-play-obra:en-es-sentence-veto-play-jugar-shadow:candidate-01 | shadow_example | en-es:sentence-veto:play:obra | en-es:sentence-veto:play:jugar:shadow | 1 | 311 |
