# en-es Semantic Veto Veto-Only Validation

- Status: `review`
- Decision: `veto_only_validation_overall_product_target_pass_source_failures`
- Generated: `2026-05-05T18:22:07Z`
- Policy: `docs/test_inputs/semantic_veto_product_quality_policy_en_es.json`
- Sources: `3`
- Rows evaluated: `540`
- Product target pass rows: `16`
- Strict source-pass rows: `0`

## E2E Checks

| Check | Value |
| --- | --- |
| `calculus_source` | `scripts/testing/semantic_veto_product_quality_en_es.py::score_product_outcome_counts` |
| `source_reports_read` | `3` |
| `input_case_rows_read` | `168` |
| `policy_rows_emitted` | `540` |
| `phrase_modes` | `shadow_only, shadow_or_phrase, shadow_or_phrase_score` |
| `shadow_lead_grid` | `-0.1, -0.08, -0.05, -0.03, -0.02, -0.01, 0.0, 0.01, 0.02, 0.03, 0.05, 0.08, 0.1, 0.15, 0.2` |
| `shadow_score_grid` | `0.0, 0.02, 0.05, 0.1, 0.2, 0.35, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7` |

## Sources

| Source | Suite | Cases | Positives | Negatives | Original harmful | Original false abstain |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| semantic_veto_sampling_stage1_representative_scoring_en_es | semantic_veto_sampling_stage1_representative_scoring_en_es | 120 | 53 | 67 | 0 | 40 |
| semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout | non_v10_wave7_source_class_breadth_active_shadow | 32 | 16 | 16 | 1 | 2 |
| semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase | non_v10_wave7_source_class_breadth_phrase_no_winner | 16 | 0 | 16 | 6 | 0 |

## Top Validation Rows

| Phrase mode | Shadow lead | Shadow score | Pos allow | Neg abstain | Utility | Target | Strict | Source breakdowns |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| shadow_or_phrase_score | 0.02 | 0.0 | 88.4% | 53.5% | 72.6 | pass | fail | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 50.0%, neg 100.0%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 87.5%; semantic_veto_sampling_stage1_representative_scoring_en_es: pos 100.0%, neg 34.3% |
| shadow_or_phrase_score | 0.02 | 0.02 | 88.4% | 53.5% | 72.6 | pass | fail | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 50.0%, neg 100.0%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 87.5%; semantic_veto_sampling_stage1_representative_scoring_en_es: pos 100.0%, neg 34.3% |
| shadow_or_phrase_score | 0.0 | 0.02 | 84.1% | 55.6% | 71.2 | pass | fail | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 37.5%, neg 100.0%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 100.0%; semantic_veto_sampling_stage1_representative_scoring_en_es: pos 98.1%, neg 34.3% |
| shadow_or_phrase | 0.01 | 0.0 | 88.4% | 51.5% | 69.8 | pass | fail | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 62.5%, neg 93.8%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 68.8%; semantic_veto_sampling_stage1_representative_scoring_en_es: pos 96.2%, neg 37.3% |
| shadow_or_phrase_score | 0.01 | 0.0 | 82.6% | 55.6% | 69.8 | pass | fail | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 37.5%, neg 100.0%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 87.5%; semantic_veto_sampling_stage1_representative_scoring_en_es: pos 96.2%, neg 37.3% |
| shadow_or_phrase | -0.01 | 0.02 | 87.0% | 51.5% | 68.4 | pass | fail | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 50.0%, neg 93.8%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 81.2%; semantic_veto_sampling_stage1_representative_scoring_en_es: pos 98.1%, neg 34.3% |
| shadow_or_phrase | -0.02 | 0.02 | 85.5% | 52.5% | 68.4 | pass | fail | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 43.8%, neg 93.8%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 87.5%; semantic_veto_sampling_stage1_representative_scoring_en_es: pos 98.1%, neg 34.3% |
| shadow_or_phrase | -0.03 | 0.02 | 84.1% | 53.5% | 68.4 | pass | fail | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 37.5%, neg 93.8%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 93.8%; semantic_veto_sampling_stage1_representative_scoring_en_es: pos 98.1%, neg 34.3% |
| shadow_or_phrase_score | 0.01 | 0.02 | 84.1% | 53.5% | 68.4 | pass | fail | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 37.5%, neg 100.0%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 87.5%; semantic_veto_sampling_stage1_representative_scoring_en_es: pos 98.1%, neg 34.3% |
| shadow_or_phrase_score | -0.01 | 0.02 | 81.2% | 55.6% | 68.4 | pass | fail | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 25.0%, neg 100.0%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 100.0%; semantic_veto_sampling_stage1_representative_scoring_en_es: pos 98.1%, neg 34.3% |
| shadow_or_phrase_score | 0.0 | 0.05 | 85.5% | 51.5% | 67.0 | pass | fail | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 37.5%, neg 100.0%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 100.0%; semantic_veto_sampling_stage1_representative_scoring_en_es: pos 100.0%, neg 28.4% |
| shadow_or_phrase | -0.05 | 0.05 | 82.6% | 51.5% | 64.2 | pass | fail | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 25.0%, neg 100.0%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 100.0%; semantic_veto_sampling_stage1_representative_scoring_en_es: pos 100.0%, neg 28.4% |

## Passing Rows

| Phrase mode | Shadow lead | Shadow score | Pos allow | Neg abstain | Utility | Target | Strict | Source breakdowns |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| shadow_or_phrase_score | 0.02 | 0.0 | 88.4% | 53.5% | 72.6 | pass | fail | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 50.0%, neg 100.0%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 87.5%; semantic_veto_sampling_stage1_representative_scoring_en_es: pos 100.0%, neg 34.3% |
| shadow_or_phrase_score | 0.02 | 0.02 | 88.4% | 53.5% | 72.6 | pass | fail | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 50.0%, neg 100.0%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 87.5%; semantic_veto_sampling_stage1_representative_scoring_en_es: pos 100.0%, neg 34.3% |
| shadow_or_phrase_score | 0.0 | 0.02 | 84.1% | 55.6% | 71.2 | pass | fail | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 37.5%, neg 100.0%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 100.0%; semantic_veto_sampling_stage1_representative_scoring_en_es: pos 98.1%, neg 34.3% |
| shadow_or_phrase | 0.01 | 0.0 | 88.4% | 51.5% | 69.8 | pass | fail | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 62.5%, neg 93.8%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 68.8%; semantic_veto_sampling_stage1_representative_scoring_en_es: pos 96.2%, neg 37.3% |
| shadow_or_phrase_score | 0.01 | 0.0 | 82.6% | 55.6% | 69.8 | pass | fail | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 37.5%, neg 100.0%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 87.5%; semantic_veto_sampling_stage1_representative_scoring_en_es: pos 96.2%, neg 37.3% |
| shadow_or_phrase | -0.01 | 0.02 | 87.0% | 51.5% | 68.4 | pass | fail | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 50.0%, neg 93.8%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 81.2%; semantic_veto_sampling_stage1_representative_scoring_en_es: pos 98.1%, neg 34.3% |
| shadow_or_phrase | -0.02 | 0.02 | 85.5% | 52.5% | 68.4 | pass | fail | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 43.8%, neg 93.8%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 87.5%; semantic_veto_sampling_stage1_representative_scoring_en_es: pos 98.1%, neg 34.3% |
| shadow_or_phrase | -0.03 | 0.02 | 84.1% | 53.5% | 68.4 | pass | fail | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 37.5%, neg 93.8%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 93.8%; semantic_veto_sampling_stage1_representative_scoring_en_es: pos 98.1%, neg 34.3% |
| shadow_or_phrase_score | 0.01 | 0.02 | 84.1% | 53.5% | 68.4 | pass | fail | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 37.5%, neg 100.0%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 87.5%; semantic_veto_sampling_stage1_representative_scoring_en_es: pos 98.1%, neg 34.3% |
| shadow_or_phrase_score | -0.01 | 0.02 | 81.2% | 55.6% | 68.4 | pass | fail | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 25.0%, neg 100.0%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 100.0%; semantic_veto_sampling_stage1_representative_scoring_en_es: pos 98.1%, neg 34.3% |
| shadow_or_phrase_score | 0.0 | 0.05 | 85.5% | 51.5% | 67.0 | pass | fail | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 37.5%, neg 100.0%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 100.0%; semantic_veto_sampling_stage1_representative_scoring_en_es: pos 100.0%, neg 28.4% |
| shadow_or_phrase | -0.05 | 0.05 | 82.6% | 51.5% | 64.2 | pass | fail | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 25.0%, neg 100.0%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 100.0%; semantic_veto_sampling_stage1_representative_scoring_en_es: pos 100.0%, neg 28.4% |

## Strict Source-Passing Rows

_No rows._

## Failure Samples For Best Row

| Source | Case | Trigger | Gold | Winner | Outcome | Reason | Active | Shadow | Lead | Sentence |
| --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- |
| semantic_veto_sampling_stage1_representative_scoring_en_es | en-es:representative-gap:v1:002 | ball | abstain | shadow | negative_allow |  | 0.0 | 0.0 | 0.0 | The winter ball sold out within an hour. |
| semantic_veto_sampling_stage1_representative_scoring_en_es | en-es:sentence-veto:ball:003 | ball | abstain | shadow | negative_allow |  | 0.0 | 0.0 | 0.0 | They danced at the royal ball until dawn. |
| semantic_veto_sampling_stage1_representative_scoring_en_es | en-es:sentence-veto:ball:004 | ball | abstain | shadow | negative_allow |  | 0.0 | 0.0 | 0.0 | The charity ball raised thousands of dollars. |
| semantic_veto_sampling_stage1_representative_scoring_en_es | en-es:sentence-veto:ball:005 | ball | abstain | none | negative_allow |  | 0.0359 | 0.0 | -0.0359 | The ball is in your court now. |
| semantic_veto_sampling_stage1_representative_scoring_en_es | en-es:sentence-veto:bank:004 | bank | abstain | shadow | negative_allow |  | 0.0 | 0.0 | 0.0 | Wildflowers grew along the muddy bank. |
| semantic_veto_sampling_stage1_representative_scoring_en_es | en-es:representative-gap:v1:016 | board | abstain | shadow | negative_allow |  | 0.0 | 0.0 | 0.0 | The board voted to approve the budget. |
| semantic_veto_sampling_stage1_representative_scoring_en_es | en-es:sentence-veto:board:003 | board | abstain | shadow | negative_allow |  | 0.0 | 0.0 | 0.0 | The board approved the merger on Tuesday. |
| semantic_veto_sampling_stage1_representative_scoring_en_es | en-es:sentence-veto:board:005 | board | abstain | none | negative_allow |  | 0.0 | 0.0 | 0.0 | Are you on board with the revised plan? |
| semantic_veto_sampling_stage1_representative_scoring_en_es | en-es:representative-gap:v1:020 | branch | abstain | shadow | negative_allow |  | 0.0 | 0.0174 | 0.0174 | A broken branch blocked the sidewalk. |
| semantic_veto_sampling_stage1_representative_scoring_en_es | en-es:sentence-veto:branch:003 | branch | abstain | shadow | negative_allow |  | 0.0264 | 0.0132 | -0.0132 | A bird landed on the highest branch of the oak. |
| semantic_veto_sampling_stage1_representative_scoring_en_es | en-es:sentence-veto:branch:004 | branch | abstain | shadow | negative_allow |  | 0.0 | 0.0142 | 0.0142 | The storm snapped a heavy branch in the yard. |
| semantic_veto_sampling_stage1_representative_scoring_en_es | en-es:sentence-veto:check:003 | check | abstain | shadow | negative_allow |  | 0.0 | 0.0 | 0.0 | Please check the figures one more time. |
| semantic_veto_sampling_stage1_representative_scoring_en_es | en-es:sentence-veto:check:004 | check | abstain | shadow | negative_allow |  | 0.0 | 0.0 | 0.0 | Technicians check the pressure every hour. |
| semantic_veto_sampling_stage1_representative_scoring_en_es | en-es:sentence-veto:check:005 | check | abstain | none | negative_allow |  | 0.0 | 0.0 | 0.0 | You should check out the new exhibit downtown. |
| semantic_veto_sampling_stage1_representative_scoring_en_es | en-es:sentence-veto:drink:003 | drink | abstain | shadow | negative_allow |  | 0.0 | 0.0 | 0.0 | Athletes should drink more water during practice. |
| semantic_veto_sampling_stage1_representative_scoring_en_es | en-es:sentence-veto:drink:004 | drink | abstain | shadow | negative_allow |  | 0.0 | 0.0 | 0.0 | He refused to drink after the surgery. |
| semantic_veto_sampling_stage1_representative_scoring_en_es | en-es:sentence-veto:drink:005 | drink | abstain | none | negative_allow |  | 0.0 | 0.0 | 0.0 | She tried to drink in the view from the balcony. |
| semantic_veto_sampling_stage1_representative_scoring_en_es | en-es:sentence-veto:match:004 | match | abstain | shadow | negative_allow |  | 0.0 | 0.0 | 0.0 | He dropped the burning match into the sink. |
| semantic_veto_sampling_stage1_representative_scoring_en_es | en-es:sentence-veto:order:003 | order | abstain | shadow | negative_allow |  | 0.021 | 0.0 | -0.021 | Teachers order the class to remain silent. |
| semantic_veto_sampling_stage1_representative_scoring_en_es | en-es:sentence-veto:order:004 | order | abstain | shadow | negative_allow |  | 0.0 | 0.0 | 0.0 | Commanders order the troops forward. |
| semantic_veto_sampling_stage1_representative_scoring_en_es | en-es:sentence-veto:order:005 | order | abstain | none | negative_allow |  | 0.0 | 0.0 | 0.0 | We should order out tonight. |
| semantic_veto_sampling_stage1_representative_scoring_en_es | en-es:sentence-veto:park:003 | park | abstain | shadow | negative_allow |  | 0.0 | 0.0 | 0.0 | Please park behind the building. |
| semantic_veto_sampling_stage1_representative_scoring_en_es | en-es:sentence-veto:park:005 | park | abstain | none | negative_allow |  | 0.036 | 0.0 | -0.036 | The committee will park that issue for now. |
| semantic_veto_sampling_stage1_representative_scoring_en_es | en-es:representative-gap:v1:005 | plant | abstain | shadow | negative_allow |  | 0.0 | 0.0 | 0.0 | The plant produces parts for electric buses. |

## Recommendation

- At least one veto-only blocker policy meets the aggregate product target, but no row passes every measured source.
- Do not promote this as a shared candidate until the failing source lane is repaired or a stricter candidate is found.
- Use source breakdowns to decide whether the weakness is representative negatives, stress positives, or phrase/no-winner blocking.
