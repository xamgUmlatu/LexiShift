# en-es Non-v10 Source Support Conversion Audit

- Status: `review`
- Decision: `support_conversion_needed`
- Dataset: `en_es_source_non_v10_wave7_source_class_breadth_v1_unsupported_selected`
- Generated: `2026-04-30T17:57:37Z`
- Translation support mode: `forward_only_upper_bound`
- Families: `16`
- Fully supported families: `0`
- Candidate-swap review families: `0`
- Needs reviewed source support: `16`
- Supported senses: `7` / `37`
- Unsupported active/shadow senses: `11` / `19`

## Family Conversion Table

| Trigger | State | Supported senses | Unsupported | Active | Shadows |
| --- | --- | ---: | ---: | --- | --- |
| `like` | `needs_reviewed_source_support` | `0 / 2` | `2` | `gustos` | `atraer` |
| `gross` | `needs_reviewed_source_support` | `0 / 2` | `2` | `repulsivo` | `gruesa` |
| `cast` | `needs_reviewed_source_support` | `0 / 3` | `3` | `lanzamiento` | `molde, lanzar` |
| `fix` | `needs_reviewed_source_support` | `1 / 3` | `2` | `aprieto` | `localización, reparar` |
| `full` | `needs_reviewed_source_support` | `1 / 2` | `1` | `lleno` | `abatanar` |
| `waste` | `needs_reviewed_source_support` | `1 / 3` | `2` | `desperdicio` | `baldío, malgastar` |
| `firm` | `needs_reviewed_source_support` | `1 / 2` | `1` | `firma` | `afirmar` |
| `even` | `needs_reviewed_source_support` | `0 / 2` | `2` | `tarde` | `allanar` |
| `wrong` | `needs_reviewed_source_support` | `0 / 2` | `2` | `incorrecto` | `herir` |
| `meet` | `needs_reviewed_source_support` | `1 / 2` | `1` | `adecuado` | `encontrar` |
| `stretch` | `needs_reviewed_source_support` | `1 / 2` | `1` | `estirón` | `estirar` |
| `score` | `needs_reviewed_source_support` | `1 / 3` | `2` | `tantos` | `marcador, anotar` |
| `crash` | `needs_reviewed_source_support` | `0 / 3` | `3` | `choque` | `fallo, chocar` |
| `trim` | `needs_reviewed_source_support` | `0 / 2` | `2` | `compensador` | `recortar` |
| `squeeze` | `needs_reviewed_source_support` | `0 / 2` | `2` | `crisis` | `apretujar` |
| `foul` | `needs_reviewed_source_support` | `0 / 2` | `2` | `falta` | `ensuciar` |

## Unsupported Sense Details

| Trigger | Role | Target | POS | State | Same-POS supported alternatives |
| --- | --- | --- | --- | --- | --- |
| `like` | `active` | `gustos` | `noun` | `needs_reviewed_source_support` | `none` |
| `like` | `shadow` | `atraer` | `verb` | `needs_reviewed_source_support` | `none` |
| `gross` | `active` | `repulsivo` | `adjective` | `needs_reviewed_source_support` | `none` |
| `gross` | `shadow` | `gruesa` | `noun` | `needs_reviewed_source_support` | `none` |
| `cast` | `active` | `lanzamiento` | `noun` | `needs_reviewed_source_support` | `none` |
| `cast` | `shadow` | `molde` | `noun` | `needs_reviewed_source_support` | `none` |
| `cast` | `shadow` | `lanzar` | `verb` | `needs_reviewed_source_support` | `none` |
| `fix` | `active` | `aprieto` | `noun` | `needs_reviewed_source_support` | `none` |
| `fix` | `shadow` | `localización` | `noun` | `needs_reviewed_source_support` | `none` |
| `full` | `shadow` | `abatanar` | `verb` | `needs_reviewed_source_support` | `none` |
| `waste` | `shadow` | `baldío` | `noun` | `candidate_swap_review_available` | `desechos (3)` |
| `waste` | `shadow` | `malgastar` | `verb` | `needs_reviewed_source_support` | `none` |
| `firm` | `shadow` | `afirmar` | `verb` | `needs_reviewed_source_support` | `none` |
| `even` | `active` | `tarde` | `noun` | `needs_reviewed_source_support` | `none` |
| `even` | `shadow` | `allanar` | `verb` | `needs_reviewed_source_support` | `none` |
| `wrong` | `active` | `incorrecto` | `adjective` | `needs_reviewed_source_support` | `none` |
| `wrong` | `shadow` | `herir` | `verb` | `needs_reviewed_source_support` | `none` |
| `meet` | `active` | `adecuado` | `adjective` | `needs_reviewed_source_support` | `none` |
| `stretch` | `shadow` | `estirar` | `verb` | `needs_reviewed_source_support` | `none` |
| `score` | `shadow` | `marcador` | `noun` | `needs_reviewed_source_support` | `none` |
| `score` | `shadow` | `anotar` | `verb` | `needs_reviewed_source_support` | `none` |
| `crash` | `active` | `choque` | `noun` | `needs_reviewed_source_support` | `none` |
| `crash` | `shadow` | `fallo` | `noun` | `needs_reviewed_source_support` | `none` |
| `crash` | `shadow` | `chocar` | `verb` | `needs_reviewed_source_support` | `none` |
| `trim` | `active` | `compensador` | `noun` | `needs_reviewed_source_support` | `none` |
| `trim` | `shadow` | `recortar` | `verb` | `needs_reviewed_source_support` | `none` |
| `squeeze` | `active` | `crisis` | `noun` | `needs_reviewed_source_support` | `none` |
| `squeeze` | `shadow` | `apretujar` | `verb` | `needs_reviewed_source_support` | `none` |
| `foul` | `active` | `falta` | `noun` | `needs_reviewed_source_support` | `none` |
| `foul` | `shadow` | `ensuciar` | `verb` | `needs_reviewed_source_support` | `none` |

## Support Acquisition Worklist

| Priority | Trigger | Role | Target | State | Source lanes |
| ---: | --- | --- | --- | --- | --- |
| `0` | `cast` | `active` | `lanzamiento` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `0` | `crash` | `active` | `choque` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `0` | `even` | `active` | `tarde` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `0` | `fix` | `active` | `aprieto` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `0` | `foul` | `active` | `falta` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `0` | `gross` | `active` | `repulsivo` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `0` | `like` | `active` | `gustos` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `0` | `meet` | `active` | `adecuado` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `0` | `squeeze` | `active` | `crisis` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `0` | `trim` | `active` | `compensador` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `0` | `wrong` | `active` | `incorrecto` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `1` | `waste` | `shadow` | `baldío` | `candidate_swap_review_available` | `review_same_pos_supported_target_swap, reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `2` | `cast` | `shadow` | `lanzar` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `2` | `cast` | `shadow` | `molde` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `2` | `crash` | `shadow` | `chocar` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `2` | `crash` | `shadow` | `fallo` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `2` | `even` | `shadow` | `allanar` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `2` | `firm` | `shadow` | `afirmar` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `2` | `fix` | `shadow` | `localización` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `2` | `foul` | `shadow` | `ensuciar` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `2` | `full` | `shadow` | `abatanar` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `2` | `gross` | `shadow` | `gruesa` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `2` | `like` | `shadow` | `atraer` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `2` | `score` | `shadow` | `anotar` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `2` | `score` | `shadow` | `marcador` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `2` | `squeeze` | `shadow` | `apretujar` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `2` | `stretch` | `shadow` | `estirar` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `2` | `trim` | `shadow` | `recortar` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `2` | `waste` | `shadow` | `malgastar` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `2` | `wrong` | `shadow` | `herir` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |

## Limitations

- `conversion_audit_does_not_change_selected_family_targets`
- `same_pos_alternatives_require_review_and_re_admission_before_use`
- `forward_only_rows_are_not_promotion_evidence_without_source_support`
- `phrase_containment_coverage_is_out_of_scope_for_this_audit`

## Next Steps

- add reverse/FreeDict/Wiktextract/reviewed translation support for rows without supported alternatives
- materialize only a supported selected wave after source support is complete
- add independent active/shadow and phrase held-out cases before quality claims
