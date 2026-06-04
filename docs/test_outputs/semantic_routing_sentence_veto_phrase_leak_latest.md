# Semantic Routing Sentence Veto Phrase-Leak Probe

- Status: `ok`
- Generated: `2026-04-23T19:15:34Z`
- Dataset: `docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v10.json`
- Pair: `en-es`
- Focus cases: `en-es:sentence-veto:play:001, en-es:sentence-veto:play:002, en-es:sentence-veto:play:003, en-es:sentence-veto:play:004, en-es:sentence-veto:play:005, en-es:sentence-veto:watch:001, en-es:sentence-veto:watch:002, en-es:sentence-veto:watch:003, en-es:sentence-veto:watch:004, en-es:sentence-veto:watch:005, en-es:sentence-veto:drink:001, en-es:sentence-veto:drink:002, en-es:sentence-veto:drink:005, en-es:sentence-veto:park:001, en-es:sentence-veto:park:005, en-es:sentence-veto:check:001, en-es:sentence-veto:check:002, en-es:sentence-veto:check:005, en-es:sentence-veto:order:001, en-es:sentence-veto:order:002, en-es:sentence-veto:order:005, en-es:sentence-veto:trip:001, en-es:sentence-veto:trip:002, en-es:sentence-veto:trip:005, en-es:sentence-veto:report:001, en-es:sentence-veto:report:002, en-es:sentence-veto:report:005`
- Base scorer: `sentence_transformer_cosine`
- Base context / evidence: `masked_sentence` / `all_evidence_text`

## Hard-Row Comparison

| Config | POS Scope | Harmful | False Abstain | Replace Recall | Decision Acc. | Phrase Hits | Rescue Cases |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Current mixed-POS phrase guard | family_all | 1 | 9 | 76.3% | 89.5% | 7 | `en-es:sentence-veto:ball:002`, `en-es:sentence-veto:drink:001`, `en-es:sentence-veto:play:001` |
| Active-sense noun phrase guard | active_only | 0 | 9 | 76.3% | 90.5% | 21 | `en-es:sentence-veto:ball:002`, `en-es:sentence-veto:drink:001`, `en-es:sentence-veto:play:001` |

## Hard-Row Delta

- Changed decision cases: `en-es:sentence-veto:play:005`
  - `en-es:sentence-veto:play:005`: `replace` -> `abstain` | phrase `` -> `modal_trigger_frame`
- Newly phrase-preempted without decision change: `en-es:sentence-veto:park:003`, `en-es:sentence-veto:park:004`, `en-es:sentence-veto:park:005`, `en-es:sentence-veto:drink:003`, `en-es:sentence-veto:drink:004`, `en-es:sentence-veto:drink:005`, `en-es:sentence-veto:play:004`, `en-es:sentence-veto:watch:005`, `en-es:sentence-veto:check:003`, `en-es:sentence-veto:check:005`, `en-es:sentence-veto:order:005`, `en-es:sentence-veto:trip:005`, `en-es:sentence-veto:report:005`

## Overlay Comparison

| Config | POS Scope | Harmful | False Abstain | Replace Recall | Decision Acc. | Phrase Hits | Rescue Cases |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Current widened overlay | family_all | 1 | 6 | 84.2% | 92.6% | 7 | `en-es:sentence-veto:ball:002`, `en-es:sentence-veto:plant:002`, `en-es:sentence-veto:park:001`, `en-es:sentence-veto:drink:001`, `en-es:sentence-veto:drink:002`, `en-es:sentence-veto:play:001` |
| Active-sense noun guard overlay | active_only | 0 | 6 | 84.2% | 93.7% | 21 | `en-es:sentence-veto:ball:002`, `en-es:sentence-veto:plant:002`, `en-es:sentence-veto:park:001`, `en-es:sentence-veto:drink:001`, `en-es:sentence-veto:drink:002`, `en-es:sentence-veto:play:001` |

## Overlay Delta

- Changed decision cases: `en-es:sentence-veto:play:005`
  - `en-es:sentence-veto:play:005`: `replace` -> `abstain` | phrase `` -> `modal_trigger_frame`
- Newly phrase-preempted without decision change: `en-es:sentence-veto:park:003`, `en-es:sentence-veto:park:004`, `en-es:sentence-veto:park:005`, `en-es:sentence-veto:drink:003`, `en-es:sentence-veto:drink:004`, `en-es:sentence-veto:drink:005`, `en-es:sentence-veto:play:004`, `en-es:sentence-veto:watch:005`, `en-es:sentence-veto:check:003`, `en-es:sentence-veto:check:005`, `en-es:sentence-veto:order:005`, `en-es:sentence-veto:trip:005`, `en-es:sentence-veto:report:005`

## Focus Case Outcomes

| Config | Case | Gold | Predicted | Phrase | Reason | Rescue |
| --- | --- | --- | --- | --- | --- | --- |
| current_default | en-es:sentence-veto:play:001 | replace | replace | no |  | yes |
| current_default | en-es:sentence-veto:play:002 | replace | abstain | no |  | no |
| current_default | en-es:sentence-veto:play:003 | abstain | abstain | no |  | no |
| current_default | en-es:sentence-veto:play:004 | abstain | abstain | no |  | no |
| current_default | en-es:sentence-veto:play:005 | abstain | replace | no |  | no |
| current_default | en-es:sentence-veto:watch:001 | replace | replace | no |  | no |
| current_default | en-es:sentence-veto:watch:002 | replace | replace | no |  | no |
| current_default | en-es:sentence-veto:watch:003 | abstain | abstain | no |  | no |
| current_default | en-es:sentence-veto:watch:004 | abstain | abstain | no |  | no |
| current_default | en-es:sentence-veto:watch:005 | abstain | abstain | no |  | no |
| current_default | en-es:sentence-veto:drink:001 | replace | replace | no |  | yes |
| current_default | en-es:sentence-veto:drink:002 | replace | abstain | no |  | no |
| current_default | en-es:sentence-veto:drink:005 | abstain | abstain | no |  | no |
| current_default | en-es:sentence-veto:park:001 | replace | abstain | no |  | no |
| current_default | en-es:sentence-veto:park:005 | abstain | abstain | no |  | no |
| current_default | en-es:sentence-veto:check:001 | replace | replace | no |  | no |
| current_default | en-es:sentence-veto:check:002 | replace | abstain | no |  | no |
| current_default | en-es:sentence-veto:check:005 | abstain | abstain | no |  | no |
| current_default | en-es:sentence-veto:order:001 | replace | replace | no |  | no |
| current_default | en-es:sentence-veto:order:002 | replace | abstain | no |  | no |
| current_default | en-es:sentence-veto:order:005 | abstain | abstain | no |  | no |
| current_default | en-es:sentence-veto:trip:001 | replace | replace | no |  | no |
| current_default | en-es:sentence-veto:trip:002 | replace | abstain | no |  | no |
| current_default | en-es:sentence-veto:trip:005 | abstain | abstain | no |  | no |
| current_default | en-es:sentence-veto:report:001 | replace | abstain | no |  | no |
| current_default | en-es:sentence-veto:report:002 | replace | abstain | no |  | no |
| current_default | en-es:sentence-veto:report:005 | abstain | abstain | no |  | no |
| active_only_phrase_guard | en-es:sentence-veto:play:001 | replace | replace | no |  | yes |
| active_only_phrase_guard | en-es:sentence-veto:play:002 | replace | abstain | no |  | no |
| active_only_phrase_guard | en-es:sentence-veto:play:003 | abstain | abstain | no |  | no |
| active_only_phrase_guard | en-es:sentence-veto:play:004 | abstain | abstain | yes | infinitive_trigger_frame | no |
| active_only_phrase_guard | en-es:sentence-veto:play:005 | abstain | abstain | yes | modal_trigger_frame | no |
| active_only_phrase_guard | en-es:sentence-veto:watch:001 | replace | replace | no |  | no |
| active_only_phrase_guard | en-es:sentence-veto:watch:002 | replace | replace | no |  | no |
| active_only_phrase_guard | en-es:sentence-veto:watch:003 | abstain | abstain | no |  | no |
| active_only_phrase_guard | en-es:sentence-veto:watch:004 | abstain | abstain | no |  | no |
| active_only_phrase_guard | en-es:sentence-veto:watch:005 | abstain | abstain | yes | modal_trigger_frame | no |
| active_only_phrase_guard | en-es:sentence-veto:drink:001 | replace | replace | no |  | yes |
| active_only_phrase_guard | en-es:sentence-veto:drink:002 | replace | abstain | no |  | no |
| active_only_phrase_guard | en-es:sentence-veto:drink:005 | abstain | abstain | yes | infinitive_trigger_frame | no |
| active_only_phrase_guard | en-es:sentence-veto:park:001 | replace | abstain | no |  | no |
| active_only_phrase_guard | en-es:sentence-veto:park:005 | abstain | abstain | yes | modal_trigger_frame | no |
| active_only_phrase_guard | en-es:sentence-veto:check:001 | replace | replace | no |  | no |
| active_only_phrase_guard | en-es:sentence-veto:check:002 | replace | abstain | no |  | no |
| active_only_phrase_guard | en-es:sentence-veto:check:005 | abstain | abstain | yes | modal_trigger_frame | no |
| active_only_phrase_guard | en-es:sentence-veto:order:001 | replace | replace | no |  | no |
| active_only_phrase_guard | en-es:sentence-veto:order:002 | replace | abstain | no |  | no |
| active_only_phrase_guard | en-es:sentence-veto:order:005 | abstain | abstain | yes | modal_trigger_frame | no |
| active_only_phrase_guard | en-es:sentence-veto:trip:001 | replace | replace | no |  | no |
| active_only_phrase_guard | en-es:sentence-veto:trip:002 | replace | abstain | no |  | no |
| active_only_phrase_guard | en-es:sentence-veto:trip:005 | abstain | abstain | yes | modal_trigger_frame | no |
| active_only_phrase_guard | en-es:sentence-veto:report:001 | replace | abstain | no |  | no |
| active_only_phrase_guard | en-es:sentence-veto:report:002 | replace | abstain | no |  | no |
| active_only_phrase_guard | en-es:sentence-veto:report:005 | abstain | abstain | yes | polite_imperative_trigger_frame | no |
| current_overlay | en-es:sentence-veto:play:001 | replace | replace | no |  | yes |
| current_overlay | en-es:sentence-veto:play:002 | replace | abstain | no |  | no |
| current_overlay | en-es:sentence-veto:play:003 | abstain | abstain | no |  | no |
| current_overlay | en-es:sentence-veto:play:004 | abstain | abstain | no |  | no |
| current_overlay | en-es:sentence-veto:play:005 | abstain | replace | no |  | no |
| current_overlay | en-es:sentence-veto:watch:001 | replace | replace | no |  | no |
| current_overlay | en-es:sentence-veto:watch:002 | replace | replace | no |  | no |
| current_overlay | en-es:sentence-veto:watch:003 | abstain | abstain | no |  | no |
| current_overlay | en-es:sentence-veto:watch:004 | abstain | abstain | no |  | no |
| current_overlay | en-es:sentence-veto:watch:005 | abstain | abstain | no |  | no |
| current_overlay | en-es:sentence-veto:drink:001 | replace | replace | no |  | yes |
| current_overlay | en-es:sentence-veto:drink:002 | replace | replace | no |  | yes |
| current_overlay | en-es:sentence-veto:drink:005 | abstain | abstain | no |  | no |
| current_overlay | en-es:sentence-veto:park:001 | replace | replace | no |  | yes |
| current_overlay | en-es:sentence-veto:park:005 | abstain | abstain | no |  | no |
| current_overlay | en-es:sentence-veto:check:001 | replace | replace | no |  | no |
| current_overlay | en-es:sentence-veto:check:002 | replace | abstain | no |  | no |
| current_overlay | en-es:sentence-veto:check:005 | abstain | abstain | no |  | no |
| current_overlay | en-es:sentence-veto:order:001 | replace | replace | no |  | no |
| current_overlay | en-es:sentence-veto:order:002 | replace | abstain | no |  | no |
| current_overlay | en-es:sentence-veto:order:005 | abstain | abstain | no |  | no |
| current_overlay | en-es:sentence-veto:trip:001 | replace | replace | no |  | no |
| current_overlay | en-es:sentence-veto:trip:002 | replace | abstain | no |  | no |
| current_overlay | en-es:sentence-veto:trip:005 | abstain | abstain | no |  | no |
| current_overlay | en-es:sentence-veto:report:001 | replace | abstain | no |  | no |
| current_overlay | en-es:sentence-veto:report:002 | replace | abstain | no |  | no |
| current_overlay | en-es:sentence-veto:report:005 | abstain | abstain | no |  | no |
| active_only_overlay | en-es:sentence-veto:play:001 | replace | replace | no |  | yes |
| active_only_overlay | en-es:sentence-veto:play:002 | replace | abstain | no |  | no |
| active_only_overlay | en-es:sentence-veto:play:003 | abstain | abstain | no |  | no |
| active_only_overlay | en-es:sentence-veto:play:004 | abstain | abstain | yes | infinitive_trigger_frame | no |
| active_only_overlay | en-es:sentence-veto:play:005 | abstain | abstain | yes | modal_trigger_frame | no |
| active_only_overlay | en-es:sentence-veto:watch:001 | replace | replace | no |  | no |
| active_only_overlay | en-es:sentence-veto:watch:002 | replace | replace | no |  | no |
| active_only_overlay | en-es:sentence-veto:watch:003 | abstain | abstain | no |  | no |
| active_only_overlay | en-es:sentence-veto:watch:004 | abstain | abstain | no |  | no |
| active_only_overlay | en-es:sentence-veto:watch:005 | abstain | abstain | yes | modal_trigger_frame | no |
| active_only_overlay | en-es:sentence-veto:drink:001 | replace | replace | no |  | yes |
| active_only_overlay | en-es:sentence-veto:drink:002 | replace | replace | no |  | yes |
| active_only_overlay | en-es:sentence-veto:drink:005 | abstain | abstain | yes | infinitive_trigger_frame | no |
| active_only_overlay | en-es:sentence-veto:park:001 | replace | replace | no |  | yes |
| active_only_overlay | en-es:sentence-veto:park:005 | abstain | abstain | yes | modal_trigger_frame | no |
| active_only_overlay | en-es:sentence-veto:check:001 | replace | replace | no |  | no |
| active_only_overlay | en-es:sentence-veto:check:002 | replace | abstain | no |  | no |
| active_only_overlay | en-es:sentence-veto:check:005 | abstain | abstain | yes | modal_trigger_frame | no |
| active_only_overlay | en-es:sentence-veto:order:001 | replace | replace | no |  | no |
| active_only_overlay | en-es:sentence-veto:order:002 | replace | abstain | no |  | no |
| active_only_overlay | en-es:sentence-veto:order:005 | abstain | abstain | yes | modal_trigger_frame | no |
| active_only_overlay | en-es:sentence-veto:trip:001 | replace | replace | no |  | no |
| active_only_overlay | en-es:sentence-veto:trip:002 | replace | abstain | no |  | no |
| active_only_overlay | en-es:sentence-veto:trip:005 | abstain | abstain | yes | modal_trigger_frame | no |
| active_only_overlay | en-es:sentence-veto:report:001 | replace | abstain | no |  | no |
| active_only_overlay | en-es:sentence-veto:report:002 | replace | abstain | no |  | no |
| active_only_overlay | en-es:sentence-veto:report:005 | abstain | abstain | yes | polite_imperative_trigger_frame | no |
