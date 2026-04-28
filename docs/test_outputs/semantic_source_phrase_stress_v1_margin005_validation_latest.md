# en-es Semantic Source Held-out Validation

- Status: `ok`
- Decision: `heldout_pass`
- Generated: `2026-04-26T02:33:07Z`
- Base dataset: `en_es_sentence_veto_v10`
- Held-out dataset: `en_es_source_phrase_stress_cases_v1`
- Case scope: `phrase_no_winner_only`
- Evidence batch: `en-es:example-frame-composite:reverse-aux-wordnet-wiktextract-wordnet-active-related-plant-cell-depth3-heldout-v2-policy-v1:sense-admitted`

## Summary

- Families: `19`
- Cases: `19`
- Gold replacements: `0`
- Gold abstains: `19`
- Harmful replacements: `0` / max `0`
- False abstains: `0` / max `0`
- Replace recall: `0.0%`
- Decision accuracy: `100.0%`

## Configured Row

| Source | Scorer | Context | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `promotion_candidate_composite` | `sentence_transformer_cosine` | `masked_sentence` | `active_shadow_containment_surface_pos` | 19 | 0 | 0 | 0.0% | 100.0% |

## Empty Baseline Comparator

| Source | Scorer | Context | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `empty_batch` | `sentence_transformer_cosine` | `masked_sentence` | `active_shadow_containment_surface_pos` | 19 | 0 | 0 | 0.0% | 100.0% |

## Family Coverage

| Family | Trigger | Cases | Replace | Abstain |
| --- | --- | ---: | ---: | ---: |
| `en-es:sentence-veto:ball:pelota` | `ball` | 1 | 0 | 1 |
| `en-es:sentence-veto:bank:banco` | `bank` | 1 | 0 | 1 |
| `en-es:sentence-veto:plant:planta` | `plant` | 1 | 0 | 1 |
| `en-es:sentence-veto:cell:celula` | `cell` | 1 | 0 | 1 |
| `en-es:sentence-veto:spring:primavera` | `spring` | 1 | 0 | 1 |
| `en-es:sentence-veto:seal:sello` | `seal` | 1 | 0 | 1 |
| `en-es:sentence-veto:file:archivo` | `file` | 1 | 0 | 1 |
| `en-es:sentence-veto:match:partido` | `match` | 1 | 0 | 1 |
| `en-es:sentence-veto:board:tablero` | `board` | 1 | 0 | 1 |
| `en-es:sentence-veto:table:mesa` | `table` | 1 | 0 | 1 |
| `en-es:sentence-veto:branch:sucursal` | `branch` | 1 | 0 | 1 |
| `en-es:sentence-veto:park:parque` | `park` | 1 | 0 | 1 |
| `en-es:sentence-veto:drink:bebida` | `drink` | 1 | 0 | 1 |
| `en-es:sentence-veto:play:obra` | `play` | 1 | 0 | 1 |
| `en-es:sentence-veto:watch:reloj` | `watch` | 1 | 0 | 1 |
| `en-es:sentence-veto:check:cheque` | `check` | 1 | 0 | 1 |
| `en-es:sentence-veto:order:pedido` | `order` | 1 | 0 | 1 |
| `en-es:sentence-veto:trip:viaje` | `trip` | 1 | 0 | 1 |
| `en-es:sentence-veto:report:informe` | `report` | 1 | 0 | 1 |

## Failure Cases

- Harmful replace cases: `none`
- False abstain cases: `none`

## Limitations

- `bounded_non_benchmark_slice_not_full_en_es_proof`
- `semantic_active_shadow_only_phrase_policy_excluded`
- `does_not_audit_runtime_packaging_or_latency`

## Next Steps

- stress the passing phrase policy on fresh no-winner and non-v10 rows
- keep phrase-source or pattern provenance separate from active/shadow semantic scoring
- rerun phrase held-out, phrase challenge, active/shadow v2, and margin sweep before accepting a phrase-policy change
