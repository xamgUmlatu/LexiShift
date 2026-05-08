# en-es Semantic Veto Full-Family Manual Packet Authoring

- Status: `ok`
- Decision: `full_family_manual_packet_ready_for_scoring`
- Generated: `2026-05-06T20:18:34Z`
- Dataset: `docs/test_inputs/semantic_routing_cases/en_es_full_family_representative_manual_v1.json`
- Families: `58`
- Cases: `206`
- Review state: `agent_draft_human_review_pending`

## Methodology

Use exact or source-adapted WordNet examples before definition fallbacks; do not duplicate shadow-negative rows when only one real alternate context is available; keep missing or single-sense shadows as not_applicable.

The source-target family sample remains frozen. This pass only fills the sentence-veto dataset shape so the current veto algorithm can be measured against the representative queue.

## Counts

| Key | Value |
| --- | --- |
| `sampled_family_count` | `58` |
| `dataset_family_count` | `58` |
| `dataset_case_count` | `206` |
| `case_type_counts` | `{"phrase_no_winner": 58, "positive_active": 73, "shadow_negative": 75}` |
| `shadow_contract_case_counts` | `{"candidate_polysemic": 170, "not_applicable": 36}` |
| `source_band_case_counts` | `{"missing": 6, "zipf_3_to_4_mid": 50, "zipf_4_to_5_common": 59, "zipf_5_plus_very_common": 59, "zipf_below_3_rare": 32}` |
| `active_positive_count` | `73` |
| `shadow_negative_count` | `75` |
| `phrase_no_winner_count` | `58` |
| `draft_review_state` | `agent_draft_human_review_pending` |
| `dataset_fingerprint` | `b5c7fc1e7b83b1fb1c20f94a940f6ed9f81434e59f87a11c0a1840c8a752a65b` |

## Families

| Trigger | Target | Shadows | Cases | Case Mix |
| --- | --- | ---: | ---: | --- |
| `june` | `junio` | 0 | 2 | {"phrase_no_winner": 1, "positive_active": 1} |
| `december` | `diciembre` | 0 | 2 | {"phrase_no_winner": 1, "positive_active": 1} |
| `except` | `excepto` | 1 | 3 | {"phrase_no_winner": 1, "positive_active": 1, "shadow_negative": 1} |
| `health` | `salud` | 1 | 3 | {"phrase_no_winner": 1, "positive_active": 1, "shadow_negative": 1} |
| `russian` | `ruso` | 2 | 4 | {"phrase_no_winner": 1, "positive_active": 1, "shadow_negative": 2} |
| `tomorrow` | `mañana` | 2 | 4 | {"phrase_no_winner": 1, "positive_active": 1, "shadow_negative": 2} |
| `region` | `comarca` | 2 | 4 | {"phrase_no_winner": 1, "positive_active": 1, "shadow_negative": 2} |
| `brother` | `hermano` | 2 | 4 | {"phrase_no_winner": 1, "positive_active": 1, "shadow_negative": 2} |
| `american` | `americano` | 2 | 5 | {"phrase_no_winner": 1, "positive_active": 2, "shadow_negative": 2} |
| `current` | `contemporáneo` | 2 | 5 | {"phrase_no_winner": 1, "positive_active": 2, "shadow_negative": 2} |
| `heart` | `corazón` | 2 | 5 | {"phrase_no_winner": 1, "positive_active": 2, "shadow_negative": 2} |
| `continue` | `durar` | 2 | 5 | {"phrase_no_winner": 1, "positive_active": 2, "shadow_negative": 2} |
| `control` | `gobernar` | 2 | 4 | {"phrase_no_winner": 1, "positive_active": 1, "shadow_negative": 2} |
| `break` | `quebrar` | 2 | 5 | {"phrase_no_winner": 1, "positive_active": 2, "shadow_negative": 2} |
| `among` | `entre` | 0 | 2 | {"phrase_no_winner": 1, "positive_active": 1} |
| `upon` | `sobre` | 0 | 2 | {"phrase_no_winner": 1, "positive_active": 1} |
| `pub` | `taberna` | 0 | 2 | {"phrase_no_winner": 1, "positive_active": 1} |
| `emotion` | `emoción` | 0 | 2 | {"phrase_no_winner": 1, "positive_active": 1} |
| `entirely` | `enteramente` | 1 | 4 | {"phrase_no_winner": 1, "positive_active": 2, "shadow_negative": 1} |
| `owe` | `deber` | 2 | 4 | {"phrase_no_winner": 1, "positive_active": 1, "shadow_negative": 2} |
| `german` | `alemán` | 2 | 5 | {"phrase_no_winner": 1, "positive_active": 2, "shadow_negative": 2} |
| `smile` | `sonreír` | 2 | 4 | {"phrase_no_winner": 1, "positive_active": 1, "shadow_negative": 2} |
| `sale` | `deducción` | 2 | 5 | {"phrase_no_winner": 1, "positive_active": 2, "shadow_negative": 2} |
| `acceptable` | `razonable` | 2 | 5 | {"phrase_no_winner": 1, "positive_active": 2, "shadow_negative": 2} |
| `shed` | `puesto` | 2 | 5 | {"phrase_no_winner": 1, "positive_active": 2, "shadow_negative": 2} |
| `pair` | `par` | 2 | 4 | {"phrase_no_winner": 1, "positive_active": 1, "shadow_negative": 2} |
| `begin` | `comenzar` | 2 | 5 | {"phrase_no_winner": 1, "positive_active": 2, "shadow_negative": 2} |
| `grow` | `acontecer` | 2 | 4 | {"phrase_no_winner": 1, "positive_active": 1, "shadow_negative": 2} |
| `bar` | `cercar` | 2 | 4 | {"phrase_no_winner": 1, "positive_active": 1, "shadow_negative": 2} |
| `demand` | `deducción` | 2 | 4 | {"phrase_no_winner": 1, "positive_active": 1, "shadow_negative": 2} |
| `recover` | `sanar` | 0 | 2 | {"phrase_no_winner": 1, "positive_active": 1} |
| `dentist` | `dentista` | 0 | 2 | {"phrase_no_winner": 1, "positive_active": 1} |
| `salesman` | `vendedor` | 0 | 2 | {"phrase_no_winner": 1, "positive_active": 1} |
| `altitude` | `elevación` | 2 | 4 | {"phrase_no_winner": 1, "positive_active": 1, "shadow_negative": 2} |
| `shortage` | `falta` | 1 | 3 | {"phrase_no_winner": 1, "positive_active": 1, "shadow_negative": 1} |
| `chic` | `elegante` | 1 | 4 | {"phrase_no_winner": 1, "positive_active": 2, "shadow_negative": 1} |
| `parrot` | `loro` | 2 | 4 | {"phrase_no_winner": 1, "positive_active": 1, "shadow_negative": 2} |
| `govern` | `gobernar` | 2 | 5 | {"phrase_no_winner": 1, "positive_active": 2, "shadow_negative": 2} |
| `endure` | `durar` | 2 | 5 | {"phrase_no_winner": 1, "positive_active": 2, "shadow_negative": 2} |
| `cite` | `mencionar` | 2 | 4 | {"phrase_no_winner": 1, "positive_active": 1, "shadow_negative": 2} |
| `rebate` | `descuento` | 2 | 4 | {"phrase_no_winner": 1, "positive_active": 1, "shadow_negative": 2} |
| `stall` | `cuadra` | 2 | 4 | {"phrase_no_winner": 1, "positive_active": 1, "shadow_negative": 2} |
| `offset` | `distancia` | 2 | 5 | {"phrase_no_winner": 1, "positive_active": 2, "shadow_negative": 2} |
| `adjoining` | `vecino` | 0 | 2 | {"phrase_no_winner": 1, "positive_active": 1} |
| `adjoining` | `contiguo` | 0 | 2 | {"phrase_no_winner": 1, "positive_active": 1} |
| `handiwork` | `artesanía` | 0 | 2 | {"phrase_no_winner": 1, "positive_active": 1} |
| `bouillon` | `caldo` | 0 | 2 | {"phrase_no_winner": 1, "positive_active": 1} |
| `aberration` | `equivocación` | 2 | 4 | {"phrase_no_winner": 1, "positive_active": 1, "shadow_negative": 2} |
| `adder` | `víbora` | 2 | 4 | {"phrase_no_winner": 1, "positive_active": 1, "shadow_negative": 2} |
| `snore` | `roncar` | 2 | 4 | {"phrase_no_winner": 1, "positive_active": 1, "shadow_negative": 2} |
| `rumanian` | `rumano` | 2 | 4 | {"phrase_no_winner": 1, "positive_active": 1, "shadow_negative": 2} |
| `bridle` | `reprimir` | 2 | 4 | {"phrase_no_winner": 1, "positive_active": 1, "shadow_negative": 2} |
| `billow` | `oleaje` | 2 | 4 | {"phrase_no_winner": 1, "positive_active": 1, "shadow_negative": 2} |
| `turnon` | `poner` | 0 | 2 | {"phrase_no_winner": 1, "positive_active": 1} |
| `argentinean` | `argentino` | 0 | 2 | {"phrase_no_winner": 1, "positive_active": 1} |
| `conversance` | `notoriedad` | 0 | 2 | {"phrase_no_winner": 1, "positive_active": 1} |
| `femalejournalist` | `periodista` | 0 | 2 | {"phrase_no_winner": 1, "positive_active": 1} |
| `mosaicwork` | `mosaico` | 0 | 2 | {"phrase_no_winner": 1, "positive_active": 1} |

## Guardrails

| Check | Value |
| --- | --- |
| `sample_rows_available` | `True` |
| `one_family_per_sample_row` | `True` |
| `case_ids_unique` | `True` |
| `all_cases_have_review_state` | `True` |
| `active_positive_cases_present` | `True` |
| `phrase_no_winner_cases_present` | `True` |
| `mid_cases_present` | `True` |
| `rare_cases_present` | `True` |

## Limitations

- `agent_draft_sentences_are_not_human_locked_evaluation_rows`
- `wordnet_first_sense_may_not_match_the_dictionary_source_target_sense`
- `automated_phrase_no_winner_rows_are_diagnostic_not_browser_distribution`
- `shadow_negative_rows_depend_on_available_wordnet_alternate_senses`

## Next Steps

- Run TF-IDF and sentence-transformer sentence-veto scoring as a diagnostic lane.
- Inspect failures and questionable authored rows before any promotion claim.
- Use source-band and polysemy breakdowns to decide whether mid and rare bands are easier.
- Replace weak draft rows with human-reviewed contexts if the curve signal is promising or ambiguous.
