# en-es Semantic Veto Evidence-Gap Generation Run

- Status: `partial`
- Generated: `2026-05-11T23:46:45Z`
- Execution mode: `live`
- Batch id: `en-es:semantic-veto-evidence-gap-generation:en-es-active-only-full-v1-tranche-002-approved`
- Pilot id: `semantic_veto_active_only_full_en_es_v1`
- Prompt id: `semantic_veto_evidence_gap_generation_v7_shadow_target_correctness`
- Selected model: `gpt-5.4-mini`

## Summary

- Selected requests: `44`
- Accepted responses: `42`
- Accepted generated items: `84`
- API errors: `0`
- Invalid outputs: `2`
- Input tokens: `22066`
- Output tokens: `7941`
- Accepted responses by arm: `P0_exposure_first: 36, P1_exposure_first: 6`
- Accepted items by slot: `active_evidence_expansion: 84`

## Admission Preview

- Admission status: `review`
- Admission decision: `generated_responses_need_repair`
- Admitted items: `84`
- Rejected items: `0`
- Waived items: `0`
- Coverage shortfall: `4`

## Artifacts

- Run manifest: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-en-es-active-only-full-v1-tranche-002-approved_run_manifest.json`
- Request queue: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-en-es-active-only-full-v1-tranche-002-approved_request_queue.jsonl`
- Journal: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-en-es-active-only-full-v1-tranche-002-approved_journal.jsonl`
- Raw responses JSONL: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-en-es-active-only-full-v1-tranche-002-approved_raw_responses.jsonl`
- Failures JSONL: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-en-es-active-only-full-v1-tranche-002-approved_failures.jsonl`
- Raw response bundle: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-en-es-active-only-full-v1-tranche-002-approved_raw_responses.json`
- Generated responses: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-en-es-active-only-full-v1-tranche-002-approved_generated_responses.json`

## Request Outcomes

| Request | Arm | Slot | Status | Items | Output / Error |
| --- | --- | --- | --- | ---: | --- |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:light:debil:2cf12e4e:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | After the illness, he felt too light to carry his own suitcase. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:maybe:quizas:5c3f45a1:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `invalid_output` | 0 | ValueError: request_id did not match request packet |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:million:millon:1eb67060:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The charity raised a million dollars for the new clinic. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:never:jamas:93b82cf1:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | I will never betray my friends. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:nice:rico:4430e567:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The soup was nice and hot, with a deep tomato flavor. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:officer:funcionario:dae225aa:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The customs officer reviewed the paperwork and stamped our passports. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:official:funcionario:b160a162:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The official from the city hall answered questions about the new permit rules. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:old:anciano:2c3b44d9:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The old man walked slowly with a cane to the bench in the park. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:present:contemporaneo:6a5bc877:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The museum opened a present art wing with works by local painters. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:race:correr:fcb7ba09:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | I had to race to catch the last train before it left the station. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:red:rojo:43f57e5e:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | She painted the bedroom red to create a warm, bold look. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:report:informar:e73a0d90:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | Please report any changes to the team lead before noon. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:rest:descansar:75cbcdb9:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | After the hike, we stopped by the lake to rest before heading home. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:run:correr:1b592b59:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | I go to the park every morning to run before work. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:show:mostrar:c078d25e:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | Please show me the new design on the tablet. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:start:comenzar:dc408000:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | Please start the meeting at 9 a.m. sharp. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:tax:imponer:e1fe585a:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `invalid_output` | 0 | ValueError: request_id did not match request packet |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:visit:visita:73faef93:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | I will visit my grandmother this weekend at her house. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:west:oeste:febbff35:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The sun set in the west behind the hills. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:wife:esposa:84d8bd95:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | My wife and I are celebrating our tenth anniversary tonight. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:absence:falta:19c6195c:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | Her absence from the meeting caused the project to lose its final approval. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:afternoon:tarde:43049987:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | We have a meeting in the afternoon, after lunch and before the day ends. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:author:autor:d4af7245:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The author signed copies of the novel after the reading. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:background:fondo:486c1600:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The white text stood out clearly against the dark background of the poster. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:boss:jefe:7dce968c:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | My boss approved the budget for the new team project. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:exclusively:solo:2db6ddde:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | This offer is available exclusively to new subscribers. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:favour:favor:18639b63:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | Could you do me a favour and call the supplier before noon? |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:lack:falta:99e2f8f3:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The report noted a lack of clean water in the village. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:lay:poner:88e4d6a7:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | Please lay the book on the table before you leave. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:leader:jefe:40cbdd5f:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The leader set our work schedule and approved every request. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:majority:mayoria:f1c946e7:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The majority of voters supported the new plan. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:manager:director:f001fe23:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | After the merger, the new manager approved the season lineup and supervised every department. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:politician:politico:affee2fd:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The politician promised to lower taxes and spoke at the town hall last night. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:republic:republica:af4a945b:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The founders wanted the new republic to guarantee voting rights for all citizens. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:sun:sol:d3e33a85:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The sun rose over the mountains, warming the valley before breakfast. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:thousand:mil:eb4dcfd8:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The fundraiser reached a thousand dollars by sunset. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:writer:autor:ff4e19b6:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The writer signed copies of her new novel at the bookstore. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:yesterday:ayer:124f1659:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | I submitted the report yesterday after the meeting ended. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:academy:academia:717639a3:active_evidence_expansion` | `P1_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | She enrolled at the academy to study art, history, and philosophy. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:adjacent:vecino:f732391d:active_evidence_expansion` | `P1_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The library is adjacent to the park, so we can walk there in two minutes. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:arrange:arreglar:4513f094:active_evidence_expansion` | `P1_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | Can you arrange the broken chair before guests arrive? |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:axis:eje:0048e9cf:active_evidence_expansion` | `P1_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The wheel was slightly bent, so the mechanic checked the axis before tightening the bearings. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:bare:desnudo:9adf3ea8:active_evidence_expansion` | `P1_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The statue stood bare in the center of the courtyard, with no clothes or covering at all. |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:battle:batalla:4bc7c7b3:active_evidence_expansion` | `P1_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The generals planned the battle at dawn before the troops moved into the valley. |
