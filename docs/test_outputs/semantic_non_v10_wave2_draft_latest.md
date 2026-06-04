# en-es Non-v10 Source Wave Draft

- Status: `review`
- Decision: `draft_wave_ready_for_source_linkage`
- Generated: `2026-04-27T22:23:06Z`
- Wave: `source_non_v10_wave2_draft_v1`
- Selected families: `8` / `8`
- Reverse-supported families: `3`
- FreeDict-supported families: `8`
- WordNet-link-supported families: `8`
- Readiness reason: `translation_family_draft_complete_but_unreviewed`

## Draft Families

| Rank | Trigger | Active | Shadows | Reverse support | FreeDict support |
| ---: | --- | --- | --- | --- | --- |
| `1` | `look` | `aspecto (noun)` | `parecer (verb)` | `False` | `True` |
| `2` | `use` | `uso (noun)` | `usar (verb)` | `True` | `True` |
| `3` | `train` | `tren (noun)` | `adiestrar (verb)` | `True` | `True` |
| `4` | `land` | `tierra (noun)` | `país (noun), atracar (verb)` | `False` | `True` |
| `5` | `end` | `fin (noun)` | `acabar (verb)` | `True` | `True` |
| `6` | `offer` | `oferta (noun)` | `ofrecer (verb)` | `False` | `True` |
| `7` | `sign` | `seña (noun)` | `firmar (verb)` | `False` | `True` |
| `8` | `quiet` | `silencio (noun)` | `calmar (verb)` | `False` | `True` |

## Skipped Candidates

| Trigger | Reason |
| --- | --- |
| `leave` | `missing_reverse_or_freedict_supported_noun_or_verb_translation` |
| `blue` | `missing_wordnet_linked_noun_or_verb_translation` |
| `black` | `missing_noun_or_verb_translation` |
| `change` | `missing_distinct_noun_or_verb_translation` |
| `serve` | `missing_reverse_or_freedict_supported_noun_or_verb_translation` |
| `dry` | `missing_noun_or_verb_translation` |
| `fit` | `missing_wordnet_linked_noun_or_verb_translation` |
| `low` | `missing_noun_or_verb_translation` |
| `part` | `missing_reverse_or_freedict_supported_noun_or_verb_translation` |
| `range` | `missing_noun_or_verb_translation` |
| `feel` | `missing_reverse_or_freedict_supported_noun_or_verb_translation` |
| `still` | `missing_wordnet_linked_noun_or_verb_translation` |

## Limitations

- `draft_translation_family_requires_review_before_quality_claims`
- `only_loader_seed_cases_generated_no_heldout_cases_in_this_step`
- `wordnet_source_admission_can_test_source_linkage_but_not_end_to_end_quality`

## Next Steps

- run WordNet definition-preferred extraction on the draft dataset
- run source admission with ablation skipped until independent cases exist
- review or generate held-out active/shadow cases for the admitted draft families
- rerun failure-class mining once held-out validation exists for the new wave
