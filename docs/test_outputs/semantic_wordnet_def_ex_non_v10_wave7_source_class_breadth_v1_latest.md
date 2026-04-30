# en-es WordNet Example-Frame Batch

- Status: `ok`
- Generated: `2026-04-30T18:03:56Z`
- Batch: `en-es:wordnet-example-frames:wordnet-def-ex-non-v10-wave7-source-class-breadth-v1-latest`
- Source: `wordnet_example_frames` / `external_sense_graph`
- Scope: `prompt_queue`
- Rows: `68`
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
| `en-es:sentence-veto:like:gustos` | `target` | 2 | 2 | 0 | 4 | `gustos:05854415-n@0.2`<br>`atraer:01781131-v@0.2` |
| `en-es:sentence-veto:gross:repulsivo` | `target` | 2 | 1 | 0 | 3 | `repulsivo:00686808-s@0.2`<br>`gruesa:13772644-n@0.4` |
| `en-es:sentence-veto:cast:lanzamiento` | `target` | 2 | 4 | 0 | 6 | `lanzamiento:01248360-n@0.4`<br>`molde:13936581-n@0.3333`<br>`lanzar:01636439-v@0.2222` |
| `en-es:sentence-veto:fix:aprieto` | `target` | 2 | 4 | 0 | 6 | `aprieto:14432893-n@0.3333`<br>`localización:00156307-n@0.4`<br>`reparar:00261534-v@0.4` |
| `en-es:sentence-veto:full:lleno` | `target` | 2 | 2 | 0 | 4 | `lleno:01086845-a@0.2857`<br>`abatanar:01401959-v@0.1667` |
| `en-es:sentence-veto:waste:desperdicio` | `target` | 2 | 4 | 0 | 6 | `desperdicio:14880414-n@0.1667`<br>`baldío:08521615-n@0.1667`<br>`malgastar:02273196-v@0.25` |
| `en-es:sentence-veto:firm:firma` | `target` | 2 | 2 | 0 | 4 | `firma:08076706-n@0.2`<br>`afirmar:00421387-v@0.2` |
| `en-es:sentence-veto:even:tarde` | `target` | 2 | 2 | 0 | 4 | `tarde:15191509-n@0.25`<br>`allanar:01309802-v@0.25` |
| `en-es:sentence-veto:wrong:incorrecto` | `target` | 2 | 1 | 0 | 3 | `incorrecto:00635278-a@0.25`<br>`herir:02519655-v@0.4` |
| `en-es:sentence-veto:meet:adecuado` | `target` | 2 | 2 | 0 | 4 | `adecuado:01373068-s@0.125`<br>`encontrar:02026953-v@0.2857` |
| `en-es:sentence-veto:stretch:estir-n` | `target` | 1 | 2 | 0 | 3 | `estirón:00342069-n@0.25`<br>`estirar:00241696-v@0.2` |
| `en-es:sentence-veto:score:tantos` | `target` | 2 | 4 | 0 | 6 | `tantos:05745098-n@0.1667`<br>`marcador:05745098-n@0.1667`<br>`anotar:01114241-v@0.3333` |
| `en-es:sentence-veto:crash:choque` | `target` | 2 | 4 | 0 | 6 | `choque:07316568-n@0.2`<br>`fallo:07494014-n@0.2`<br>`chocar:01976584-v@0.4286` |
| `en-es:sentence-veto:trim:compensador` | `target` | 1 | 2 | 0 | 3 | `compensador:13850733-n@0.1667`<br>`recortar:00430013-v@0.2` |
| `en-es:sentence-veto:squeeze:crisis` | `target` | 1 | 2 | 0 | 3 | `crisis:14512496-n@0.2`<br>`apretujar:01530059-v@0.1667` |
| `en-es:sentence-veto:foul:falta` | `target` | 1 | 2 | 0 | 3 | `falta:00772486-n@0.2`<br>`ensuciar:00493642-v@0.2` |

## Recommendation

- This adapter is a real local source pass for active/shadow semantic evidence, but it intentionally does not solve phrase containment. Run the source-admission cycle before using it as a challenger, and treat missing/low-score links as source gaps rather than generated coverage.
