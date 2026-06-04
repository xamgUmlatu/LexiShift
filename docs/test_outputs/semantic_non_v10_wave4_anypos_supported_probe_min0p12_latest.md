# en-es Non-v10 Source Wave Draft

- Status: `review`
- Decision: `partial_draft_wave_ready_for_source_linkage`
- Generated: `2026-04-28T01:14:51Z`
- Wave: `source_non_v10_wave4_anypos_supported_probe_min0p12`
- Selected families: `16` / `64`
- Reverse-supported families: `7`
- FreeDict-supported families: `16`
- WordNet-link-supported families: `16`
- Readiness reason: `not_enough_candidate_translations_for_requested_wave_size`

## Draft Families

| Rank | Trigger | Active | Shadows | Reverse support | FreeDict support |
| ---: | --- | --- | --- | --- | --- |
| `1` | `change` | `cambio (noun)` | `cambiar (verb)` | `False` | `True` |
| `2` | `look` | `aspecto (noun)` | `parecer (verb)` | `False` | `True` |
| `3` | `dry` | `seco (adjective)` | `secar (verb)` | `True` | `True` |
| `4` | `use` | `uso (noun)` | `usar (verb)` | `True` | `True` |
| `5` | `plain` | `llano (adjective)` | `llanura (noun)` | `True` | `True` |
| `6` | `fast` | `rápido (adjective)` | `ayunar (verb)` | `False` | `True` |
| `7` | `train` | `tren (noun)` | `adiestrar (verb)` | `True` | `True` |
| `8` | `land` | `tierra (noun)` | `país (noun), atracar (verb)` | `False` | `True` |
| `9` | `mean` | `medio (adjective)` | `significar (verb)` | `False` | `True` |
| `10` | `end` | `fin (noun)` | `acabar (verb)` | `True` | `True` |
| `11` | `offer` | `oferta (noun)` | `ofrecer (verb)` | `False` | `True` |
| `12` | `rest` | `reposo (noun)` | `descanso (noun), descansar (verb)` | `True` | `True` |
| `13` | `present` | `presente (adjective)` | `actual (noun)` | `False` | `True` |
| `14` | `sign` | `señal (noun)` | `seña (noun), firmar (verb)` | `True` | `True` |
| `15` | `answer` | `respuesta (noun)` | `contestación (noun), responder (verb)` | `False` | `True` |
| `16` | `quiet` | `silencio (noun)` | `calmar (verb)` | `False` | `True` |

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
