# en-es Source Row Alignment Audit

- Status: `ok`
- Generated: `2026-04-28T21:09:58Z`
- Rows audited: `126`
- Selector-ready rows: `55`
- Trigger-present rows: `55`
- Two-sided trigger-frame rows: `46`

## Recommendation

The audited source rows only partially support context-conditioned selection. Use them for sparse semantic support, but build trigger-bearing sentence-frame rows before treating dynamic evidence selection as fairly tested.

## Batch Coverage

| Batch | Rows | Selector-Ready | SHA-256 |
| --- | ---: | ---: | --- |
| /Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_example_frame_batches/en-es-def-example-plus-llm-aligned-frame-gap-v2-20260429a_cycle_sense_admitted_normalized_evidence.json | 126 | 55 | efd217419778dae331058696abb2accb2d7901cafdb097f3322083f58465576c |

## Source Families

| Source Family | Rows | Trigger-Present | Selector-Ready |
| --- | ---: | ---: | ---: |
| external_sense_graph | 55 | 15 | 15 |
| silver_llm_generation | 39 | 39 | 39 |
| installed_translation_pack | 32 | 1 | 1 |

## Relation Types

| Relation | Rows | Trigger-Present | Selector-Ready |
| --- | ---: | ---: | ---: |
| shadow_candidate | 64 | 30 | 30 |
| anchor_cue | 62 | 25 | 25 |

## Family Readiness

| Family | Active Rows | Shadow Rows | Active Selector-Ready | Shadow Selector-Ready | Ready For Dynamic Selection |
| --- | ---: | ---: | ---: | ---: | --- |
| en-es:sentence-veto:seal:sello | 4 | 6 | 1 | 4 | `yes` |
| en-es:sentence-veto:board:tablero | 4 | 4 | 1 | 3 | `yes` |
| en-es:sentence-veto:file:archivo | 5 | 3 | 3 | 1 | `yes` |
| en-es:sentence-veto:spring:primavera | 3 | 3 | 2 | 2 | `yes` |
| en-es:sentence-veto:ball:pelota | 3 | 4 | 1 | 2 | `yes` |
| en-es:sentence-veto:branch:sucursal | 3 | 5 | 1 | 2 | `yes` |
| en-es:sentence-veto:cell:celula | 2 | 5 | 1 | 2 | `yes` |
| en-es:sentence-veto:drink:bebida | 4 | 3 | 2 | 1 | `yes` |
| en-es:sentence-veto:match:partido | 2 | 3 | 1 | 2 | `yes` |
| en-es:sentence-veto:play:obra | 4 | 3 | 2 | 1 | `yes` |
| en-es:sentence-veto:report:informe | 5 | 1 | 2 | 1 | `yes` |
| en-es:sentence-veto:watch:reloj | 3 | 5 | 1 | 2 | `yes` |
| en-es:sentence-veto:bank:banco | 3 | 3 | 1 | 1 | `yes` |
| en-es:sentence-veto:check:cheque | 2 | 2 | 1 | 1 | `yes` |
| en-es:sentence-veto:order:pedido | 3 | 3 | 1 | 1 | `yes` |
| en-es:sentence-veto:park:parque | 3 | 3 | 1 | 1 | `yes` |
| en-es:sentence-veto:plant:planta | 3 | 2 | 1 | 1 | `yes` |
| en-es:sentence-veto:table:mesa | 3 | 2 | 1 | 1 | `yes` |
| en-es:sentence-veto:trip:viaje | 3 | 4 | 1 | 1 | `yes` |

## Sample Rows

| Row | Relation | Trigger Present | Selector-Ready | Text |
| --- | --- | --- | --- | --- |
| en-es-sentence-veto-ball-pelota:active-reverse-aux | anchor_cue | `no` | `no` | object, generally spherical, used for playing games |
| en-es-sentence-veto-ball-pelota:shadow-en-es-sentence-veto-ball-baile-shadow-reverse-aux | shadow_candidate | `no` | `no` | formal dance |
| en-es-sentence-veto-bank-banco:active-reverse-aux | anchor_cue | `no` | `no` | institution |
| en-es-sentence-veto-bank-banco:shadow-en-es-sentence-veto-bank-orilla-shadow-reverse-aux | shadow_candidate | `no` | `no` | edge of river or lake |
| en-es-sentence-veto-plant-planta:active-reverse-aux | anchor_cue | `no` | `no` | organism capable of photosynthesis |
| en-es-sentence-veto-cell-celula:shadow-en-es-sentence-veto-cell-celda-shadow-reverse-aux | shadow_candidate | `no` | `no` | component of an electrical battery |
| en-es-sentence-veto-spring-primavera:active-reverse-aux | anchor_cue | `no` | `no` | season between winter and summer in temperate climates |
| en-es-sentence-veto-spring-primavera:shadow-en-es-sentence-veto-spring-resorte-shadow-reverse-aux | shadow_candidate | `no` | `no` | device made of flexible material |
| en-es-sentence-veto-seal-sello:active-reverse-aux | anchor_cue | `no` | `no` | stamp used to impress a design on a soft substance |
| en-es-sentence-veto-seal-sello:shadow-en-es-sentence-veto-seal-foca-shadow-reverse-aux | shadow_candidate | `no` | `no` | pinniped |
| en-es-sentence-veto-file-archivo:active-reverse-aux | anchor_cue | `no` | `no` | collection of papers |
| en-es-sentence-veto-file-archivo:shadow-en-es-sentence-veto-file-lima-shadow-reverse-aux | shadow_candidate | `no` | `no` | cutting or smoothing tool |
| en-es-sentence-veto-match-partido:active-reverse-aux | anchor_cue | `no` | `no` | sporting event |
| en-es-sentence-veto-match-partido:shadow-en-es-sentence-veto-match-cerilla-shadow-reverse-aux | shadow_candidate | `no` | `no` | device to make fire |
| en-es-sentence-veto-board-tablero:active-reverse-aux | anchor_cue | `no` | `no` | long, wide and thin piece of wood or other material |
| en-es-sentence-veto-board-tablero:shadow-en-es-sentence-veto-board-junta-shadow-reverse-aux | shadow_candidate | `no` | `no` | managing committee |
| en-es-sentence-veto-table-mesa:active-reverse-aux | anchor_cue | `no` | `no` | item of furniture |
| en-es-sentence-veto-table-mesa:shadow-en-es-sentence-veto-table-tabla-shadow-reverse-aux | shadow_candidate | `no` | `no` | grid of data in rows and columns |
| en-es-sentence-veto-branch-sucursal:active-reverse-aux | anchor_cue | `no` | `no` | location of an organization with several locations |
| en-es-sentence-veto-branch-sucursal:shadow-en-es-sentence-veto-branch-rama-shadow-reverse-aux | shadow_candidate | `no` | `no` | woody part of a tree arising from the trunk |
