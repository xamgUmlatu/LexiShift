# en-es Semantic Veto Veto-Only Validation

- Status: `ok`
- Decision: `veto_only_validation_strict_source_product_target_pass_found`
- Generated: `2026-05-05T18:22:02Z`
- Policy: `docs/test_inputs/semantic_veto_product_quality_policy_en_es.json`
- Sources: `2`
- Rows evaluated: `540`
- Product target pass rows: `100`
- Strict source-pass rows: `12`

## E2E Checks

| Check | Value |
| --- | --- |
| `calculus_source` | `scripts/testing/semantic_veto_product_quality_en_es.py::score_product_outcome_counts` |
| `source_reports_read` | `2` |
| `input_case_rows_read` | `48` |
| `policy_rows_emitted` | `540` |
| `phrase_modes` | `shadow_only, shadow_or_phrase, shadow_or_phrase_score` |
| `shadow_lead_grid` | `-0.1, -0.08, -0.05, -0.03, -0.02, -0.01, 0.0, 0.01, 0.02, 0.03, 0.05, 0.08, 0.1, 0.15, 0.2` |
| `shadow_score_grid` | `0.0, 0.02, 0.05, 0.1, 0.2, 0.35, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7` |

## Sources

| Source | Suite | Cases | Positives | Negatives | Original harmful | Original false abstain |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout | non_v10_wave7_source_class_breadth_active_shadow | 32 | 16 | 16 | 1 | 2 |
| semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase | non_v10_wave7_source_class_breadth_phrase_no_winner | 16 | 0 | 16 | 6 | 0 |

## Top Validation Rows

| Phrase mode | Shadow lead | Shadow score | Pos allow | Neg abstain | Utility | Target | Strict | Source breakdowns |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| shadow_or_phrase_score | 0.05 | 0.0 | 81.2% | 75.0% | 26.2 | pass | pass | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 81.2%, neg 87.5%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 62.5% |
| shadow_or_phrase_score | 0.05 | 0.02 | 81.2% | 75.0% | 26.2 | pass | pass | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 81.2%, neg 87.5%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 62.5% |
| shadow_or_phrase_score | 0.05 | 0.05 | 81.2% | 75.0% | 26.2 | pass | pass | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 81.2%, neg 87.5%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 62.5% |
| shadow_or_phrase_score | 0.05 | 0.1 | 81.2% | 75.0% | 26.2 | pass | pass | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 81.2%, neg 87.5%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 62.5% |
| shadow_or_phrase_score | 0.05 | 0.2 | 81.2% | 75.0% | 26.2 | pass | pass | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 81.2%, neg 87.5%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 62.5% |
| shadow_or_phrase_score | 0.05 | 0.35 | 81.2% | 75.0% | 26.2 | pass | pass | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 81.2%, neg 87.5%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 62.5% |
| shadow_or_phrase_score | 0.05 | 0.45 | 81.2% | 75.0% | 26.2 | pass | pass | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 81.2%, neg 87.5%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 62.5% |
| shadow_or_phrase_score | 0.05 | 0.5 | 81.2% | 75.0% | 26.2 | pass | pass | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 81.2%, neg 87.5%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 62.5% |
| shadow_or_phrase_score | 0.05 | 0.55 | 81.2% | 75.0% | 26.2 | pass | pass | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 81.2%, neg 87.5%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 62.5% |
| shadow_or_phrase_score | 0.05 | 0.6 | 81.2% | 75.0% | 26.2 | pass | pass | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 81.2%, neg 87.5%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 62.5% |
| shadow_or_phrase_score | 0.05 | 0.7 | 87.5% | 68.8% | 24.8 | pass | pass | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 87.5%, neg 87.5%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 50.0% |
| shadow_or_phrase_score | 0.05 | 0.65 | 81.2% | 71.9% | 24.8 | pass | pass | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 81.2%, neg 87.5%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 56.2% |

## Passing Rows

| Phrase mode | Shadow lead | Shadow score | Pos allow | Neg abstain | Utility | Target | Strict | Source breakdowns |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| shadow_or_phrase_score | 0.05 | 0.0 | 81.2% | 75.0% | 26.2 | pass | pass | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 81.2%, neg 87.5%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 62.5% |
| shadow_or_phrase_score | 0.05 | 0.02 | 81.2% | 75.0% | 26.2 | pass | pass | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 81.2%, neg 87.5%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 62.5% |
| shadow_or_phrase_score | 0.05 | 0.05 | 81.2% | 75.0% | 26.2 | pass | pass | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 81.2%, neg 87.5%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 62.5% |
| shadow_or_phrase_score | 0.05 | 0.1 | 81.2% | 75.0% | 26.2 | pass | pass | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 81.2%, neg 87.5%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 62.5% |
| shadow_or_phrase_score | 0.05 | 0.2 | 81.2% | 75.0% | 26.2 | pass | pass | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 81.2%, neg 87.5%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 62.5% |
| shadow_or_phrase_score | 0.05 | 0.35 | 81.2% | 75.0% | 26.2 | pass | pass | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 81.2%, neg 87.5%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 62.5% |
| shadow_or_phrase_score | 0.05 | 0.45 | 81.2% | 75.0% | 26.2 | pass | pass | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 81.2%, neg 87.5%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 62.5% |
| shadow_or_phrase_score | 0.05 | 0.5 | 81.2% | 75.0% | 26.2 | pass | pass | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 81.2%, neg 87.5%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 62.5% |
| shadow_or_phrase_score | 0.05 | 0.55 | 81.2% | 75.0% | 26.2 | pass | pass | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 81.2%, neg 87.5%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 62.5% |
| shadow_or_phrase_score | 0.05 | 0.6 | 81.2% | 75.0% | 26.2 | pass | pass | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 81.2%, neg 87.5%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 62.5% |
| shadow_or_phrase_score | 0.05 | 0.7 | 87.5% | 68.8% | 24.8 | pass | pass | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 87.5%, neg 87.5%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 50.0% |
| shadow_or_phrase_score | 0.05 | 0.65 | 81.2% | 71.9% | 24.8 | pass | pass | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 81.2%, neg 87.5%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 56.2% |

## Strict Source-Passing Rows

| Phrase mode | Shadow lead | Shadow score | Pos allow | Neg abstain | Utility | Target | Strict | Source breakdowns |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| shadow_or_phrase_score | 0.05 | 0.0 | 81.2% | 75.0% | 26.2 | pass | pass | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 81.2%, neg 87.5%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 62.5% |
| shadow_or_phrase_score | 0.05 | 0.02 | 81.2% | 75.0% | 26.2 | pass | pass | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 81.2%, neg 87.5%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 62.5% |
| shadow_or_phrase_score | 0.05 | 0.05 | 81.2% | 75.0% | 26.2 | pass | pass | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 81.2%, neg 87.5%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 62.5% |
| shadow_or_phrase_score | 0.05 | 0.1 | 81.2% | 75.0% | 26.2 | pass | pass | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 81.2%, neg 87.5%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 62.5% |
| shadow_or_phrase_score | 0.05 | 0.2 | 81.2% | 75.0% | 26.2 | pass | pass | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 81.2%, neg 87.5%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 62.5% |
| shadow_or_phrase_score | 0.05 | 0.35 | 81.2% | 75.0% | 26.2 | pass | pass | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 81.2%, neg 87.5%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 62.5% |
| shadow_or_phrase_score | 0.05 | 0.45 | 81.2% | 75.0% | 26.2 | pass | pass | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 81.2%, neg 87.5%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 62.5% |
| shadow_or_phrase_score | 0.05 | 0.5 | 81.2% | 75.0% | 26.2 | pass | pass | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 81.2%, neg 87.5%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 62.5% |
| shadow_or_phrase_score | 0.05 | 0.55 | 81.2% | 75.0% | 26.2 | pass | pass | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 81.2%, neg 87.5%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 62.5% |
| shadow_or_phrase_score | 0.05 | 0.6 | 81.2% | 75.0% | 26.2 | pass | pass | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 81.2%, neg 87.5%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 62.5% |
| shadow_or_phrase_score | 0.05 | 0.7 | 87.5% | 68.8% | 24.8 | pass | pass | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 87.5%, neg 87.5%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 50.0% |
| shadow_or_phrase_score | 0.05 | 0.65 | 81.2% | 71.9% | 24.8 | pass | pass | semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout: pos 81.2%, neg 87.5%; semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase: pos n/a, neg 56.2% |

## Failure Samples For Best Row

| Source | Case | Trigger | Gold | Winner | Outcome | Reason | Active | Shadow | Lead | Sentence |
| --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- |
| semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout | en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:gross:002 | gross | abstain | shadow | negative_allow |  | 0.6767 | 0.7145 | 0.0378 | The shop ordered a gross of pencils. |
| semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout | en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:fix:001 | fix | replace | active | positive_abstain | shadow_lead | 0.626 | 0.7449 | 0.1189 | Losing the only key left us in a real fix. |
| semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout | en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:waste:002 | waste | abstain | shadow | negative_allow |  | 0.6721 | 0.6283 | -0.0438 | Factories should not waste clean water. |
| semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout | en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:even:001 | even | replace | active | positive_abstain | phrase_preemption | 0.7265 | 0.5392 | -0.1873 | At even, the village lamps began to glow. |
| semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout | en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:meet:001 | meet | replace | active | positive_abstain | shadow_lead | 0.5444 | 0.6926 | 0.1482 | It is meet to thank the volunteers before dinner. |
| semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase | en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:like:001 | like | abstain | none | negative_allow |  | 0.6394 | 0.634 | -0.0054 | The speaker used like as a filler in every sentence. |
| semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase | en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:full:001 | full | abstain | none | negative_allow |  | 0.5631 | 0.5314 | -0.0317 | The committee met in full on Monday. |
| semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase | en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:wrong:001 | wrong | abstain | none | negative_allow |  | 0.679 | 0.6892 | 0.0102 | He rubbed the organizer the wrong way. |
| semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase | en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:score:001 | score | abstain | none | negative_allow |  | 0.7298 | 0.7096 | -0.0202 | The composer wrote the score for the film. |
| semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase | en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:crash:001 | crash | abstain | none | negative_allow |  | 0.7003 | 0.6995 | -0.0008 | Can I crash on your couch tonight? |
| semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase | en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:foul:001 | foul | abstain | none | negative_allow |  | 0.5938 | 0.6342 | 0.0404 | The foul weather delayed the ferry. |

## Recommendation

- At least one veto-only blocker policy meets the configured product target on every measured source.
- Compare the winning blocker against the frozen v10 matrix winner before considering runtime policy changes.
- Use source breakdowns and failure samples to decide which blocker signals need broader representative evaluation.
