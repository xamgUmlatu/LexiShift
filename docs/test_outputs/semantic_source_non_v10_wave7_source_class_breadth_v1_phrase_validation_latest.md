# en-es Semantic Source Held-out Validation

- Status: `review`
- Decision: `heldout_review`
- Generated: `2026-04-30T19:19:56Z`
- Base dataset: `en_es_source_non_v10_wave7_source_class_breadth_v1_unsupported_selected`
- Held-out dataset: `en_es_source_non_v10_wave7_source_class_breadth_v1_phrase_cases`
- Case scope: `non_v10_wave7_source_class_breadth_phrase_no_winner`
- Evidence batch: `en-es:wordnet-translation-sense-source-class:non-v10-wave7-source-class-breadth-v1:cycle:sense-admitted`

## Summary

- Families: `16`
- Cases: `16`
- Gold replacements: `0`
- Gold abstains: `16`
- Harmful replacements: `7` / max `0`
- False abstains: `0` / max `0`
- Replace recall: `0.0%`
- Decision accuracy: `56.2%`

## Configured Row

| Source | Scorer | Context | Margin | Phrase Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `promotion_candidate_composite` | `sentence_transformer_cosine` | `raw_sentence` | 0.0 | 0.02 | `active_shadow_phrase_semantic_surface_pos` | 16 | 7 | 0 | 0.0% | 56.2% |

## Empty Baseline Comparator

| Source | Scorer | Context | Margin | Phrase Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `empty_batch` | `sentence_transformer_cosine` | `raw_sentence` | 0.0 | 0.02 | `active_shadow_phrase_semantic_surface_pos` | 16 | 0 | 0 | 0.0% | 100.0% |

## Family Coverage

| Family | Trigger | Cases | Replace | Abstain |
| --- | --- | ---: | ---: | ---: |
| `en-es:sentence-veto:like:gustos` | `like` | 1 | 0 | 1 |
| `en-es:sentence-veto:gross:repulsivo` | `gross` | 1 | 0 | 1 |
| `en-es:sentence-veto:cast:lanzamiento` | `cast` | 1 | 0 | 1 |
| `en-es:sentence-veto:fix:aprieto` | `fix` | 1 | 0 | 1 |
| `en-es:sentence-veto:full:lleno` | `full` | 1 | 0 | 1 |
| `en-es:sentence-veto:waste:desperdicio` | `waste` | 1 | 0 | 1 |
| `en-es:sentence-veto:firm:firma` | `firm` | 1 | 0 | 1 |
| `en-es:sentence-veto:even:tarde` | `even` | 1 | 0 | 1 |
| `en-es:sentence-veto:wrong:incorrecto` | `wrong` | 1 | 0 | 1 |
| `en-es:sentence-veto:meet:adecuado` | `meet` | 1 | 0 | 1 |
| `en-es:sentence-veto:stretch:estir-n` | `stretch` | 1 | 0 | 1 |
| `en-es:sentence-veto:score:tantos` | `score` | 1 | 0 | 1 |
| `en-es:sentence-veto:crash:choque` | `crash` | 1 | 0 | 1 |
| `en-es:sentence-veto:trim:compensador` | `trim` | 1 | 0 | 1 |
| `en-es:sentence-veto:squeeze:crisis` | `squeeze` | 1 | 0 | 1 |
| `en-es:sentence-veto:foul:falta` | `foul` | 1 | 0 | 1 |

## Failure Cases

- Harmful replace cases: `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:cast:001, en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:full:001, en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:wrong:001, en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:stretch:001, en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:score:001, en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:squeeze:001, en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:foul:001`
- False abstain cases: `none`

| Case | Gold | Predicted | Active | Shadow | Phrase | Margin | Phrase Lead | Active Evidence | Shadow Evidence | Phrase Evidence | Signals |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |
| `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:cast:001` | `abstain` | `replace` | `0.5626` | `0.6113` | `0.0` | `-0.0486` | `-0.6113` | cast noun sense: act of throwing | cast verb sense: to perform, bring forth a magical spell or enchantment | `none` | active_noun_frame |
| `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:full:001` | `abstain` | `replace` | `0.5631` | `0.5314` | `0.0` | `0.0316` | `-0.5631` | filled to maximum capacity | full the cloth | `none` | `none` |
| `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:wrong:001` | `abstain` | `replace` | `0.679` | `0.6892` | `0.0` | `-0.0102` | `-0.6892` | incorrect or improper | treat unjustly; do wrong to | `none` | active_modifier_frame |
| `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:stretch:001` | `abstain` | `replace` | `0.7496` | `0.7342` | `0.0` | `0.0155` | `-0.7496` | stretch noun sense: act of stretching | become longer by being stretched and pulled | `none` | active_noun_frame |
| `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:score:001` | `abstain` | `replace` | `0.7298` | `0.7096` | `0.0` | `0.0202` | `-0.7298` | score noun sense: number of points earned | score noun sense: number of points accrued | `none` | active_noun_frame |
| `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:squeeze:001` | `abstain` | `replace` | `0.683` | `0.734` | `0.0` | `-0.051` | `-0.734` | squeeze noun sense: difficult position | squeeze like a wedge into a tight space | `none` | active_noun_frame |
| `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:foul:001` | `abstain` | `replace` | `0.5938` | `0.6342` | `0.0` | `-0.0403` | `-0.6342` | foul noun sense: offence in sports | The industrial wastes polluted the lake | `none` | active_noun_frame |

## Limitations

- `bounded_non_benchmark_slice_not_full_en_es_proof`
- `semantic_active_shadow_only_phrase_policy_excluded`
- `does_not_audit_runtime_packaging_or_latency`

## Next Steps

- expand held-out families and cases without tuning on this v2 result
- add phrase-sensitive held-out rows under a separate phrase-source policy harness
- freeze the promotion-candidate evidence manifest before broad source scaling
