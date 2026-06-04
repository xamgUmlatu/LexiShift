# en-es Semantic Veto Evidence-Gap Generation Run

- Status: `ok`
- Generated: `2026-05-09T20:29:52Z`
- Execution mode: `live`
- Batch id: `en-es:semantic-veto-evidence-gap-generation:product-scope-band-grading-v1-20260510-001`
- Pilot id: `semantic_veto_product_scope_band_grading_v1_allocation_en_es`
- Prompt id: `semantic_veto_evidence_gap_generation_v7_shadow_target_correctness`
- Selected model: `gpt-5.4-mini`

## Summary

- Selected requests: `54`
- Accepted responses: `54`
- Accepted generated items: `80`
- API errors: `0`
- Invalid outputs: `0`
- Input tokens: `36840`
- Output tokens: `11899`
- Accepted responses by arm: `high_need: 18, low_control: 18, middle_control: 18`
- Accepted items by slot: `active_evidence_expansion: 36, no_winner_context_probe: 18, shadow_or_competitor_evidence_probe: 26`

## Admission Preview

- Admission status: `review`
- Admission decision: `generated_responses_need_repair`
- Admitted items: `67`
- Rejected items: `5`
- Waived items: `10`
- Coverage shortfall: `13`

## Artifacts

- Journal: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-product-scope-band-grading-v1-20260510-001_journal.jsonl`
- Raw responses: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-product-scope-band-grading-v1-20260510-001_raw_responses.json`
- Generated responses: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-product-scope-band-grading-v1-20260510-001_generated_responses.json`

## Request Outcomes

| Request | Arm | Slot | Status | Items | Output / Error |
| --- | --- | --- | --- | ---: | --- |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:cite:mencionar:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | `accepted` | 2 | In the report, please cite the study that supports your conclusion. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:cite:mencionar:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | `accepted` | 2 | The officer will cite the driver for speeding after the stop. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:cite:mencionar:no_winner_context_probe` | `high_need` | `no_winner_context_probe` | `accepted` | 1 | The book title "cite" appears on the cover, but it is just a title and not a request to mention a source. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:smile:sonre-r:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | `accepted` | 2 | She tried to smile after hearing the good news. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:smile:sonre-r:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | `accepted` | 2 | Her smile lit up the room during the ceremony. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:smile:sonre-r:no_winner_context_probe` | `high_need` | `no_winner_context_probe` | `accepted` | 1 | The dictionary entry for smile says it is a verb, but the quoted word "smile" in the note is being discussed as a term, not used to mean... |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:bar:cercar:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | `accepted` | 2 | The police used a truck to bar the road after the landslide. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:bar:cercar:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | `accepted` | 2 | We met at the bar after work for a quick drink. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:bar:cercar:no_winner_context_probe` | `high_need` | `no_winner_context_probe` | `accepted` | 1 | The song "bar" was played again, but the title is just a music label and not a command to block anything. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:control:gobernar:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | `accepted` | 2 | The mayor used his control to govern the city through a difficult winter. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:control:gobernar:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | `accepted` | 2 | Please control the thermostat before the guests arrive. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:control:gobernar:no_winner_context_probe` | `high_need` | `no_winner_context_probe` | `accepted` | 1 | The translation note says the word "control" is a noun here, not a verb, and the dictionary entry stays in English. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:except:excepto:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | `accepted` | 2 | Everyone may join the hike except the injured runner. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:except:excepto:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | `accepted` | 2 | Everyone except Maria arrived on time. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:except:excepto:no_winner_context_probe` | `high_need` | `no_winner_context_probe` | `accepted` | 1 | The dictionary entry for "except" was highlighted, but the note said it was a quoted word, not a translation target. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:region:comarca:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | `accepted` | 2 | The council mapped each region by its villages, roads, and shared local services. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:region:comarca:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | `accepted` | 2 | The county divided the region into three voting districts after the census. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:region:comarca:no_winner_context_probe` | `high_need` | `no_winner_context_probe` | `accepted` | 1 | The translation note says the word region is broad in English, but the quoted term here is just a label in the glossary. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:govern:gobernar:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | `accepted` | 2 | The elected council will govern the city for the next four years. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:govern:gobernar:shadow_or_competitor_evidence_probe` | `middle_control` | `shadow_or_competitor_evidence_probe` | `accepted` | 2 | The committee will govern the use of the lab equipment with strict safety rules. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:govern:gobernar:no_winner_context_probe` | `middle_control` | `no_winner_context_probe` | `accepted` | 1 | The translation note says govern is a verb, but here the word is quoted as a term in the dictionary entry. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:german:alem-n:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | `accepted` | 2 | She is learning german so she can speak with her relatives in Berlin. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:german:alem-n:shadow_or_competitor_evidence_probe` | `middle_control` | `shadow_or_competitor_evidence_probe` | `accepted` | 2 | The recipe calls for one german of salt, not a full cup. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:german:alem-n:no_winner_context_probe` | `middle_control` | `no_winner_context_probe` | `accepted` | 1 | The translation note says the word german is borrowed from another language, but the English discussion keeps it as a quoted term. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:american:americano:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | `accepted` | 2 | She became an american citizen after living in Chicago for ten years. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:american:americano:shadow_or_competitor_evidence_probe` | `middle_control` | `shadow_or_competitor_evidence_probe` | `accepted` | 2 | She bought an american flag to hang outside the school. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:american:americano:no_winner_context_probe` | `middle_control` | `no_winner_context_probe` | `accepted` | 1 | The dictionary entry for american was discussed in class, but the word was quoted only as a term and not as a nationality. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:endure:durar:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | `accepted` | 2 | The old bridge can endure for another fifty years with regular maintenance. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:endure:durar:shadow_or_competitor_evidence_probe` | `middle_control` | `shadow_or_competitor_evidence_probe` | `accepted` | 2 | The old bridge will endure for another century if it is maintained properly. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:endure:durar:no_winner_context_probe` | `middle_control` | `no_winner_context_probe` | `accepted` | 1 | The translation note says the English word endure is marked as a quoted term, but the Spanish gloss is intentionally left blank. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:tomorrow:ma-ana:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | `accepted` | 2 | I have a dentist appointment tomorrow morning. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:tomorrow:ma-ana:shadow_or_competitor_evidence_probe` | `middle_control` | `shadow_or_competitor_evidence_probe` | `accepted` | 0 | n/a |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:tomorrow:ma-ana:no_winner_context_probe` | `middle_control` | `no_winner_context_probe` | `accepted` | 1 | The song called tomorrow is on repeat in the studio, but here it is just a title, not a date. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:russian:ruso:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | `accepted` | 2 | She studied russian history and could read the old letters from Moscow. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:russian:ruso:shadow_or_competitor_evidence_probe` | `middle_control` | `shadow_or_competitor_evidence_probe` | `accepted` | 0 | n/a |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:russian:ruso:no_winner_context_probe` | `middle_control` | `no_winner_context_probe` | `accepted` | 1 | The book called russian is shelved in the language section, but the word is being discussed as English vocabulary rather than a translati... |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:dentist:dentista:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | `accepted` | 2 | The dentist checked my teeth and filled a small cavity. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:dentist:dentista:shadow_or_competitor_evidence_probe` | `low_control` | `shadow_or_competitor_evidence_probe` | `accepted` | 0 | n/a |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:dentist:dentista:no_winner_context_probe` | `low_control` | `no_winner_context_probe` | `accepted` | 1 | The translation note says the word dentist is kept in English because the dictionary entry is discussing usage, not a Spanish replacement. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:pub:taberna:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | `accepted` | 2 | We met at the pub for a quick drink and some chips after work. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:pub:taberna:shadow_or_competitor_evidence_probe` | `low_control` | `shadow_or_competitor_evidence_probe` | `accepted` | 2 | The university pub released a special issue on climate policy last week. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:pub:taberna:no_winner_context_probe` | `low_control` | `no_winner_context_probe` | `accepted` | 1 | The translation note says the word pub is quoted in the dictionary, but it should stay in English because the entry is discussing spellin... |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:shortage:falta:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | `accepted` | 2 | The clinic had to cancel appointments because of a shortage of nurses. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:shortage:falta:shadow_or_competitor_evidence_probe` | `low_control` | `shadow_or_competitor_evidence_probe` | `accepted` | 2 | The city faced a shortage of bus drivers during the winter storm. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:shortage:falta:no_winner_context_probe` | `low_control` | `no_winner_context_probe` | `accepted` | 1 | The word shortage was quoted in the dictionary note, but the discussion was about spelling, not meaning. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:rumanian:rumano:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | `accepted` | 2 | She studied rumanian history to better understand the country's traditions and identity. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:rumanian:rumano:shadow_or_competitor_evidence_probe` | `low_control` | `shadow_or_competitor_evidence_probe` | `accepted` | 0 | n/a |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:rumanian:rumano:no_winner_context_probe` | `low_control` | `no_winner_context_probe` | `accepted` | 1 | The dictionary entry marked rumanian is quoted as a spelling note, not as a nationality term. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:argentinean:argentino:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | `accepted` | 2 | She proudly described herself as argentinean when talking about her family roots in Buenos Aires. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:argentinean:argentino:shadow_or_competitor_evidence_probe` | `low_control` | `shadow_or_competitor_evidence_probe` | `accepted` | 0 | n/a |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:argentinean:argentino:no_winner_context_probe` | `low_control` | `no_winner_context_probe` | `accepted` | 1 | The book called argentinean stays in English because the title is a proper name, not a nationality term. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:owe:deber:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | `accepted` | 2 | I owe the bank three hundred dollars for the car repair. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:owe:deber:shadow_or_competitor_evidence_probe` | `low_control` | `shadow_or_competitor_evidence_probe` | `accepted` | 2 | I still owe the bank 500 dollars, so I need to make a payment this week. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:owe:deber:no_winner_context_probe` | `low_control` | `no_winner_context_probe` | `accepted` | 1 | In the dictionary, the word owe is marked as a verb, but the note says the translation should stay in English for this entry. |
