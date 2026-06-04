# en-es WordNet Example-Frame Batch

- Status: `ok`
- Generated: `2026-04-27T22:32:37Z`
- Batch: `en-es:wordnet-example-frames:wordnet-def-ex-non-v10-wave2-selected-v1-20260428c`
- Source: `wordnet_example_frames` / `external_sense_graph`
- Scope: `all_dataset_families`
- Rows: `38`
- Min link score: `0.16`
- Evidence mode: `definition_and_example`

## Coverage

- Queue families: `8`
- Source families: `8`
- Target families: `8`
- Target families with active WordNet rows: `8`
- Target families with shadow WordNet rows: `8`
- Families with phrase-control examples: `0`

| Family | Role | Active | Shadow | Phrase | Rows | Best Links |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `en-es:sentence-veto:look:aspecto` | `target` | 2 | 2 | 0 | 4 | `aspecto:04682072-n@0.4`<br>`parecer:02137900-v@0.4` |
| `en-es:sentence-veto:use:uso` | `target` | 2 | 2 | 0 | 4 | `uso:00948944-n@0.4`<br>`usar:02567247-v@0.4` |
| `en-es:sentence-veto:train:tren` | `target` | 2 | 2 | 0 | 4 | `tren:04475240-n@0.2857`<br>`adiestrar:02559394-v@0.2` |
| `en-es:sentence-veto:land:tierra` | `target` | 2 | 4 | 0 | 6 | `tierra:09357302-n@0.2222`<br>`país:13267561-n@0.25`<br>`atracar:01985450-v@0.2222` |
| `en-es:sentence-veto:offer:oferta` | `target` | 2 | 2 | 0 | 4 | `oferta:07179197-n@0.25`<br>`ofrecer:02303593-v@0.25` |
| `en-es:sentence-veto:rest:reposo` | `target` | 2 | 2 | 0 | 4 | `reposo:15299060-n@0.1667`<br>`descansar:02670742-v@0.1667` |
| `en-es:sentence-veto:sign:se-al` | `target` | 2 | 4 | 0 | 6 | `señal:06806088-n@0.1667`<br>`seña:07290723-n@0.4`<br>`firmar:00998530-v@0.2222` |
| `en-es:sentence-veto:answer:respuesta` | `target` | 2 | 4 | 0 | 6 | `respuesta:06758700-n@0.25`<br>`contestación:06758700-n@0.2`<br>`responder:00817348-v@0.1667` |

## Recommendation

- This adapter is a real local source pass for active/shadow semantic evidence, but it intentionally does not solve phrase containment. Run the source-admission cycle before using it as a challenger, and treat missing/low-score links as source gaps rather than generated coverage.
