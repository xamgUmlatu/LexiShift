# en-es Semantic Source Held-out Validation

- Status: `ok`
- Decision: `heldout_pass`
- Generated: `2026-04-27T22:44:24Z`
- Base dataset: `en_es_source_non_v10_wave2_admission_selected_v1`
- Held-out dataset: `en_es_source_non_v10_wave2_selected_phrase_cases_v1`
- Case scope: `non_v10_wave2_admission_selected_phrase_no_winner`
- Evidence batch: `en-es:wordnet-def-ex-non-v10-wave2-selected-v1:source-admission-cycle:sense-admitted`

## Summary

- Families: `8`
- Cases: `8`
- Gold replacements: `0`
- Gold abstains: `8`
- Harmful replacements: `0` / max `0`
- False abstains: `0` / max `0`
- Replace recall: `0.0%`
- Decision accuracy: `100.0%`

## Configured Row

| Source | Scorer | Context | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `promotion_candidate_composite` | `sentence_transformer_cosine` | `masked_sentence` | `active_shadow_containment_surface_pos` | 8 | 0 | 0 | 0.0% | 100.0% |

## Empty Baseline Comparator

| Source | Scorer | Context | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `empty_batch` | `sentence_transformer_cosine` | `masked_sentence` | `active_shadow_containment_surface_pos` | 8 | 0 | 0 | 0.0% | 100.0% |

## Family Coverage

| Family | Trigger | Cases | Replace | Abstain |
| --- | --- | ---: | ---: | ---: |
| `en-es:sentence-veto:look:aspecto` | `look` | 1 | 0 | 1 |
| `en-es:sentence-veto:use:uso` | `use` | 1 | 0 | 1 |
| `en-es:sentence-veto:train:tren` | `train` | 1 | 0 | 1 |
| `en-es:sentence-veto:land:tierra` | `land` | 1 | 0 | 1 |
| `en-es:sentence-veto:offer:oferta` | `offer` | 1 | 0 | 1 |
| `en-es:sentence-veto:rest:reposo` | `rest` | 1 | 0 | 1 |
| `en-es:sentence-veto:sign:se-al` | `sign` | 1 | 0 | 1 |
| `en-es:sentence-veto:answer:respuesta` | `answer` | 1 | 0 | 1 |

## Failure Cases

- Harmful replace cases: `none`
- False abstain cases: `none`

## Limitations

- `bounded_non_benchmark_slice_not_full_en_es_proof`
- `semantic_active_shadow_only_phrase_policy_excluded`
- `does_not_audit_runtime_packaging_or_latency`

## Next Steps

- expand held-out families and cases without tuning on this v2 result
- add phrase-sensitive held-out rows under a separate phrase-source policy harness
- freeze the promotion-candidate evidence manifest before broad source scaling
