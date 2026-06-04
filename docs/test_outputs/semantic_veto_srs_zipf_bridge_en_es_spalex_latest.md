# en-es Semantic Veto SRS Zipf Bridge

- Status: `ok`
- Decision: `srs_zipf_bridge_established`
- Generated: `2026-05-16T18:40:43+00:00`
- Full SRS-admissible targets: `45131`
- Journey candidate-slice targets: `200`
- Selected initial-active targets: `3`
- Journey source-target pairs: `10`
- Full source-target pairs: `0`
- Source mapping status: `source_target_pairs_available`
- Full targets very-common/common: `3521` (7.8%)
- Journey targets very-common/common: `172` (86.0%)

## Target-Side SRS Distribution

| Scope | Band | Targets | Share | Weight Share | Sample Terms |
| --- | --- | ---: | ---: | ---: | --- |
| `full_srs_admissible_universe` | `zipf_5_plus_very_common` | 545 | 1.2% | 1.4% | `abril`, `acceso`, `acción`, `actividad`, `actual`, `actualmente`, `acuerdo`, `acá` |
| `full_srs_admissible_universe` | `zipf_4_to_5_common` | 2976 | 6.6% | 8.2% | `abajo`, `abandonado`, `abandonar`, `abandono`, `abarca`, `abierta`, `abiertamente`, `abierto` |
| `full_srs_admissible_universe` | `zipf_3_to_4_mid` | 8322 | 18.4% | 22.0% | `abad`, `abadía`, `abanderado`, `abanico`, `abarcar`, `abastecer`, `abasto`, `abatido` |
| `full_srs_admissible_universe` | `zipf_below_3_rare` | 23178 | 51.4% | 54.2% | `ababa`, `ababol`, `abacería`, `abacial`, `abacá`, `abada`, `abadejo`, `abadengo` |
| `full_srs_admissible_universe` | `missing` | 10110 | 22.4% | 14.1% | `abacero`, `abadiato`, `abajadero`, `abajamiento`, `abalanzar`, `abalar`, `abalaustrado`, `abalear` |
| `journey_srs_candidate_slice` | `zipf_5_plus_very_common` | 62 | 31.0% | 33.0% | `actualmente`, `auto`, `autor`, `capital`, `común`, `corazón`, `crear`, `crisis` |
| `journey_srs_candidate_slice` | `zipf_4_to_5_common` | 110 | 55.0% | 55.5% | `alemán`, `altura`, `americano`, `ampliar`, `argentino`, `arreglar`, `asimismo`, `asistir` |
| `journey_srs_candidate_slice` | `zipf_3_to_4_mid` | 26 | 13.0% | 10.7% | `acusar`, `advertir`, `alimentar`, `arrastrar`, `atravesar`, `basar`, `caber`, `calcular` |
| `journey_srs_candidate_slice` | `zipf_below_3_rare` | 2 | 1.0% | 0.8% | `consistir`, `oponer` |
| `srs_selected_initial_active` | `zipf_5_plus_very_common` | 2 | 66.7% | 66.9% | `hora`, `siglo` |
| `srs_selected_initial_active` | `zipf_4_to_5_common` | 1 | 33.3% | 33.1% | `millón` |
| `latest_admitted_srs_items` | `zipf_5_plus_very_common` | 6 | 85.7% | 85.3% | `hora`, `luz`, `movimiento`, `música`, `principio`, `siglo` |
| `latest_admitted_srs_items` | `zipf_4_to_5_common` | 1 | 14.3% | 14.7% | `millón` |
| `latest_due_srs_items` | `zipf_5_plus_very_common` | 3 | 100.0% | 100.0% | `hora`, `luz`, `movimiento` |
| `latest_published_srs_targets` | `zipf_5_plus_very_common` | 5 | 83.3% | 82.9% | `hora`, `luz`, `música`, `principio`, `siglo` |
| `latest_published_srs_targets` | `zipf_4_to_5_common` | 1 | 16.7% | 17.1% | `millón` |
| `journey_union_published_targets` | `zipf_5_plus_very_common` | 5 | 83.3% | n/a | `hora`, `luz`, `música`, `principio`, `siglo` |
| `journey_union_published_targets` | `zipf_4_to_5_common` | 1 | 16.7% | n/a | `millón` |

## Source-Side Rule Distribution

### Full Generated Rule Sources

| Scope | Band | Sources | Share | Sample Terms |
| --- | --- | ---: | ---: | --- |
| `none` | `n/a` | 0 | n/a |  |

### Journey Rule Sources

| Scope | Band | Sources | Share | Sample Terms |
| --- | --- | ---: | ---: | --- |
| `journey_union_rule_source_triggers` | `zipf_5_plus_very_common` | 8 | 80.0% | `beginning`, `century`, `hour`, `light`, `million`, `music`, `start`, `time` |
| `journey_union_rule_source_triggers` | `zipf_3_to_4_mid` | 2 | 20.0% | `centennial`, `commencement` |

## Full Source-Target Family Matrix

No source-target family rows are available in the current input.

## Journey Source-Target Family Matrix

| Source Band | Target Band | Families | Share | Sample Families |
| --- | --- | ---: | ---: | --- |
| `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 7 | 70.0% | `beginning` -> `principio`, `century` -> `siglo`, `hour` -> `hora`, `light` -> `luz`, `music` -> `música`, `start` -> `principio`, `time` -> `hora` |
| `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 1 | 10.0% | `million` -> `millón` |
| `zipf_3_to_4_mid` | `zipf_5_plus_very_common` | 2 | 20.0% | `centennial` -> `siglo`, `commencement` -> `principio` |

## Interpretation

- The full SRS-admissible target distribution is the denominator for possible user learning exposure under current installed resources.
- The journey slice remains useful as a runtime harness, but it is not the corpus-level denominator.
- The English source-trigger distribution is the denominator for semantic-veto evidence cost.
- Cost planning should join both: high-exposure SRS targets only need LLM semantic-veto data when their published source-trigger families are ambiguity-prone.

## Limitations

- `srs_target_frequency_is_not_the_same_as_source_trigger_veto_difficulty`
- `zipf_frequency_is_not_cefr_or_user_known_word_level`
- `journey_candidate_universe_is_current_top_n_slice_not_full_srs_universe`
- `full_srs_universe_uses_candidate_frequency_db_override`
- `source_target_matrix_depends_on_journey_artifact_preserving_rule_pairs`
- `full_source_target_matrix_requires_explicit_full_rulegen_run`
- `report_is_cost_planning_evidence_not_runtime_policy`

## Next Steps

- Use target-side rows to estimate which SRS words users actually experience.
- Use source-trigger rows to estimate which published replacement families need semantic-veto evidence.
- Weight future LLM generation by SRS admission exposure and source-trigger veto difficulty, not by source frequency alone.
- Keep target-side learner difficulty and source-side veto ambiguity as separate axes.
