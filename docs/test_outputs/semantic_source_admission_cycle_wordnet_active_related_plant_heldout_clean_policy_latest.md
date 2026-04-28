# en-es Semantic Source Admission Cycle

- Status: `ok`
- Decision: `promotion_candidate`
- Generated: `2026-04-25T04:49:21Z`

## Gate Summary

- Leakage rejected rows: `0`
- Sense rejected rows: `0`
- Pre-sense merged rows: `79`
- Final admitted rows: `79`
- Semantic contract: `19` / `19`
- Phrase contract: `0` / `19`
- Combined contract status: `review`
- Held-out validation: `ok` / `heldout_pass`
- Held-out cases: `12`
- Held-out harmful / false abstain: `0` / `0`
- Offline lane: `semantic_active_shadow` / `promotion_candidate`
- Runtime publication: `blocked`
- Runtime blockers: `runtime_phrase_source_policy`, `broader_heldout_breadth`, `runtime_packaging_feasibility`

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

- heldout_validation_json: `docs/test_outputs/semantic_source_heldout_validation_latest.json`
- leakage_json: `docs/test_outputs/semantic_source_admission_cycle_wordnet_active_related_plant_heldout_clean_policy_latest_leakage.json`
- leakage_markdown: `docs/test_outputs/semantic_source_admission_cycle_wordnet_active_related_plant_heldout_clean_policy_latest_leakage.md`
- sense_json: `docs/test_outputs/semantic_source_admission_cycle_wordnet_active_related_plant_heldout_clean_policy_latest_sense.json`
- sense_markdown: `docs/test_outputs/semantic_source_admission_cycle_wordnet_active_related_plant_heldout_clean_policy_latest_sense.md`
- merge_json: `docs/test_outputs/semantic_source_admission_cycle_wordnet_active_related_plant_heldout_clean_policy_latest_merge.json`
- merge_markdown: `docs/test_outputs/semantic_source_admission_cycle_wordnet_active_related_plant_heldout_clean_policy_latest_merge.md`
- contract_json: `docs/test_outputs/semantic_source_admission_cycle_wordnet_active_related_plant_heldout_clean_policy_latest_contract.json`
- contract_markdown: `docs/test_outputs/semantic_source_admission_cycle_wordnet_active_related_plant_heldout_clean_policy_latest_contract.md`
- ablation_json: `docs/test_outputs/semantic_source_admission_cycle_wordnet_active_related_plant_heldout_clean_policy_latest_ablation.json`
- ablation_markdown: `docs/test_outputs/semantic_source_admission_cycle_wordnet_active_related_plant_heldout_clean_policy_latest_ablation.md`
