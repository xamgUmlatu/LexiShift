# en-es Non-v10 Source Support Conversion Audit

- Status: `ok`
- Decision: `selected_wave_source_supported`
- Dataset: `en_es_source_non_v10_wave4_anypos_supported_probe_min0p12`
- Generated: `2026-04-28T01:15:09Z`
- Translation support mode: ``
- Families: `16`
- Fully supported families: `16`
- Candidate-swap review families: `0`
- Needs reviewed source support: `0`
- Supported senses: `36` / `36`
- Unsupported active/shadow senses: `0` / `0`

## Family Conversion Table

| Trigger | State | Supported senses | Unsupported | Active | Shadows |
| --- | --- | ---: | ---: | --- | --- |
| `change` | `already_supported` | `2 / 2` | `0` | `cambio` | `cambiar` |
| `look` | `already_supported` | `2 / 2` | `0` | `aspecto` | `parecer` |
| `dry` | `already_supported` | `2 / 2` | `0` | `seco` | `secar` |
| `use` | `already_supported` | `2 / 2` | `0` | `uso` | `usar` |
| `plain` | `already_supported` | `2 / 2` | `0` | `llano` | `llanura` |
| `fast` | `already_supported` | `2 / 2` | `0` | `rápido` | `ayunar` |
| `train` | `already_supported` | `2 / 2` | `0` | `tren` | `adiestrar` |
| `land` | `already_supported` | `3 / 3` | `0` | `tierra` | `país, atracar` |
| `mean` | `already_supported` | `2 / 2` | `0` | `medio` | `significar` |
| `end` | `already_supported` | `2 / 2` | `0` | `fin` | `acabar` |
| `offer` | `already_supported` | `2 / 2` | `0` | `oferta` | `ofrecer` |
| `rest` | `already_supported` | `3 / 3` | `0` | `reposo` | `descanso, descansar` |
| `present` | `already_supported` | `2 / 2` | `0` | `presente` | `actual` |
| `sign` | `already_supported` | `3 / 3` | `0` | `señal` | `seña, firmar` |
| `answer` | `already_supported` | `3 / 3` | `0` | `respuesta` | `contestación, responder` |
| `quiet` | `already_supported` | `2 / 2` | `0` | `silencio` | `calmar` |

## Unsupported Sense Details

No unsupported selected senses.

## Limitations

- `conversion_audit_does_not_change_selected_family_targets`
- `same_pos_alternatives_require_review_and_re_admission_before_use`
- `forward_only_rows_are_not_promotion_evidence_without_source_support`
- `phrase_containment_coverage_is_out_of_scope_for_this_audit`

## Next Steps

- rerun the supported admission sweep and add independent held-out validation
