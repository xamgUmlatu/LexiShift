# en-es Semantic Source Held-out Validation

- Status: `review`
- Decision: `heldout_review`
- Generated: `2026-04-30T03:35:45Z`
- Base dataset: `en_es_source_non_v10_wave6_anypos_unsupported_upper_bound_selected_v1`
- Held-out dataset: `en_es_source_non_v10_wave6_wiktextract_supported_heldout_cases_v1`
- Case scope: `non_v10_wave6_wiktextract_supported_active_shadow`
- Evidence batch: `en-es:wordnet-translation-plus-alt-phrase:non-v10-wave6-wiktextract-supported-v1:cycle:sense-admitted`

## Summary

- Families: `16`
- Cases: `38`
- Gold replacements: `16`
- Gold abstains: `22`
- Harmful replacements: `0` / max `0`
- False abstains: `1` / max `0`
- Replace recall: `93.8%`
- Decision accuracy: `97.4%`

## Configured Row

| Source | Scorer | Context | Margin | Phrase Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `promotion_candidate_composite` | `sentence_transformer_cosine` | `raw_sentence` | 0.0 | 0.02 | `active_shadow_phrase_semantic_surface_pos` | 38 | 0 | 1 | 93.8% | 97.4% |

## Empty Baseline Comparator

| Source | Scorer | Context | Margin | Phrase Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `empty_batch` | `sentence_transformer_cosine` | `raw_sentence` | 0.0 | 0.02 | `active_shadow_phrase_semantic_surface_pos` | 38 | 0 | 16 | 0.0% | 57.9% |

## Family Coverage

| Family | Trigger | Cases | Replace | Abstain |
| --- | --- | ---: | ---: | ---: |
| `en-es:sentence-veto:leave:permiso` | `leave` | 3 | 1 | 2 |
| `en-es:sentence-veto:black:oscuro` | `black` | 2 | 1 | 1 |
| `en-es:sentence-veto:serve:servicio` | `serve` | 2 | 1 | 1 |
| `en-es:sentence-veto:low:bajo` | `low` | 2 | 1 | 1 |
| `en-es:sentence-veto:part:parte` | `part` | 3 | 1 | 2 |
| `en-es:sentence-veto:feel:talento` | `feel` | 2 | 1 | 1 |
| `en-es:sentence-veto:still:quietud` | `still` | 3 | 1 | 2 |
| `en-es:sentence-veto:bear:bajista` | `bear` | 2 | 1 | 1 |
| `en-es:sentence-veto:finish:meta` | `finish` | 3 | 1 | 2 |
| `en-es:sentence-veto:throw:lanzamiento` | `throw` | 2 | 1 | 1 |
| `en-es:sentence-veto:upset:disgustado` | `upset` | 2 | 1 | 1 |
| `en-es:sentence-veto:piece:trozo` | `piece` | 3 | 1 | 2 |
| `en-es:sentence-veto:fair:pastel` | `fair` | 2 | 1 | 1 |
| `en-es:sentence-veto:show:espect-culo` | `show` | 2 | 1 | 1 |
| `en-es:sentence-veto:advance:avance` | `advance` | 3 | 1 | 2 |
| `en-es:sentence-veto:rank:rancio` | `rank` | 2 | 1 | 1 |

## Failure Cases

- Harmful replace cases: `none`
- False abstain cases: `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001`

| Case | Gold | Predicted | Active | Shadow | Phrase | Margin | Phrase Lead | Active Evidence | Shadow Evidence | Phrase Evidence | Signals |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |
| `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001` | `replace` | `abstain` | `0.6165` | `0.6307` | `0.617` | `-0.0142` | `-0.0137` | a ten day's leave to visit his mother | the period of time during which you are absent from work or duty | go away from a place example: At what time does your train leave? | active_noun_frame, strongest_shadow_not_verb_like |

## Limitations

- `bounded_non_benchmark_slice_not_full_en_es_proof`
- `semantic_active_shadow_only_phrase_policy_excluded`
- `does_not_audit_runtime_packaging_or_latency`

## Next Steps

- expand held-out families and cases without tuning on this v2 result
- add phrase-sensitive held-out rows under a separate phrase-source policy harness
- freeze the promotion-candidate evidence manifest before broad source scaling
