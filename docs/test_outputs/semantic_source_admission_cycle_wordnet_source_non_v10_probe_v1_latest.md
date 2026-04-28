# en-es Semantic Source Admission Cycle

- Status: `review`
- Decision: `analysis_only`
- Generated: `2026-04-26T03:21:02Z`

## Gate Summary

- Leakage rejected rows: `0`
- Sense rejected rows: `4`
- Pre-sense merged rows: `18`
- Final admitted rows: `14`
- Semantic contract: `4` / `8`
- Phrase contract: `0` / `8`
- Combined contract status: `review`
- Held-out validation: `not_provided` / `not_provided`
- Held-out cases: `0`
- Held-out harmful / false abstain: `0` / `0`
- Offline lane: `semantic_active_shadow` / `analysis_only`
- Runtime publication: `not_assessed`

## Best Ablation

- Source: `cycle_merged`
- Shape: `active_shadow_active_pos_guard`
- Metrics: `70.8%` accuracy / `53.3%` recall / `0` harmful / `7` false abstains

## Residuals

- Semantic gap families: `4`
- Phrase gap families: `8`
- Harmful ablation cases: `0`
- False-abstain ablation cases: `7`

## Artifacts

- leakage_json: `docs/test_outputs/semantic_source_admission_cycle_wordnet_source_non_v10_probe_v1_latest_leakage.json`
- leakage_markdown: `docs/test_outputs/semantic_source_admission_cycle_wordnet_source_non_v10_probe_v1_latest_leakage.md`
- sense_json: `docs/test_outputs/semantic_source_admission_cycle_wordnet_source_non_v10_probe_v1_latest_sense.json`
- sense_markdown: `docs/test_outputs/semantic_source_admission_cycle_wordnet_source_non_v10_probe_v1_latest_sense.md`
- merge_json: `docs/test_outputs/semantic_source_admission_cycle_wordnet_source_non_v10_probe_v1_latest_merge.json`
- merge_markdown: `docs/test_outputs/semantic_source_admission_cycle_wordnet_source_non_v10_probe_v1_latest_merge.md`
- contract_json: `docs/test_outputs/semantic_source_admission_cycle_wordnet_source_non_v10_probe_v1_latest_contract.json`
- contract_markdown: `docs/test_outputs/semantic_source_admission_cycle_wordnet_source_non_v10_probe_v1_latest_contract.md`
- ablation_json: `docs/test_outputs/semantic_source_admission_cycle_wordnet_source_non_v10_probe_v1_latest_ablation.json`
- ablation_markdown: `docs/test_outputs/semantic_source_admission_cycle_wordnet_source_non_v10_probe_v1_latest_ablation.md`
- candidate_admitted_batch_json: `docs/test_outputs/experiments/semantic_example_frame_batches/en-es-wordnet-source-non-v10-probe-v1-20260426a_admitted_delta_normalized_evidence.json`
