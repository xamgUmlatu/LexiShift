# en-es Semantic Source Held-out Validation

- Status: `review`
- Decision: `heldout_review`
- Generated: `2026-04-29T01:48:04Z`
- Base dataset: `en_es_source_non_v10_wave6_anypos_unsupported_upper_bound_selected_v1`
- Held-out dataset: `en_es_source_non_v10_wave6_wiktextract_supported_phrase_cases_v1`
- Case scope: `non_v10_wave6_wiktextract_supported_phrase_no_winner`
- Evidence batch: `en-es:wordnet-def-ex-non-v10-wave6-wiktextract-supported:source-admission-cycle-latest:sense-admitted`

## Summary

- Families: `16`
- Cases: `16`
- Gold replacements: `0`
- Gold abstains: `16`
- Harmful replacements: `2` / max `0`
- False abstains: `0` / max `0`
- Replace recall: `0.0%`
- Decision accuracy: `87.5%`

## Configured Row

| Source | Scorer | Context | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `promotion_candidate_composite` | `sentence_transformer_cosine` | `masked_sentence` | `active_shadow_containment_surface_pos` | 16 | 2 | 0 | 0.0% | 87.5% |

## Empty Baseline Comparator

| Source | Scorer | Context | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `empty_batch` | `sentence_transformer_cosine` | `masked_sentence` | `active_shadow_containment_surface_pos` | 16 | 0 | 0 | 0.0% | 100.0% |

## Family Coverage

| Family | Trigger | Cases | Replace | Abstain |
| --- | --- | ---: | ---: | ---: |
| `en-es:sentence-veto:leave:permiso` | `leave` | 1 | 0 | 1 |
| `en-es:sentence-veto:black:oscuro` | `black` | 1 | 0 | 1 |
| `en-es:sentence-veto:serve:servicio` | `serve` | 1 | 0 | 1 |
| `en-es:sentence-veto:low:bajo` | `low` | 1 | 0 | 1 |
| `en-es:sentence-veto:part:parte` | `part` | 1 | 0 | 1 |
| `en-es:sentence-veto:feel:talento` | `feel` | 1 | 0 | 1 |
| `en-es:sentence-veto:still:quietud` | `still` | 1 | 0 | 1 |
| `en-es:sentence-veto:bear:bajista` | `bear` | 1 | 0 | 1 |
| `en-es:sentence-veto:finish:meta` | `finish` | 1 | 0 | 1 |
| `en-es:sentence-veto:throw:lanzamiento` | `throw` | 1 | 0 | 1 |
| `en-es:sentence-veto:upset:disgustado` | `upset` | 1 | 0 | 1 |
| `en-es:sentence-veto:piece:trozo` | `piece` | 1 | 0 | 1 |
| `en-es:sentence-veto:fair:pastel` | `fair` | 1 | 0 | 1 |
| `en-es:sentence-veto:show:espect-culo` | `show` | 1 | 0 | 1 |
| `en-es:sentence-veto:advance:avance` | `advance` | 1 | 0 | 1 |
| `en-es:sentence-veto:rank:rancio` | `rank` | 1 | 0 | 1 |

## Failure Cases

- Harmful replace cases: `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:fair:001`
- False abstain cases: `none`

| Case | Gold | Predicted | Active | Shadow | Margin | Active Evidence | Shadow Evidence | Signals |
| --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |
| `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `abstain` | `replace` | `0.4952` | `0.5911` | `-0.0959` | an investor with a pessimistic market outlook; an investor who expects prices to fall and so sells now in order to buy later at a lower price | contain or hold; have within | active_noun_frame |
| `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:fair:001` | `abstain` | `replace` | `0.5473` | `0.5759` | `-0.0285` | a fair complexion | world fair | active_modifier_frame |

## Limitations

- `bounded_non_benchmark_slice_not_full_en_es_proof`
- `semantic_active_shadow_only_phrase_policy_excluded`
- `does_not_audit_runtime_packaging_or_latency`

## Next Steps

- expand held-out families and cases without tuning on this v2 result
- add phrase-sensitive held-out rows under a separate phrase-source policy harness
- freeze the promotion-candidate evidence manifest before broad source scaling
