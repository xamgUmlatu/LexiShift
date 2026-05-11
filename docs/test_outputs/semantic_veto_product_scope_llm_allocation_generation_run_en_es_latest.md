# en-es Semantic Veto Evidence-Gap Generation Run

- Status: `ok`
- Generated: `2026-05-09T05:25:39Z`
- Execution mode: `live`
- Batch id: `en-es:semantic-veto-evidence-gap-generation:product-scope-allocation-20260509-003`
- Pilot id: `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1`
- Prompt id: `semantic_veto_evidence_gap_generation_v7_shadow_target_correctness`
- Selected model: `gpt-5.4-mini`

## Summary

- Selected requests: `60`
- Accepted responses: `60`
- Accepted generated items: `90`
- API errors: `0`
- Invalid outputs: `0`
- Input tokens: `41107`
- Output tokens: `13405`
- Accepted responses by arm: `high_need: 24, low_control: 24, middle_control: 12`
- Accepted items by slot: `active_evidence_expansion: 40, no_winner_context_probe: 20, shadow_or_competitor_evidence_probe: 30`

## Admission Preview

- Admission status: `review`
- Admission decision: `generated_responses_need_repair`
- Admitted items: `84`
- Rejected items: `4`
- Waived items: `10`
- Coverage shortfall: `6`

## Artifacts

- Journal: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-product-scope-allocation-20260509-003_journal.jsonl`
- Raw responses: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-product-scope-allocation-20260509-003_raw_responses.json`
- Generated responses: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-product-scope-allocation-20260509-003_generated_responses.json`

## Request Outcomes

| Request | Arm | Slot | Status | Items | Output / Error |
| --- | --- | --- | --- | ---: | --- |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:acceptable:razonable:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | `accepted` | 2 | The draft is acceptable for a first review, but it still needs a few edits before publication. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:acceptable:razonable:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | `accepted` | 2 | The committee said the proposal was acceptable under the new rules. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:acceptable:razonable:no_winner_context_probe` | `high_need` | `no_winner_context_probe` | `accepted` | 1 | The song called acceptable was added to the playlist, but the title is just a word choice and not a quality judgment. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:billow:oleaje:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | `accepted` | 2 | A billow rolled across the harbor and lifted the small boat. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:billow:oleaje:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | `accepted` | 2 | The curtains billow in the warm breeze. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:billow:oleaje:no_winner_context_probe` | `high_need` | `no_winner_context_probe` | `accepted` | 1 | The song called "billow" is a title, so the word should stay as written and not be translated. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:bridle:reprimir:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | `accepted` | 2 | She had to bridle her anger before answering the rude remark. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:bridle:reprimir:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | `accepted` | 2 | The rider checked the bridle before mounting the horse. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:bridle:reprimir:no_winner_context_probe` | `high_need` | `no_winner_context_probe` | `accepted` | 1 | The dictionary entry for bridle gives the English word and its pronunciation, but the translation note does not call for any Spanish repl... |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:current:contempor-neo:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | `accepted` | 2 | The museum opened a current exhibition of contemporary sculpture. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:current:contempor-neo:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | `accepted` | 2 | The current in the wire dropped after the switch was opened. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:current:contempor-neo:no_winner_context_probe` | `high_need` | `no_winner_context_probe` | `accepted` | 1 | The dictionary entry for current says it can mean a flow of water or electricity, but here the word is only being discussed as a term. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:offset:distancia:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | `accepted` | 2 | The survey marked an offset of 12 meters from the original benchmark. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:offset:distancia:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | `accepted` | 2 | The tax credit will offset part of the renovation cost. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:offset:distancia:no_winner_context_probe` | `high_need` | `no_winner_context_probe` | `accepted` | 1 | The song title "offset" appears in the playlist, but it is being discussed as a title, not as a measurement. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:parrot:loro:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | `accepted` | 2 | The parrot perched on the cage and repeated the greeting it had learned from its owner. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:parrot:loro:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | `accepted` | 2 | The parrot perched on the windowsill and watched the room quietly. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:parrot:loro:no_winner_context_probe` | `high_need` | `no_winner_context_probe` | `accepted` | 1 | The song "parrot" was called a joke by the band after the live show. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:rebate:descuento:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | `accepted` | 2 | The store offered a rebate on the laptop after checkout, lowering the final price. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:rebate:descuento:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | `accepted` | 2 | The carpenter cut a rebate along the edge of the board so the glass would sit flush. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:rebate:descuento:no_winner_context_probe` | `high_need` | `no_winner_context_probe` | `accepted` | 1 | The word rebate was quoted in the translation note, but the dictionary entry stayed in English. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:stall:cuadra:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | `accepted` | 2 | The horse was led into a clean stall after the ride. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:stall:cuadra:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | `accepted` | 2 | The broken elevator will stall the meeting for at least twenty minutes. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:stall:cuadra:no_winner_context_probe` | `high_need` | `no_winner_context_probe` | `accepted` | 1 | The translation note says stall is a noun in this glossary, but the English word stays unchanged here. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:adder:v-bora:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | `accepted` | 2 | The hiker spotted an adder basking on the warm stone path. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:adder:v-bora:shadow_or_competitor_evidence_probe` | `middle_control` | `shadow_or_competitor_evidence_probe` | `accepted` | 2 | The engineer used an adder to test the circuit board. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:adder:v-bora:no_winner_context_probe` | `middle_control` | `no_winner_context_probe` | `accepted` | 1 | The book called "Adder" is a thriller, so the word is a title and not a snake term. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:chic:elegante:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | `accepted` | 2 | Her apartment looks chic, with clean lines, soft lighting, and carefully chosen furniture. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:chic:elegante:shadow_or_competitor_evidence_probe` | `middle_control` | `shadow_or_competitor_evidence_probe` | `accepted` | 0 | n/a |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:chic:elegante:no_winner_context_probe` | `middle_control` | `no_winner_context_probe` | `accepted` | 1 | The menu label chic is visible in the app, but it refers to a style filter name rather than a translatable adjective. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:pair:par:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | `accepted` | 2 | I bought a pair of socks for the trip. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:pair:par:shadow_or_competitor_evidence_probe` | `middle_control` | `shadow_or_competitor_evidence_probe` | `accepted` | 2 | I bought a pair of gloves for the winter. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:pair:par:no_winner_context_probe` | `middle_control` | `no_winner_context_probe` | `accepted` | 1 | The menu label says pair, but it is only the English word shown in the app and not a translation request. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:snore:roncar:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | `accepted` | 2 | He began to snore loudly as soon as he fell asleep on the couch. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:snore:roncar:shadow_or_competitor_evidence_probe` | `middle_control` | `shadow_or_competitor_evidence_probe` | `accepted` | 2 | The snore from the next room kept me awake all night. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:snore:roncar:no_winner_context_probe` | `middle_control` | `no_winner_context_probe` | `accepted` | 1 | The song called "snore" is a playful title, but the lyrics never mean sleeping noise. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:adjoining:contiguo:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | `accepted` | 2 | The café is in an adjoining building, just next to the library. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:adjoining:contiguo:shadow_or_competitor_evidence_probe` | `low_control` | `shadow_or_competitor_evidence_probe` | `accepted` | 0 | n/a |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:adjoining:contiguo:no_winner_context_probe` | `low_control` | `no_winner_context_probe` | `accepted` | 1 | The menu label says adjoining, but it is a quoted word in the help panel, not a place description. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:adjoining:vecino:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | `accepted` | 2 | The bakery is in the adjoining building, so we can pick up bread without crossing the street. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:adjoining:vecino:shadow_or_competitor_evidence_probe` | `low_control` | `shadow_or_competitor_evidence_probe` | `accepted` | 2 | The museum opened a new wing in an adjoining building connected by a glass bridge. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:adjoining:vecino:no_winner_context_probe` | `low_control` | `no_winner_context_probe` | `accepted` | 1 | The word adjoining was quoted in the English glossary, but the note said it was not the translation to use for this entry. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:begin:comenzar:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | `accepted` | 2 | We will begin the meeting at nine o'clock. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:begin:comenzar:shadow_or_competitor_evidence_probe` | `low_control` | `shadow_or_competitor_evidence_probe` | `accepted` | 2 | We will begin the meeting at nine o'clock. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:begin:comenzar:no_winner_context_probe` | `low_control` | `no_winner_context_probe` | `accepted` | 1 | The book title is "begin", and the author said it was chosen for its simplicity. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:bouillon:caldo:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | `accepted` | 2 | The chef simmered the vegetables in bouillon before adding the noodles. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:bouillon:caldo:shadow_or_competitor_evidence_probe` | `low_control` | `shadow_or_competitor_evidence_probe` | `accepted` | 0 | n/a |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:bouillon:caldo:no_winner_context_probe` | `low_control` | `no_winner_context_probe` | `accepted` | 1 | The menu button opens a glossary entry for bouillon, and the note says it is a French term, not a translation target. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:december:diciembre:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | `accepted` | 2 | The holiday lights go up in december, the twelfth month of the year. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:december:diciembre:shadow_or_competitor_evidence_probe` | `low_control` | `shadow_or_competitor_evidence_probe` | `accepted` | 0 | n/a |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:december:diciembre:no_winner_context_probe` | `low_control` | `no_winner_context_probe` | `accepted` | 1 | The translation note says the word december is a month name, but here it is only a quoted term in the glossary. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:entirely:enteramente:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | `accepted` | 2 | The room was entirely dark after the power went out. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:entirely:enteramente:shadow_or_competitor_evidence_probe` | `low_control` | `shadow_or_competitor_evidence_probe` | `accepted` | 0 | n/a |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:entirely:enteramente:no_winner_context_probe` | `low_control` | `no_winner_context_probe` | `accepted` | 1 | The song called entirely was played during the interview, but the title is just a quoted word and not a translation target. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:handiwork:artesan-a:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | `accepted` | 2 | The carved wooden bowl was beautiful handiwork, showing the maker's skill and patience. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:handiwork:artesan-a:shadow_or_competitor_evidence_probe` | `low_control` | `shadow_or_competitor_evidence_probe` | `accepted` | 2 | The carpenter's handiwork was finished before noon, and the crew admired the clean joints. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:handiwork:artesan-a:no_winner_context_probe` | `low_control` | `no_winner_context_probe` | `accepted` | 1 | The song called handiwork was added to the playlist, but the title is just a proper name and not a craft description. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:upon:sobre:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | `accepted` | 2 | The report was placed upon the desk for everyone to read. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:upon:sobre:shadow_or_competitor_evidence_probe` | `low_control` | `shadow_or_competitor_evidence_probe` | `accepted` | 2 | Upon arriving at the station, she called her brother immediately. |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:upon:sobre:no_winner_context_probe` | `low_control` | `no_winner_context_probe` | `accepted` | 1 | The book titled "Upon" was discussed in the reading group, but the title is a proper name and not a translatable preposition. |
