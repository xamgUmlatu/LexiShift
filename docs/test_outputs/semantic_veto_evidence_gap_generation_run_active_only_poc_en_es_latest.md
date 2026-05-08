# en-es Semantic Veto Evidence-Gap Generation Run

- Status: `ok`
- Generated: `2026-05-08T20:35:16Z`
- Execution mode: `live`
- Batch id: `en-es:semantic-veto-evidence-gap-generation:semantic-veto-evidence-gap-active-only-poc-20260509-001`
- Pilot id: `semantic_veto_evidence_gap_control_pilot_en_es_v1`
- Prompt id: `semantic_veto_evidence_gap_generation_v5`
- Selected model: `gpt-5.4-mini`

## Summary

- Selected requests: `24`
- Accepted responses: `24`
- Accepted generated items: `48`
- API errors: `0`
- Invalid outputs: `0`
- Input tokens: `11421`
- Output tokens: `4177`
- Accepted responses by arm: `high_need: 8, low_control: 8, middle_control: 8`
- Accepted items by slot: `active_evidence_expansion: 48`

## Admission Preview

- Admission status: `ok`
- Admission decision: `generated_items_admitted_for_pilot_rescoring`
- Admitted items: `48`
- Rejected items: `0`
- Waived items: `0`
- Coverage shortfall: `0`

## Artifacts

- Journal: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-semantic-veto-evidence-gap-active-only-poc-20260509-001_journal.jsonl`
- Raw responses: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-semantic-veto-evidence-gap-active-only-poc-20260509-001_raw_responses.json`
- Generated responses: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-semantic-veto-evidence-gap-active-only-poc-20260509-001_generated_responses.json`

## Request Outcomes

| Request | Arm | Slot | Status | Items | Output / Error |
| --- | --- | --- | --- | ---: | --- |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:adjoining:vecino:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | `accepted` | 2 | The library is in the adjoining building, just next door to the museum. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:entirely:enteramente:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | `accepted` | 2 | The room was entirely dark after the power went out. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:bouillon:caldo:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | `accepted` | 2 | I simmered the bones for hours to make a rich bouillon for the soup. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:december:diciembre:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | `accepted` | 2 | The report was due in december, the twelfth month of the year. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:american:americano:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | `accepted` | 2 | She is an american citizen who was born in Texas. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:among:entre:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | `accepted` | 2 | The red umbrella was among the many gifts piled by the door. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:begin:comenzar:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | `accepted` | 2 | We will begin the meeting at nine o'clock. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:dentist:dentista:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | `accepted` | 2 | The dentist checked my teeth and filled a small cavity. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:brother:hermano:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | `accepted` | 2 | My brother helped me move into my new apartment. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:german:alem-n:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | `accepted` | 2 | She studied german history and learned how the language changed over time. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:heart:coraz-n:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | `accepted` | 2 | The doctor listened to her heart and said it was beating normally. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:rumanian:rumano:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | `accepted` | 2 | She studied rumanian history to better understand the country's modern identity. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:salesman:vendedor:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | `accepted` | 2 | The salesman explained the warranty and helped the customer choose the right laptop. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:tomorrow:ma-ana:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | `accepted` | 2 | I have a dentist appointment tomorrow at 9 a.m. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:acceptable:razonable:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | `accepted` | 2 | The proposal is acceptable because it balances cost, safety, and time. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:chic:elegante:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | `accepted` | 2 | Her apartment looked chic, with clean lines, soft lighting, and carefully chosen furniture. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:smile:sonre-r:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | `accepted` | 2 | She tried to smile after hearing the good news. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:break:quebrar:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | `accepted` | 2 | The glass will break if it hits the concrete floor. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:rebate:descuento:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | `accepted` | 2 | The store gave me a rebate on the laptop after I mailed in the receipt. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:govern:gobernar:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | `accepted` | 2 | The elected council will govern the city for the next four years. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:offset:distancia:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | `accepted` | 2 | The survey marked the offset from the trailhead to the campsite as 3 miles. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:control:gobernar:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | `accepted` | 2 | The mayor used his control to govern the city through a period of unrest. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:bridle:reprimir:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | `accepted` | 2 | She had to bridle her anger before answering the rude remark. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:bar:cercar:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | `accepted` | 2 | The workers used steel panels to bar the entrance and keep the crowd out. |
