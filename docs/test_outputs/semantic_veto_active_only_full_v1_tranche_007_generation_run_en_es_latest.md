# en-es Semantic Veto Evidence-Gap Generation Run

- Status: `partial`
- Generated: `2026-05-13T18:00:01Z`
- Execution mode: `live`
- Batch id: `en-es:semantic-veto-evidence-gap-generation:en-es-active-only-full-v1-tranche-007-approved`
- Pilot id: `en-es-active-only-full-v1-tranche-007`
- Prompt id: `semantic_veto_evidence_gap_generation_v7_shadow_target_correctness`
- Selected model: `gpt-5.4-mini`

## Summary

- Selected requests: `38`
- Accepted responses: `37`
- Accepted generated items: `74`
- API errors: `0`
- Invalid outputs: `1`
- Input tokens: `20068`
- Output tokens: `7120`
- Accepted responses by arm: `P2_exposure_first: 37`
- Accepted items by slot: `active_evidence_expansion: 74`

## Admission Preview

- Admission status: `review`
- Admission decision: `generated_responses_need_repair`
- Admitted items: `73`
- Rejected items: `1`
- Waived items: `0`
- Coverage shortfall: `3`

## Artifacts

- Run manifest: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-en-es-active-only-full-v1-tranche-007-approved_run_manifest.json`
- Request queue: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-en-es-active-only-full-v1-tranche-007-approved_request_queue.jsonl`
- Journal: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-en-es-active-only-full-v1-tranche-007-approved_journal.jsonl`
- Raw responses JSONL: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-en-es-active-only-full-v1-tranche-007-approved_raw_responses.jsonl`
- Failures JSONL: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-en-es-active-only-full-v1-tranche-007-approved_failures.jsonl`
- Raw response bundle: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-en-es-active-only-full-v1-tranche-007-approved_raw_responses.json`
- Generated responses: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-en-es-active-only-full-v1-tranche-007-approved_generated_responses.json`

## Request Outcomes

| Request | Arm | Slot | Status | Items | Output / Error |
| --- | --- | --- | --- | ---: | --- |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:sentence:condenar:fe937d64:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The judge will sentence the robber to ten years in prison. |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:separate:apartar:0ac512f9:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | Please separate the red cards from the blue ones before you file them. |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:ski:esqui:0b2a73fb:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | I rented a ski before heading up the mountain. |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:stable:cuadra:38ad8110:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The horse was led back to the stable after the ride. |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:storm:tempestad:b0697466:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `invalid_output` | 0 | ValueError: family_id did not match request packet |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:supplement:suplemento:d5d7d4a5:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The doctor recommended a vitamin supplement to fill the nutritional gap in her diet. |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:swedish:sueco:2a789fc2:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | My new neighbor is swedish and moved here from Stockholm. |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:transport:transportar:d8440aa5:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The crew will transport the equipment to the remote site before dawn. |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:yield:ceder:8a2b7b73:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The driver slowed down and chose to yield to the pedestrians at the crosswalk. |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:abiding:continuo:7dc7af5e:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The hikers felt an abiding wind all afternoon, steady and unbroken from the ridge. |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:accountable:responsable:ff12b139:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The manager is accountable for the team’s budget and must explain every expense. |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:argentine:argentino:90e01172:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The museum hired an argentine chef from Buenos Aires to design the opening banquet. |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:axle:eje:824a7d8b:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The mechanic replaced the bent axle to stop the wheel from wobbling. |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:baton:palo:9f42189b:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The conductor lifted the baton and brought the orchestra in with a crisp cue. |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:cane:palo:26b2cc41:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | He leaned on his cane after the long walk across the station. |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:colleague:colega:611ca572:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | My colleague stayed late to help finish the report before the deadline. |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:commence:comenzar:f16e86f0:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | We will commence the meeting at 9 a.m. sharp. |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:continual:continuo:dd6785fe:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The machine made continual noise all night, so nobody slept well. |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:courtyard:patio:c222c02d:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | We had coffee in the courtyard after lunch. |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:cramped:estrecho:bb254e89:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The hallway felt cramped, so we had to turn sideways to pass through. |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:dial:marcar:11669297:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | Please dial the customer service number and wait for the greeting. |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:elegant:elegante:aff70883:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | She wore an elegant black dress to the gala. |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:exploit:explotar:ec3f35a0:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The company tried to exploit cheap labor in overseas factories. |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:faint:debil:f95344a8:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The patient felt faint after standing up too quickly. |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:grease:grasa:fb197e68:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The mechanic wiped away the grease from the engine parts. |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:haste:prisa:522c32d1:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | She left in haste to catch the last train. |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:invoke:llamar:f7c06ec6:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The mayor will invoke the emergency clause to call the council into session. |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:lump:bola:418e0094:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | She found a small lump of clay and rolled it into a neat sphere. |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:nationality:nacionalidad:8b8ed371:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The form asks for your nationality before you can submit the application. |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:supper:cena:b34f3646:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | We had supper at eight, after the movie ended. |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:tasty:rico:690a6d05:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The soup was tasty and full of fresh vegetables. |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:thief:ladron:b47556b9:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The thief slipped through the open window and took the jewelry from the dresser. |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:tidy:arreglar:9dbc8b04:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | Please tidy the desk before the meeting starts. |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:urgency:prisa:892de2a1:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | I left with urgency so I would not miss the train. |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:adjacent:contiguo:f84671dc:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | The pharmacy is adjacent to the clinic, so patients can walk there without crossing a street. |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:cap:birrete:2c38ba9f:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | She adjusted her cap before walking across the stage at graduation. |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:command:capitanear:f0a3599a:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | She was chosen to command the rescue team through the storm. |
| `en-es-active-only-full-v1-tranche-007:en-es:srs-source-target:decrease:decrecer:12483615:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | `accepted` | 2 | Sales will decrease again if prices keep rising. |
