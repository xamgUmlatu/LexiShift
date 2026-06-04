# en-es Semantic Veto LLM Pilot Generation Requests

- Status: `ok`
- Decision: `ready_for_llm_batch_execution`
- Generated: `2026-05-04T21:31:10Z`
- Plan: `docs/test_inputs/semantic_veto_llm_pilot_plan_en_es.json`
- Prompt id: `semantic_veto_eval_sentence_pilot_v1`
- Candidate: `control_st_masked_all_margin_phrase_override|shadow_or_phrase_score|lead=0.05|score=0.0`
- Runtime policy change: `none`

## Summary

- Planned rows: `72`
- Requests rendered: `72`
- Families: `12`
- Requests by type: `phrase_no_winner: 12, positive_active: 36, shadow_negative: 24`
- Estimated input tokens: `32020`
- Expected output-token budget: `8640`

## Contract

- Output must be one JSON object per request.
- Output sentence must contain the English trigger.
- Output sentence must not contain the Spanish candidate replacement.
- Output sentence must not contain labels such as allow, abstain, or gold decision.
- Generated rows are evaluation data only.

## Request Samples

| Request | Family | Type | Decision | Strata |
| --- | --- | --- | --- | --- |
| `pilotrow:pilot_bank_banco:positive_active:001` | `pilot:bank:banco` | `positive_active` | `allow` | word_order=canonical_subject_verb_object, trigger_position=middle, context_distance=near_disambiguator, morphology=singular_or_base, register=headline_or_fragment, difficulty=hard |
| `pilotrow:pilot_bank_banco:positive_active:002` | `pilot:bank:banco` | `positive_active` | `allow` | word_order=fronted_context, trigger_position=late, context_distance=far_disambiguator, morphology=plural_or_inflected, register=technical_or_domain, difficulty=obvious |
| `pilotrow:pilot_bank_banco:positive_active:003` | `pilot:bank:banco` | `positive_active` | `allow` | word_order=modifier_before_trigger, trigger_position=early, context_distance=near_disambiguator, morphology=compound_or_phrase, register=ordinary_web, difficulty=moderate |
| `pilotrow:pilot_bank_banco:shadow_negative:001` | `pilot:bank:banco` | `shadow_negative` | `abstain` | word_order=modifier_after_trigger, trigger_position=middle, context_distance=far_disambiguator, morphology=singular_or_base, register=headline_or_fragment, difficulty=hard |
| `pilotrow:pilot_bank_banco:shadow_negative:002` | `pilot:bank:banco` | `shadow_negative` | `abstain` | word_order=separated_by_clause, trigger_position=late, context_distance=near_disambiguator, morphology=plural_or_inflected, register=technical_or_domain, difficulty=obvious |
| `pilotrow:pilot_bank_banco:phrase_no_winner:001` | `pilot:bank:banco` | `phrase_no_winner` | `abstain` | word_order=canonical_subject_verb_object, trigger_position=early, context_distance=far_disambiguator, morphology=compound_or_phrase, register=ordinary_web, difficulty=moderate |
| `pilotrow:pilot_plant_planta:positive_active:001` | `pilot:plant:planta` | `positive_active` | `allow` | word_order=fronted_context, trigger_position=middle, context_distance=near_disambiguator, morphology=singular_or_base, register=headline_or_fragment, difficulty=hard |
| `pilotrow:pilot_plant_planta:positive_active:002` | `pilot:plant:planta` | `positive_active` | `allow` | word_order=modifier_before_trigger, trigger_position=late, context_distance=far_disambiguator, morphology=plural_or_inflected, register=technical_or_domain, difficulty=obvious |
| `pilotrow:pilot_plant_planta:positive_active:003` | `pilot:plant:planta` | `positive_active` | `allow` | word_order=modifier_after_trigger, trigger_position=early, context_distance=near_disambiguator, morphology=compound_or_phrase, register=ordinary_web, difficulty=moderate |
| `pilotrow:pilot_plant_planta:shadow_negative:001` | `pilot:plant:planta` | `shadow_negative` | `abstain` | word_order=separated_by_clause, trigger_position=middle, context_distance=far_disambiguator, morphology=singular_or_base, register=headline_or_fragment, difficulty=hard |
| `pilotrow:pilot_plant_planta:shadow_negative:002` | `pilot:plant:planta` | `shadow_negative` | `abstain` | word_order=canonical_subject_verb_object, trigger_position=late, context_distance=near_disambiguator, morphology=plural_or_inflected, register=technical_or_domain, difficulty=obvious |
| `pilotrow:pilot_plant_planta:phrase_no_winner:001` | `pilot:plant:planta` | `phrase_no_winner` | `abstain` | word_order=fronted_context, trigger_position=early, context_distance=far_disambiguator, morphology=compound_or_phrase, register=ordinary_web, difficulty=moderate |
| `pilotrow:pilot_board_tablero:positive_active:001` | `pilot:board:tablero` | `positive_active` | `allow` | word_order=modifier_before_trigger, trigger_position=middle, context_distance=near_disambiguator, morphology=singular_or_base, register=headline_or_fragment, difficulty=hard |
| `pilotrow:pilot_board_tablero:positive_active:002` | `pilot:board:tablero` | `positive_active` | `allow` | word_order=modifier_after_trigger, trigger_position=late, context_distance=far_disambiguator, morphology=plural_or_inflected, register=technical_or_domain, difficulty=obvious |
| `pilotrow:pilot_board_tablero:positive_active:003` | `pilot:board:tablero` | `positive_active` | `allow` | word_order=separated_by_clause, trigger_position=early, context_distance=near_disambiguator, morphology=compound_or_phrase, register=ordinary_web, difficulty=moderate |
| `pilotrow:pilot_board_tablero:shadow_negative:001` | `pilot:board:tablero` | `shadow_negative` | `abstain` | word_order=canonical_subject_verb_object, trigger_position=middle, context_distance=far_disambiguator, morphology=singular_or_base, register=headline_or_fragment, difficulty=hard |
| `pilotrow:pilot_board_tablero:shadow_negative:002` | `pilot:board:tablero` | `shadow_negative` | `abstain` | word_order=fronted_context, trigger_position=late, context_distance=near_disambiguator, morphology=plural_or_inflected, register=technical_or_domain, difficulty=obvious |
| `pilotrow:pilot_board_tablero:phrase_no_winner:001` | `pilot:board:tablero` | `phrase_no_winner` | `abstain` | word_order=modifier_before_trigger, trigger_position=early, context_distance=far_disambiguator, morphology=compound_or_phrase, register=ordinary_web, difficulty=moderate |
| _54 more requests omitted from preview._ |  |  |  |  |

## Strata Coverage

| Axis | Counts |
| --- | --- |
| `word_order` | canonical_subject_verb_object: 15, fronted_context: 15, modifier_after_trigger: 14, modifier_before_trigger: 14, separated_by_clause: 14 |
| `trigger_position` | early: 24, late: 24, middle: 24 |
| `context_distance` | far_disambiguator: 36, near_disambiguator: 36 |
| `morphology` | compound_or_phrase: 24, plural_or_inflected: 24, singular_or_base: 24 |
| `register` | headline_or_fragment: 24, ordinary_web: 24, technical_or_domain: 24 |
| `difficulty` | hard: 24, moderate: 24, obvious: 24 |

## Next Steps

- Execute the request packet as a bounded LLM batch only when spend is approved.
- Preserve raw responses and normalize them into the row contract without editing labels after seeing scores.
- Run semantic_veto_llm_pilot_admission_en_es.py on the generated rows.
- Score admitted discovery and locked-eval rows separately with the frozen veto-only candidate.

## Limitations

- `no LLM call is made by this script`
- `request packet is not generated data`
- `generated rows must pass admission before scoring`
- `locked-eval rows cannot be used for threshold selection`
- `runtime policy remains unchanged`
