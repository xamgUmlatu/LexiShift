# en-es Semantic Source Admission Cycle

- Status: `review`
- Decision: `analysis_only`
- Generated: `2026-04-25T05:28:03Z`

## Gate Summary

- Leakage rejected rows: `29`
- Sense rejected rows: `3`
- Pre-sense merged rows: `136`
- Final admitted rows: `133`
- Semantic contract: `19` / `19`
- Phrase contract: `0` / `19`
- Combined contract status: `review`
- Held-out validation: `ok` / `heldout_pass`
- Held-out cases: `38`
- Held-out harmful / false abstain: `0` / `0`
- Offline lane: `semantic_active_shadow` / `analysis_only`
- Runtime publication: `not_assessed`

## Best Ablation

- Source: `cycle_merged`
- Shape: `active_shadow_containment_surface_pos`
- Metrics: `100.0%` accuracy / `100.0%` recall / `0` harmful / `0` false abstains

## Residuals

- Semantic gap families: `0`
- Phrase gap families: `19`
- Harmful ablation cases: `0`
- False-abstain ablation cases: `0`

## Artifacts

- heldout_validation_json: `docs/test_outputs/semantic_source_heldout_validation_v2_latest.json`
- leakage_json: `docs/test_outputs/semantic_source_admission_cycle_wordnet_active_related_plant_cell_depth3_heldout_v2_raw_latest_leakage.json`
- leakage_markdown: `docs/test_outputs/semantic_source_admission_cycle_wordnet_active_related_plant_cell_depth3_heldout_v2_raw_latest_leakage.md`
- sense_json: `docs/test_outputs/semantic_source_admission_cycle_wordnet_active_related_plant_cell_depth3_heldout_v2_raw_latest_sense.json`
- sense_markdown: `docs/test_outputs/semantic_source_admission_cycle_wordnet_active_related_plant_cell_depth3_heldout_v2_raw_latest_sense.md`
- merge_json: `docs/test_outputs/semantic_source_admission_cycle_wordnet_active_related_plant_cell_depth3_heldout_v2_raw_latest_merge.json`
- merge_markdown: `docs/test_outputs/semantic_source_admission_cycle_wordnet_active_related_plant_cell_depth3_heldout_v2_raw_latest_merge.md`
- contract_json: `docs/test_outputs/semantic_source_admission_cycle_wordnet_active_related_plant_cell_depth3_heldout_v2_raw_latest_contract.json`
- contract_markdown: `docs/test_outputs/semantic_source_admission_cycle_wordnet_active_related_plant_cell_depth3_heldout_v2_raw_latest_contract.md`
- ablation_json: `docs/test_outputs/semantic_source_admission_cycle_wordnet_active_related_plant_cell_depth3_heldout_v2_raw_latest_ablation.json`
- ablation_markdown: `docs/test_outputs/semantic_source_admission_cycle_wordnet_active_related_plant_cell_depth3_heldout_v2_raw_latest_ablation.md`
- candidate_admitted_batch_json: `docs/test_outputs/experiments/semantic_example_frame_batches/en-es-wordnet-cell-active-related-depth3-heldout-v2-20260425a_admitted_delta_normalized_evidence.json`
