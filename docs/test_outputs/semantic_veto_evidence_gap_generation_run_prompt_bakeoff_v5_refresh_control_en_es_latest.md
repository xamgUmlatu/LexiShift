# en-es Semantic Veto Evidence-Gap Generation Run

- Status: `ok`
- Generated: `2026-05-09T00:11:01Z`
- Execution mode: `live`
- Batch id: `en-es:semantic-veto-evidence-gap-generation:semantic-veto-evidence-gap-prompt-bakeoff-v5-refresh-control-20260509-001`
- Pilot id: `semantic_veto_evidence_gap_control_pilot_en_es_v1:prompt_variant:v5_refresh_control`
- Prompt id: `semantic_veto_evidence_gap_generation_v5_refresh_control`
- Selected model: `gpt-5.4-mini`

## Summary

- Selected requests: `24`
- Accepted responses: `24`
- Accepted generated items: `48`
- API errors: `0`
- Invalid outputs: `0`
- Input tokens: `11421`
- Output tokens: `4199`
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

- Journal: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-semantic-veto-evidence-gap-prompt-bakeoff-v5-refresh-control-20260509-001_journal.jsonl`
- Raw responses: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-semantic-veto-evidence-gap-prompt-bakeoff-v5-refresh-control-20260509-001_raw_responses.json`
- Generated responses: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-semantic-veto-evidence-gap-prompt-bakeoff-v5-refresh-control-20260509-001_generated_responses.json`

## Request Outcomes

| Request | Arm | Slot | Status | Items | Output / Error |
| --- | --- | --- | --- | ---: | --- |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:adjoining:vecino:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | `accepted` | 2 | The hotel booked us an adjoining room next to the suite. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:entirely:enteramente:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | `accepted` | 2 | The room was entirely dark after the power went out. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:bouillon:caldo:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | `accepted` | 2 | The chef simmered the bones for hours to make a rich bouillon for the soup. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:december:diciembre:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | `accepted` | 2 | We plan to visit family in december, the twelfth month of the year. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:american:americano:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | `accepted` | 2 | She studied American history in college. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:among:entre:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | `accepted` | 2 | The red umbrella was among the many gifts on the table. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:begin:comenzar:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | `accepted` | 2 | We will begin the meeting at nine o'clock. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:dentist:dentista:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | `accepted` | 2 | The dentist checked my teeth and filled a small cavity. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:brother:hermano:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | `accepted` | 2 | My brother helped me move into my new apartment. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:german:alem-n:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | `accepted` | 2 | She studied german in school so she could speak with visitors from Berlin. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:heart:coraz-n:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | `accepted` | 2 | The doctor listened to her heart and said the rhythm was steady. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:rumanian:rumano:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | `accepted` | 2 | She studied rumanian history to better understand the country's modern identity. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:salesman:vendedor:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | `accepted` | 2 | The salesman visited our office to demonstrate the new software and discuss pricing. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:tomorrow:ma-ana:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | `accepted` | 2 | I have a dentist appointment tomorrow morning. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:acceptable:razonable:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | `accepted` | 2 | The proposal is acceptable because it offers a fair compromise for both sides. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:chic:elegante:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | `accepted` | 2 | Her apartment looks chic, with clean lines, soft lighting, and carefully chosen furniture. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:smile:sonre-r:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | `accepted` | 2 | She tried to smile after hearing the good news. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:break:quebrar:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | `accepted` | 2 | The glass will break if it falls onto the tile floor. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:rebate:descuento:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | `accepted` | 2 | The store offered a rebate on the laptop, so the final price was lower than the sticker price. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:govern:gobernar:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | `accepted` | 2 | The elected council will govern the city for the next four years. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:offset:distancia:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | `accepted` | 2 | The survey marked the offset from the bridge as 12 meters. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:control:gobernar:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | `accepted` | 2 | The mayor used his control to govern the city through a difficult winter. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:bridle:reprimir:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | `accepted` | 2 | She had to bridle her anger before answering the rude remark. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:bar:cercar:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | `accepted` | 2 | The guards bar the gate to keep the crowd out. |
