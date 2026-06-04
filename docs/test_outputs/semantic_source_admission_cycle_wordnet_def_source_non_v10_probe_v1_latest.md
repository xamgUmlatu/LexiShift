# en-es Semantic Source Admission Cycle

- Status: `ok`
- Decision: `analysis_only`
- Generated: `2026-04-26T03:25:23Z`

## Gate Summary

- Leakage rejected rows: `0`
- Sense rejected rows: `0`
- Pre-sense merged rows: `18`
- Final admitted rows: `18`
- Semantic contract: `8` / `8`
- Phrase contract: `0` / `8`
- Combined contract status: `review`
- Held-out validation: `ok` / `heldout_pass`
- Held-out cases: `16`
- Held-out harmful / false abstain: `0` / `0`
- Offline lane: `semantic_active_shadow` / `analysis_only`
- Runtime publication: `not_assessed`

## Best Ablation

- Source: `cycle_merged`
- Shape: `active_shadow_active_pos_guard`
- Metrics: `83.3%` accuracy / `73.3%` recall / `0` harmful / `4` false abstains

## Residuals

- Semantic gap families: `0`
- Phrase gap families: `8`
- Harmful ablation cases: `0`
- False-abstain ablation cases: `4`

## Artifacts

- heldout_validation_json: `docs/test_outputs/semantic_source_non_v10_heldout_v1_margin005_validation_latest.json`
- leakage_json: `docs/test_outputs/semantic_source_admission_cycle_wordnet_def_source_non_v10_probe_v1_latest_leakage.json`
- leakage_markdown: `docs/test_outputs/semantic_source_admission_cycle_wordnet_def_source_non_v10_probe_v1_latest_leakage.md`
- sense_json: `docs/test_outputs/semantic_source_admission_cycle_wordnet_def_source_non_v10_probe_v1_latest_sense.json`
- sense_markdown: `docs/test_outputs/semantic_source_admission_cycle_wordnet_def_source_non_v10_probe_v1_latest_sense.md`
- merge_json: `docs/test_outputs/semantic_source_admission_cycle_wordnet_def_source_non_v10_probe_v1_latest_merge.json`
- merge_markdown: `docs/test_outputs/semantic_source_admission_cycle_wordnet_def_source_non_v10_probe_v1_latest_merge.md`
- contract_json: `docs/test_outputs/semantic_source_admission_cycle_wordnet_def_source_non_v10_probe_v1_latest_contract.json`
- contract_markdown: `docs/test_outputs/semantic_source_admission_cycle_wordnet_def_source_non_v10_probe_v1_latest_contract.md`
- ablation_json: `docs/test_outputs/semantic_source_admission_cycle_wordnet_def_source_non_v10_probe_v1_latest_ablation.json`
- ablation_markdown: `docs/test_outputs/semantic_source_admission_cycle_wordnet_def_source_non_v10_probe_v1_latest_ablation.md`
- candidate_admitted_batch_json: `docs/test_outputs/experiments/semantic_example_frame_batches/en-es-wordnet-def-source-non-v10-probe-v1-20260426a_admitted_delta_normalized_evidence.json`
