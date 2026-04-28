# en-es Semantic Source Held-out Validation

- Status: `review`
- Decision: `heldout_review`
- Generated: `2026-04-25T21:49:12Z`
- Base dataset: `en_es_sentence_veto_v10`
- Held-out dataset: `en_es_source_phrase_heldout_cases_v2`
- Case scope: `phrase_no_winner_only`
- Evidence batch: `en-es:example-frame-composite:reverse-aux-wordnet-wiktextract-wordnet-active-related-plant-cell-depth3-heldout-v2-policy-v1:sense-admitted`

## Summary

- Families: `19`
- Cases: `38`
- Gold replacements: `0`
- Gold abstains: `38`
- Harmful replacements: `1` / max `0`
- False abstains: `0` / max `0`
- Replace recall: `0.0%`
- Decision accuracy: `97.4%`

## Configured Row

| Source | Scorer | Context | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `promotion_candidate_composite` | `sentence_transformer_cosine` | `masked_sentence` | `active_shadow_containment_surface_pos` | 38 | 1 | 0 | 0.0% | 97.4% |

## Empty Baseline Comparator

| Source | Scorer | Context | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `empty_batch` | `sentence_transformer_cosine` | `masked_sentence` | `active_shadow_containment_surface_pos` | 38 | 0 | 0 | 0.0% | 100.0% |

## Family Coverage

| Family | Trigger | Cases | Replace | Abstain |
| --- | --- | ---: | ---: | ---: |
| `en-es:sentence-veto:ball:pelota` | `ball` | 2 | 0 | 2 |
| `en-es:sentence-veto:bank:banco` | `bank` | 2 | 0 | 2 |
| `en-es:sentence-veto:plant:planta` | `plant` | 2 | 0 | 2 |
| `en-es:sentence-veto:cell:celula` | `cell` | 2 | 0 | 2 |
| `en-es:sentence-veto:spring:primavera` | `spring` | 2 | 0 | 2 |
| `en-es:sentence-veto:seal:sello` | `seal` | 2 | 0 | 2 |
| `en-es:sentence-veto:file:archivo` | `file` | 2 | 0 | 2 |
| `en-es:sentence-veto:match:partido` | `match` | 2 | 0 | 2 |
| `en-es:sentence-veto:board:tablero` | `board` | 2 | 0 | 2 |
| `en-es:sentence-veto:table:mesa` | `table` | 2 | 0 | 2 |
| `en-es:sentence-veto:branch:sucursal` | `branch` | 2 | 0 | 2 |
| `en-es:sentence-veto:park:parque` | `park` | 2 | 0 | 2 |
| `en-es:sentence-veto:drink:bebida` | `drink` | 2 | 0 | 2 |
| `en-es:sentence-veto:play:obra` | `play` | 2 | 0 | 2 |
| `en-es:sentence-veto:watch:reloj` | `watch` | 2 | 0 | 2 |
| `en-es:sentence-veto:check:cheque` | `check` | 2 | 0 | 2 |
| `en-es:sentence-veto:order:pedido` | `order` | 2 | 0 | 2 |
| `en-es:sentence-veto:trip:viaje` | `trip` | 2 | 0 | 2 |
| `en-es:sentence-veto:report:informe` | `report` | 2 | 0 | 2 |

## Failure Cases

- Harmful replace cases: `en-es:source-phrase-heldout:v2:board:002`
- False abstain cases: `none`

## Limitations

- `bounded_non_benchmark_slice_not_full_en_es_proof`
- `semantic_active_shadow_only_phrase_policy_excluded`
- `does_not_audit_runtime_packaging_or_latency`

## Next Steps

- diagnose phrase/no-winner misses without tuning the active/shadow v2 reference
- test phrase-source rows or a general verb-frame no-winner policy on this slice
- rerun both phrase held-out and active/shadow v2 held-out before accepting a phrase-policy change
