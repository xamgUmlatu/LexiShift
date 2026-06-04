# en-es WordNet Example-Frame Batch

- Status: `ok`
- Generated: `2026-04-28T01:15:46Z`
- Batch: `en-es:wordnet-example-frames:wordnet-def-ex-non-v10-wave4-anypos-supported-probe-v1-20260428a`
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
| `en-es:sentence-veto:change:cambio` | `target` | 2 | 2 | 0 | 4 | `cambio:13408652-n@0.1667`<br>`cambiar:00122978-v@0.4` |
| `en-es:sentence-veto:look:aspecto` | `target` | 2 | 2 | 0 | 4 | `aspecto:04682072-n@0.4`<br>`parecer:02137900-v@0.4` |
| `en-es:sentence-veto:dry:seco` | `target` | 2 | 2 | 0 | 4 | `seco:02562150-a@0.5`<br>`secar:00218901-v@0.25` |
| `en-es:sentence-veto:use:uso` | `target` | 2 | 2 | 0 | 4 | `uso:00948944-n@0.4`<br>`usar:02567247-v@0.4` |
| `en-es:sentence-veto:plain:llano` | `target` | 2 | 2 | 0 | 4 | `llano:00060864-s@0.2857`<br>`llanura:09416498-n@0.125` |
| `en-es:sentence-veto:fast:r-pido` | `target` | 2 | 2 | 0 | 4 | `rápido:00979699-a@0.2857`<br>`ayunar:01192137-v@0.4` |
| `en-es:sentence-veto:train:tren` | `target` | 2 | 2 | 0 | 4 | `tren:04475240-n@0.2857`<br>`adiestrar:02559394-v@0.2` |
| `en-es:sentence-veto:land:tierra` | `target` | 2 | 4 | 0 | 6 | `tierra:09357302-n@0.2222`<br>`país:13267561-n@0.25`<br>`atracar:01985450-v@0.2222` |
| `en-es:sentence-veto:mean:medio` | `target` | 2 | 2 | 0 | 4 | `medio:01598728-s@0.2`<br>`significar:00957180-v@0.2` |
| `en-es:sentence-veto:end:fin` | `target` | 2 | 2 | 0 | 4 | `fin:07306517-n@0.2`<br>`acabar:02615799-v@0.3333` |
| `en-es:sentence-veto:offer:oferta` | `target` | 2 | 2 | 0 | 4 | `oferta:07179197-n@0.25`<br>`ofrecer:02303593-v@0.25` |
| `en-es:sentence-veto:rest:reposo` | `target` | 2 | 4 | 0 | 6 | `reposo:15299060-n@0.1667`<br>`descanso:15299060-n@0.125`<br>`descansar:02670742-v@0.1667` |
| `en-es:sentence-veto:present:presente` | `target` | 2 | 2 | 0 | 4 | `presente:01735600-a@0.1667`<br>`actual:15144478-n@0.2` |
| `en-es:sentence-veto:sign:se-al` | `target` | 2 | 4 | 0 | 6 | `señal:06806088-n@0.1667`<br>`seña:07290723-n@0.4`<br>`firmar:00998530-v@0.2222` |
| `en-es:sentence-veto:answer:respuesta` | `target` | 2 | 4 | 0 | 6 | `respuesta:06758700-n@0.25`<br>`contestación:06758700-n@0.2`<br>`responder:00817348-v@0.1667` |
| `en-es:sentence-veto:quiet:silencio` | `target` | 2 | 2 | 0 | 4 | `silencio:04989456-n@0.4`<br>`calmar:02194634-v@0.2` |

## Recommendation

- This adapter is a real local source pass for active/shadow semantic evidence, but it intentionally does not solve phrase containment. Run the source-admission cycle before using it as a challenger, and treat missing/low-score links as source gaps rather than generated coverage.
