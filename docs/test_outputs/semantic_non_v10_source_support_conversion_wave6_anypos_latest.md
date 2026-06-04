# en-es Non-v10 Source Support Conversion Audit

- Status: `review`
- Decision: `support_conversion_needed`
- Dataset: `en_es_source_non_v10_wave6_anypos_unsupported_upper_bound_selected_v1`
- Generated: `2026-04-29T01:14:30Z`
- Translation support mode: `forward_only_upper_bound`
- Families: `16`
- Fully supported families: `0`
- Candidate-swap review families: `0`
- Needs reviewed source support: `16`
- Supported senses: `13` / `38`
- Unsupported active/shadow senses: `10` / `15`

## Family Conversion Table

| Trigger | State | Supported senses | Unsupported | Active | Shadows |
| --- | --- | ---: | ---: | --- | --- |
| `leave` | `needs_reviewed_source_support` | `1 / 3` | `2` | `permiso` | `excedencia, dejar` |
| `black` | `needs_reviewed_source_support` | `1 / 2` | `1` | `oscuro` | `negro` |
| `serve` | `needs_reviewed_source_support` | `1 / 2` | `1` | `servicio` | `servir` |
| `low` | `needs_reviewed_source_support` | `1 / 2` | `1` | `bajo` | `decaído` |
| `part` | `needs_reviewed_source_support` | `1 / 3` | `2` | `parte` | `papel, repartir` |
| `feel` | `needs_reviewed_source_support` | `1 / 2` | `1` | `talento` | `sentir` |
| `still` | `needs_reviewed_source_support` | `0 / 3` | `3` | `quietud` | `alambique, aquietar` |
| `bear` | `needs_reviewed_source_support` | `1 / 2` | `1` | `bajista` | `llevar` |
| `finish` | `needs_reviewed_source_support` | `1 / 3` | `2` | `meta` | `acabado, acabar` |
| `throw` | `needs_reviewed_source_support` | `1 / 2` | `1` | `lanzamiento` | `lanzar` |
| `upset` | `needs_reviewed_source_support` | `1 / 2` | `1` | `disgustado` | `trastrocar` |
| `piece` | `needs_reviewed_source_support` | `1 / 3` | `2` | `trozo` | `ficha, montar` |
| `fair` | `needs_reviewed_source_support` | `0 / 2` | `2` | `pastel` | `feria de muestras` |
| `show` | `needs_reviewed_source_support` | `0 / 2` | `2` | `espectáculo` | `demostrar` |
| `advance` | `needs_reviewed_source_support` | `1 / 3` | `2` | `avance` | `adelanto, avanzar` |
| `rank` | `needs_reviewed_source_support` | `1 / 2` | `1` | `rancio` | `fila` |

## Unsupported Sense Details

| Trigger | Role | Target | POS | State | Same-POS supported alternatives |
| --- | --- | --- | --- | --- | --- |
| `leave` | `active` | `permiso` | `noun` | `needs_reviewed_source_support` | `none` |
| `leave` | `shadow` | `excedencia` | `noun` | `needs_reviewed_source_support` | `none` |
| `black` | `active` | `oscuro` | `adjective` | `needs_reviewed_source_support` | `none` |
| `serve` | `active` | `servicio` | `noun` | `needs_reviewed_source_support` | `none` |
| `low` | `shadow` | `decaído` | `adjective` | `needs_reviewed_source_support` | `none` |
| `part` | `shadow` | `papel` | `noun` | `needs_reviewed_source_support` | `none` |
| `part` | `shadow` | `repartir` | `verb` | `needs_reviewed_source_support` | `none` |
| `feel` | `active` | `talento` | `noun` | `needs_reviewed_source_support` | `none` |
| `still` | `active` | `quietud` | `noun` | `needs_reviewed_source_support` | `none` |
| `still` | `shadow` | `alambique` | `noun` | `needs_reviewed_source_support` | `none` |
| `still` | `shadow` | `aquietar` | `verb` | `needs_reviewed_source_support` | `none` |
| `bear` | `shadow` | `llevar` | `verb` | `needs_reviewed_source_support` | `none` |
| `finish` | `active` | `meta` | `noun` | `needs_reviewed_source_support` | `none` |
| `finish` | `shadow` | `acabado` | `noun` | `needs_reviewed_source_support` | `none` |
| `throw` | `active` | `lanzamiento` | `noun` | `needs_reviewed_source_support` | `none` |
| `upset` | `shadow` | `trastrocar` | `verb` | `needs_reviewed_source_support` | `none` |
| `piece` | `shadow` | `ficha` | `noun` | `candidate_swap_review_available` | `pieza (1), pedazo (2)` |
| `piece` | `shadow` | `montar` | `verb` | `needs_reviewed_source_support` | `none` |
| `fair` | `active` | `pastel` | `adjective` | `needs_reviewed_source_support` | `none` |
| `fair` | `shadow` | `feria de muestras` | `noun` | `needs_reviewed_source_support` | `none` |
| `show` | `active` | `espectáculo` | `noun` | `needs_reviewed_source_support` | `none` |
| `show` | `shadow` | `demostrar` | `verb` | `needs_reviewed_source_support` | `none` |
| `advance` | `shadow` | `adelanto` | `noun` | `candidate_swap_review_available` | `progreso (7)` |
| `advance` | `shadow` | `avanzar` | `verb` | `needs_reviewed_source_support` | `none` |
| `rank` | `active` | `rancio` | `adjective` | `needs_reviewed_source_support` | `none` |

## Support Acquisition Worklist

| Priority | Trigger | Role | Target | State | Source lanes |
| ---: | --- | --- | --- | --- | --- |
| `0` | `black` | `active` | `oscuro` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `0` | `fair` | `active` | `pastel` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `0` | `feel` | `active` | `talento` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `0` | `finish` | `active` | `meta` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `0` | `leave` | `active` | `permiso` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `0` | `rank` | `active` | `rancio` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `0` | `serve` | `active` | `servicio` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `0` | `show` | `active` | `espectáculo` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `0` | `still` | `active` | `quietud` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `0` | `throw` | `active` | `lanzamiento` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `1` | `advance` | `shadow` | `adelanto` | `candidate_swap_review_available` | `review_same_pos_supported_target_swap, reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `1` | `piece` | `shadow` | `ficha` | `candidate_swap_review_available` | `review_same_pos_supported_target_swap, reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `2` | `advance` | `shadow` | `avanzar` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `2` | `bear` | `shadow` | `llevar` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `2` | `fair` | `shadow` | `feria de muestras` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `2` | `finish` | `shadow` | `acabado` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `2` | `leave` | `shadow` | `excedencia` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `2` | `low` | `shadow` | `decaído` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `2` | `part` | `shadow` | `papel` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `2` | `part` | `shadow` | `repartir` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `2` | `piece` | `shadow` | `montar` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `2` | `show` | `shadow` | `demostrar` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `2` | `still` | `shadow` | `alambique` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `2` | `still` | `shadow` | `aquietar` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |
| `2` | `upset` | `shadow` | `trastrocar` | `needs_reviewed_source_support` | `reverse_wiktionary_or_freedict_support, wiktextract_sense_or_translation_example, reviewed_dictionary_or_example_frame_source` |

## Limitations

- `conversion_audit_does_not_change_selected_family_targets`
- `same_pos_alternatives_require_review_and_re_admission_before_use`
- `forward_only_rows_are_not_promotion_evidence_without_source_support`
- `phrase_containment_coverage_is_out_of_scope_for_this_audit`

## Next Steps

- add reverse/FreeDict/Wiktextract/reviewed translation support for rows without supported alternatives
- materialize only a supported selected wave after source support is complete
- add independent active/shadow and phrase held-out cases before quality claims
