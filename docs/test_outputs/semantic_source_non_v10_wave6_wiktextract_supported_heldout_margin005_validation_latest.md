# en-es Semantic Source Held-out Validation

- Status: `review`
- Decision: `heldout_review`
- Generated: `2026-04-29T01:48:04Z`
- Base dataset: `en_es_source_non_v10_wave6_anypos_unsupported_upper_bound_selected_v1`
- Held-out dataset: `en_es_source_non_v10_wave6_wiktextract_supported_heldout_cases_v1`
- Case scope: `non_v10_wave6_wiktextract_supported_active_shadow`
- Evidence batch: `en-es:wordnet-def-ex-non-v10-wave6-wiktextract-supported:source-admission-cycle-latest:sense-admitted`

## Summary

- Families: `16`
- Cases: `38`
- Gold replacements: `16`
- Gold abstains: `22`
- Harmful replacements: `2` / max `0`
- False abstains: `1` / max `0`
- Replace recall: `93.8%`
- Decision accuracy: `92.1%`

## Configured Row

| Source | Scorer | Context | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `promotion_candidate_composite` | `sentence_transformer_cosine` | `masked_sentence` | `active_shadow_containment_surface_pos` | 38 | 2 | 1 | 93.8% | 92.1% |

## Empty Baseline Comparator

| Source | Scorer | Context | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `empty_batch` | `sentence_transformer_cosine` | `masked_sentence` | `active_shadow_containment_surface_pos` | 38 | 0 | 16 | 0.0% | 57.9% |

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

- Harmful replace cases: `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:002, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:piece:002`
- False abstain cases: `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001`

| Case | Gold | Predicted | Active | Shadow | Margin | Active Evidence | Shadow Evidence | Signals |
| --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |
| `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001` | `replace` | `abstain` | `0.5801` | `0.5936` | `-0.0135` | a ten day's leave to visit his mother | the period of time during which you are absent from work or duty | active_noun_frame, strongest_shadow_not_verb_like |
| `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:002` | `abstain` | `replace` | `0.5635` | `0.5562` | `0.0073` | a ten day's leave to visit his mother | the period of time during which you are absent from work or duty | active_noun_frame |
| `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:piece:002` | `abstain` | `replace` | `0.6697` | `0.5602` | `0.1095` | a separate part of a whole | he taught me to set up the men on the chess board | active_noun_frame |

## Limitations

- `bounded_non_benchmark_slice_not_full_en_es_proof`
- `semantic_active_shadow_only_phrase_policy_excluded`
- `does_not_audit_runtime_packaging_or_latency`

## Next Steps

- expand held-out families and cases without tuning on this v2 result
- add phrase-sensitive held-out rows under a separate phrase-source policy harness
- freeze the promotion-candidate evidence manifest before broad source scaling
