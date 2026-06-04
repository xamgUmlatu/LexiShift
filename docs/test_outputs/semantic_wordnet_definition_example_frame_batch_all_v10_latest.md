# en-es WordNet Example-Frame Batch

- Status: `ok`
- Generated: `2026-04-25T01:42:25Z`
- Batch: `en-es:wordnet-example-frames:wordnet-definition-example-frames-all-v10-20260425a`
- Source: `wordnet_example_frames` / `external_sense_graph`
- Scope: `all_dataset_families`
- Rows: `62`
- Min link score: `0.12`
- Evidence mode: `definition_and_example`

## Coverage

- Queue families: `8`
- Source families: `19`
- Target families: `19`
- Target families with active WordNet rows: `18`
- Target families with shadow WordNet rows: `16`
- Families with phrase-control examples: `0`

| Family | Role | Active | Shadow | Phrase | Rows | Best Links |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `en-es:sentence-veto:ball:pelota` | `target` | 2 | 1 | 0 | 3 | `pelota:02782458-n@0.4`<br>`baile:07463485-n@0.2222` |
| `en-es:sentence-veto:bank:banco` | `target` | 2 | 2 | 0 | 4 | `banco:08437235-n@0.4`<br>`orilla:09236472-n@0.1429` |
| `en-es:sentence-veto:plant:planta` | `target` | 1 | 2 | 0 | 3 | `planta:00017402-n@0.2`<br>`fábrica:03963198-n@0.1429` |
| `en-es:sentence-veto:cell:celula` | `target` | 2 | 2 | 0 | 4 | `célula:00006484-n@0.3`<br>`celda:02994757-n@0.5` |
| `en-es:sentence-veto:spring:primavera` | `target` | 2 | 0 | 0 | 2 | `primavera:15261841-n@0.2222`<br>`resorte:missing` |
| `en-es:sentence-veto:seal:sello` | `target` | 2 | 1 | 0 | 3 | `sello:04167097-n@0.3`<br>`foca:02078848-n@0.2222` |
| `en-es:sentence-veto:file:archivo` | `target` | 1 | 1 | 0 | 2 | `archivo:06520807-n@0.125`<br>`lima:03341784-n@0.3` |
| `en-es:sentence-veto:match:partido` | `target` | 0 | 0 | 0 | 0 | `partido:missing`<br>`cerilla:missing` |
| `en-es:sentence-veto:board:tablero` | `target` | 2 | 0 | 0 | 2 | `tablero:03102791-n@0.3`<br>`junta:missing` |
| `en-es:sentence-veto:table:mesa` | `target` | 2 | 2 | 0 | 4 | `mesa:04386330-n@0.5`<br>`tabla:08283156-n@0.3333` |
| `en-es:sentence-veto:branch:sucursal` | `target` | 2 | 2 | 0 | 4 | `sucursal:08418205-n@0.25`<br>`rama:02740838-n@0.125` |
| `en-es:sentence-veto:park:parque` | `target` | 2 | 2 | 0 | 4 | `parque:08632949-n@0.125`<br>`aparcar:01496037-v@0.375` |
| `en-es:sentence-veto:drink:bebida` | `target` | 2 | 2 | 0 | 4 | `bebida:07897775-n@0.3333`<br>`beber:01173463-v@0.1429` |
| `en-es:sentence-veto:play:obra` | `target` | 2 | 2 | 0 | 4 | `obra:07021061-n@0.5556`<br>`jugar:01081873-v@0.3333` |
| `en-es:sentence-veto:watch:reloj` | `target` | 1 | 2 | 0 | 3 | `reloj:04563183-n@0.3`<br>`vigilar:02460829-v@0.1429` |
| `en-es:sentence-veto:check:cheque` | `target` | 2 | 2 | 0 | 4 | `cheque:13402907-n@0.6364`<br>`revisar:00665271-v@0.1667` |
| `en-es:sentence-veto:order:pedido` | `target` | 2 | 2 | 0 | 4 | `pedido:06541210-n@0.25`<br>`ordenar:00748704-v@0.1667` |
| `en-es:sentence-veto:trip:viaje` | `target` | 2 | 2 | 0 | 4 | `viaje:00309196-n@0.1667`<br>`tropezar:01904753-v@0.1667` |
| `en-es:sentence-veto:report:informe` | `target` | 2 | 2 | 0 | 4 | `informe:07233130-n@0.4`<br>`informar:00968841-v@0.25` |

## Recommendation

- This adapter is a real local source pass for active/shadow semantic evidence, but it intentionally does not solve phrase containment. Run the source-admission cycle before using it as a challenger, and treat missing/low-score links as source gaps rather than generated coverage.
