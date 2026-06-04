# en-es Non-v10 Semantic Inventory Candidates

- Status: `ok`
- Decision: `inventory_candidates_found`
- Generated: `2026-04-27T21:58:48Z`
- Candidate count: `75`
- Cross-POS candidates: `75`
- Noun/verb candidates: `75`
- Same-POS polysemy candidates: `75`
- Existing triggers excluded: `27`
- Min score: `5.0`

## Top Candidates

| Rank | Trigger | Score | Band | Archetype | POS counts | Examples | Definitions |
| ---: | --- | ---: | --- | --- | --- | ---: | ---: |
| `1` | `leave` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:3, verb:14` | `55` | `17` |
| `2` | `blue` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `adjective:8, noun:7, verb:1` | `51` | `16` |
| `3` | `black` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `adjective:14, noun:4, verb:1` | `45` | `19` |
| `4` | `change` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:10, verb:10` | `41` | `20` |
| `5` | `serve` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:1, verb:15` | `41` | `16` |
| `6` | `look` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:4, verb:10` | `41` | `14` |
| `7` | `dry` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `adjective:16, noun:1, verb:2` | `40` | `19` |
| `8` | `fit` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `adjective:3, noun:4, verb:9` | `40` | `16` |
| `9` | `low` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `adjective:10, noun:3, adverb:1, verb:1` | `40` | `15` |
| `10` | `part` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:13, adverb:1, verb:5` | `39` | `19` |
| `11` | `range` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:9, verb:8` | `38` | `17` |
| `12` | `feel` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:4, verb:13` | `38` | `17` |
| `13` | `use` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:7, verb:6` | `38` | `13` |
| `14` | `still` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `adjective:6, noun:4, adverb:4, verb:4` | `37` | `18` |
| `15` | `bear` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:2, verb:14` | `37` | `16` |
| `16` | `find` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:2, verb:15` | `36` | `17` |
| `17` | `finish` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:9, verb:6` | `36` | `15` |
| `18` | `throw` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:5, verb:15` | `35` | `20` |
| `19` | `rough` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `adjective:14, noun:1, adverb:2, verb:1` | `35` | `18` |
| `20` | `plain` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `adjective:7, noun:2, adverb:1, verb:1` | `35` | `11` |
| `21` | `control` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:11, verb:9` | `34` | `20` |
| `22` | `upset` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `adjective:5, noun:6, verb:6` | `34` | `17` |
| `23` | `home` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `adjective:3, noun:9, adverb:3, verb:2` | `34` | `17` |
| `24` | `fast` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `adjective:10, noun:1, adverb:2, verb:2` | `34` | `15` |
| `25` | `piece` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:13, verb:5` | `33` | `18` |

## Limitations

- `english_headword_inventory_only_no_spanish_target_family_yet`
- `wordnet_polysemy_is_a_source_availability_prior_not_user_frequency`
- `requires downstream translation_target_shadow_construction_before_admission`

## Next Steps

- select a bounded wave from the ranked candidates without editing the current seed slice
- construct active/shadow Spanish target families for the selected wave
- run WordNet definition-preferred source extraction and the source-admission cycle
- evaluate new held-out rows and rerun failure-class mining before algorithm changes
