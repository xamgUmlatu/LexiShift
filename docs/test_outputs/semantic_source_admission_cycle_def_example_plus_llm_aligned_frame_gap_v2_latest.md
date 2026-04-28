# en-es Semantic Source Admission Cycle

- Status: `review`
- Decision: `analysis_only`
- Generated: `2026-04-28T21:09:19Z`

## Gate Summary

- Leakage rejected rows: `2`
- Sense rejected rows: `0`
- Pre-sense merged rows: `126`
- Final admitted rows: `126`
- Semantic contract: `19` / `19`
- Phrase contract: `0` / `19`
- Combined contract status: `review`
- Held-out validation: `not_provided` / `not_provided`
- Held-out cases: `0`
- Held-out harmful / false abstain: `0` / `0`
- Offline lane: `semantic_active_shadow` / `analysis_only`
- Runtime publication: `not_assessed`

## Best Ablation

- Source: `cycle_merged`
- Shape: `active_shadow_containment_surface_pos`
- Metrics: `99.0%` accuracy / `97.4%` recall / `0` harmful / `1` false abstains

## Residuals

- Semantic gap families: `0`
- Phrase gap families: `19`
- Harmful ablation cases: `0`
- False-abstain ablation cases: `1`

## Artifacts

- leakage_json: `docs/test_outputs/semantic_source_admission_cycle_def_example_plus_llm_aligned_frame_gap_v2_latest_leakage.json`
- leakage_markdown: `docs/test_outputs/semantic_source_admission_cycle_def_example_plus_llm_aligned_frame_gap_v2_latest_leakage.md`
- sense_json: `docs/test_outputs/semantic_source_admission_cycle_def_example_plus_llm_aligned_frame_gap_v2_latest_sense.json`
- sense_markdown: `docs/test_outputs/semantic_source_admission_cycle_def_example_plus_llm_aligned_frame_gap_v2_latest_sense.md`
- merge_json: `docs/test_outputs/semantic_source_admission_cycle_def_example_plus_llm_aligned_frame_gap_v2_latest_merge.json`
- merge_markdown: `docs/test_outputs/semantic_source_admission_cycle_def_example_plus_llm_aligned_frame_gap_v2_latest_merge.md`
- contract_json: `docs/test_outputs/semantic_source_admission_cycle_def_example_plus_llm_aligned_frame_gap_v2_latest_contract.json`
- contract_markdown: `docs/test_outputs/semantic_source_admission_cycle_def_example_plus_llm_aligned_frame_gap_v2_latest_contract.md`
- ablation_json: `docs/test_outputs/semantic_source_admission_cycle_def_example_plus_llm_aligned_frame_gap_v2_latest_ablation.json`
- ablation_markdown: `docs/test_outputs/semantic_source_admission_cycle_def_example_plus_llm_aligned_frame_gap_v2_latest_ablation.md`
- candidate_admitted_batch_json: `docs/test_outputs/experiments/semantic_example_frame_batches/en-es-def-example-plus-llm-aligned-frame-gap-v2-20260429a_candidate_admitted_normalized_evidence.json`
