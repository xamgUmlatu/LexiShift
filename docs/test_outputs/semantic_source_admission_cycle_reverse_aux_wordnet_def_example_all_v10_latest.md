# en-es Semantic Source Admission Cycle

- Status: `review`
- Decision: `analysis_only`
- Generated: `2026-04-25T01:42:40Z`

## Gate Summary

- Leakage rejected rows: `1`
- Sense rejected rows: `6`
- Pre-sense merged rows: `93`
- Final admitted rows: `87`
- Semantic contract: `18` / `19`
- Phrase contract: `0` / `19`
- Combined contract status: `review`

## Best Ablation

- Source: `cycle_merged`
- Shape: `active_shadow_containment_surface_pos`
- Metrics: `90.5%` accuracy / `81.6%` recall / `2` harmful / `7` false abstains

## Residuals

- Semantic gap families: `1`
- Phrase gap families: `19`
- Harmful ablation cases: `2`
- False-abstain ablation cases: `7`

## Artifacts

- leakage_json: `docs/test_outputs/semantic_source_admission_cycle_reverse_aux_wordnet_def_example_all_v10_latest_leakage.json`
- leakage_markdown: `docs/test_outputs/semantic_source_admission_cycle_reverse_aux_wordnet_def_example_all_v10_latest_leakage.md`
- sense_json: `docs/test_outputs/semantic_source_admission_cycle_reverse_aux_wordnet_def_example_all_v10_latest_sense.json`
- sense_markdown: `docs/test_outputs/semantic_source_admission_cycle_reverse_aux_wordnet_def_example_all_v10_latest_sense.md`
- merge_json: `docs/test_outputs/semantic_source_admission_cycle_reverse_aux_wordnet_def_example_all_v10_latest_merge.json`
- merge_markdown: `docs/test_outputs/semantic_source_admission_cycle_reverse_aux_wordnet_def_example_all_v10_latest_merge.md`
- contract_json: `docs/test_outputs/semantic_source_admission_cycle_reverse_aux_wordnet_def_example_all_v10_latest_contract.json`
- contract_markdown: `docs/test_outputs/semantic_source_admission_cycle_reverse_aux_wordnet_def_example_all_v10_latest_contract.md`
- ablation_json: `docs/test_outputs/semantic_source_admission_cycle_reverse_aux_wordnet_def_example_all_v10_latest_ablation.json`
- ablation_markdown: `docs/test_outputs/semantic_source_admission_cycle_reverse_aux_wordnet_def_example_all_v10_latest_ablation.md`
