# en-es Non-v10 Source Support Conversion Audit

- Status: `review`
- Decision: `support_conversion_needed`
- Dataset: `en_es_source_non_v10_wave3_anypos_unsupported_upper_bound_selected_v1`
- Generated: `2026-04-28T01:20:17Z`
- Translation support mode: `forward_only_upper_bound`
- Families: `16`
- Fully supported families: `3`
- Candidate-swap review families: `1`
- Needs reviewed source support: `12`
- Supported senses: `20` / `37`
- Unsupported active/shadow senses: `7` / `10`

## Family Conversion Table

| Trigger | State | Supported senses | Unsupported | Active | Shadows |
| --- | --- | ---: | ---: | --- | --- |
| `leave` | `needs_reviewed_source_support` | `1 / 3` | `2` | `permiso` | `excedencia, dejar` |
| `black` | `needs_reviewed_source_support` | `1 / 2` | `1` | `oscuro` | `negro` |
| `change` | `needs_reviewed_source_support` | `1 / 2` | `1` | `feria` | `cambiar` |
| `serve` | `needs_reviewed_source_support` | `1 / 2` | `1` | `servicio` | `servir` |
| `look` | `needs_reviewed_source_support` | `2 / 3` | `1` | `aspecto` | `expresión, parecer` |
| `dry` | `already_supported` | `2 / 2` | `0` | `seco` | `secar` |
| `fit` | `needs_reviewed_source_support` | `0 / 2` | `2` | `idóneo` | `caber` |
| `low` | `needs_reviewed_source_support` | `1 / 2` | `1` | `bajo` | `decaído` |
| `part` | `needs_reviewed_source_support` | `1 / 3` | `2` | `parte` | `papel, repartir` |
| `feel` | `needs_reviewed_source_support` | `1 / 2` | `1` | `talento` | `sentir` |
| `use` | `candidate_swap_review_available` | `2 / 3` | `1` | `uso` | `función, usar` |
| `still` | `needs_reviewed_source_support` | `1 / 2` | `1` | `aún` | `aquietar` |
| `bear` | `needs_reviewed_source_support` | `1 / 2` | `1` | `bajista` | `llevar` |
| `finish` | `needs_reviewed_source_support` | `1 / 3` | `2` | `meta` | `acabado, acabar` |
| `fast` | `already_supported` | `2 / 2` | `0` | `rápido` | `ayunar` |
| `train` | `already_supported` | `2 / 2` | `0` | `tren` | `adiestrar` |

## Unsupported Sense Details

| Trigger | Role | Target | POS | State | Same-POS supported alternatives |
| --- | --- | --- | --- | --- | --- |
| `leave` | `active` | `permiso` | `noun` | `needs_reviewed_source_support` | `none` |
| `leave` | `shadow` | `excedencia` | `noun` | `needs_reviewed_source_support` | `none` |
| `black` | `active` | `oscuro` | `adjective` | `needs_reviewed_source_support` | `none` |
| `change` | `active` | `feria` | `noun` | `needs_reviewed_source_support` | `none` |
| `serve` | `active` | `servicio` | `noun` | `needs_reviewed_source_support` | `none` |
| `look` | `shadow` | `expresión` | `noun` | `needs_reviewed_source_support` | `none` |
| `fit` | `active` | `idóneo` | `adjective` | `needs_reviewed_source_support` | `none` |
| `fit` | `shadow` | `caber` | `verb` | `needs_reviewed_source_support` | `none` |
| `low` | `shadow` | `decaído` | `adjective` | `needs_reviewed_source_support` | `none` |
| `part` | `shadow` | `papel` | `noun` | `needs_reviewed_source_support` | `none` |
| `part` | `shadow` | `repartir` | `verb` | `needs_reviewed_source_support` | `none` |
| `feel` | `active` | `talento` | `noun` | `needs_reviewed_source_support` | `none` |
| `use` | `shadow` | `función` | `noun` | `candidate_swap_review_available` | `utilización (3)` |
| `still` | `shadow` | `aquietar` | `verb` | `needs_reviewed_source_support` | `none` |
| `bear` | `shadow` | `llevar` | `verb` | `needs_reviewed_source_support` | `none` |
| `finish` | `active` | `meta` | `noun` | `needs_reviewed_source_support` | `none` |
| `finish` | `shadow` | `acabado` | `noun` | `needs_reviewed_source_support` | `none` |

## Limitations

- `conversion_audit_does_not_change_selected_family_targets`
- `same_pos_alternatives_require_review_and_re_admission_before_use`
- `forward_only_rows_are_not_promotion_evidence_without_source_support`
- `phrase_containment_coverage_is_out_of_scope_for_this_audit`

## Next Steps

- review same-POS supported alternatives and rerun admission if any target swaps are accepted
- add reverse/FreeDict/Wiktextract/reviewed translation support for rows without supported alternatives
- materialize only a supported selected wave after source support is complete
- add independent active/shadow and phrase held-out cases before quality claims
