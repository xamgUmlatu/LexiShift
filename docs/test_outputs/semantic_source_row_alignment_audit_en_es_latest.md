# en-es Source Row Alignment Audit

- Status: `ok`
- Generated: `2026-04-28T20:47:37Z`
- Rows audited: `87`
- Selector-ready rows: `16`
- Trigger-present rows: `16`
- Two-sided trigger-frame rows: `7`

## Recommendation

The audited source rows only partially support context-conditioned selection. Use them for sparse semantic support, but build trigger-bearing sentence-frame rows before treating dynamic evidence selection as fairly tested.

## Batch Coverage

| Batch | Rows | Selector-Ready | SHA-256 |
| --- | ---: | ---: | --- |
| /Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_example_frame_batches/en-es-reverse-aux-wordnet-def-example-all-v10-20260425a_cycle_sense_admitted_normalized_evidence.json | 87 | 16 | 790fc2dd96588d1a083f727ee4b120439110c2416e7dfd754bbe91df07492954 |

## Source Families

| Source Family | Rows | Trigger-Present | Selector-Ready |
| --- | ---: | ---: | ---: |
| external_sense_graph | 55 | 15 | 15 |
| installed_translation_pack | 32 | 1 | 1 |

## Relation Types

| Relation | Rows | Trigger-Present | Selector-Ready |
| --- | ---: | ---: | ---: |
| anchor_cue | 47 | 10 | 10 |
| shadow_candidate | 40 | 6 | 6 |

## Family Readiness

| Family | Active Rows | Shadow Rows | Active Selector-Ready | Shadow Selector-Ready | Ready For Dynamic Selection |
| --- | ---: | ---: | ---: | ---: | --- |
| en-es:sentence-veto:spring:primavera | 3 | 1 | 2 | 0 | `no` |
| en-es:sentence-veto:ball:pelota | 3 | 2 | 1 | 0 | `no` |
| en-es:sentence-veto:branch:sucursal | 3 | 3 | 1 | 0 | `no` |
| en-es:sentence-veto:plant:planta | 2 | 2 | 0 | 1 | `no` |
| en-es:sentence-veto:trip:viaje | 3 | 3 | 1 | 0 | `no` |
| en-es:sentence-veto:board:tablero | 3 | 1 | 0 | 0 | `no` |
| en-es:sentence-veto:cell:celula | 1 | 3 | 0 | 0 | `no` |
| en-es:sentence-veto:drink:bebida | 2 | 2 | 0 | 0 | `no` |
| en-es:sentence-veto:file:archivo | 2 | 2 | 0 | 0 | `no` |
| en-es:sentence-veto:match:partido | 1 | 1 | 0 | 0 | `no` |
| en-es:sentence-veto:play:obra | 2 | 2 | 0 | 0 | `no` |
| en-es:sentence-veto:report:informe | 3 | 0 | 0 | 0 | `no` |
| en-es:sentence-veto:seal:sello | 3 | 2 | 0 | 0 | `no` |
| en-es:sentence-veto:watch:reloj | 2 | 3 | 0 | 0 | `no` |
| en-es:sentence-veto:bank:banco | 3 | 3 | 1 | 1 | `yes` |
| en-es:sentence-veto:check:cheque | 2 | 2 | 1 | 1 | `yes` |
| en-es:sentence-veto:order:pedido | 3 | 3 | 1 | 1 | `yes` |
| en-es:sentence-veto:park:parque | 3 | 3 | 1 | 1 | `yes` |
| en-es:sentence-veto:table:mesa | 3 | 2 | 1 | 1 | `yes` |

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
