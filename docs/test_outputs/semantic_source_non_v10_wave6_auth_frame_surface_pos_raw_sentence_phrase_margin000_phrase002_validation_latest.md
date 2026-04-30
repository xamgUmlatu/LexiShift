# en-es Semantic Source Held-out Validation

- Status: `review`
- Decision: `heldout_review`
- Generated: `2026-04-30T03:36:32Z`
- Base dataset: `en_es_source_non_v10_wave6_anypos_unsupported_upper_bound_selected_v1`
- Held-out dataset: `en_es_source_non_v10_wave6_wiktextract_supported_phrase_cases_v1`
- Case scope: `non_v10_wave6_wiktextract_supported_phrase_no_winner`
- Evidence batch: `en-es:wordnet-translation-alt-phrase-plus-auth-frame:non-v10-wave6-wiktextract-supported-v1:cycle:sense-admitted:sense-admitted`

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

| Source | Scorer | Context | Margin | Phrase Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `promotion_candidate_composite` | `sentence_transformer_cosine` | `raw_sentence` | 0.0 | 0.02 | `active_shadow_phrase_semantic_surface_pos` | 16 | 2 | 0 | 0.0% | 87.5% |

## Empty Baseline Comparator

| Source | Scorer | Context | Margin | Phrase Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `empty_batch` | `sentence_transformer_cosine` | `raw_sentence` | 0.0 | 0.02 | `active_shadow_phrase_semantic_surface_pos` | 16 | 0 | 0 | 0.0% | 100.0% |

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

- Harmful replace cases: `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001`
- False abstain cases: `none`

| Case | Gold | Predicted | Active | Shadow | Phrase | Margin | Phrase Lead | Active Evidence | Shadow Evidence | Phrase Evidence | Signals |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |
| `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001` | `abstain` | `replace` | `0.6379` | `0.6508` | `0.7117` | `-0.0129` | `0.0608` | low adverb sense: close to the ground | low adjective sense: depressed, sad | unrefined in character example: low comedy | active_modifier_frame |
| `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `abstain` | `replace` | `0.5076` | `0.6332` | `0.6446` | `-0.1256` | `0.0114` | bear noun sense: investor who sells in anticipation of falling prices | bear verb sense: to carry | move while holding up or supporting example: Bear gifts | active_noun_frame |

## Limitations

- `bounded_non_benchmark_slice_not_full_en_es_proof`
- `semantic_active_shadow_only_phrase_policy_excluded`
- `does_not_audit_runtime_packaging_or_latency`

## Next Steps

- expand held-out families and cases without tuning on this v2 result
- add phrase-sensitive held-out rows under a separate phrase-source policy harness
- freeze the promotion-candidate evidence manifest before broad source scaling
