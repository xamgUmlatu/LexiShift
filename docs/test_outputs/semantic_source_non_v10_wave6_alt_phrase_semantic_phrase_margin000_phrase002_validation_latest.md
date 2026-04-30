# en-es Semantic Source Held-out Validation

- Status: `ok`
- Decision: `heldout_pass`
- Generated: `2026-04-29T03:34:28Z`
- Base dataset: `en_es_source_non_v10_wave6_anypos_unsupported_upper_bound_selected_v1`
- Held-out dataset: `en_es_source_non_v10_wave6_wiktextract_supported_phrase_cases_v1`
- Case scope: `non_v10_wave6_wiktextract_supported_phrase_no_winner`
- Evidence batch: `en-es:wordnet-translation-plus-alt-phrase:non-v10-wave6-wiktextract-supported-v1:cycle:sense-admitted`

## Summary

- Families: `16`
- Cases: `16`
- Gold replacements: `0`
- Gold abstains: `16`
- Harmful replacements: `0` / max `0`
- False abstains: `0` / max `0`
- Replace recall: `0.0%`
- Decision accuracy: `100.0%`

## Configured Row

| Source | Scorer | Context | Margin | Phrase Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `promotion_candidate_composite` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.02 | `active_shadow_phrase_semantic_prototypes` | 16 | 0 | 0 | 0.0% | 100.0% |

## Empty Baseline Comparator

| Source | Scorer | Context | Margin | Phrase Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `empty_batch` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.02 | `active_shadow_phrase_semantic_prototypes` | 16 | 0 | 0 | 0.0% | 100.0% |

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

- Harmful replace cases: `none`
- False abstain cases: `none`

No configured-lane failure case details.

## Limitations

- `bounded_non_benchmark_slice_not_full_en_es_proof`
- `semantic_active_shadow_only_phrase_policy_excluded`
- `does_not_audit_runtime_packaging_or_latency`

## Next Steps

- expand held-out families and cases without tuning on this v2 result
- add phrase-sensitive held-out rows under a separate phrase-source policy harness
- freeze the promotion-candidate evidence manifest before broad source scaling
