# en-es Semantic Decision Rule Matrix

- Status: `ok`
- Generated: `2026-04-28T18:06:13Z`
- Matrix: `en_es_semantic_decision_suite_confirmation_v1`
- Dataset: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v10.json`
- Manifest: `docs/test_inputs/semantic_decision_suite_confirmation_en_es.json`
- Evaluation suites: `4`
- Config rows: `7`
- Case score traces: `1330`
- Case traces included in JSON: `True`
- Negative-control sanity: `not_applicable`

## Recommendation

No candidate cleared the incumbent-aware promotability screen; treat the matrix as evidence for source coverage or representation work before policy promotion.

## Best By Constraint

- incumbent_control: `suite_control_margin_a005_m0`
  - Harmful / false abstain: `1` / `46`
  - Decision / winner accuracy: `75.26%` / `58.77%`
  - Shape: `tfidf_cosine:masked_sentence:all_evidence_text:single_concatenated_text:active_minus_strongest_shadow:phrase_override`

- best_overall: `suite_control_margin_a005_m0`
  - Harmful / false abstain: `1` / `46`
  - Decision / winner accuracy: `75.26%` / `58.77%`
  - Shape: `tfidf_cosine:masked_sentence:all_evidence_text:single_concatenated_text:active_minus_strongest_shadow:phrase_override`

## Algorithm Family Winners

| Family | Rows | Best Config | Zero-Harm Config | Harmful | False Abstain | Winner Acc. | Objective |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| control_margin | 1 | suite_control_margin_a005_m0 |  | 1 | 46 | 58.77% | 1460.6596 |
| margin | 2 | suite_margin_a005_m0 |  | 1 | 46 | 58.77% | 1460.6596 |
| pairwise_all | 1 | suite_pairwise_all_a005_m0 |  | 1 | 46 | 58.77% | 1460.6596 |
| pairwise_most | 1 | suite_pairwise_most_a005_m0005_w05 |  | 1 | 46 | 58.77% | 1460.6596 |
| ratio | 1 | suite_ratio_a005_r1 |  | 1 | 46 | 58.77% | 1460.6596 |
| softmax_probability | 1 | suite_softmax_a005_p052_t12 |  | 1 | 46 | 58.77% | 1460.6596 |

## Evaluation Suite Breakdown

| Config | Suite | Cases | Harmful | False Abstain | Accuracy |
| --- | --- | ---: | ---: | ---: | ---: |
| suite_control_margin_a005_m0 | frozen_v10 | 95 | 0 | 28 | 70.53% |
| suite_control_margin_a005_m0 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| suite_control_margin_a005_m0 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| suite_control_margin_a005_m0 | source_heldout_v2 | 38 | 1 | 18 | 50.00% |
| suite_margin_a005_m0 | frozen_v10 | 95 | 0 | 28 | 70.53% |
| suite_margin_a005_m0 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| suite_margin_a005_m0 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| suite_margin_a005_m0 | source_heldout_v2 | 38 | 1 | 18 | 50.00% |
| suite_pairwise_all_a005_m0 | frozen_v10 | 95 | 0 | 28 | 70.53% |
| suite_pairwise_all_a005_m0 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| suite_pairwise_all_a005_m0 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| suite_pairwise_all_a005_m0 | source_heldout_v2 | 38 | 1 | 18 | 50.00% |
| suite_pairwise_most_a005_m0005_w05 | frozen_v10 | 95 | 0 | 28 | 70.53% |
| suite_pairwise_most_a005_m0005_w05 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| suite_pairwise_most_a005_m0005_w05 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| suite_pairwise_most_a005_m0005_w05 | source_heldout_v2 | 38 | 1 | 18 | 50.00% |
| suite_ratio_a005_r1 | frozen_v10 | 95 | 0 | 28 | 70.53% |
| suite_ratio_a005_r1 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| suite_ratio_a005_r1 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| suite_ratio_a005_r1 | source_heldout_v2 | 38 | 1 | 18 | 50.00% |
| suite_softmax_a005_p052_t12 | frozen_v10 | 95 | 0 | 28 | 70.53% |
| suite_softmax_a005_p052_t12 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| suite_softmax_a005_p052_t12 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| suite_softmax_a005_p052_t12 | source_heldout_v2 | 38 | 1 | 18 | 50.00% |
| suite_margin_a002_m0 | frozen_v10 | 95 | 4 | 24 | 70.53% |
| suite_margin_a002_m0 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| suite_margin_a002_m0 | phrase_heldout_v2 | 38 | 1 | 0 | 97.37% |
| suite_margin_a002_m0 | source_heldout_v2 | 38 | 2 | 16 | 52.63% |

## Decision Signature Clusters

- Unique replace signatures: `2`
- Largest replace-signature cluster: `6` configs
- `b637f4024f2b6ab3`: `6` configs, sample `suite_control_margin_a005_m0, suite_margin_a005_m0, suite_pairwise_all_a005_m0, suite_pairwise_most_a005_m0005_w05, suite_ratio_a005_r1`
- `5caf06c4db04dc24`: `1` configs, sample `suite_margin_a002_m0`

## Headline Metric Ties

- Tied primary-metric groups: `1`
- Largest tied group: `6` configs
- `harm=1|false=46|decision=0.752632|winner=0.587719`: `6` configs, unique replace signatures `1`, ROC AUC `0.5363..0.6560`, Avg Prec. `0.4439..0.5790`

## Discovery Selection vs Locked Eval

- Policy: select the best config inside each algorithm family using discovery-split objective only; report locked-eval metrics after selection
| Family | Selected On Discovery | Discovery Harmful | Discovery False Abstain | Locked Harmful | Locked False Abstain | Locked Objective | Locked Oracle |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| control_margin | suite_control_margin_a005_m0 | 0 | 28 | 1 | 18 | 1180.8302 | suite_control_margin_a005_m0 |
| margin | suite_margin_a005_m0 | 0 | 28 | 1 | 18 | 1180.8302 | suite_margin_a005_m0 |
| pairwise_all | suite_pairwise_all_a005_m0 | 0 | 28 | 1 | 18 | 1180.8302 | suite_pairwise_all_a005_m0 |
| pairwise_most | suite_pairwise_most_a005_m0005_w05 | 0 | 28 | 1 | 18 | 1180.8302 | suite_pairwise_most_a005_m0005_w05 |
| ratio | suite_ratio_a005_r1 | 0 | 28 | 1 | 18 | 1180.8302 | suite_ratio_a005_r1 |
| softmax_probability | suite_softmax_a005_p052_t12 | 0 | 28 | 1 | 18 | 1180.8302 | suite_softmax_a005_p052_t12 |

## Incumbent Case Deltas

- Incumbent config: `suite_control_margin_a005_m0`
- Configs identical to incumbent decisions: `5`
- `suite_margin_a002_m0`: decisions changed `12`, false abstains fixed/introduced `6`/`0`, harmful fixed/introduced `0`/`6`
- `suite_margin_a005_m0`: decisions changed `0`, false abstains fixed/introduced `0`/`0`, harmful fixed/introduced `0`/`0`
- `suite_pairwise_all_a005_m0`: decisions changed `0`, false abstains fixed/introduced `0`/`0`, harmful fixed/introduced `0`/`0`
- `suite_pairwise_most_a005_m0005_w05`: decisions changed `0`, false abstains fixed/introduced `0`/`0`, harmful fixed/introduced `0`/`0`
- `suite_ratio_a005_r1`: decisions changed `0`, false abstains fixed/introduced `0`/`0`, harmful fixed/introduced `0`/`0`
- `suite_softmax_a005_p052_t12`: decisions changed `0`, false abstains fixed/introduced `0`/`0`, harmful fixed/introduced `0`/`0`

## Top Candidate Configs

| Rank | Family | Config | Scorer | Context | Evidence | Aggregation | Decision | Phrase | Control | Harmful | False Abstain | Winner Acc. | ROC AUC | Avg Prec. | Objective |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | control_margin | suite_control_margin_a005_m0 | tfidf_cosine | masked_sentence | all_evidence_text | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 1 | 46 | 58.77% | 0.6560 | 0.5790 | 1460.6596 |
| 2 | margin | suite_margin_a005_m0 | tfidf_cosine | masked_sentence | all_evidence_text | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 1 | 46 | 58.77% | 0.6560 | 0.5790 | 1460.6596 |
| 3 | pairwise_all | suite_pairwise_all_a005_m0 | tfidf_cosine | masked_sentence | all_evidence_text | single_concatenated_text | pairwise_active_beats_all_shadows | phrase_override | normal | 1 | 46 | 58.77% | 0.5363 | 0.4439 | 1460.6596 |
| 4 | pairwise_most | suite_pairwise_most_a005_m0005_w05 | tfidf_cosine | masked_sentence | all_evidence_text | single_concatenated_text | pairwise_active_beats_most_shadows | phrase_override | normal | 1 | 46 | 58.77% | 0.6065 | 0.4799 | 1460.6596 |
| 5 | ratio | suite_ratio_a005_r1 | tfidf_cosine | masked_sentence | all_evidence_text | single_concatenated_text | active_ratio_strongest_shadow | phrase_override | normal | 1 | 46 | 58.77% | 0.6335 | 0.4896 | 1460.6596 |
| 6 | softmax_probability | suite_softmax_a005_p052_t12 | tfidf_cosine | masked_sentence | all_evidence_text | single_concatenated_text | softmax_probability | phrase_override | normal | 1 | 46 | 58.77% | 0.6560 | 0.5790 | 1460.6596 |
| 7 | margin | suite_margin_a002_m0 | tfidf_cosine | masked_sentence | all_evidence_text | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 7 | 40 | 61.40% | 0.6560 | 0.5790 | 7400.6333 |

## Overfitting Checks

- Split policy: `deterministic_case_id_hash_modulo` (locked remainders `[0]`)
- `suite_control_margin_a005_m0`: discovery objective `280.5790`, locked objective `1180.8302`, worst leave-one-family objective `1460.6813`
- `suite_margin_a005_m0`: discovery objective `280.5790`, locked objective `1180.8302`, worst leave-one-family objective `1460.6813`
- `suite_pairwise_all_a005_m0`: discovery objective `280.5790`, locked objective `1180.8302`, worst leave-one-family objective `1460.6813`
- `suite_pairwise_most_a005_m0005_w05`: discovery objective `280.5790`, locked objective `1180.8302`, worst leave-one-family objective `1460.6813`
- `suite_ratio_a005_r1`: discovery objective `280.5790`, locked objective `1180.8302`, worst leave-one-family objective `1460.6813`
- `suite_softmax_a005_p052_t12`: discovery objective `280.5790`, locked objective `1180.8302`, worst leave-one-family objective `1460.6813`
- `suite_margin_a002_m0`: discovery objective `4270.6151`, locked objective `3130.6721`, worst leave-one-family objective `7400.6541`
