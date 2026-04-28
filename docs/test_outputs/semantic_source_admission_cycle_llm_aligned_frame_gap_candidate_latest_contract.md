# en-es Semantic Example-Frame Contract

- Status: `review`
- Generated: `2026-04-28T21:02:34Z`
- Batch: `en-es:example-frame-composite:llm-aligned-source-frame-gap-v1-20260429a:sense-admitted`
- Source: `llm_aligned_sentence_frame_rows_candidate_only`
- Rows: `36`
- Semantic complete families: `8` / `19`
- Phrase-containment complete families: `0` / `19`
- Complete families: `0` / `19`
- Combined status: `review`

## Family Coverage

| Family | Active | Shadow | Phrase Control | Semantic | Phrase | Combined | Missing |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| `en-es:sentence-veto:ball:pelota` | 0 | 2 | 0 | `review` | `review` | `review` | `active_examples`, `phrase_control_examples` |
| `en-es:sentence-veto:bank:banco` | 0 | 0 | 0 | `review` | `review` | `review` | `active_examples`, `shadow_examples`, `phrase_control_examples` |
| `en-es:sentence-veto:board:tablero` | 1 | 0 | 0 | `review` | `review` | `review` | `shadow_examples`, `phrase_control_examples` |
| `en-es:sentence-veto:branch:sucursal` | 0 | 2 | 0 | `review` | `review` | `review` | `active_examples`, `phrase_control_examples` |
| `en-es:sentence-veto:cell:celula` | 1 | 2 | 0 | `ok` | `review` | `review` | `phrase_control_examples` |
| `en-es:sentence-veto:check:cheque` | 0 | 0 | 0 | `review` | `review` | `review` | `active_examples`, `shadow_examples`, `phrase_control_examples` |
| `en-es:sentence-veto:drink:bebida` | 2 | 1 | 0 | `ok` | `review` | `review` | `phrase_control_examples` |
| `en-es:sentence-veto:file:archivo` | 3 | 1 | 0 | `ok` | `review` | `review` | `phrase_control_examples` |
| `en-es:sentence-veto:match:partido` | 1 | 2 | 0 | `ok` | `review` | `review` | `phrase_control_examples` |
| `en-es:sentence-veto:order:pedido` | 0 | 0 | 0 | `review` | `review` | `review` | `active_examples`, `shadow_examples`, `phrase_control_examples` |
| `en-es:sentence-veto:park:parque` | 0 | 0 | 0 | `review` | `review` | `review` | `active_examples`, `shadow_examples`, `phrase_control_examples` |
| `en-es:sentence-veto:plant:planta` | 1 | 0 | 0 | `review` | `review` | `review` | `shadow_examples`, `phrase_control_examples` |
| `en-es:sentence-veto:play:obra` | 2 | 1 | 0 | `ok` | `review` | `review` | `phrase_control_examples` |
| `en-es:sentence-veto:report:informe` | 2 | 1 | 0 | `ok` | `review` | `review` | `phrase_control_examples` |
| `en-es:sentence-veto:seal:sello` | 1 | 4 | 0 | `ok` | `review` | `review` | `phrase_control_examples` |
| `en-es:sentence-veto:spring:primavera` | 0 | 2 | 0 | `review` | `review` | `review` | `active_examples`, `phrase_control_examples` |
| `en-es:sentence-veto:table:mesa` | 0 | 0 | 0 | `review` | `review` | `review` | `active_examples`, `shadow_examples`, `phrase_control_examples` |
| `en-es:sentence-veto:trip:viaje` | 0 | 1 | 0 | `review` | `review` | `review` | `active_examples`, `phrase_control_examples` |
| `en-es:sentence-veto:watch:reloj` | 1 | 2 | 0 | `ok` | `review` | `review` | `phrase_control_examples` |

## Recommendation

- Do not treat this batch as promotion-relevant for prototype admission. Semantic gaps: active=9, shadow=7. Phrase containment gaps: phrase_control=19. Generate or ingest admitted active/shadow rows first, and keep phrase rows on the containment-only path.
