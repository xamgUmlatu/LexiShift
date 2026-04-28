# en-es Semantic Source Held-out Validation

- Status: `ok`
- Decision: `heldout_pass`
- Generated: `2026-04-25T21:52:33Z`
- Base dataset: `en_es_sentence_veto_v10`
- Held-out dataset: `en_es_source_heldout_cases_v2`
- Case scope: `semantic_active_shadow_only`
- Evidence batch: `en-es:example-frame-composite:reverse-aux-wordnet-wiktextract-wordnet-active-related-plant-cell-depth3-heldout-v2-policy-v1:sense-admitted`

## Summary

- Families: `19`
- Cases: `38`
- Gold replacements: `19`
- Gold abstains: `19`
- Harmful replacements: `0` / max `0`
- False abstains: `0` / max `0`
- Replace recall: `100.0%`
- Decision accuracy: `100.0%`

## Configured Row

| Source | Scorer | Context | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `promotion_candidate_composite` | `sentence_transformer_cosine` | `masked_sentence` | `active_shadow_containment_surface_pos` | 38 | 0 | 0 | 100.0% | 100.0% |

## Empty Baseline Comparator

| Source | Scorer | Context | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `empty_batch` | `sentence_transformer_cosine` | `masked_sentence` | `active_shadow_containment_surface_pos` | 38 | 0 | 19 | 0.0% | 50.0% |

## Family Coverage

| Family | Trigger | Cases | Replace | Abstain |
| --- | --- | ---: | ---: | ---: |
| `en-es:sentence-veto:ball:pelota` | `ball` | 2 | 1 | 1 |
| `en-es:sentence-veto:bank:banco` | `bank` | 2 | 1 | 1 |
| `en-es:sentence-veto:plant:planta` | `plant` | 2 | 1 | 1 |
| `en-es:sentence-veto:cell:celula` | `cell` | 2 | 1 | 1 |
| `en-es:sentence-veto:spring:primavera` | `spring` | 2 | 1 | 1 |
| `en-es:sentence-veto:seal:sello` | `seal` | 2 | 1 | 1 |
| `en-es:sentence-veto:file:archivo` | `file` | 2 | 1 | 1 |
| `en-es:sentence-veto:match:partido` | `match` | 2 | 1 | 1 |
| `en-es:sentence-veto:board:tablero` | `board` | 2 | 1 | 1 |
| `en-es:sentence-veto:table:mesa` | `table` | 2 | 1 | 1 |
| `en-es:sentence-veto:branch:sucursal` | `branch` | 2 | 1 | 1 |
| `en-es:sentence-veto:park:parque` | `park` | 2 | 1 | 1 |
| `en-es:sentence-veto:drink:bebida` | `drink` | 2 | 1 | 1 |
| `en-es:sentence-veto:play:obra` | `play` | 2 | 1 | 1 |
| `en-es:sentence-veto:watch:reloj` | `watch` | 2 | 1 | 1 |
| `en-es:sentence-veto:check:cheque` | `check` | 2 | 1 | 1 |
| `en-es:sentence-veto:order:pedido` | `order` | 2 | 1 | 1 |
| `en-es:sentence-veto:trip:viaje` | `trip` | 2 | 1 | 1 |
| `en-es:sentence-veto:report:informe` | `report` | 2 | 1 | 1 |

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
