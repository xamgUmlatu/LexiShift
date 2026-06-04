# en-es Semantic Veto LLM Data Priority Scan

- Status: `ok`
- Decision: `llm_data_priority_scan_established`
- Generated: `2026-05-05T19:07:42+00:00`
- Candidate pairs: `35`
- Top N: `25`
- Forbidden feature fields: `8`

## Methodology

Allocate LLM generation budget to trigger/target pairs where more active, shadow, or phrase/no-winner evidence is most likely to improve semantic-veto quality.

Ranking uses programmatic metadata and raw scorer surfaces only. Gold labels, manual case labels, and product outcomes are kept out of the ranking feature vector.

## Score Summary

| Metric | Value |
| --- | ---: |
| top static need | 0.4076 |
| top scored-context need | 0.2694 |
| source rank known rate | 31.4% |
| target rank known rate | 14.3% |
| WordNet sense known rate | 45.7% |
| translation count known rate | 45.7% |

## Recommended LLM Packets

| Rank | Trigger | Target | Need | Static | Active | Shadow | Phrase | Locked | Reasons | Validation shadow |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 1 | `wrong` | `incorrecto` | 0.2694 | 0.4076 | 0 | 4 | 12 | 4 | high_source_exposure, high_programmatic_ambiguity, score_surface_uncertainty, generate_shadow_rows, generate_phrase_rows | 1 / 3 |
| 2 | `watch` | `reloj` | 0.1518 | 0.2201 | 4 | 4 | 8 | 4 | high_source_exposure, score_surface_uncertainty, generate_active_rows, generate_shadow_rows, generate_phrase_rows | 3 / 12 |
| 3 | `score` | `tantos` | 0.1388 | 0.2245 | 0 | 4 | 8 | 2 | high_programmatic_ambiguity, generate_shadow_rows, generate_phrase_rows | 1 / 3 |
| 4 | `bank` | `banco` | 0.1305 | 0.1871 | 4 | 0 | 8 | 2 | high_source_exposure, score_surface_uncertainty, generate_active_rows, generate_phrase_rows | 4 / 12 |
| 5 | `stretch` | `estirón` | 0.1061 | 0.1465 | 0 | 0 | 4 | 0 | missing_source_rank, high_programmatic_ambiguity, score_surface_uncertainty, generate_phrase_rows | 1 / 3 |
| 6 | `like` | `gustos` | 0.0952 | 0.1334 | 0 | 0 | 4 | 0 | missing_source_rank, high_programmatic_ambiguity, score_surface_uncertainty, generate_phrase_rows | 0 / 3 |
| 7 | `cast` | `lanzamiento` | 0.0951 | 0.1429 | 0 | 0 | 4 | 0 | missing_source_rank, high_programmatic_ambiguity, score_surface_uncertainty, generate_phrase_rows | 1 / 3 |
| 8 | `crash` | `choque` | 0.0898 | 0.1416 | 0 | 0 | 4 | 0 | missing_source_rank, high_programmatic_ambiguity, generate_phrase_rows | 0 / 3 |
| 9 | `firm` | `firma` | 0.0893 | 0.1503 | 0 | 0 | 4 | 0 | missing_source_rank, high_programmatic_ambiguity, generate_phrase_rows | 0 / 3 |
| 10 | `waste` | `desperdicio` | 0.0880 | 0.1483 | 0 | 0 | 4 | 0 | missing_source_rank, high_programmatic_ambiguity, generate_phrase_rows | 0 / 3 |
| 11 | `full` | `lleno` | 0.0852 | 0.1509 | 0 | 0 | 0 | 0 | missing_source_rank, high_programmatic_ambiguity | 0 / 3 |
| 12 | `foul` | `falta` | 0.0847 | 0.1374 | 0 | 0 | 4 | 0 | missing_source_rank, high_programmatic_ambiguity, generate_phrase_rows | 1 / 3 |
| 13 | `fix` | `aprieto` | 0.0795 | 0.1416 | 0 | 0 | 4 | 0 | missing_source_rank, high_programmatic_ambiguity, generate_phrase_rows | 1 / 3 |
| 14 | `squeeze` | `crisis` | 0.0783 | 0.1279 | 0 | 0 | 4 | 0 | missing_source_rank, high_programmatic_ambiguity, generate_phrase_rows | 1 / 3 |
| 15 | `match` | `partido` | 0.0693 | 0.0991 | 0 | 0 | 4 | 0 | score_surface_uncertainty, generate_phrase_rows | 3 / 13 |
| 16 | `seal` | `sello` | 0.0666 | 0.0991 | 0 | 0 | 4 | 0 | score_surface_uncertainty, generate_phrase_rows | 1 / 13 |
| 17 | `plant` | `planta` | 0.0627 | 0.0828 | 0 | 0 | 4 | 0 | missing_source_rank, score_surface_uncertainty, generate_phrase_rows | 6 / 13 |
| 18 | `report` | `informe` | 0.0615 | 0.0828 | 0 | 0 | 4 | 0 | missing_source_rank, score_surface_uncertainty, generate_phrase_rows | 6 / 11 |
| 19 | `drink` | `bebida` | 0.0610 | 0.0828 | 0 | 0 | 0 | 0 | missing_source_rank, score_surface_uncertainty | 3 / 6 |
| 20 | `trip` | `viaje` | 0.0610 | 0.0828 | 0 | 0 | 0 | 0 | missing_source_rank, score_surface_uncertainty | 2 / 5 |
| 21 | `trim` | `compensador` | 0.0595 | 0.0967 | 0 | 0 | 4 | 0 | high_programmatic_ambiguity, generate_phrase_rows | 0 / 3 |
| 22 | `branch` | `sucursal` | 0.0595 | 0.0828 | 0 | 0 | 4 | 0 | missing_source_rank, score_surface_uncertainty, generate_phrase_rows | 3 / 13 |
| 23 | `play` | `obra` | 0.0594 | 0.0828 | 0 | 0 | 4 | 0 | missing_source_rank, score_surface_uncertainty, generate_phrase_rows | 5 / 12 |
| 24 | `check` | `cheque` | 0.0582 | 0.0828 | 0 | 0 | 4 | 0 | missing_source_rank, score_surface_uncertainty, generate_phrase_rows | 5 / 11 |
| 25 | `spring` | `primavera` | 0.0582 | 0.0828 | 0 | 0 | 0 | 0 | missing_source_rank, score_surface_uncertainty | 2 / 7 |

## Feature Guardrails

| Check | Value |
| --- | --- |
| `forbidden_fields_absent_from_programmatic_features` | `True` |
| `all_programmatic_features_declared` | `True` |
| `rows_sorted_by_scored_context_need` | `True` |
| `validation_shadow_kept_separate` | `True` |

## Limitations

- `current_scan_reads_measured_scored_contexts_not_full_database_inventory`
- `english_source_rank_and_spanish_target_rank_coverage_are_incomplete`
- `wordnet_and_translation_metadata_are_not_available_for_every_candidate`
- `score_surface_features_require_observed_or_generated_contexts`
- `ranking_is_for_data_spend_allocation_not_runtime_policy_promotion`

## Next Steps

- Run this scanner after every difficulty-stratification refresh.
- Use top rows to request LLM active/shadow/phrase evidence packets.
- Add a wider inventory input once rulegen can emit the same programmatic metadata for all candidate rules.
- Evaluate rank quality with labels only after the priority list is frozen.
