# en-es Semantic Source Held-out Validation

- Status: `review`
- Decision: `heldout_review`
- Generated: `2026-04-29T03:34:28Z`
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
- False abstains: `7` / max `0`
- Replace recall: `56.2%`
- Decision accuracy: `81.6%`

## Configured Row

| Source | Scorer | Context | Margin | Phrase Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `promotion_candidate_composite` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.02 | `active_shadow_phrase_semantic_prototypes` | 38 | 0 | 7 | 56.2% | 81.6% |

## Empty Baseline Comparator

| Source | Scorer | Context | Margin | Phrase Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `empty_batch` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.02 | `active_shadow_phrase_semantic_prototypes` | 38 | 0 | 16 | 0.0% | 57.9% |

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
- False abstain cases: `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:serve:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:finish:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:throw:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:upset:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:piece:001`

| Case | Gold | Predicted | Active | Shadow | Phrase | Margin | Phrase Lead | Active Evidence | Shadow Evidence | Phrase Evidence | Signals |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |
| `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001` | `replace` | `abstain` | `0.5801` | `0.5936` | `0.5699` | `-0.0135` | `-0.0237` | a ten day's leave to visit his mother | the period of time during which you are absent from work or duty | go away from a place example: At what time does your train leave? | `none` |
| `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001` | `replace` | `abstain` | `0.544` | `0.5115` | `0.6064` | `0.0325` | `0.0625` | black adjective sense: without light | the quality or state of the achromatic color of least lightness (bearing the least resemblance to white) | offering little or no hope example: the future looked black | `none` |
| `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:serve:001` | `replace` | `abstain` | `0.5642` | `0.5757` | `0.6086` | `-0.0115` | `0.0329` | his powerful serves won the game | serve verb sense: to work for | devote (part of) one's life or efforts to, as of countries, institutions, or ideas example: She served the art of music | `none` |
| `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:finish:001` | `replace` | `abstain` | `0.5972` | `0.6727` | `0.6714` | `-0.0754` | `-0.0013` | the temporal end; the concluding time | come or bring to a finish or an end | finish eating all the food on one's plate or on the table example: She polished off the remaining potatoes | `none` |
| `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:throw:001` | `replace` | `abstain` | `0.5208` | `0.5571` | `0.6607` | `-0.0362` | `0.1036` | throw noun sense: flight of a thrown object | propel through the air | to remove example: he shed his image as a pushy boss | `none` |
| `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:upset:001` | `replace` | `abstain` | `0.5598` | `0.5805` | `0.6072` | `-0.0207` | `0.0267` | afflicted with or marked by anxious uneasiness or trouble or grief | upset verb sense: disturb, disrupt, unfavorably alter | used of an unexpected defeat of a team favored to win example: the Bills' upset victory over the Houston Oilers | `none` |
| `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:piece:001` | `replace` | `abstain` | `0.597` | `0.6779` | `0.712` | `-0.0809` | `0.0341` | piece noun sense: part of a larger whole | She pieced a quilt | a serving that has been cut from a larger portion example: a piece of pie | `none` |

## Limitations

- `bounded_non_benchmark_slice_not_full_en_es_proof`
- `semantic_active_shadow_only_phrase_policy_excluded`
- `does_not_audit_runtime_packaging_or_latency`

## Next Steps

- expand held-out families and cases without tuning on this v2 result
- add phrase-sensitive held-out rows under a separate phrase-source policy harness
- freeze the promotion-candidate evidence manifest before broad source scaling
