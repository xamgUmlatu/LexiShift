# en-es Semantic Veto Difficulty Stratification

- Status: `ok`
- Decision: `difficulty_stratification_baseline_established`
- Generated: `2026-05-05T21:54:34Z`
- Runtime policy change: `none`
- Case rows: `240`

## E2E Checks

| Field | Value |
| --- | --- |
| `policy_case_rows_read` | 168 |
| `llm_case_rows_read` | 72 |
| `total_case_rows` | 240 |
| `unique_families` | 35 |
| `unique_triggers` | 35 |
| `source_rank_known_rows` | 81 |
| `target_rank_known_rows` | 15 |
| `source_frequency_status` | ok |
| `target_frequency_status` | ok |
| `source_zipf_status` | wordfreq |
| `source_zipf_known_rows` | 240 |

## Overall

| Scope | Cases | Families | Pos allow | Neg abstain | Pos abstain | Neg allow | Utility | Source rank known | Source Zipf known | Target rank known | Target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| overall | 240 | 35 | 56.2% | 82.2% | 46 | 24 | 115.0 | 33.8% | 100.0% | 6.2% | fail |

## Lanes

| Scope | Cases | Families | Pos allow | Neg abstain | Pos abstain | Neg allow | Utility | Source rank known | Source Zipf known | Target rank known | Target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| sampling_stage1_representative_proxy | 120 | 19 | 24.5% | 100.0% | 40 | 0 | 50.6 | 27.5% | 100.0% | 0.0% | fail |
| semantic_veto_llm_pilot_en_es_v1 | 72 | 12 | 88.9% | 52.8% | 4 | 17 | 35.4 | 41.7% | 100.0% | 0.0% | pass |
| wave7_phrase_control_triage_stress | 48 | 16 | 87.5% | 78.1% | 2 | 7 | 29.0 | 37.5% | 100.0% | 31.2% | pass |

## Source Trigger Rank (English)

| Scope | Cases | Families | Pos allow | Neg abstain | Pos abstain | Neg allow | Utility | Source rank known | Source Zipf known | Target rank known | Target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1-500 | 15 | 2 | 71.4% | 75.0% | 2 | 2 | 7.8 | 100.0% | 100.0% | 0.0% | fail |
| 501-1000 | 12 | 1 | 50.0% | 83.3% | 3 | 1 | 5.2 | 100.0% | 100.0% | 0.0% | fail |
| 1001-2000 | 3 | 1 | 100.0% | 50.0% | 0 | 1 | 1.2 | 100.0% | 100.0% | 100.0% | pass |
| 2001-5000 | 26 | 2 | 75.0% | 92.9% | 3 | 1 | 17.6 | 100.0% | 100.0% | 0.0% | fail |
| >5000 | 25 | 5 | 60.0% | 93.3% | 4 | 1 | 15.0 | 100.0% | 100.0% | 12.0% | fail |
| missing | 159 | 24 | 50.7% | 80.0% | 34 | 18 | 68.2 | 0.0% | 100.0% | 5.7% | fail |

## Source Zipf Frequency (English)

| Scope | Cases | Families | Pos allow | Neg abstain | Pos abstain | Neg allow | Utility | Source rank known | Source Zipf known | Target rank known | Target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| zipf_5_plus_very_common | 131 | 16 | 49.1% | 80.6% | 30 | 14 | 55.0 | 45.0% | 100.0% | 4.6% | fail |
| zipf_4_to_5_common | 103 | 17 | 63.6% | 84.8% | 16 | 9 | 56.2 | 18.4% | 100.0% | 5.8% | fail |
| zipf_3_to_4_mid | 6 | 2 | 100.0% | 75.0% | 0 | 1 | 3.8 | 50.0% | 100.0% | 50.0% | pass |

## Target Lemma Rank (Spanish)

| Scope | Cases | Families | Pos allow | Neg abstain | Pos abstain | Neg allow | Utility | Source rank known | Source Zipf known | Target rank known | Target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1-500 | 6 | 2 | 100.0% | 75.0% | 0 | 1 | 3.8 | 100.0% | 100.0% | 100.0% | pass |
| 501-1000 | 6 | 2 | 100.0% | 50.0% | 0 | 2 | 2.4 | 0.0% | 100.0% | 100.0% | pass |
| 1001-2000 | 3 | 1 | 100.0% | 100.0% | 0 | 0 | 2.6 | 0.0% | 100.0% | 100.0% | pass |
| missing | 225 | 30 | 54.0% | 83.2% | 46 | 21 | 106.2 | 33.3% | 100.0% | 0.0% | fail |

## Ambiguity Proxies

### Declared Ambiguity

| Scope | Cases | Families | Pos allow | Neg abstain | Pos abstain | Neg allow | Utility | Source rank known | Source Zipf known | Target rank known | Target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| high | 123 | 10 | 60.3% | 76.9% | 23 | 15 | 56.8 | 51.2% | 100.0% | 0.0% | fail |
| medium | 23 | 2 | 45.5% | 83.3% | 6 | 2 | 9.4 | 0.0% | 100.0% | 0.0% | fail |
| missing | 94 | 23 | 52.8% | 87.9% | 17 | 7 | 48.8 | 19.1% | 100.0% | 16.0% | fail |

### WordNet Sense Count

| Scope | Cases | Families | Pos allow | Neg abstain | Pos abstain | Neg allow | Utility | Source rank known | Source Zipf known | Target rank known | Target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 10+ | 48 | 16 | 87.5% | 78.1% | 2 | 7 | 29.0 | 37.5% | 100.0% | 31.2% | pass |
| missing | 192 | 19 | 50.6% | 83.5% | 44 | 17 | 86.0 | 32.8% | 100.0% | 0.0% | fail |

### Translation Candidate Count

| Scope | Cases | Families | Pos allow | Neg abstain | Pos abstain | Neg allow | Utility | Source rank known | Source Zipf known | Target rank known | Target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 5-9 | 9 | 3 | 100.0% | 66.7% | 0 | 2 | 5.0 | 33.3% | 100.0% | 0.0% | pass |
| 10+ | 39 | 13 | 84.6% | 80.8% | 2 | 5 | 24.0 | 38.5% | 100.0% | 38.5% | pass |
| missing | 192 | 19 | 50.6% | 83.5% | 44 | 17 | 86.0 | 32.8% | 100.0% | 0.0% | fail |

## Score-Surface Proxies

### Shadow Lead

| Scope | Cases | Families | Pos allow | Neg abstain | Pos abstain | Neg allow | Utility | Source rank known | Source Zipf known | Target rank known | Target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| active_clear_0.05+ | 51 | 19 | 100.0% | 0.0% | 0 | 7 | 39.8 | 43.1% | 100.0% | 3.9% | fail |
| active_near_tie_0_0.05 | 43 | 19 | 52.6% | 66.7% | 9 | 8 | 14.4 | 20.9% | 100.0% | 7.0% | fail |
| shadow_blocker_0.05_0.10 | 23 | 15 | n/a | 95.7% | 0 | 1 | 17.0 | 30.4% | 100.0% | 13.0% | pass |
| shadow_clear_0.10+ | 21 | 15 | 0.0% | 100.0% | 3 | 0 | 13.2 | 52.4% | 100.0% | 9.5% | fail |
| shadow_near_tie_0_0.05 | 102 | 30 | 12.8% | 87.3% | 34 | 8 | 30.6 | 31.4% | 100.0% | 4.9% | fail |

### Phrase Lead

| Scope | Cases | Families | Pos allow | Neg abstain | Pos abstain | Neg allow | Utility | Source rank known | Source Zipf known | Target rank known | Target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| active_clear_0.05+ | 55 | 19 | 100.0% | 57.7% | 0 | 11 | 34.4 | 45.5% | 100.0% | 3.6% | pass |
| active_near_tie_0_0.05 | 24 | 16 | 84.6% | 45.5% | 2 | 6 | 10.6 | 12.5% | 100.0% | 12.5% | fail |
| missing | 120 | 19 | 24.5% | 100.0% | 40 | 0 | 50.6 | 27.5% | 100.0% | 0.0% | fail |
| phrase_blocker_0.05_0.10 | 10 | 8 | 0.0% | 85.7% | 3 | 1 | 3.0 | 50.0% | 100.0% | 0.0% | fail |
| phrase_clear_0.10+ | 5 | 5 | n/a | 80.0% | 0 | 1 | 2.6 | 60.0% | 100.0% | 20.0% | pass |
| phrase_near_tie_0_0.05 | 26 | 17 | 85.7% | 73.7% | 1 | 5 | 13.8 | 46.2% | 100.0% | 34.6% | pass |

## Trigger Risk Summary

| Trigger | Cases | Failures | Neg allow | Pos abstain | Source rank | Zipf band | Sense count | Lanes |
| --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| plant | 13 | 6 | 3 | 3 | missing | zipf_4_to_5_common |  | sampling_stage1_representative_proxy, semantic_veto_llm_pilot_en_es_v1 |
| order | 11 | 5 | 3 | 2 | missing | zipf_5_plus_very_common |  | sampling_stage1_representative_proxy, semantic_veto_llm_pilot_en_es_v1 |
| check | 11 | 5 | 3 | 2 | missing | zipf_5_plus_very_common |  | sampling_stage1_representative_proxy, semantic_veto_llm_pilot_en_es_v1 |
| report | 11 | 6 | 2 | 4 | missing | zipf_5_plus_very_common |  | sampling_stage1_representative_proxy, semantic_veto_llm_pilot_en_es_v1 |
| play | 12 | 5 | 2 | 3 | missing | zipf_5_plus_very_common |  | sampling_stage1_representative_proxy, semantic_veto_llm_pilot_en_es_v1 |
| bank | 12 | 4 | 1 | 3 | 501-1000 | zipf_5_plus_very_common |  | sampling_stage1_representative_proxy, semantic_veto_llm_pilot_en_es_v1 |
| watch | 12 | 3 | 1 | 2 | 1-500 | zipf_5_plus_very_common |  | sampling_stage1_representative_proxy, semantic_veto_llm_pilot_en_es_v1 |
| match | 13 | 3 | 1 | 2 | 2001-5000 | zipf_5_plus_very_common |  | sampling_stage1_representative_proxy, semantic_veto_llm_pilot_en_es_v1 |
| branch | 13 | 3 | 1 | 2 | missing | zipf_4_to_5_common |  | sampling_stage1_representative_proxy, semantic_veto_llm_pilot_en_es_v1 |
| wrong | 3 | 1 | 1 | 0 | 1-500 | zipf_5_plus_very_common | 13 | wave7_phrase_control_triage_stress |
| score | 3 | 1 | 1 | 0 | 1001-2000 | zipf_4_to_5_common | 18 | wave7_phrase_control_triage_stress |
| gross | 3 | 1 | 1 | 0 | >5000 | zipf_4_to_5_common | 10 | wave7_phrase_control_triage_stress |

## Failure Rows

| Case | Lane | Trigger | Target | Outcome | Source rank | Zipf band | Target rank | Sense count | Sentence |
| --- | --- | --- | --- | --- | --- | --- | --- | ---: | --- |
| pilotrow:pilot_watch_reloj:phrase_no_winner:001 | semantic_veto_llm_pilot_en_es_v1 | watch | reloj | negative_allow | 1-500 | zipf_5_plus_very_common | missing |  | Before the meeting starts, watch your step on the wet tiles. |
| en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:wrong:001 | wave7_phrase_control_triage_stress | wrong | incorrecto | negative_allow | 1-500 | zipf_5_plus_very_common | missing | 13 | He rubbed the organizer the wrong way. |
| pilotrow:pilot_bank_banco:phrase_no_winner:001 | semantic_veto_llm_pilot_en_es_v1 | bank | banco | negative_allow | 501-1000 | zipf_5_plus_very_common | missing |  | Bank on getting there early, because the parking lot fills up fast before the concert starts. |
| en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:score:001 | wave7_phrase_control_triage_stress | score | tantos | negative_allow | 1001-2000 | zipf_4_to_5_common | 1-500 | 18 | The composer wrote the score for the film. |
| pilotrow:pilot_match_partido:shadow_negative:001 | semantic_veto_llm_pilot_en_es_v1 | match | partido | negative_allow | 2001-5000 | zipf_5_plus_very_common | missing |  | Headline: a perfect match for the frame, with the finish finally aligned. |
| en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:gross:002 | wave7_phrase_control_triage_stress | gross | repulsivo | negative_allow | >5000 | zipf_4_to_5_common | missing | 10 | The shop ordered a gross of pencils. |
| en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:cast:001 | wave7_phrase_control_triage_stress | cast | lanzamiento | negative_allow | missing | zipf_4_to_5_common | missing | 20 | The director praised the cast after rehearsal. |
| en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:stretch:001 | wave7_phrase_control_triage_stress | stretch | estirón | negative_allow | missing | zipf_4_to_5_common | missing | 20 | That estimate is a stretch. |
| en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:squeeze:001 | wave7_phrase_control_triage_stress | squeeze | crisis | negative_allow | missing | zipf_3_to_4_mid | 501-1000 | 17 | The squeeze play surprised the defense. |
| en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:foul:001 | wave7_phrase_control_triage_stress | foul | falta | negative_allow | missing | zipf_4_to_5_common | 501-1000 | 16 | The foul weather delayed the ferry. |
| pilotrow:pilot_branch_sucursal:shadow_negative:002 | semantic_veto_llm_pilot_en_es_v1 | branch | sucursal | negative_allow | missing | zipf_4_to_5_common | missing |  | The database query returned a branch of the decision tree after the latest update. |
| pilotrow:pilot_check_cheque:phrase_no_winner:001 | semantic_veto_llm_pilot_en_es_v1 | check | cheque | negative_allow | missing | zipf_5_plus_very_common | missing |  | Check the box below to continue, then review the form before you submit it. |

## Metadata Gaps

| Field | Value |
| --- | --- |
| `case_count` | 240 |
| `source_rank_known_rows` | 81 |
| `source_rank_known_rate` | 0.3375 |
| `source_zipf_known_rows` | 240 |
| `source_zipf_known_rate` | 1.0 |
| `target_rank_known_rows` | 15 |
| `target_rank_known_rate` | 0.0625 |
| `source_frequency_match_counts` | exact=81, missing=159 |
| `source_zipf_match_counts` | wordfreq=240 |
| `target_frequency_match_counts` | exact=9, missing=225, spanish_plural_fallback=6 |
| `missing_source_rank_trigger_count` | 24 |
| `missing_source_rank_triggers` | ball, branch, cast, cell, check, crash, drink, file, firm, fix, foul, full, like, order, park, plant, play, report, spring, squeeze, stretch, table, trip, waste |
| `missing_source_zipf_trigger_count` | 0 |
| `missing_source_zipf_triggers` |  |
| `missing_target_rank_candidate_count` | 30 |
| `missing_target_rank_candidates` | adecuado, aprieto, archivo, banco, bebida, cheque, choque, compensador, célula, desperdicio, estirón, firma, incorrecto, informe, lanzamiento, lleno, mesa, obra, parque, partido, pedido, pelota, planta, primavera, reloj, repulsivo, sello, sucursal, tablero, viaje |
| `wordnet_sense_count_known_rows` | 48 |
| `translation_candidate_count_known_rows` | 48 |

## Key Findings

- Overall measured lanes are 56.2% positive allow and 82.2% negative abstain.
- English source-trigger rank coverage is 33.8%; missing rank remains a first-class metadata gap rather than a reason to drop rows.
- English source-trigger Zipf coverage is 100.0%; use it as a denser frequency proxy while keeping corpus rank and learner level separate.
- Spanish target-rank coverage is 6.2%; this is too sparse to use as a standalone learner-difficulty proof.
- Known top-1000 English trigger rows have 8 product failures over 27 measured cases.
- Zipf frequency fallback separates very-common and common triggers at 49.1% versus 63.6% positive allow.
- Rows with 10+ WordNet senses have 9 failures over 48 cases in the measured lanes.

## Limitations

- difficulty_report_is_diagnostic_only
- stress_llm_and_representative_proxy_lanes_are_reported_together_but_not_promotion_equivalent
- frequency_rank_is_a_proxy_not_a_cefr_or_user-known-word_model
- source_zipf_frequency_is_a_package_proxy_not_a_corpus_rank_or_cefr_level
- target_lemma_rank_can_be_sparse_when_spanish_replacements_are_inflected_or_absent
- source_rank_coverage_below_50_percent
- target_rank_coverage_below_50_percent

## Next Steps

- Use this report to choose the first frequency/ambiguity strata for expanded LLM evaluation rows.
- Improve target-lemma normalization or target-frequency coverage before using Spanish rank as an SRS difficulty gate.
- Keep source-trigger rank, source Zipf frequency, target rank, and ambiguity proxies separate in future acceptance claims.
- Add or configure a denser English source frequency list before claiming a beginner-trigger accuracy curve.
- Use Zipf bands as the next no-spend expansion axis, then verify the very-common false-abstain signal with more representative rows.
- Add exact lemma normalization for Spanish replacements before estimating learner difficulty at scale.
