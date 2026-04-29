# en-es WordNet Example-Frame Batch

- Status: `ok`
- Generated: `2026-04-29T01:27:54Z`
- Batch: `en-es:wordnet-example-frames:wordnet-def-ex-non-v10-wave6-wiktextract-supported-v1-latest`
- Source: `wordnet_example_frames` / `external_sense_graph`
- Scope: `all_dataset_families`
- Rows: `72`
- Min link score: `0.12`
- Evidence mode: `definition_and_example`

## Coverage

- Queue families: `16`
- Source families: `16`
- Target families: `16`
- Target families with active WordNet rows: `16`
- Target families with shadow WordNet rows: `16`
- Families with phrase-control examples: `0`

| Family | Role | Active | Shadow | Phrase | Rows | Best Links |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `en-es:sentence-veto:leave:permiso` | `target` | 2 | 4 | 0 | 6 | `permiso:15164090-n@0.2`<br>`excedencia:15164090-n@0.4`<br>`dejar:02727313-v@0.2` |
| `en-es:sentence-veto:black:oscuro` | `target` | 2 | 1 | 0 | 3 | `oscuro:00393873-a@0.2`<br>`negro:04967454-n@0.2` |
| `en-es:sentence-veto:serve:servicio` | `target` | 2 | 2 | 0 | 4 | `servicio:00569467-n@0.3333`<br>`servir:02546367-v@0.25` |
| `en-es:sentence-veto:low:bajo` | `target` | 2 | 2 | 0 | 4 | `bajo:00395053-r@0.2`<br>`bajo:missing`<br>`decaído:00707060-s@0.2` |
| `en-es:sentence-veto:part:parte` | `target` | 2 | 4 | 0 | 6 | `parte:03898588-n@0.2`<br>`papel:00721817-n@0.2857`<br>`repartir:01560556-v@0.4` |
| `en-es:sentence-veto:feel:talento` | `target` | 2 | 2 | 0 | 4 | `talento:05685184-n@0.2`<br>`sentir:02110460-v@0.2` |
| `en-es:sentence-veto:still:quietud` | `target` | 2 | 3 | 0 | 5 | `quietud:04989727-n@0.1667`<br>`alambique:04326120-n@0.1667`<br>`aquietar:01768652-v@0.25` |
| `en-es:sentence-veto:bear:bajista` | `target` | 1 | 2 | 0 | 3 | `bajista:09864599-n@0.5`<br>`llevar:02706727-v@0.25` |
| `en-es:sentence-veto:finish:meta` | `target` | 2 | 4 | 0 | 6 | `meta:15292365-n@0.25`<br>`acabado:04707990-n@0.2`<br>`acabar:00485097-v@0.25` |
| `en-es:sentence-veto:throw:lanzamiento` | `target` | 2 | 2 | 0 | 4 | `lanzamiento:04437105-n@0.1667`<br>`lanzar:01511000-v@0.125` |
| `en-es:sentence-veto:upset:disgustado` | `target` | 2 | 2 | 0 | 4 | `disgustado:02466219-s@0.1667`<br>`trastrocar:00522376-v@0.1429` |
| `en-es:sentence-veto:piece:trozo` | `target` | 2 | 4 | 0 | 6 | `trozo:03938441-n@0.3333`<br>`ficha:03721866-n@0.2222`<br>`montar:01660471-v@0.1429` |
| `en-es:sentence-veto:fair:pastel` | `target` | 2 | 2 | 0 | 4 | `pastel:00244911-s@0.5`<br>`feria de muestras:08425514-n@0.1429` |
| `en-es:sentence-veto:show:espect-culo` | `target` | 2 | 2 | 0 | 4 | `espectáculo:00521313-n@0.2`<br>`demostrar:00925764-v@0.1667` |
| `en-es:sentence-veto:advance:avance` | `target` | 2 | 3 | 0 | 5 | `avance:07459865-n@0.2`<br>`adelanto:13397064-n@0.2`<br>`avanzar:01996535-v@0.3333` |
| `en-es:sentence-veto:rank:rancio` | `target` | 2 | 2 | 0 | 4 | `rancio:00582390-s@0.1429`<br>`fila:08448952-n@0.2222` |

## Recommendation

- This adapter is a real local source pass for active/shadow semantic evidence, but it intentionally does not solve phrase containment. Run the source-admission cycle before using it as a challenger, and treat missing/low-score links as source gaps rather than generated coverage.
