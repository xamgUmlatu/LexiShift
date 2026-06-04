# en-es Semantic Source Reference Lane

- Status: `ok`
- Decision: `reference_lane_frozen`
- Generated: `2026-04-25T23:58:54Z`
- Lane: `en_es_semantic_source_reference_lane_v1`
- Checks: `59`
- Failed checks: `0`

## Artifacts

- source_cycle_json: `docs/test_outputs/semantic_source_admission_cycle_wordnet_active_related_plant_cell_depth3_heldout_v2_policy_latest.json`
- heldout_validation_json: `docs/test_outputs/semantic_source_heldout_validation_v2_latest.json`
- phrase_heldout_validation_json: `docs/test_outputs/semantic_source_phrase_heldout_v2_margin005_validation_latest.json`
- admitted_evidence_batch_json: `docs/test_outputs/experiments/semantic_example_frame_batches/en-es-wordnet-active-related-plant-cell-depth3-heldout-v2-policy-v1-20260425a_cycle_sense_admitted_normalized_evidence.json`
- heldout_cases_json: `docs/test_inputs/semantic_routing_cases/en_es_source_heldout_cases_v2.json`
- phrase_heldout_cases_json: `docs/test_inputs/semantic_routing_cases/en_es_source_phrase_heldout_cases_v2.json`

## Configured Lane

- source_mode: `cycle_merged`
- scorer_id: `sentence_transformer_cosine`
- context_view: `masked_sentence`
- min_active_score: `0.0`
- min_margin: `0.0`
- decision_shape: `active_shadow_containment_surface_pos`

## Phrase Policy Candidate Lane

- source_mode: `promotion_candidate_composite`
- scorer_id: `sentence_transformer_cosine`
- context_view: `masked_sentence`
- min_active_score: `0.0`
- min_margin: `0.005`
- decision_shape: `active_shadow_containment_surface_pos`

## Checks

| Check | Status | Expected | Actual |
| --- | --- | --- | --- |
| `source_cycle.status` | `ok` | `ok` | `ok` |
| `source_cycle.decision` | `ok` | `promotion_candidate` | `promotion_candidate` |
| `source_cycle.offline_promotion_lane` | `ok` | `semantic_active_shadow` | `semantic_active_shadow` |
| `source_cycle.offline_semantic_lane_status` | `ok` | `promotion_candidate` | `promotion_candidate` |
| `source_cycle.runtime_publication_status` | `ok` | `blocked` | `blocked` |
| `source_cycle.runtime_publication_blockers` | `ok` | `['runtime_phrase_source_policy', 'broader_heldout_breadth', 'runtime_packaging_feasibility']` | `['runtime_phrase_source_policy', 'broader_heldout_breadth', 'runtime_packaging_feasibility']` |
| `source_cycle.heldout_validation_status` | `ok` | `ok` | `ok` |
| `source_cycle.heldout_validation_decision` | `ok` | `heldout_pass` | `heldout_pass` |
| `source_cycle.heldout_validation_passed` | `ok` | `True` | `True` |
| `source_cycle.leakage_rejected_row_count` | `ok` | `0` | `0` |
| `source_cycle.sense_rejected_row_count` | `ok` | `0` | `0` |
| `source_cycle.final_admitted_row_count` | `ok` | `133` | `133` |
| `source_cycle.families_total` | `ok` | `19` | `19` |
| `source_cycle.semantic_contract_complete_family_count` | `ok` | `19` | `19` |
| `source_cycle.phrase_contract_complete_family_count` | `ok` | `0` | `0` |
| `source_cycle.best_ablation_cases_total` | `ok` | `95` | `95` |
| `source_cycle.best_ablation_harmful_replace_count` | `ok` | `0` | `0` |
| `source_cycle.best_ablation_false_abstain_count` | `ok` | `0` | `0` |
| `source_cycle.best_ablation_replace_recall` | `ok` | `1.0` | `1.0` |
| `source_cycle.best_ablation_decision_accuracy` | `ok` | `1.0` | `1.0` |
| `source_cycle.configured_lane.source_mode` | `ok` | `cycle_merged` | `cycle_merged` |
| `source_cycle.configured_lane.scorer_id` | `ok` | `sentence_transformer_cosine` | `sentence_transformer_cosine` |
| `source_cycle.configured_lane.context_view` | `ok` | `masked_sentence` | `masked_sentence` |
| `source_cycle.configured_lane.min_active_score` | `ok` | `0.0` | `0.0` |
| `source_cycle.configured_lane.min_margin` | `ok` | `0.0` | `0.0` |
| `source_cycle.configured_lane.decision_shape` | `ok` | `active_shadow_containment_surface_pos` | `active_shadow_containment_surface_pos` |
| `heldout.status` | `ok` | `ok` | `ok` |
| `heldout.decision` | `ok` | `heldout_pass` | `heldout_pass` |
| `heldout.family_count` | `ok` | `19` | `19` |
| `heldout.case_count` | `ok` | `38` | `38` |
| `heldout.harmful_replace_count` | `ok` | `0` | `0` |
| `heldout.false_abstain_count` | `ok` | `0` | `0` |
| `heldout.replace_recall` | `ok` | `1.0` | `1.0` |
| `heldout.decision_accuracy` | `ok` | `1.0` | `1.0` |
| `heldout.configured_lane.scorer_id` | `ok` | `sentence_transformer_cosine` | `sentence_transformer_cosine` |
| `heldout.configured_lane.context_view` | `ok` | `masked_sentence` | `masked_sentence` |
| `heldout.configured_lane.min_active_score` | `ok` | `0.0` | `0.0` |
| `heldout.configured_lane.min_margin` | `ok` | `0.0` | `0.0` |
| `heldout.configured_lane.decision_shape` | `ok` | `active_shadow_containment_surface_pos` | `active_shadow_containment_surface_pos` |
| `phrase_heldout.status` | `ok` | `ok` | `ok` |
| `phrase_heldout.decision` | `ok` | `heldout_pass` | `heldout_pass` |
| `phrase_heldout.family_count` | `ok` | `19` | `19` |
| `phrase_heldout.case_count` | `ok` | `38` | `38` |
| `phrase_heldout.harmful_replace_count` | `ok` | `0` | `0` |
| `phrase_heldout.false_abstain_count` | `ok` | `0` | `0` |
| `phrase_heldout.replace_recall` | `ok` | `0.0` | `0.0` |
| `phrase_heldout.decision_accuracy` | `ok` | `1.0` | `1.0` |
| `phrase_heldout.configured_lane.scorer_id` | `ok` | `sentence_transformer_cosine` | `sentence_transformer_cosine` |
| `phrase_heldout.configured_lane.context_view` | `ok` | `masked_sentence` | `masked_sentence` |
| `phrase_heldout.configured_lane.min_active_score` | `ok` | `0.0` | `0.0` |
| `phrase_heldout.configured_lane.min_margin` | `ok` | `0.005` | `0.005` |
| `phrase_heldout.configured_lane.decision_shape` | `ok` | `active_shadow_containment_surface_pos` | `active_shadow_containment_surface_pos` |
| `evidence.source_id` | `ok` | `reverse_aux_wordnet_wiktextract_wordnet_active_related_plant_cell_depth3_heldout_v2_policy` | `reverse_aux_wordnet_wiktextract_wordnet_active_related_plant_cell_depth3_heldout_v2_policy` |
| `evidence.batch_id` | `ok` | `en-es:example-frame-composite:reverse-aux-wordnet-wiktextract-wordnet-active-related-plant-cell-depth3-heldout-v2-policy-v1:sense-admitted` | `en-es:example-frame-composite:reverse-aux-wordnet-wiktextract-wordnet-active-related-plant-cell-depth3-heldout-v2-policy-v1:sense-admitted` |
| `evidence.row_count` | `ok` | `133` | `133` |
| `evidence.relation_type.anchor_cue` | `ok` | `95` | `95` |
| `evidence.relation_type.shadow_candidate` | `ok` | `38` | `38` |
| `evidence.plant_active_related_wordnet_min_count` | `ok` | `>= 1` | `11` |
| `evidence.cell_active_related_wordnet_depth2_plus_min_count` | `ok` | `>= 1` | `26` |

## Non-runtime Blockers

- `runtime_phrase_source_policy`
- `runtime_packaging_feasibility`
- `broader_heldout_breadth`
