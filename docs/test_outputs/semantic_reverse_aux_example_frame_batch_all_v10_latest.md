# en-es Reverse Aux Example-Frame Batch

- Status: `ok`
- Generated: `2026-04-25T01:23:20Z`
- Batch: `en-es:reverse-aux-example-frames:reverse-aux-example-frames-all-v10-20260425a`
- Source: `reverse_aux_example_frames` / `installed_translation_pack`
- Scope: `all_dataset_families`
- Rows: `35`

## Coverage

- Queue families: `8`
- Source families: `19`
- Target families: `19`
- Target families with active reverse aux: `18`
- Target families with shadow reverse aux: `17`
- Families with phrase-control examples: `0`

| Family | Role | Active Aux | Shadow Aux | Phrase Control | Rows |
| --- | --- | ---: | ---: | ---: | ---: |
| `en-es:sentence-veto:ball:pelota` | `target` | 1 | 1 | 0 | 2 |
| `en-es:sentence-veto:bank:banco` | `target` | 1 | 1 | 0 | 2 |
| `en-es:sentence-veto:plant:planta` | `target` | 1 | 0 | 0 | 1 |
| `en-es:sentence-veto:cell:celula` | `target` | 1 | 1 | 0 | 2 |
| `en-es:sentence-veto:spring:primavera` | `target` | 1 | 1 | 0 | 2 |
| `en-es:sentence-veto:seal:sello` | `target` | 1 | 1 | 0 | 2 |
| `en-es:sentence-veto:file:archivo` | `target` | 1 | 1 | 0 | 2 |
| `en-es:sentence-veto:match:partido` | `target` | 1 | 1 | 0 | 2 |
| `en-es:sentence-veto:board:tablero` | `target` | 1 | 1 | 0 | 2 |
| `en-es:sentence-veto:table:mesa` | `target` | 1 | 1 | 0 | 2 |
| `en-es:sentence-veto:branch:sucursal` | `target` | 1 | 1 | 0 | 2 |
| `en-es:sentence-veto:park:parque` | `target` | 1 | 1 | 0 | 2 |
| `en-es:sentence-veto:drink:bebida` | `target` | 1 | 1 | 0 | 2 |
| `en-es:sentence-veto:play:obra` | `target` | 0 | 1 | 0 | 1 |
| `en-es:sentence-veto:watch:reloj` | `target` | 1 | 1 | 0 | 2 |
| `en-es:sentence-veto:check:cheque` | `target` | 1 | 0 | 0 | 1 |
| `en-es:sentence-veto:order:pedido` | `target` | 1 | 1 | 0 | 2 |
| `en-es:sentence-veto:trip:viaje` | `target` | 1 | 1 | 0 | 2 |
| `en-es:sentence-veto:report:informe` | `target` | 1 | 1 | 0 | 2 |

## Recommendation

- This is a real non-LLM source batch, but it is not contract-complete: reverse aux covers active text for `18` target families and shadow text for `17`, with no phrase-control examples. Use the required-family contract gate to route the remaining rows to source ingestion or a narrow LLM example-frame generator.
