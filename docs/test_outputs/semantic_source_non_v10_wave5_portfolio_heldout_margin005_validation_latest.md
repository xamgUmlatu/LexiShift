# en-es Semantic Source Held-out Validation

- Status: `review`
- Decision: `heldout_review`
- Generated: `2026-04-28T22:37:52Z`
- Base dataset: `en_es_source_non_v10_wave5_anypos_ranked_slate_selected_v1`
- Held-out dataset: `en_es_source_non_v10_wave5_portfolio_heldout_cases_v1`
- Case scope: `non_v10_wave5_source_portfolio_active_shadow`
- Evidence batch: `en-es:wordnet-source-portfolio:non-v10-wave5-anypos-v1:cycle:sense-admitted`

## Summary

- Families: `16`
- Cases: `32`
- Gold replacements: `16`
- Gold abstains: `16`
- Harmful replacements: `2` / max `0`
- False abstains: `3` / max `0`
- Replace recall: `81.2%`
- Decision accuracy: `84.4%`

## Configured Row

| Source | Scorer | Context | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `promotion_candidate_composite` | `sentence_transformer_cosine` | `masked_sentence` | `active_shadow_containment_surface_pos` | 32 | 2 | 3 | 81.2% | 84.4% |

## Empty Baseline Comparator

| Source | Scorer | Context | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `empty_batch` | `sentence_transformer_cosine` | `masked_sentence` | `active_shadow_containment_surface_pos` | 32 | 0 | 16 | 0.0% | 50.0% |

## Family Coverage

| Family | Trigger | Cases | Replace | Abstain |
| --- | --- | ---: | ---: | ---: |
| `en-es:sentence-veto:dry:seco` | `dry` | 2 | 1 | 1 |
| `en-es:sentence-veto:use:uso` | `use` | 2 | 1 | 1 |
| `en-es:sentence-veto:plain:llano` | `plain` | 2 | 1 | 1 |
| `en-es:sentence-veto:fast:r-pido` | `fast` | 2 | 1 | 1 |
| `en-es:sentence-veto:train:tren` | `train` | 2 | 1 | 1 |
| `en-es:sentence-veto:land:tierra` | `land` | 2 | 1 | 1 |
| `en-es:sentence-veto:mean:medio` | `mean` | 2 | 1 | 1 |
| `en-es:sentence-veto:offer:oferta` | `offer` | 2 | 1 | 1 |
| `en-es:sentence-veto:present:presente` | `present` | 2 | 1 | 1 |
| `en-es:sentence-veto:sign:se-al` | `sign` | 2 | 1 | 1 |
| `en-es:sentence-veto:quiet:silencio` | `quiet` | 2 | 1 | 1 |
| `en-es:sentence-veto:change:cambio` | `change` | 2 | 1 | 1 |
| `en-es:sentence-veto:look:aspecto` | `look` | 2 | 1 | 1 |
| `en-es:sentence-veto:rest:reposo` | `rest` | 2 | 1 | 1 |
| `en-es:sentence-veto:answer:respuesta` | `answer` | 2 | 1 | 1 |
| `en-es:sentence-veto:end:fin` | `end` | 2 | 1 | 1 |

## Failure Cases

- Harmful replace cases: `en-es:source-non-v10-wave5-portfolio-heldout:v1:present:002, en-es:source-non-v10-wave5-portfolio-heldout:v1:rest:002`
- False abstain cases: `en-es:source-non-v10-wave5-portfolio-heldout:v1:dry:001, en-es:source-non-v10-wave5-portfolio-heldout:v1:train:001, en-es:source-non-v10-wave5-portfolio-heldout:v1:present:001`

## Limitations

- `bounded_non_benchmark_slice_not_full_en_es_proof`
- `semantic_active_shadow_only_phrase_policy_excluded`
- `does_not_audit_runtime_packaging_or_latency`

## Next Steps

- expand held-out families and cases without tuning on this v2 result
- add phrase-sensitive held-out rows under a separate phrase-source policy harness
- freeze the promotion-candidate evidence manifest before broad source scaling
