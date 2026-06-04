# en-es Semantic Source Admission Cycle

- Status: `review`
- Decision: `analysis_only`
- Generated: `2026-04-25T01:24:11Z`

## Gate Summary

- Leakage rejected rows: `0`
- Sense rejected rows: `3`
- Pre-sense merged rows: `35`
- Final admitted rows: `32`
- Semantic contract: `14` / `19`
- Phrase contract: `0` / `19`
- Combined contract status: `review`

## Best Ablation

- Source: `cycle_merged`
- Shape: `active_shadow_containment_surface_pos`
- Metrics: `90.5%` accuracy / `86.8%` recall / `4` harmful / `5` false abstains

## Residuals

- Semantic gap families: `5`
- Phrase gap families: `19`
- Harmful ablation cases: `4`
- False-abstain ablation cases: `5`

## Artifacts

- leakage_json: `docs/test_outputs/semantic_source_admission_cycle_reverse_aux_all_v10_latest_leakage.json`
- leakage_markdown: `docs/test_outputs/semantic_source_admission_cycle_reverse_aux_all_v10_latest_leakage.md`
- sense_json: `docs/test_outputs/semantic_source_admission_cycle_reverse_aux_all_v10_latest_sense.json`
- sense_markdown: `docs/test_outputs/semantic_source_admission_cycle_reverse_aux_all_v10_latest_sense.md`
- merge_json: `docs/test_outputs/semantic_source_admission_cycle_reverse_aux_all_v10_latest_merge.json`
- merge_markdown: `docs/test_outputs/semantic_source_admission_cycle_reverse_aux_all_v10_latest_merge.md`
- contract_json: `docs/test_outputs/semantic_source_admission_cycle_reverse_aux_all_v10_latest_contract.json`
- contract_markdown: `docs/test_outputs/semantic_source_admission_cycle_reverse_aux_all_v10_latest_contract.md`
- ablation_json: `docs/test_outputs/semantic_source_admission_cycle_reverse_aux_all_v10_latest_ablation.json`
- ablation_markdown: `docs/test_outputs/semantic_source_admission_cycle_reverse_aux_all_v10_latest_ablation.md`
