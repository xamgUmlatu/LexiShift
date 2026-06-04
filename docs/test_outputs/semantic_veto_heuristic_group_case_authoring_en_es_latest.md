# en-es Semantic Veto Heuristic Group Case Authoring

- Status: `ok`
- Decision: `heuristic_group_case_authoring_dataset_ready_for_scoring`
- Generated: `2026-05-05T02:16:07Z`
- Pilot: `docs/test_outputs/semantic_veto_heuristic_group_pilot_en_es_latest.json`
- Dataset: `docs/test_inputs/semantic_routing_cases/en_es_heuristic_group_pilot_v1.json`
- Dataset fingerprint: `134f139f12981d6565e4c7c3b1ac4edddd88b08aee5ddecb856c5eb11f2e244e`
- Authored triggers: `29`
- Dataset cases: `121`

## Methodology

This packet materializes the frozen heuristic groups into a sentence-veto dataset without changing runtime policy. The primary groups still come from pre-outcome frequency and WordNet polysemy metadata. The measured sentinel group remains outcome-informed and is only a regression anchor.

Low-polysemy controls are intentionally not forced to invent shadow senses. If a trigger is effectively one-sense for this replacement target, the packet uses active cases plus a mention or phrase no-winner case and records the shadow contract as `not_applicable`.

## Summary

| Key | Value |
| --- | --- |
| `pilot_manual_review_rows` | `29` |
| `authored_trigger_count` | `29` |
| `dataset_family_count` | `29` |
| `dataset_case_count` | `121` |
| `missing_authoring_specs` | `[]` |
| `unused_authoring_specs` | `[]` |
| `shadow_contract_counts` | `{"full": 16, "limited": 1, "not_applicable": 12}` |
| `case_type_counts` | `{"phrase_no_winner": 29, "positive_active": 58, "shadow_negative": 34}` |
| `group_case_type_counts` | `{"core_high_polysemy": {"phrase_no_winner": 4, "positive_active": 8, "shadow_negative": 8}, "core_low_polysemy_control": {"phrase_no_winner": 4, "positive_active": 8}, "measured_missing_rank_high_failure_sentinel": {"phrase_no_winner": 5, "positive_active": 10, "shadow_negative": 10}, "mid_high_polysemy": {"phrase_no_winner": 4, "positive_active": 8, "shadow_negative": 8}, "mid_low_polysemy_control": {"phrase_no_winner": 4, "positive_active": 8}, "tail_high_polysemy": {"phrase_no_winner": 4, "positive_active": 8, "shadow_negative": 8}, "tail_low_polysemy_control": {"phrase_no_winner": 4, "positive_active": 8}}` |
| `dataset_fingerprint` | `134f139f12981d6565e4c7c3b1ac4edddd88b08aee5ddecb856c5eb11f2e244e` |

## Group Case Mix

| Group | phrase_no_winner | positive_active | shadow_negative | Total |
| --- | ---: | ---: | ---: | ---: |
| `core_high_polysemy` | 4 | 8 | 8 | 20 |
| `core_low_polysemy_control` | 4 | 8 | 0 | 12 |
| `measured_missing_rank_high_failure_sentinel` | 5 | 10 | 10 | 25 |
| `mid_high_polysemy` | 4 | 8 | 8 | 20 |
| `mid_low_polysemy_control` | 4 | 8 | 0 | 12 |
| `tail_high_polysemy` | 4 | 8 | 8 | 20 |
| `tail_low_polysemy_control` | 4 | 8 | 0 | 12 |

## Authored Triggers

| Trigger | Group | Target | Senses | Contract | Cases | Expected difficulty |
| --- | --- | --- | ---: | --- | ---: | --- |
| `man` | `core_high_polysemy` | `hombre` | 12 | `full` | 5 | high |
| `work` | `core_high_polysemy` | `trabajo` | 34 | `full` | 5 | high |
| `call` | `core_high_polysemy` | `llamada` | 41 | `full` | 5 | high |
| `help` | `core_high_polysemy` | `ayuda` | 12 | `limited` | 5 | medium_high |
| `yes` | `core_low_polysemy_control` | `sí` | 1 | `not_applicable` | 3 | low |
| `money` | `core_low_polysemy_control` | `dinero` | 3 | `not_applicable` | 3 | low |
| `percent` | `core_low_polysemy_control` | `por ciento` | 1 | `not_applicable` | 3 | low |
| `often` | `core_low_polysemy_control` | `a menudo` | 3 | `not_applicable` | 3 | low |
| `green` | `mid_high_polysemy` | `verde` | 13 | `full` | 5 | high |
| `trade` | `mid_high_polysemy` | `comercio` | 12 | `full` | 5 | medium_high |
| `deep` | `mid_high_polysemy` | `profundo` | 21 | `full` | 5 | medium_high |
| `particular` | `mid_high_polysemy` | `específico` | 9 | `full` | 5 | medium |
| `therefore` | `mid_low_polysemy_control` | `por lo tanto` | 2 | `not_applicable` | 3 | low |
| `senate` | `mid_low_polysemy_control` | `senado` | 1 | `not_applicable` | 3 | low |
| `participant` | `mid_low_polysemy_control` | `participante` | 2 | `not_applicable` | 3 | low |
| `crisis` | `mid_low_polysemy_control` | `crisis` | 2 | `not_applicable` | 3 | low |
| `upgrade` | `tail_high_polysemy` | `actualización` | 11 | `full` | 5 | medium |
| `yield` | `tail_high_polysemy` | `rendimiento` | 17 | `full` | 5 | high |
| `hammer` | `tail_high_polysemy` | `martillo` | 10 | `full` | 5 | medium |
| `low` | `tail_high_polysemy` | `bajo` | 15 | `full` | 5 | medium_high |
| `unnecessary` | `tail_low_polysemy_control` | `innecesario` | 1 | `not_applicable` | 3 | low |
| `suitable` | `tail_low_polysemy_control` | `adecuado` | 2 | `not_applicable` | 3 | low |
| `purely` | `tail_low_polysemy_control` | `puramente` | 1 | `not_applicable` | 3 | low |
| `prosecute` | `tail_low_polysemy_control` | `enjuiciar` | 3 | `not_applicable` | 3 | low |
| `check` | `measured_missing_rank_high_failure_sentinel` | `cheque` | 38 | `full` | 5 | high |
| `order` | `measured_missing_rank_high_failure_sentinel` | `pedido` | 23 | `full` | 5 | high |
| `plant` | `measured_missing_rank_high_failure_sentinel` | `plantar` | 10 | `full` | 5 | high |
| `play` | `measured_missing_rank_high_failure_sentinel` | `jugar` | 52 | `full` | 5 | high |
| `report` | `measured_missing_rank_high_failure_sentinel` | `informe` | 13 | `full` | 5 | high |

## Limitations

- `agent_authored_cases_need_human_review_before_promotion_claims`
- `low_polysemy_controls_are_not_shadow_balanced_when_no_honest_shadow_exists`
- `case_sentences_are_manual_draft_rows_not_representative_browsing_samples`
- `spanish_target_choices_are_plausible_research_targets_not_admitted_source_truth`

## Next Steps

- Score this dataset with the existing sentence-veto harness as a diagnostic lane.
- Compare group-level positive allow and negative abstain rates without mixing sentinel rows into primary-heuristic claims.
- Human-review or replace any questionable target/shadow choices before treating the lane as locked evaluation.
- Use failures to decide whether frequency/polysemy predicts veto difficulty or whether richer source coverage dominates.
