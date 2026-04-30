# Semantic Veto Wave7 Source-Class Breadth Runbook

Status: current reference
Role: Execution setup / runbook
Last updated: 2026-05-01
Gate: `wave7_source_class_breadth_v1`

This runbook turns `docs/rulegen/semantic_veto_breadth_expansion_gate.md` into
an executable artifact map. It does not change runtime policy. The current
candidate remains `wave6_auth_frame_raw_sentence_surface_pos_rescue`; the
executed wave7 breadth gate is a failed breadth probe until its harmful
replacement classes are triaged and rerun.

## Preflight

Run this first to confirm the setup inputs and harnesses exist:

```bash
test -f docs/test_inputs/semantic_routing/semantic_veto_wave7_exclusion_inventory_en_es.json
test -f docs/rulegen/semantic_veto_breadth_expansion_gate.md
test -f docs/rulegen/semantic_veto_assumption_ledger.md
test -f docs/rulegen/semantic_veto_archive_consolidation.md
test -f scripts/testing/semantic_non_v10_inventory_candidates_en_es.py
test -f scripts/testing/semantic_non_v10_wave_admission_sweep_en_es.py
test -f scripts/testing/semantic_wiktextract_translation_support_en_es.py
test -f scripts/testing/semantic_non_v10_source_support_conversion_en_es.py
test -f scripts/testing/semantic_translation_sense_evidence_batch_en_es.py
test -f scripts/testing/semantic_wordnet_example_frame_batch_en_es.py
test -f scripts/testing/semantic_source_class_frame_evidence_en_es.py
test -f scripts/testing/semantic_source_admission_cycle_en_es.py
test -f scripts/testing/semantic_source_heldout_validation_en_es.py
test -f scripts/testing/semantic_surface_pos_rescue_policy_validation_en_es.py
test -f scripts/testing/semantic_source_failure_class_mining_en_es.py
test -f docs/test_inputs/semantic_routing_cases/en_es_source_non_v10_wave7_source_class_breadth_v1_heldout_cases.json
test -f docs/test_inputs/semantic_routing_cases/en_es_source_non_v10_wave7_source_class_breadth_v1_phrase_cases.json

python3 -m json.tool \
  docs/test_inputs/semantic_routing/semantic_veto_wave7_exclusion_inventory_en_es.json \
  >/dev/null
```

Current execution result:

- Setup blockers are resolved: the heldout files exist, and
  `semantic_source_class_frame_evidence_en_es.py` produced `7`
  non-authorization source-detectable semantic-class buckets.
- The gate did not pass. The scorer-backed rescue validation reports `7`
  harmful replacements and `5` false abstains across `48` locked cases.
- `docs/test_outputs/semantic_source_failure_class_mining_wave7_source_class_breadth_v1_latest.md`
  is the current starting point for blocker triage.

## Artifact Names

Use these names for the wave7 chain:

- Inventory:
  `docs/test_outputs/semantic_non_v10_inventory_candidates_wave7_source_class_breadth_v1_latest.{json,md}`
- Unsupported upper-bound selection:
  `docs/test_outputs/semantic_non_v10_wave_admission_sweep_wave7_source_class_breadth_v1_upper_bound_latest.{json,md}`
- Unsupported selected dataset:
  `docs/test_outputs/experiments/semantic_non_v10_wave_drafts/en_es_source_non_v10_wave7_source_class_breadth_v1_unsupported_selected_dataset.json`
- Unsupported selected queue:
  `docs/test_outputs/experiments/semantic_non_v10_wave_drafts/semantic_source_non_v10_wave7_source_class_breadth_v1_unsupported_selected_queue_en_es.json`
- Initial source-support conversion audit:
  `docs/test_outputs/semantic_non_v10_source_support_conversion_wave7_source_class_breadth_v1_upper_bound_latest.{json,md}`
- Wiktextract-supported dataset:
  `docs/test_outputs/experiments/semantic_non_v10_wave_drafts/en_es_source_non_v10_wave7_source_class_breadth_v1_wiktextract_supported_dataset.json`
- Wiktextract support report:
  `docs/test_outputs/semantic_wiktextract_translation_support_wave7_source_class_breadth_v1_latest.{json,md}`
- Supported conversion audit:
  `docs/test_outputs/semantic_non_v10_source_support_conversion_wave7_source_class_breadth_v1_wiktextract_supported_latest.{json,md}`
- WordNet source evidence:
  `docs/test_outputs/semantic_wordnet_def_ex_non_v10_wave7_source_class_breadth_v1_latest.{json,md}`
- Translation-sense evidence:
  `docs/test_outputs/semantic_translation_sense_evidence_non_v10_wave7_source_class_breadth_v1_latest.{json,md}`
- Source-class frame evidence:
  `docs/test_outputs/semantic_source_class_frame_evidence_wave7_source_class_breadth_v1_latest.{json,md}`
- Merged evidence composite:
  `docs/test_outputs/semantic_example_frame_batch_merge_wave7_source_class_breadth_v1_latest.{json,md}`
- Source-admission cycle:
  `docs/test_outputs/semantic_source_admission_cycle_wave7_source_class_breadth_v1_latest.{json,md}`
- Active/shadow heldout validation:
  `docs/test_outputs/semantic_source_non_v10_wave7_source_class_breadth_v1_heldout_validation_latest.{json,md}`
- Phrase/no-winner heldout validation:
  `docs/test_outputs/semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_validation_latest.{json,md}`
- Rescue policy validation:
  `docs/test_outputs/semantic_surface_pos_rescue_policy_validation_wave7_source_class_breadth_v1_latest.{json,md}`
- Failure-class mining:
  `docs/test_outputs/semantic_source_failure_class_mining_wave7_source_class_breadth_v1_latest.{json,md}`

## 1. Fresh Inventory

The exclusion manifest already combines v10, seed non-v10, selected wave2,
wave5, and current wave6 triggers.

```bash
python3 scripts/testing/semantic_non_v10_inventory_candidates_en_es.py \
  --existing-inventory-json docs/test_inputs/semantic_routing/semantic_veto_wave7_exclusion_inventory_en_es.json \
  --limit 100 \
  --json-out docs/test_outputs/semantic_non_v10_inventory_candidates_wave7_source_class_breadth_v1_latest.json \
  --markdown-out docs/test_outputs/semantic_non_v10_inventory_candidates_wave7_source_class_breadth_v1_latest.md
```

Stop if the inventory has fewer than `64` ranked candidates after exclusions.

## 2. Unsupported Upper-Bound Selection

This is an upper bound only. It may select forward-only translations that still
need source-support conversion.

```bash
python3 scripts/testing/semantic_non_v10_wave_admission_sweep_en_es.py \
  --candidate-json docs/test_outputs/semantic_non_v10_inventory_candidates_wave7_source_class_breadth_v1_latest.json \
  --wave-size 64 \
  --selection-size 16 \
  --family-pos-strategy any_cross_pos \
  --allow-unsupported-translations \
  --json-out docs/test_outputs/semantic_non_v10_wave_admission_sweep_wave7_source_class_breadth_v1_upper_bound_latest.json \
  --markdown-out docs/test_outputs/semantic_non_v10_wave_admission_sweep_wave7_source_class_breadth_v1_upper_bound_latest.md \
  --selected-dataset-out docs/test_outputs/experiments/semantic_non_v10_wave_drafts/en_es_source_non_v10_wave7_source_class_breadth_v1_unsupported_selected_dataset.json \
  --selected-queue-out docs/test_outputs/experiments/semantic_non_v10_wave_drafts/semantic_source_non_v10_wave7_source_class_breadth_v1_unsupported_selected_queue_en_es.json \
  --selected-dataset-id en_es_source_non_v10_wave7_source_class_breadth_v1_unsupported_selected \
  --selected-queue-id semantic_source_non_v10_wave7_source_class_breadth_v1_unsupported_selected_queue_en_es
```

```bash
python3 scripts/testing/semantic_non_v10_source_support_conversion_en_es.py \
  --dataset-json docs/test_outputs/experiments/semantic_non_v10_wave_drafts/en_es_source_non_v10_wave7_source_class_breadth_v1_unsupported_selected_dataset.json \
  --json-out docs/test_outputs/semantic_non_v10_source_support_conversion_wave7_source_class_breadth_v1_upper_bound_latest.json \
  --markdown-out docs/test_outputs/semantic_non_v10_source_support_conversion_wave7_source_class_breadth_v1_upper_bound_latest.md
```

Stop here if the selected wave cannot reach `16` source-supportable families.

## 3. Wiktextract Support Overlay

```bash
python3 scripts/testing/semantic_wiktextract_translation_support_en_es.py \
  --dataset-json docs/test_outputs/experiments/semantic_non_v10_wave_drafts/en_es_source_non_v10_wave7_source_class_breadth_v1_unsupported_selected_dataset.json \
  --dataset-out docs/test_outputs/experiments/semantic_non_v10_wave_drafts/en_es_source_non_v10_wave7_source_class_breadth_v1_wiktextract_supported_dataset.json \
  --json-out docs/test_outputs/semantic_wiktextract_translation_support_wave7_source_class_breadth_v1_latest.json \
  --markdown-out docs/test_outputs/semantic_wiktextract_translation_support_wave7_source_class_breadth_v1_latest.md
```

```bash
python3 scripts/testing/semantic_non_v10_source_support_conversion_en_es.py \
  --dataset-json docs/test_outputs/experiments/semantic_non_v10_wave_drafts/en_es_source_non_v10_wave7_source_class_breadth_v1_wiktextract_supported_dataset.json \
  --json-out docs/test_outputs/semantic_non_v10_source_support_conversion_wave7_source_class_breadth_v1_wiktextract_supported_latest.json \
  --markdown-out docs/test_outputs/semantic_non_v10_source_support_conversion_wave7_source_class_breadth_v1_wiktextract_supported_latest.md
```

Stop here if the supported conversion audit is not
`selected_wave_source_supported`.

## 4. Evidence Construction

Build WordNet evidence, translation-sense evidence, and deterministic
source-class frame evidence. The class detector fires only from source gloss,
translation-sense, or source example text.

```bash
python3 scripts/testing/semantic_wordnet_example_frame_batch_en_es.py \
  --queue-json docs/test_outputs/experiments/semantic_non_v10_wave_drafts/semantic_source_non_v10_wave7_source_class_breadth_v1_unsupported_selected_queue_en_es.json \
  --dataset docs/test_outputs/experiments/semantic_non_v10_wave_drafts/en_es_source_non_v10_wave7_source_class_breadth_v1_wiktextract_supported_dataset.json \
  --scope prompt_queue \
  --evidence-mode definition_and_example \
  --max-rows-per-sense 2 \
  --run-id wordnet-def-ex-non-v10-wave7-source-class-breadth-v1-latest \
  --intake-batch-out docs/test_outputs/experiments/semantic_example_frame_batches/en-es-wordnet-def-ex-non-v10-wave7-source-class-breadth-v1-latest_intake_batch.json \
  --normalized-batch-out docs/test_outputs/experiments/semantic_example_frame_batches/en-es-wordnet-def-ex-non-v10-wave7-source-class-breadth-v1-latest_normalized_evidence.json \
  --json-out docs/test_outputs/semantic_wordnet_def_ex_non_v10_wave7_source_class_breadth_v1_latest.json \
  --markdown-out docs/test_outputs/semantic_wordnet_def_ex_non_v10_wave7_source_class_breadth_v1_latest.md
```

```bash
python3 scripts/testing/semantic_translation_sense_evidence_batch_en_es.py \
  --dataset docs/test_outputs/experiments/semantic_non_v10_wave_drafts/en_es_source_non_v10_wave7_source_class_breadth_v1_wiktextract_supported_dataset.json \
  --run-id translation-sense-non-v10-wave7-source-class-breadth-v1-latest \
  --normalized-batch-out docs/test_outputs/experiments/semantic_example_frame_batches/en-es-translation-sense-non-v10-wave7-source-class-breadth-v1-latest_normalized_evidence.json \
  --json-out docs/test_outputs/semantic_translation_sense_evidence_non_v10_wave7_source_class_breadth_v1_latest.json \
  --markdown-out docs/test_outputs/semantic_translation_sense_evidence_non_v10_wave7_source_class_breadth_v1_latest.md
```

```bash
python3 scripts/testing/semantic_source_class_frame_evidence_en_es.py \
  --dataset docs/test_outputs/experiments/semantic_non_v10_wave_drafts/en_es_source_non_v10_wave7_source_class_breadth_v1_wiktextract_supported_dataset.json \
  --run-id source-class-frame-non-v10-wave7-source-class-breadth-v1-latest \
  --normalized-batch-out docs/test_outputs/experiments/semantic_example_frame_batches/en-es-source-class-frame-non-v10-wave7-source-class-breadth-v1-latest_normalized_evidence.json \
  --json-out docs/test_outputs/semantic_source_class_frame_evidence_wave7_source_class_breadth_v1_latest.json \
  --markdown-out docs/test_outputs/semantic_source_class_frame_evidence_wave7_source_class_breadth_v1_latest.md
```

```bash
python3 scripts/testing/semantic_example_frame_batch_merge_en_es.py \
  --base-batch-json docs/test_outputs/experiments/semantic_example_frame_batches/en-es-wordnet-def-ex-non-v10-wave7-source-class-breadth-v1-latest_normalized_evidence.json \
  --add-batch-json docs/test_outputs/experiments/semantic_example_frame_batches/en-es-translation-sense-non-v10-wave7-source-class-breadth-v1-latest_normalized_evidence.json \
  --add-batch-json docs/test_outputs/experiments/semantic_example_frame_batches/en-es-source-class-frame-non-v10-wave7-source-class-breadth-v1-latest_normalized_evidence.json \
  --batch-id en-es:wave7-source-class-breadth-v1:evidence-composite \
  --source-id wordnet_translation_sense_source_class_non_v10_wave7_source_class_breadth_v1 \
  --merged-batch-out docs/test_outputs/experiments/semantic_example_frame_batches/en-es-wave7-source-class-breadth-v1-evidence-composite_normalized_evidence.json \
  --json-out docs/test_outputs/semantic_example_frame_batch_merge_wave7_source_class_breadth_v1_latest.json \
  --markdown-out docs/test_outputs/semantic_example_frame_batch_merge_wave7_source_class_breadth_v1_latest.md
```

## 5. Admission And Validation

After the supported dataset, evidence batches, class detector rows, and locked
heldout files exist, run source admission and validation:

```bash
python3 scripts/testing/semantic_source_admission_cycle_en_es.py \
  --dataset docs/test_outputs/experiments/semantic_non_v10_wave_drafts/en_es_source_non_v10_wave7_source_class_breadth_v1_wiktextract_supported_dataset.json \
  --queue-json docs/test_outputs/experiments/semantic_non_v10_wave_drafts/semantic_source_non_v10_wave7_source_class_breadth_v1_unsupported_selected_queue_en_es.json \
  --required-family-json docs/test_outputs/experiments/semantic_non_v10_wave_drafts/en_es_source_non_v10_wave7_source_class_breadth_v1_wiktextract_supported_dataset.json \
  --empty-base \
  --candidate-batch-json docs/test_outputs/experiments/semantic_example_frame_batches/en-es-wave7-source-class-breadth-v1-evidence-composite_normalized_evidence.json \
  --batch-id en-es:wordnet-translation-sense-source-class:non-v10-wave7-source-class-breadth-v1:cycle \
  --source-id wordnet_translation_sense_source_class_non_v10_wave7_source_class_breadth_v1 \
  --skip-ablation \
  --json-out docs/test_outputs/semantic_source_admission_cycle_wave7_source_class_breadth_v1_latest.json \
  --markdown-out docs/test_outputs/semantic_source_admission_cycle_wave7_source_class_breadth_v1_latest.md \
  --filtered-batch-out docs/test_outputs/experiments/semantic_example_frame_batches/en-es-wave7-source-class-breadth-v1-latest_cycle_filtered_normalized_evidence.json \
  --sense-batch-out docs/test_outputs/experiments/semantic_example_frame_batches/en-es-wave7-source-class-breadth-v1-latest_cycle_sense_admitted_normalized_evidence.json \
  --merged-batch-out docs/test_outputs/experiments/semantic_example_frame_batches/en-es-wave7-source-class-breadth-v1-latest_cycle_merged_normalized_evidence.json \
  --candidate-admitted-batch-out docs/test_outputs/experiments/semantic_example_frame_batches/en-es-wave7-source-class-breadth-v1-latest_admitted_delta_normalized_evidence.json
```

```bash
python3 scripts/testing/semantic_source_heldout_validation_en_es.py \
  --base-dataset docs/test_outputs/experiments/semantic_non_v10_wave_drafts/en_es_source_non_v10_wave7_source_class_breadth_v1_wiktextract_supported_dataset.json \
  --heldout-cases docs/test_inputs/semantic_routing_cases/en_es_source_non_v10_wave7_source_class_breadth_v1_heldout_cases.json \
  --evidence-batch-json docs/test_outputs/experiments/semantic_example_frame_batches/en-es-wave7-source-class-breadth-v1-latest_cycle_sense_admitted_normalized_evidence.json \
  --scorer-id sentence_transformer_cosine \
  --context-view raw_sentence \
  --min-active-score 0 \
  --min-margin 0 \
  --phrase-prototype-margin 0.02 \
  --decision-shape active_shadow_phrase_semantic_surface_pos \
  --json-out docs/test_outputs/semantic_source_non_v10_wave7_source_class_breadth_v1_heldout_validation_latest.json \
  --markdown-out docs/test_outputs/semantic_source_non_v10_wave7_source_class_breadth_v1_heldout_validation_latest.md \
  --fail-on-review
```

```bash
python3 scripts/testing/semantic_source_heldout_validation_en_es.py \
  --base-dataset docs/test_outputs/experiments/semantic_non_v10_wave_drafts/en_es_source_non_v10_wave7_source_class_breadth_v1_wiktextract_supported_dataset.json \
  --heldout-cases docs/test_inputs/semantic_routing_cases/en_es_source_non_v10_wave7_source_class_breadth_v1_phrase_cases.json \
  --evidence-batch-json docs/test_outputs/experiments/semantic_example_frame_batches/en-es-wave7-source-class-breadth-v1-latest_cycle_sense_admitted_normalized_evidence.json \
  --scorer-id sentence_transformer_cosine \
  --context-view raw_sentence \
  --min-active-score 0 \
  --min-margin 0 \
  --phrase-prototype-margin 0.02 \
  --decision-shape active_shadow_phrase_semantic_surface_pos \
  --json-out docs/test_outputs/semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_validation_latest.json \
  --markdown-out docs/test_outputs/semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_validation_latest.md \
  --fail-on-review
```

```bash
python3 scripts/testing/semantic_surface_pos_rescue_policy_validation_en_es.py \
  --base-dataset docs/test_outputs/experiments/semantic_non_v10_wave_drafts/en_es_source_non_v10_wave7_source_class_breadth_v1_wiktextract_supported_dataset.json \
  --active-heldout-cases docs/test_inputs/semantic_routing_cases/en_es_source_non_v10_wave7_source_class_breadth_v1_heldout_cases.json \
  --phrase-heldout-cases docs/test_inputs/semantic_routing_cases/en_es_source_non_v10_wave7_source_class_breadth_v1_phrase_cases.json \
  --evidence-batch-json docs/test_outputs/experiments/semantic_example_frame_batches/en-es-wave7-source-class-breadth-v1-latest_cycle_sense_admitted_normalized_evidence.json \
  --scorer-id sentence_transformer_cosine \
  --context-view raw_sentence \
  --min-active-score 0 \
  --min-margin 0 \
  --phrase-prototype-margin 0.02 \
  --decision-shape active_shadow_phrase_semantic_surface_pos \
  --rescue-min-active-score 0.52 \
  --noun-max-phrase-lead none \
  --modifier-max-phrase-lead 0.02 \
  --json-out docs/test_outputs/semantic_surface_pos_rescue_policy_validation_wave7_source_class_breadth_v1_latest.json \
  --markdown-out docs/test_outputs/semantic_surface_pos_rescue_policy_validation_wave7_source_class_breadth_v1_latest.md \
  --fail-on-review
```

```bash
python3 scripts/testing/semantic_source_failure_class_mining_en_es.py \
  --primary-admission-json docs/test_outputs/semantic_source_admission_cycle_wave7_source_class_breadth_v1_latest.json \
  --primary-heldout-json docs/test_outputs/semantic_source_non_v10_wave7_source_class_breadth_v1_heldout_validation_latest.json \
  --additional-heldout-json docs/test_outputs/semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_validation_latest.json \
  --source-report-json docs/test_outputs/semantic_wiktextract_translation_support_wave7_source_class_breadth_v1_latest.json \
  --source-report-json docs/test_outputs/semantic_source_class_frame_evidence_wave7_source_class_breadth_v1_latest.json \
  --source-report-json docs/test_outputs/semantic_wordnet_def_ex_non_v10_wave7_source_class_breadth_v1_latest.json \
  --source-report-json docs/test_outputs/semantic_translation_sense_evidence_non_v10_wave7_source_class_breadth_v1_latest.json \
  --min-broad-family-count 16 \
  --min-broad-case-count 48 \
  --json-out docs/test_outputs/semantic_source_failure_class_mining_wave7_source_class_breadth_v1_latest.json \
  --markdown-out docs/test_outputs/semantic_source_failure_class_mining_wave7_source_class_breadth_v1_latest.md
```

## Completion

After the wave7 evidence chain exists:

1. Classify every wave7 artifact in
   `docs/test_inputs/semantic_veto_system_registry_en_es.json`.
2. Regenerate `docs/test_outputs/semantic_veto_system_registry_latest.{json,md}`.
3. Update `docs/rulegen/semantic_veto_reconciliation_workstream.md` with the
   pass/fail read and next action.
4. Run:

```bash
python3 scripts/testing/semantic_veto_system_registry_summary.py --fail-on-issue

PYTHONPATH=apps/gui/src:core python3 -m pytest \
  core/tests/dev/test_semantic_veto_system_registry_summary.py

python3 scripts/dev/check_doc_references.py

git diff --check
```
