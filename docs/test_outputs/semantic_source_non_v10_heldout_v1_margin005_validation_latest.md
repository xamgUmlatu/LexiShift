# en-es Semantic Source Held-out Validation

- Status: `ok`
- Decision: `heldout_pass`
- Generated: `2026-04-26T03:24:58Z`
- Base dataset: `en_es_source_non_v10_probe_v1`
- Held-out dataset: `en_es_source_non_v10_heldout_cases_v1`
- Case scope: `non_v10_source_probe`
- Evidence batch: `en-es:source-admission-cycle:wordnet-def-source-non-v10-probe-v1-20260426a:sense-admitted`

## Summary

- Families: `8`
- Cases: `16`
- Gold replacements: `8`
- Gold abstains: `8`
- Harmful replacements: `0` / max `0`
- False abstains: `0` / max `0`
- Replace recall: `100.0%`
- Decision accuracy: `100.0%`

## Configured Row

| Source | Scorer | Context | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `promotion_candidate_composite` | `sentence_transformer_cosine` | `masked_sentence` | `active_shadow_containment_surface_pos` | 16 | 0 | 0 | 100.0% | 100.0% |

## Empty Baseline Comparator

| Source | Scorer | Context | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `empty_batch` | `sentence_transformer_cosine` | `masked_sentence` | `active_shadow_containment_surface_pos` | 16 | 0 | 8 | 0.0% | 50.0% |

## Family Coverage

| Family | Trigger | Cases | Replace | Abstain |
| --- | --- | ---: | ---: | ---: |
| `en-es:sentence-veto:rock:roca` | `rock` | 2 | 1 | 1 |
| `en-es:sentence-veto:draft:borrador` | `draft` | 2 | 1 | 1 |
| `en-es:sentence-veto:case:caso` | `case` | 2 | 1 | 1 |
| `en-es:sentence-veto:scale:escala` | `scale` | 2 | 1 | 1 |
| `en-es:sentence-veto:line:linea` | `line` | 2 | 1 | 1 |
| `en-es:sentence-veto:point:punto` | `point` | 2 | 1 | 1 |
| `en-es:sentence-veto:ring:anillo` | `ring` | 2 | 1 | 1 |
| `en-es:sentence-veto:date:fecha` | `date` | 2 | 1 | 1 |

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
