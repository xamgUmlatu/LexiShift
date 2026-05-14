# Semantic Veto Current Wave6 Rerun Chain

Status: active rerun runbook
Role: Runbook / operational
Last updated: 2026-05-14
Last verified: 2026-04-30
Source-of-truth: rerun runbook only; current semantic-veto policy truth lives in code, generated artifacts, registry summaries, and canonical semantic-veto docs.

This runbook rebuilds the current `wave6_auth_frame_raw_sentence_surface_pos_rescue`
research lane from tracked inputs. It does not promote a runtime policy.

Expected notable statuses:

- `semantic_source_admission_cycle_alt_phrase_non_v10_wave6_wiktextract_supported_latest`
  returns `review` because the leakage audit filters alternate-sense phrase rows.
- `semantic_source_non_v10_wave6_auth_frame_surface_pos_raw_sentence_phrase_margin000_phrase002_validation_latest`
  returns `review` before rescue replay because two phrase/no-winner cases remain harmful.
- `semantic_surface_pos_rescue_policy_sweep_non_v10_wave6_auth_frame_raw_sentence_latest`
  returns `ok` as fixed-trace replay evidence only.
- `semantic_surface_pos_rescue_policy_validation_non_v10_wave6_auth_frame_raw_sentence_latest`
  returns `ok` as scorer-backed offline confirmation for the recommended rescue
  policy, still not runtime promotion evidence.
- `semantic_source_failure_class_mining_non_v10_wave6_auth_frame_latest` returns
  `review` to keep promotion blocked until broader semantic-class breadth is
  tested.

## 1. Translation-Sense Adapter

```bash
python3 scripts/testing/semantic_translation_sense_evidence_batch_en_es.py
```

```bash
python3 scripts/testing/semantic_source_admission_cycle_en_es.py \
  --dataset docs/test_outputs/experiments/semantic_non_v10_wave_drafts/en_es_source_non_v10_wave6_anypos_wiktextract_supported_v1_dataset.json \
  --required-family-json docs/test_outputs/experiments/semantic_non_v10_wave_drafts/en_es_source_non_v10_wave6_anypos_wiktextract_supported_v1_dataset.json \
  --base-batch-json docs/test_outputs/experiments/semantic_example_frame_batches/en-es-wordnet-def-ex-non-v10-wave6-wiktextract-supported-v1-latest_cycle_sense_admitted_normalized_evidence.json \
  --candidate-batch-json docs/test_outputs/experiments/semantic_example_frame_batches/en-es-translation-sense-non-v10-wave6-wiktextract-supported-v1-latest_normalized_evidence.json \
  --batch-id en-es:wordnet-plus-translation-sense:non-v10-wave6-wiktextract-supported-v1:cycle \
  --source-id wordnet_plus_translation_sense_non_v10_wave6_wiktextract_supported_v1 \
  --skip-ablation \
  --json-out docs/test_outputs/semantic_source_admission_cycle_translation_sense_non_v10_wave6_wiktextract_supported_latest.json \
  --markdown-out docs/test_outputs/semantic_source_admission_cycle_translation_sense_non_v10_wave6_wiktextract_supported_latest.md \
  --filtered-batch-out docs/test_outputs/experiments/semantic_example_frame_batches/en-es-translation-sense-non-v10-wave6-wiktextract-supported-v1-latest_cycle_filtered_normalized_evidence.json \
  --sense-batch-out docs/test_outputs/experiments/semantic_example_frame_batches/en-es-translation-sense-non-v10-wave6-wiktextract-supported-v1-latest_cycle_sense_admitted_normalized_evidence.json \
  --merged-batch-out docs/test_outputs/experiments/semantic_example_frame_batches/en-es-translation-sense-non-v10-wave6-wiktextract-supported-v1-latest_cycle_merged_normalized_evidence.json \
  --candidate-admitted-batch-out docs/test_outputs/experiments/semantic_example_frame_batches/en-es-translation-sense-non-v10-wave6-wiktextract-supported-v1-latest_admitted_delta_normalized_evidence.json
```

## 2. Alternate-Sense Phrase Control

```bash
python3 scripts/testing/semantic_wordnet_alternate_sense_phrase_evidence_en_es.py
```

```bash
python3 scripts/testing/semantic_source_admission_cycle_en_es.py \
  --dataset docs/test_outputs/experiments/semantic_non_v10_wave_drafts/en_es_source_non_v10_wave6_anypos_wiktextract_supported_v1_dataset.json \
  --required-family-json docs/test_outputs/experiments/semantic_non_v10_wave_drafts/en_es_source_non_v10_wave6_anypos_wiktextract_supported_v1_dataset.json \
  --base-batch-json docs/test_outputs/experiments/semantic_example_frame_batches/en-es-translation-sense-non-v10-wave6-wiktextract-supported-v1-latest_cycle_sense_admitted_normalized_evidence.json \
  --candidate-batch-json docs/test_outputs/experiments/semantic_example_frame_batches/en-es-wordnet-alternate-sense-phrase-non-v10-wave6-wiktextract-supported-v1-latest_normalized_evidence.json \
  --batch-id en-es:wordnet-translation-plus-alt-phrase:non-v10-wave6-wiktextract-supported-v1:cycle \
  --source-id wordnet_translation_alt_phrase_non_v10_wave6_wiktextract_supported_v1 \
  --skip-ablation \
  --json-out docs/test_outputs/semantic_source_admission_cycle_alt_phrase_non_v10_wave6_wiktextract_supported_latest.json \
  --markdown-out docs/test_outputs/semantic_source_admission_cycle_alt_phrase_non_v10_wave6_wiktextract_supported_latest.md \
  --filtered-batch-out docs/test_outputs/experiments/semantic_example_frame_batches/en-es-wordnet-alternate-sense-phrase-non-v10-wave6-wiktextract-supported-v1-latest_cycle_filtered_normalized_evidence.json \
  --sense-batch-out docs/test_outputs/experiments/semantic_example_frame_batches/en-es-wordnet-alternate-sense-phrase-non-v10-wave6-wiktextract-supported-v1-latest_cycle_sense_admitted_normalized_evidence.json \
  --merged-batch-out docs/test_outputs/experiments/semantic_example_frame_batches/en-es-wordnet-alternate-sense-phrase-non-v10-wave6-wiktextract-supported-v1-latest_cycle_merged_normalized_evidence.json \
  --candidate-admitted-batch-out docs/test_outputs/experiments/semantic_example_frame_batches/en-es-wordnet-alternate-sense-phrase-non-v10-wave6-wiktextract-supported-v1-latest_admitted_delta_normalized_evidence.json
```

```bash
python3 scripts/testing/semantic_source_heldout_validation_en_es.py \
  --base-dataset docs/test_outputs/experiments/semantic_non_v10_wave_drafts/en_es_source_non_v10_wave6_anypos_wiktextract_supported_v1_dataset.json \
  --heldout-cases docs/test_inputs/semantic_routing_cases/en_es_source_non_v10_wave6_wiktextract_supported_heldout_cases_v1.json \
  --evidence-batch-json docs/test_outputs/experiments/semantic_example_frame_batches/en-es-wordnet-alternate-sense-phrase-non-v10-wave6-wiktextract-supported-v1-latest_cycle_sense_admitted_normalized_evidence.json \
  --scorer-id sentence_transformer_cosine \
  --context-view raw_sentence \
  --min-active-score 0 \
  --min-margin 0 \
  --phrase-prototype-margin 0.02 \
  --decision-shape active_shadow_phrase_semantic_surface_pos \
  --json-out docs/test_outputs/semantic_source_non_v10_wave6_alt_phrase_semantic_surface_pos_raw_sentence_heldout_margin000_phrase002_validation_latest.json \
  --markdown-out docs/test_outputs/semantic_source_non_v10_wave6_alt_phrase_semantic_surface_pos_raw_sentence_heldout_margin000_phrase002_validation_latest.md
```

```bash
python3 scripts/testing/semantic_source_heldout_validation_en_es.py \
  --base-dataset docs/test_outputs/experiments/semantic_non_v10_wave_drafts/en_es_source_non_v10_wave6_anypos_wiktextract_supported_v1_dataset.json \
  --heldout-cases docs/test_inputs/semantic_routing_cases/en_es_source_non_v10_wave6_wiktextract_supported_phrase_cases_v1.json \
  --evidence-batch-json docs/test_outputs/experiments/semantic_example_frame_batches/en-es-wordnet-alternate-sense-phrase-non-v10-wave6-wiktextract-supported-v1-latest_cycle_sense_admitted_normalized_evidence.json \
  --scorer-id sentence_transformer_cosine \
  --context-view raw_sentence \
  --min-active-score 0 \
  --min-margin 0 \
  --phrase-prototype-margin 0.02 \
  --decision-shape active_shadow_phrase_semantic_surface_pos \
  --json-out docs/test_outputs/semantic_source_non_v10_wave6_alt_phrase_semantic_surface_pos_raw_sentence_phrase_margin000_phrase002_validation_latest.json \
  --markdown-out docs/test_outputs/semantic_source_non_v10_wave6_alt_phrase_semantic_surface_pos_raw_sentence_phrase_margin000_phrase002_validation_latest.md
```

```bash
python3 scripts/testing/semantic_surface_pos_rescue_policy_sweep_en_es.py \
  --active-report-json docs/test_outputs/semantic_source_non_v10_wave6_alt_phrase_semantic_surface_pos_raw_sentence_heldout_margin000_phrase002_validation_latest.json \
  --phrase-report-json docs/test_outputs/semantic_source_non_v10_wave6_alt_phrase_semantic_surface_pos_raw_sentence_phrase_margin000_phrase002_validation_latest.json \
  --min-margin-grid 0 \
  --phrase-prototype-margin-grid 0.02 \
  --json-out docs/test_outputs/semantic_surface_pos_rescue_policy_sweep_non_v10_wave6_raw_sentence_latest.json \
  --markdown-out docs/test_outputs/semantic_surface_pos_rescue_policy_sweep_non_v10_wave6_raw_sentence_latest.md
```

## 3. Authorization-Frame Candidate

```bash
python3 scripts/testing/semantic_authorization_frame_evidence_en_es.py
```

```bash
python3 scripts/testing/semantic_source_admission_cycle_en_es.py \
  --dataset docs/test_outputs/experiments/semantic_non_v10_wave_drafts/en_es_source_non_v10_wave6_anypos_wiktextract_supported_v1_dataset.json \
  --required-family-json docs/test_outputs/experiments/semantic_non_v10_wave_drafts/en_es_source_non_v10_wave6_anypos_wiktextract_supported_v1_dataset.json \
  --base-batch-json docs/test_outputs/experiments/semantic_example_frame_batches/en-es-wordnet-alternate-sense-phrase-non-v10-wave6-wiktextract-supported-v1-latest_cycle_sense_admitted_normalized_evidence.json \
  --candidate-batch-json docs/test_outputs/experiments/semantic_example_frame_batches/en-es-authorization-frame-non-v10-wave6-wiktextract-supported-v1-latest_normalized_evidence.json \
  --batch-id en-es:wordnet-translation-alt-phrase-plus-auth-frame:non-v10-wave6-wiktextract-supported-v1:cycle:sense-admitted \
  --source-id wordnet_translation_alt_phrase_auth_frame_non_v10_wave6_wiktextract_supported_v1 \
  --skip-ablation \
  --json-out docs/test_outputs/semantic_source_admission_cycle_auth_frame_non_v10_wave6_wiktextract_supported_latest.json \
  --markdown-out docs/test_outputs/semantic_source_admission_cycle_auth_frame_non_v10_wave6_wiktextract_supported_latest.md \
  --filtered-batch-out docs/test_outputs/experiments/semantic_example_frame_batches/en-es-authorization-frame-non-v10-wave6-wiktextract-supported-v1-latest_cycle_filtered_normalized_evidence.json \
  --sense-batch-out docs/test_outputs/experiments/semantic_example_frame_batches/en-es-authorization-frame-non-v10-wave6-wiktextract-supported-v1-latest_cycle_sense_admitted_normalized_evidence.json \
  --merged-batch-out docs/test_outputs/experiments/semantic_example_frame_batches/en-es-authorization-frame-non-v10-wave6-wiktextract-supported-v1-latest_cycle_merged_normalized_evidence.json \
  --candidate-admitted-batch-out docs/test_outputs/experiments/semantic_example_frame_batches/en-es-authorization-frame-non-v10-wave6-wiktextract-supported-v1-latest_admitted_delta_normalized_evidence.json
```

```bash
python3 scripts/testing/semantic_source_heldout_validation_en_es.py \
  --base-dataset docs/test_outputs/experiments/semantic_non_v10_wave_drafts/en_es_source_non_v10_wave6_anypos_wiktextract_supported_v1_dataset.json \
  --heldout-cases docs/test_inputs/semantic_routing_cases/en_es_source_non_v10_wave6_wiktextract_supported_heldout_cases_v1.json \
  --evidence-batch-json docs/test_outputs/experiments/semantic_example_frame_batches/en-es-authorization-frame-non-v10-wave6-wiktextract-supported-v1-latest_cycle_sense_admitted_normalized_evidence.json \
  --scorer-id sentence_transformer_cosine \
  --context-view raw_sentence \
  --min-active-score 0 \
  --min-margin 0 \
  --phrase-prototype-margin 0.02 \
  --decision-shape active_shadow_phrase_semantic_surface_pos \
  --json-out docs/test_outputs/semantic_source_non_v10_wave6_auth_frame_surface_pos_raw_sentence_heldout_margin000_phrase002_validation_latest.json \
  --markdown-out docs/test_outputs/semantic_source_non_v10_wave6_auth_frame_surface_pos_raw_sentence_heldout_margin000_phrase002_validation_latest.md
```

```bash
python3 scripts/testing/semantic_source_heldout_validation_en_es.py \
  --base-dataset docs/test_outputs/experiments/semantic_non_v10_wave_drafts/en_es_source_non_v10_wave6_anypos_wiktextract_supported_v1_dataset.json \
  --heldout-cases docs/test_inputs/semantic_routing_cases/en_es_source_non_v10_wave6_wiktextract_supported_phrase_cases_v1.json \
  --evidence-batch-json docs/test_outputs/experiments/semantic_example_frame_batches/en-es-authorization-frame-non-v10-wave6-wiktextract-supported-v1-latest_cycle_sense_admitted_normalized_evidence.json \
  --scorer-id sentence_transformer_cosine \
  --context-view raw_sentence \
  --min-active-score 0 \
  --min-margin 0 \
  --phrase-prototype-margin 0.02 \
  --decision-shape active_shadow_phrase_semantic_surface_pos \
  --json-out docs/test_outputs/semantic_source_non_v10_wave6_auth_frame_surface_pos_raw_sentence_phrase_margin000_phrase002_validation_latest.json \
  --markdown-out docs/test_outputs/semantic_source_non_v10_wave6_auth_frame_surface_pos_raw_sentence_phrase_margin000_phrase002_validation_latest.md
```

```bash
python3 scripts/testing/semantic_surface_pos_rescue_policy_sweep_en_es.py \
  --active-report-json docs/test_outputs/semantic_source_non_v10_wave6_auth_frame_surface_pos_raw_sentence_heldout_margin000_phrase002_validation_latest.json \
  --phrase-report-json docs/test_outputs/semantic_source_non_v10_wave6_auth_frame_surface_pos_raw_sentence_phrase_margin000_phrase002_validation_latest.json \
  --min-margin-grid 0 \
  --phrase-prototype-margin-grid 0.02 \
  --json-out docs/test_outputs/semantic_surface_pos_rescue_policy_sweep_non_v10_wave6_auth_frame_raw_sentence_latest.json \
  --markdown-out docs/test_outputs/semantic_surface_pos_rescue_policy_sweep_non_v10_wave6_auth_frame_raw_sentence_latest.md
```

```bash
python3 scripts/testing/semantic_surface_pos_rescue_policy_validation_en_es.py \
  --json-out docs/test_outputs/semantic_surface_pos_rescue_policy_validation_non_v10_wave6_auth_frame_raw_sentence_latest.json \
  --markdown-out docs/test_outputs/semantic_surface_pos_rescue_policy_validation_non_v10_wave6_auth_frame_raw_sentence_latest.md \
  --fail-on-review
```

```bash
python3 scripts/testing/semantic_source_failure_class_mining_en_es.py \
  --primary-admission-json docs/test_outputs/semantic_source_admission_cycle_auth_frame_non_v10_wave6_wiktextract_supported_latest.json \
  --primary-heldout-json docs/test_outputs/semantic_source_non_v10_wave6_auth_frame_surface_pos_raw_sentence_heldout_margin000_phrase002_validation_latest.json \
  --additional-heldout-json docs/test_outputs/semantic_source_non_v10_wave6_auth_frame_surface_pos_raw_sentence_phrase_margin000_phrase002_validation_latest.json \
  --comparator-admission-json docs/test_outputs/semantic_source_admission_cycle_alt_phrase_non_v10_wave6_wiktextract_supported_latest.json \
  --source-report-json docs/test_outputs/semantic_authorization_frame_evidence_non_v10_wave6_wiktextract_supported_latest.json \
  --margin-sweep-json docs/test_outputs/semantic_surface_pos_rescue_policy_sweep_non_v10_wave6_auth_frame_raw_sentence_latest.json \
  --json-out docs/test_outputs/semantic_source_failure_class_mining_non_v10_wave6_auth_frame_latest.json \
  --markdown-out docs/test_outputs/semantic_source_failure_class_mining_non_v10_wave6_auth_frame_latest.md
```
