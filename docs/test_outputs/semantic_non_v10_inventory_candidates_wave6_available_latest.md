# en-es Non-v10 Semantic Inventory Candidates

- Status: `ok`
- Decision: `inventory_candidates_found`
- Generated: `2026-04-29T00:19:41Z`
- Candidate count: `100`
- Cross-POS candidates: `100`
- Noun/verb candidates: `100`
- Same-POS polysemy candidates: `100`
- Existing triggers excluded: `43`
- Min score: `5.0`

## Top Candidates

| Rank | Trigger | Score | Band | Archetype | POS counts | Examples | Definitions |
| ---: | --- | ---: | --- | --- | --- | ---: | ---: |
| `1` | `leave` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:3, verb:14` | `55` | `17` |
| `2` | `blue` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `adjective:8, noun:7, verb:1` | `51` | `16` |
| `3` | `black` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `adjective:14, noun:4, verb:1` | `45` | `19` |
| `4` | `serve` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:1, verb:15` | `41` | `16` |
| `5` | `fit` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `adjective:3, noun:4, verb:9` | `40` | `16` |
| `6` | `low` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `adjective:10, noun:3, adverb:1, verb:1` | `40` | `15` |
| `7` | `part` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:13, adverb:1, verb:5` | `39` | `19` |
| `8` | `range` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:9, verb:8` | `38` | `17` |
| `9` | `feel` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:4, verb:13` | `38` | `17` |
| `10` | `still` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `adjective:6, noun:4, adverb:4, verb:4` | `37` | `18` |
| `11` | `bear` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:2, verb:14` | `37` | `16` |
| `12` | `find` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:2, verb:15` | `36` | `17` |
| `13` | `finish` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:9, verb:6` | `36` | `15` |
| `14` | `throw` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:5, verb:15` | `35` | `20` |
| `15` | `rough` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `adjective:14, noun:1, adverb:2, verb:1` | `35` | `18` |
| `16` | `control` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:11, verb:9` | `34` | `20` |
| `17` | `upset` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `adjective:5, noun:6, verb:6` | `34` | `17` |
| `18` | `home` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `adjective:3, noun:9, adverb:3, verb:2` | `34` | `17` |
| `19` | `piece` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:13, verb:5` | `33` | `18` |
| `20` | `think` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:1, verb:13` | `33` | `14` |
| `21` | `cool` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `adjective:7, noun:2, verb:3` | `33` | `12` |
| `22` | `fair` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `adjective:10, noun:4, adverb:2, verb:1` | `31` | `17` |
| `23` | `show` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:3, verb:12` | `31` | `15` |
| `24` | `advance` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `adjective:2, noun:6, verb:12` | `30` | `20` |
| `25` | `hang` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:3, verb:15` | `30` | `18` |

## Limitations

- `english_headword_inventory_only_no_spanish_target_family_yet`
- `wordnet_polysemy_is_a_source_availability_prior_not_user_frequency`
- `requires downstream translation_target_shadow_construction_before_admission`

## Next Steps

- select a bounded wave from the ranked candidates without editing the current seed slice
- construct active/shadow Spanish target families for the selected wave
- run WordNet definition-preferred source extraction and the source-admission cycle
- evaluate new held-out rows and rerun failure-class mining before algorithm changes
