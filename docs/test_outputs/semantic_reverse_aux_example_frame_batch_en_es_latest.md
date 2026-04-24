# en-es Reverse Aux Example-Frame Batch

- Status: `ok`
- Generated: `2026-04-24T20:15:40Z`
- Batch: `en-es:reverse-aux-example-frames:reverse-aux-example-frames-v10-20260425a`
- Source: `reverse_aux_example_frames` / `installed_translation_pack`
- Rows: `13`

## Coverage

- Queue families: `8`
- Target families: `6`
- Target families with active reverse aux: `6`
- Target families with shadow reverse aux: `4`
- Families with phrase-control examples: `0`

| Family | Active Aux | Shadow Aux | Phrase Control | Rows |
| --- | ---: | ---: | ---: | ---: |
| `en-es:sentence-veto:plant:planta` | 1 | 0 | 0 | 1 |
| `en-es:sentence-veto:drink:bebida` | 1 | 1 | 0 | 2 |
| `en-es:sentence-veto:play:obra` | 0 | 1 | 0 | 1 |
| `en-es:sentence-veto:watch:reloj` | 1 | 1 | 0 | 2 |
| `en-es:sentence-veto:check:cheque` | 1 | 0 | 0 | 1 |
| `en-es:sentence-veto:order:pedido` | 1 | 1 | 0 | 2 |
| `en-es:sentence-veto:trip:viaje` | 1 | 1 | 0 | 2 |
| `en-es:sentence-veto:report:informe` | 1 | 1 | 0 | 2 |

## Recommendation

- This is a real non-LLM source batch, but it is not contract-complete: reverse aux covers active text for `6` target families and shadow text for `4`, with no phrase-control examples. Use the required-family contract gate to route the remaining rows to source ingestion or a narrow LLM example-frame generator.
