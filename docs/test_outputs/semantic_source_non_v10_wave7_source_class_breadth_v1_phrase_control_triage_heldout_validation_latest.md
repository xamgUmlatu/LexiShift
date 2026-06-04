# en-es Semantic Source Held-out Validation

- Status: `review`
- Decision: `heldout_review`
- Generated: `2026-04-30T20:47:48Z`
- Base dataset: `en_es_source_non_v10_wave7_source_class_breadth_v1_unsupported_selected`
- Held-out dataset: `en_es_source_non_v10_wave7_source_class_breadth_v1_heldout_cases`
- Case scope: `non_v10_wave7_source_class_breadth_active_shadow`
- Evidence batch: `en-es:wave7-source-class-breadth-v1:phrase-control-triage:cycle:sense-admitted`

## Summary

- Families: `16`
- Cases: `32`
- Gold replacements: `16`
- Gold abstains: `16`
- Harmful replacements: `1` / max `0`
- False abstains: `2` / max `0`
- Replace recall: `87.5%`
- Decision accuracy: `90.6%`

## Configured Row

| Source | Scorer | Context | Margin | Phrase Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `promotion_candidate_composite` | `sentence_transformer_cosine` | `raw_sentence` | 0.0 | 0.02 | `active_shadow_phrase_semantic_surface_pos` | 32 | 1 | 2 | 87.5% | 90.6% |

## Empty Baseline Comparator

| Source | Scorer | Context | Margin | Phrase Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `empty_batch` | `sentence_transformer_cosine` | `raw_sentence` | 0.0 | 0.02 | `active_shadow_phrase_semantic_surface_pos` | 32 | 0 | 16 | 0.0% | 50.0% |

## Family Coverage

| Family | Trigger | Cases | Replace | Abstain |
| --- | --- | ---: | ---: | ---: |
| `en-es:sentence-veto:like:gustos` | `like` | 2 | 1 | 1 |
| `en-es:sentence-veto:gross:repulsivo` | `gross` | 2 | 1 | 1 |
| `en-es:sentence-veto:cast:lanzamiento` | `cast` | 2 | 1 | 1 |
| `en-es:sentence-veto:fix:aprieto` | `fix` | 2 | 1 | 1 |
| `en-es:sentence-veto:full:lleno` | `full` | 2 | 1 | 1 |
| `en-es:sentence-veto:waste:desperdicio` | `waste` | 2 | 1 | 1 |
| `en-es:sentence-veto:firm:firma` | `firm` | 2 | 1 | 1 |
| `en-es:sentence-veto:even:tarde` | `even` | 2 | 1 | 1 |
| `en-es:sentence-veto:wrong:incorrecto` | `wrong` | 2 | 1 | 1 |
| `en-es:sentence-veto:meet:adecuado` | `meet` | 2 | 1 | 1 |
| `en-es:sentence-veto:stretch:estir-n` | `stretch` | 2 | 1 | 1 |
| `en-es:sentence-veto:score:tantos` | `score` | 2 | 1 | 1 |
| `en-es:sentence-veto:crash:choque` | `crash` | 2 | 1 | 1 |
| `en-es:sentence-veto:trim:compensador` | `trim` | 2 | 1 | 1 |
| `en-es:sentence-veto:squeeze:crisis` | `squeeze` | 2 | 1 | 1 |
| `en-es:sentence-veto:foul:falta` | `foul` | 2 | 1 | 1 |

## Failure Cases

- Harmful replace cases: `en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:gross:002`
- False abstain cases: `en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:fix:001, en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:meet:001`

| Case | Gold | Predicted | Active | Shadow | Phrase | Margin | Phrase Lead | Active Evidence | Shadow Evidence | Phrase Evidence | Signals |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |
| `en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:gross:002` | `abstain` | `replace` | `0.6767` | `0.7145` | `0.6307` | `-0.0378` | `-0.0839` | gross adjective sense: causing disgust | a gross is a count for ordered goods | lacking fine distinctions or detail example: the gross details of the structure appear reasonable | active_modifier_frame |
| `en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:fix:001` | `replace` | `abstain` | `0.626` | `0.7449` | `0.7136` | `-0.1189` | `-0.0313` | fix noun sense: a difficult situation or dilemma | restore something broken | a determination of the place where something is example: he got a good fix on the target | shadow_verb_frame |
| `en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:meet:001` | `replace` | `abstain` | `0.5444` | `0.6926` | `0.7272` | `-0.1481` | `0.0347` | suitable and proper | I'll probably see you at the meeting | come together example: I'll probably see you at the meeting | `none` |

## Limitations

- `bounded_non_benchmark_slice_not_full_en_es_proof`
- `semantic_active_shadow_only_phrase_policy_excluded`
- `does_not_audit_runtime_packaging_or_latency`

## Next Steps

- expand held-out families and cases without tuning on this v2 result
- add phrase-sensitive held-out rows under a separate phrase-source policy harness
- freeze the promotion-candidate evidence manifest before broad source scaling
