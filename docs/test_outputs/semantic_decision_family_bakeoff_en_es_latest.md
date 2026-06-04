# en-es Semantic Decision Rule Matrix

- Status: `ok`
- Generated: `2026-04-28T18:04:13Z`
- Matrix: `en_es_semantic_decision_family_bakeoff_v1`
- Dataset: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v10.json`
- Manifest: `docs/test_inputs/semantic_decision_family_bakeoff_en_es.json`
- Evaluation suites: `1`
- Config rows: `269`
- Case score traces: `25555`
- Case traces included in JSON: `False`
- Negative-control sanity: `not_applicable`

## Recommendation

Best promotable candidate is `family_margin:a0_05__m0`; with harmful `0`; and false abstain `28`; against incumbent `scalar_control_margin_a005_m0`; with negative controls delegated to the companion broad matrix.

## Best By Constraint

- incumbent_control: `scalar_control_margin_a005_m0`
  - Harmful / false abstain: `0` / `28`
  - Decision / winner accuracy: `70.53%` / `63.16%`
  - Shape: `tfidf_cosine:masked_sentence:all_evidence_text:single_concatenated_text:active_minus_strongest_shadow:phrase_override`

- best_overall: `family_margin:a0_05__m0`
  - Harmful / false abstain: `0` / `28`
  - Decision / winner accuracy: `70.53%` / `63.16%`
  - Shape: `tfidf_cosine:masked_sentence:all_evidence_text:single_concatenated_text:active_minus_strongest_shadow:phrase_override`

- best_zero_harm: `family_margin:a0_05__m0`
  - Harmful / false abstain: `0` / `28`
  - Decision / winner accuracy: `70.53%` / `63.16%`
  - Shape: `tfidf_cosine:masked_sentence:all_evidence_text:single_concatenated_text:active_minus_strongest_shadow:phrase_override`

- best_promotable_candidate: `family_margin:a0_05__m0`
  - Harmful / false abstain: `0` / `28`
  - Decision / winner accuracy: `70.53%` / `63.16%`
  - Shape: `tfidf_cosine:masked_sentence:all_evidence_text:single_concatenated_text:active_minus_strongest_shadow:phrase_override`

## Algorithm Family Winners

| Family | Rows | Best Config | Zero-Harm Config | Harmful | False Abstain | Winner Acc. | Objective |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| control_margin | 1 | scalar_control_margin_a005_m0 | scalar_control_margin_a005_m0 | 0 | 28 | 63.16% | 280.6632 |
| margin | 36 | family_margin:a0_05__m0 | family_margin:a0_05__m0 | 0 | 28 | 63.16% | 280.6632 |
| pairwise_all | 36 | family_pairwise_all:a0_05__m0 | family_pairwise_all:a0_05__m0 | 0 | 28 | 63.16% | 280.6632 |
| pairwise_most | 64 | family_pairwise_most:a0_05__m0_005__w0_5 | family_pairwise_most:a0_05__m0_005__w0_5 | 0 | 28 | 63.16% | 280.6632 |
| ratio | 42 | family_ratio:a0_05__r1 | family_ratio:a0_05__r1 | 0 | 28 | 63.16% | 280.6632 |
| softmax_probability | 90 | family_softmax:a0_05__p0_52__t12 | family_softmax:a0_05__p0_52__t12 | 0 | 28 | 63.16% | 280.6632 |

## Decision Signature Clusters

- Unique replace signatures: `14`
- Largest replace-signature cluster: `80` configs
- `e3b0c44298fc1c14`: `80` configs, sample `family_margin:a0_2__m0, family_margin:a0_2__m0_005, family_margin:a0_2__m0_01, family_margin:a0_2__m0_02, family_margin:a0_2__m0_05`
- `482ec237a4bde36b`: `62` configs, sample `family_margin:a0_02__m0_1, family_margin:a0_05__m0_1, family_margin:a0_1__m0, family_margin:a0_1__m0_005, family_margin:a0_1__m0_01`
- `a723281989699fc0`: `37` configs, sample `family_margin:a0_05__m0, family_margin:a0_05__m0_005, family_margin:a0_05__m0_01, family_margin:a0_05__m0_02, family_pairwise_all:a0_05__m0`
- `46f1752c973d4d4c`: `23` configs, sample `family_margin:a0_02__m0_05, family_margin:a0_05__m0_05, family_margin:a0__m0_05, family_pairwise_all:a0_02__m0_05, family_pairwise_all:a0_05__m0_05`
- `3957b0e16a6e54a2`: `15` configs, sample `family_margin:a0_02__m0_005, family_margin:a0_02__m0_01, family_margin:a0__m0_01, family_pairwise_all:a0_02__m0_005, family_pairwise_all:a0_02__m0_01`

## Headline Metric Ties

- Tied primary-metric groups: `14`
- Largest tied group: `80` configs
- `harm=0|false=38|decision=0.600000|winner=0.500000`: `80` configs, unique replace signatures `1`, ROC AUC `0.5263..0.7119`, Avg Prec. `0.5093..0.7065`
- `harm=0|false=36|decision=0.621053|winner=0.526316`: `62` configs, unique replace signatures `1`, ROC AUC `0.5263..0.7119`, Avg Prec. `0.5093..0.7065`
- `harm=0|false=28|decision=0.705263|winner=0.631579`: `37` configs, unique replace signatures `1`, ROC AUC `0.5877..0.7119`, Avg Prec. `0.5224..0.7065`
- `harm=0|false=29|decision=0.694737|winner=0.618421`: `23` configs, unique replace signatures `1`, ROC AUC `0.6184..0.7119`, Avg Prec. `0.6572..0.7065`
- `harm=4|false=25|decision=0.694737|winner=0.644737`: `15` configs, unique replace signatures `1`, ROC AUC `0.6272..0.7119`, Avg Prec. `0.5699..0.7065`
- `harm=3|false=25|decision=0.705263|winner=0.657895`: `12` configs, unique replace signatures `1`, ROC AUC `0.6360..0.7119`, Avg Prec. `0.5948..0.7065`
- `harm=36|false=2|decision=0.600000|winner=0.631579`: `9` configs, unique replace signatures `1`, ROC AUC `0.5877..0.7119`, Avg Prec. `0.5224..0.7065`
- `harm=4|false=24|decision=0.705263|winner=0.657895`: `7` configs, unique replace signatures `1`, ROC AUC `0.5877..0.7119`, Avg Prec. `0.5224..0.7065`

## Discovery Selection vs Locked Eval

- Policy: select the best config inside each algorithm family using discovery-split objective only; report locked-eval metrics after selection
| Family | Selected On Discovery | Discovery Harmful | Discovery False Abstain | Locked Harmful | Locked False Abstain | Locked Objective | Locked Oracle |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| control_margin | scalar_control_margin_a005_m0 | 0 | 20 | 0 | 8 | 80.8810 | scalar_control_margin_a005_m0 |
| margin | family_margin:a0_05__m0 | 0 | 20 | 0 | 8 | 80.8810 | family_margin:a0_02__m0 |
| pairwise_all | family_pairwise_all:a0_05__m0 | 0 | 20 | 0 | 8 | 80.8810 | family_pairwise_all:a0_02__m0 |
| pairwise_most | family_pairwise_most:a0_05__m0_005__w0_5 | 0 | 20 | 0 | 8 | 80.8810 | family_pairwise_most:a0__m0_005__w0_5 |
| ratio | family_ratio:a0_05__r1 | 0 | 20 | 0 | 8 | 80.8810 | family_ratio:a0__r1 |
| softmax_probability | family_softmax:a0_05__p0_52__t12 | 0 | 20 | 0 | 8 | 80.8810 | family_softmax:a0_02__p0_5__t12 |

## Incumbent Case Deltas

- Incumbent config: `scalar_control_margin_a005_m0`
- Configs identical to incumbent decisions: `36`
- `family_margin:a0__m0`: decisions changed `62`, false abstains fixed/introduced `26`/`0`, harmful fixed/introduced `0`/`36`
- `family_pairwise_all:a0__m0`: decisions changed `62`, false abstains fixed/introduced `26`/`0`, harmful fixed/introduced `0`/`36`
- `family_pairwise_most:a0__m0__w0_5`: decisions changed `62`, false abstains fixed/introduced `26`/`0`, harmful fixed/introduced `0`/`36`
- `family_pairwise_most:a0__m0__w0_67`: decisions changed `62`, false abstains fixed/introduced `26`/`0`, harmful fixed/introduced `0`/`36`
- `family_pairwise_most:a0__m0__w0_75`: decisions changed `62`, false abstains fixed/introduced `26`/`0`, harmful fixed/introduced `0`/`36`
- `family_pairwise_most:a0__m0__w1`: decisions changed `62`, false abstains fixed/introduced `26`/`0`, harmful fixed/introduced `0`/`36`
- `family_softmax:a0__p0_5__t12`: decisions changed `62`, false abstains fixed/introduced `26`/`0`, harmful fixed/introduced `0`/`36`
- `family_softmax:a0__p0_5__t4`: decisions changed `62`, false abstains fixed/introduced `26`/`0`, harmful fixed/introduced `0`/`36`

## Top Candidate Configs

| Rank | Family | Config | Scorer | Context | Evidence | Aggregation | Decision | Phrase | Control | Harmful | False Abstain | Winner Acc. | ROC AUC | Avg Prec. | Objective |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | margin | family_margin:a0_05__m0 | tfidf_cosine | masked_sentence | all_evidence_text | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 0 | 28 | 63.16% | 0.7119 | 0.7065 | 280.6632 |
| 2 | margin | family_margin:a0_05__m0_005 | tfidf_cosine | masked_sentence | all_evidence_text | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 0 | 28 | 63.16% | 0.7119 | 0.7065 | 280.6632 |
| 3 | margin | family_margin:a0_05__m0_01 | tfidf_cosine | masked_sentence | all_evidence_text | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 0 | 28 | 63.16% | 0.7119 | 0.7065 | 280.6632 |
| 4 | margin | family_margin:a0_05__m0_02 | tfidf_cosine | masked_sentence | all_evidence_text | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 0 | 28 | 63.16% | 0.7119 | 0.7065 | 280.6632 |
| 5 | pairwise_all | family_pairwise_all:a0_05__m0 | tfidf_cosine | masked_sentence | all_evidence_text | single_concatenated_text | pairwise_active_beats_all_shadows | phrase_override | normal | 0 | 28 | 63.16% | 0.5877 | 0.5224 | 280.6632 |
| 6 | pairwise_all | family_pairwise_all:a0_05__m0_005 | tfidf_cosine | masked_sentence | all_evidence_text | single_concatenated_text | pairwise_active_beats_all_shadows | phrase_override | normal | 0 | 28 | 63.16% | 0.6316 | 0.5713 | 280.6632 |
| 7 | pairwise_all | family_pairwise_all:a0_05__m0_01 | tfidf_cosine | masked_sentence | all_evidence_text | single_concatenated_text | pairwise_active_beats_all_shadows | phrase_override | normal | 0 | 28 | 63.16% | 0.6272 | 0.5699 | 280.6632 |
| 8 | pairwise_all | family_pairwise_all:a0_05__m0_02 | tfidf_cosine | masked_sentence | all_evidence_text | single_concatenated_text | pairwise_active_beats_all_shadows | phrase_override | normal | 0 | 28 | 63.16% | 0.6360 | 0.5948 | 280.6632 |
| 9 | pairwise_most | family_pairwise_most:a0_05__m0_005__w0_5 | tfidf_cosine | masked_sentence | all_evidence_text | single_concatenated_text | pairwise_active_beats_most_shadows | phrase_override | normal | 0 | 28 | 63.16% | 0.6316 | 0.5713 | 280.6632 |
| 10 | pairwise_most | family_pairwise_most:a0_05__m0_005__w0_67 | tfidf_cosine | masked_sentence | all_evidence_text | single_concatenated_text | pairwise_active_beats_most_shadows | phrase_override | normal | 0 | 28 | 63.16% | 0.6316 | 0.5713 | 280.6632 |
| 11 | pairwise_most | family_pairwise_most:a0_05__m0_005__w0_75 | tfidf_cosine | masked_sentence | all_evidence_text | single_concatenated_text | pairwise_active_beats_most_shadows | phrase_override | normal | 0 | 28 | 63.16% | 0.6316 | 0.5713 | 280.6632 |
| 12 | pairwise_most | family_pairwise_most:a0_05__m0_005__w1 | tfidf_cosine | masked_sentence | all_evidence_text | single_concatenated_text | pairwise_active_beats_most_shadows | phrase_override | normal | 0 | 28 | 63.16% | 0.6316 | 0.5713 | 280.6632 |
| 13 | pairwise_most | family_pairwise_most:a0_05__m0_02__w0_5 | tfidf_cosine | masked_sentence | all_evidence_text | single_concatenated_text | pairwise_active_beats_most_shadows | phrase_override | normal | 0 | 28 | 63.16% | 0.6360 | 0.5948 | 280.6632 |
| 14 | pairwise_most | family_pairwise_most:a0_05__m0_02__w0_67 | tfidf_cosine | masked_sentence | all_evidence_text | single_concatenated_text | pairwise_active_beats_most_shadows | phrase_override | normal | 0 | 28 | 63.16% | 0.6360 | 0.5948 | 280.6632 |
| 15 | pairwise_most | family_pairwise_most:a0_05__m0_02__w0_75 | tfidf_cosine | masked_sentence | all_evidence_text | single_concatenated_text | pairwise_active_beats_most_shadows | phrase_override | normal | 0 | 28 | 63.16% | 0.6360 | 0.5948 | 280.6632 |
| 16 | pairwise_most | family_pairwise_most:a0_05__m0_02__w1 | tfidf_cosine | masked_sentence | all_evidence_text | single_concatenated_text | pairwise_active_beats_most_shadows | phrase_override | normal | 0 | 28 | 63.16% | 0.6360 | 0.5948 | 280.6632 |
| 17 | pairwise_most | family_pairwise_most:a0_05__m0__w0_5 | tfidf_cosine | masked_sentence | all_evidence_text | single_concatenated_text | pairwise_active_beats_most_shadows | phrase_override | normal | 0 | 28 | 63.16% | 0.5877 | 0.5224 | 280.6632 |
| 18 | pairwise_most | family_pairwise_most:a0_05__m0__w0_67 | tfidf_cosine | masked_sentence | all_evidence_text | single_concatenated_text | pairwise_active_beats_most_shadows | phrase_override | normal | 0 | 28 | 63.16% | 0.5877 | 0.5224 | 280.6632 |
| 19 | pairwise_most | family_pairwise_most:a0_05__m0__w0_75 | tfidf_cosine | masked_sentence | all_evidence_text | single_concatenated_text | pairwise_active_beats_most_shadows | phrase_override | normal | 0 | 28 | 63.16% | 0.5877 | 0.5224 | 280.6632 |
| 20 | pairwise_most | family_pairwise_most:a0_05__m0__w1 | tfidf_cosine | masked_sentence | all_evidence_text | single_concatenated_text | pairwise_active_beats_most_shadows | phrase_override | normal | 0 | 28 | 63.16% | 0.5877 | 0.5224 | 280.6632 |

## Overfitting Checks

- Split policy: `deterministic_case_id_hash_modulo` (locked remainders `[0]`)
- `family_ratio:a0__r1`: discovery objective `6170.6441`, locked objective `50.5506`, worst leave-one-family objective `6220.6583`
- `family_ratio:a0__r1_01`: discovery objective `6170.6441`, locked objective `50.5506`, worst leave-one-family objective `6220.6583`
- `family_margin:a0_02__m0`: discovery objective `4180.6306`, locked objective `60.6607`, worst leave-one-family objective `4240.6722`
- `family_pairwise_all:a0_02__m0`: discovery objective `4180.6306`, locked objective `60.6607`, worst leave-one-family objective `4240.6722`
- `family_ratio:a0_02__r1`: discovery objective `4180.6306`, locked objective `60.6607`, worst leave-one-family objective `4240.6722`
- `family_ratio:a0_02__r1_01`: discovery objective `4180.6306`, locked objective `60.6607`, worst leave-one-family objective `4240.6722`
- `family_softmax:a0_02__p0_5__t12`: discovery objective `4180.6306`, locked objective `60.6607`, worst leave-one-family objective `4240.6722`
- `family_softmax:a0_02__p0_5__t4`: discovery objective `4180.6306`, locked objective `60.6607`, worst leave-one-family objective `4240.6722`
- `family_softmax:a0_02__p0_5__t8`: discovery objective `4180.6306`, locked objective `60.6607`, worst leave-one-family objective `4240.6722`
- `family_margin:a0__m0_005`: discovery objective `5180.6608`, locked objective `60.6607`, worst leave-one-family objective `5240.6972`
