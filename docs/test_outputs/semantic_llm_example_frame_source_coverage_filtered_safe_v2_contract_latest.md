# en-es Semantic Example-Frame Contract

- Status: `review`
- Generated: `2026-04-25T00:33:40Z`
- Batch: `en-es:example-frame-composite:balanced-plus-source-coverage-filtered-safe-v2-20260425a`
- Source: `reverse_aux_llm_balanced_plus_source_coverage_filtered_safe_v2`
- Rows: `60`
- Semantic complete families: `19` / `19`
- Phrase-containment complete families: `8` / `19`
- Complete families: `8` / `19`
- Combined status: `review`

## Family Coverage

| Family | Active | Shadow | Phrase Control | Semantic | Phrase | Combined | Missing |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| `en-es:sentence-veto:ball:pelota` | 1 | 1 | 0 | `ok` | `review` | `review` | `phrase_control_examples` |
| `en-es:sentence-veto:bank:banco` | 1 | 1 | 0 | `ok` | `review` | `review` | `phrase_control_examples` |
| `en-es:sentence-veto:board:tablero` | 1 | 1 | 0 | `ok` | `review` | `review` | `phrase_control_examples` |
| `en-es:sentence-veto:branch:sucursal` | 1 | 1 | 0 | `ok` | `review` | `review` | `phrase_control_examples` |
| `en-es:sentence-veto:cell:celula` | 1 | 1 | 0 | `ok` | `review` | `review` | `phrase_control_examples` |
| `en-es:sentence-veto:check:cheque` | 3 | 1 | 1 | `ok` | `ok` | `ok` | none |
| `en-es:sentence-veto:drink:bebida` | 1 | 1 | 1 | `ok` | `ok` | `ok` | none |
| `en-es:sentence-veto:file:archivo` | 1 | 1 | 0 | `ok` | `review` | `review` | `phrase_control_examples` |
| `en-es:sentence-veto:match:partido` | 1 | 1 | 0 | `ok` | `review` | `review` | `phrase_control_examples` |
| `en-es:sentence-veto:order:pedido` | 3 | 1 | 1 | `ok` | `ok` | `ok` | none |
| `en-es:sentence-veto:park:parque` | 1 | 1 | 0 | `ok` | `review` | `review` | `phrase_control_examples` |
| `en-es:sentence-veto:plant:planta` | 3 | 1 | 1 | `ok` | `ok` | `ok` | none |
| `en-es:sentence-veto:play:obra` | 3 | 1 | 1 | `ok` | `ok` | `ok` | none |
| `en-es:sentence-veto:report:informe` | 3 | 3 | 1 | `ok` | `ok` | `ok` | none |
| `en-es:sentence-veto:seal:sello` | 1 | 1 | 0 | `ok` | `review` | `review` | `phrase_control_examples` |
| `en-es:sentence-veto:spring:primavera` | 1 | 1 | 0 | `ok` | `review` | `review` | `phrase_control_examples` |
| `en-es:sentence-veto:table:mesa` | 1 | 1 | 0 | `ok` | `review` | `review` | `phrase_control_examples` |
| `en-es:sentence-veto:trip:viaje` | 2 | 1 | 1 | `ok` | `ok` | `ok` | none |
| `en-es:sentence-veto:watch:reloj` | 2 | 1 | 1 | `ok` | `ok` | `ok` | none |

## Recommendation

- Semantic active/shadow coverage is complete, but the combined source contract remains review. Phrase containment gaps: missing_phrase_control=11, phrase_role_issues=0. Keep this batch analysis-only unless a downstream no-phrase ablation explicitly carries the candidate lane and promotion policy accepts the split contract.
