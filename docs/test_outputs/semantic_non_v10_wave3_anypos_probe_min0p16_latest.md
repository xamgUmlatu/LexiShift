# en-es Non-v10 Source Wave Draft

- Status: `review`
- Decision: `partial_draft_wave_ready_for_source_linkage`
- Generated: `2026-04-27T23:10:04Z`
- Wave: `source_non_v10_wave3_anypos_probe_min0p16`
- Selected families: `15` / `32`
- Reverse-supported families: `6`
- FreeDict-supported families: `15`
- WordNet-link-supported families: `15`
- Readiness reason: `not_enough_candidate_translations_for_requested_wave_size`

## Draft Families

| Rank | Trigger | Active | Shadows | Reverse support | FreeDict support |
| ---: | --- | --- | --- | --- | --- |
| `1` | `change` | `cambio (noun)` | `cambiar (verb)` | `False` | `True` |
| `2` | `look` | `aspecto (noun)` | `parecer (verb)` | `False` | `True` |
| `3` | `dry` | `seco (adjective)` | `secar (verb)` | `True` | `True` |
| `4` | `use` | `uso (noun)` | `usar (verb)` | `True` | `True` |
| `5` | `fast` | `rápido (adjective)` | `ayunar (verb)` | `False` | `True` |
| `6` | `train` | `tren (noun)` | `adiestrar (verb)` | `True` | `True` |
| `7` | `land` | `tierra (noun)` | `país (noun), atracar (verb)` | `False` | `True` |
| `8` | `mean` | `medio (adjective)` | `significar (verb)` | `False` | `True` |
| `9` | `end` | `fin (noun)` | `acabar (verb)` | `True` | `True` |
| `10` | `offer` | `oferta (noun)` | `ofrecer (verb)` | `False` | `True` |
| `11` | `rest` | `reposo (noun)` | `descansar (verb)` | `True` | `True` |
| `12` | `present` | `presente (adjective)` | `actual (noun)` | `False` | `True` |
| `13` | `sign` | `señal (noun)` | `seña (noun), firmar (verb)` | `True` | `True` |
| `14` | `answer` | `respuesta (noun)` | `contestación (noun), responder (verb)` | `False` | `True` |
| `15` | `quiet` | `silencio (noun)` | `calmar (verb)` | `False` | `True` |

## Skipped Candidates

| Trigger | Reason |
| --- | --- |
| `leave` | `missing_reverse_or_freedict_supported_cross_pos_translation` |
| `blue` | `missing_wordnet_linked_cross_pos_translation` |
| `black` | `missing_reverse_or_freedict_supported_cross_pos_translation` |
| `serve` | `missing_reverse_or_freedict_supported_cross_pos_translation` |
| `fit` | `missing_reverse_or_freedict_supported_cross_pos_translation` |
| `low` | `missing_reverse_or_freedict_supported_cross_pos_translation` |
| `part` | `missing_reverse_or_freedict_supported_cross_pos_translation` |
| `range` | `missing_cross_pos_translation` |
| `feel` | `missing_reverse_or_freedict_supported_cross_pos_translation` |
| `still` | `missing_reverse_or_freedict_supported_cross_pos_translation` |
| `bear` | `missing_reverse_or_freedict_supported_cross_pos_translation` |
| `find` | `missing_wordnet_linked_cross_pos_translation` |

## Limitations

- `draft_translation_family_requires_review_before_quality_claims`
- `only_loader_seed_cases_generated_no_heldout_cases_in_this_step`
- `wordnet_source_admission_can_test_source_linkage_but_not_end_to_end_quality`

## Next Steps

- run WordNet definition-preferred extraction on the draft dataset
- run source admission with ablation skipped until independent cases exist
- review or generate held-out active/shadow cases for the admitted draft families
- rerun failure-class mining once held-out validation exists for the new wave
