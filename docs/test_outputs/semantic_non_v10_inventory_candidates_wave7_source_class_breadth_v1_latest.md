# en-es Non-v10 Semantic Inventory Candidates

- Status: `ok`
- Decision: `inventory_candidates_found`
- Generated: `2026-04-30T17:56:17Z`
- Candidate count: `100`
- Cross-POS candidates: `100`
- Noun/verb candidates: `100`
- Same-POS polysemy candidates: `100`
- Existing triggers excluded: `59`
- Min score: `5.0`

## Top Candidates

| Rank | Trigger | Score | Band | Archetype | POS counts | Examples | Definitions |
| ---: | --- | ---: | --- | --- | --- | ---: | ---: |
| `1` | `blue` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `adjective:8, noun:7, verb:1` | `51` | `16` |
| `2` | `fit` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `adjective:3, noun:4, verb:9` | `40` | `16` |
| `3` | `range` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:9, verb:8` | `38` | `17` |
| `4` | `find` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:2, verb:15` | `36` | `17` |
| `5` | `rough` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `adjective:14, noun:1, adverb:2, verb:1` | `35` | `18` |
| `6` | `control` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:11, verb:9` | `34` | `20` |
| `7` | `home` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `adjective:3, noun:9, adverb:3, verb:2` | `34` | `17` |
| `8` | `think` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:1, verb:13` | `33` | `14` |
| `9` | `cool` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `adjective:7, noun:2, verb:3` | `33` | `12` |
| `10` | `hang` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:3, verb:15` | `30` | `18` |
| `11` | `true` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `adjective:12, noun:1, adverb:1, verb:1` | `30` | `15` |
| `12` | `render` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:1, verb:13` | `30` | `14` |
| `13` | `reach` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:4, verb:9` | `30` | `13` |
| `14` | `like` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `adjective:4, noun:2, verb:5` | `30` | `11` |
| `15` | `gross` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `adjective:7, noun:2, verb:1` | `30` | `10` |
| `16` | `cast` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:9, verb:11` | `29` | `20` |
| `17` | `level` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `adjective:5, noun:8, verb:6` | `29` | `19` |
| `18` | `fix` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:5, verb:13` | `29` | `18` |
| `19` | `act` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:5, verb:9` | `29` | `14` |
| `20` | `full` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `adjective:8, noun:1, adverb:1, verb:3` | `29` | `13` |
| `21` | `pay` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:1, verb:11` | `29` | `12` |
| `22` | `know` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:1, verb:10` | `29` | `11` |
| `23` | `walk` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:7, verb:10` | `28` | `17` |
| `24` | `waste` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `adjective:1, noun:5, verb:10` | `28` | `16` |
| `25` | `issue` | `16.1` | `broad` | `wordnet_noun_verb_cross_pos` | `noun:11, verb:5` | `28` | `16` |

## Limitations

- `english_headword_inventory_only_no_spanish_target_family_yet`
- `wordnet_polysemy_is_a_source_availability_prior_not_user_frequency`
- `requires downstream translation_target_shadow_construction_before_admission`

## Next Steps

- select a bounded wave from the ranked candidates without editing the current seed slice
- construct active/shadow Spanish target families for the selected wave
- run WordNet definition-preferred source extraction and the source-admission cycle
- evaluate new held-out rows and rerun failure-class mining before algorithm changes
