# en-es Semantic Veto Product Quality

- Status: `review`
- Decision: `product_target_missed`
- Generated: `2026-05-01T01:03:28Z`
- Policy: `docs/test_inputs/semantic_veto_product_quality_policy_en_es.json`
- Cases: `143`
- Measured lane types: `representative, stress`
- Planned unmeasured lane types: `llm_expanded_eval, representative_expanded`

## Overall Product Metrics

| Scope | Cases | Positives | Negatives | Pos allow | Pos allow rate | Neg abstain | Neg abstain rate | Neg allow | Utility | Target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| overall | 143 | 54 | 89 | 27 | 50.0% | 82 | 92.1% | 7 | 77.6 | fail |

## Baselines

| Baseline | Utility | Utility/case | Positive allow rate | Negative abstain rate | Delta current utility |
| --- | ---: | ---: | ---: | ---: | ---: |
| lexical_allow_all | 0.6 | 0.0042 | 100.0% | 0.0% | 77.0 |
| abstain_all | 49.6 | 0.3469 | 0.0% | 100.0% | 28.0 |

## Lanes

| Lane | Type | Cases | Pos allow rate | Neg abstain rate | Utility | Target | Interpretation |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| wave7_phrase_control_triage_stress | stress | 48 | 87.5% | 78.1% | 29.0 | pass | Useful for guarding known hard cases; not representative browsing evidence. |
| sentence_veto_v10_representative_proxy | representative | 95 | 34.2% | 100.0% | 48.6 | fail | Useful for measuring product-facing recall on broader active/shadow/no-winner examples; still not a final browsing distribution. |

## Suite Breakdowns

| Scope | Cases | Positives | Negatives | Pos allow | Pos allow rate | Neg abstain | Neg abstain rate | Neg allow | Utility | Target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| active_shadow | 32 | 16 | 16 | 14 | 87.5% | 15 | 93.8% | 1 | 24.6 | pass |
| phrase_no_winner | 16 | 0 | 16 | 0 | n/a | 10 | 62.5% | 6 | 4.4 | pass |
| sentence_veto_v10 | 95 | 38 | 57 | 13 | 34.2% | 57 | 100.0% | 0 | 48.6 | fail |

## Failure Rows

| Case | Suite | Trigger | Outcome | Error | Sentence |
| --- | --- | --- | --- | --- | --- |
| en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:gross:002 | active_shadow | gross | negative_allow | harmful_replace | The shop ordered a gross of pencils. |
| en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:fix:001 | active_shadow | fix | positive_abstain | false_abstain | Losing the only key left us in a real fix. |
| en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:meet:001 | active_shadow | meet | positive_abstain | false_abstain | It is meet to thank the volunteers before dinner. |
| en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:cast:001 | phrase_no_winner | cast | negative_allow | harmful_replace | The director praised the cast after rehearsal. |
| en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:wrong:001 | phrase_no_winner | wrong | negative_allow | harmful_replace | He rubbed the organizer the wrong way. |
| en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:stretch:001 | phrase_no_winner | stretch | negative_allow | harmful_replace | That estimate is a stretch. |
| en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:score:001 | phrase_no_winner | score | negative_allow | harmful_replace | The composer wrote the score for the film. |
| en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:squeeze:001 | phrase_no_winner | squeeze | negative_allow | harmful_replace | The squeeze play surprised the defense. |
| en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:foul:001 | phrase_no_winner | foul | negative_allow | harmful_replace | The foul weather delayed the ferry. |
| en-es:sentence-veto:ball:001 | sentence_veto_v10 | ball | positive_abstain | false_abstain | The goalkeeper punched the ball over the bar. |
| en-es:sentence-veto:ball:002 | sentence_veto_v10 | ball | positive_abstain | false_abstain | The child kicked the ball into the street. |
| en-es:sentence-veto:bank:001 | sentence_veto_v10 | bank | positive_abstain | false_abstain | She deposited the cash at the bank before lunch. |
| en-es:sentence-veto:bank:002 | sentence_veto_v10 | bank | positive_abstain | false_abstain | The bank approved our mortgage application. |
| en-es:sentence-veto:plant:001 | sentence_veto_v10 | plant | positive_abstain | false_abstain | She watered the plant on the windowsill. |
| en-es:sentence-veto:plant:002 | sentence_veto_v10 | plant | positive_abstain | false_abstain | The plant needs more sunlight in the afternoon. |
| en-es:sentence-veto:spring:001 | sentence_veto_v10 | spring | positive_abstain | false_abstain | Warm rain usually arrives in spring. |
| en-es:sentence-veto:spring:002 | sentence_veto_v10 | spring | positive_abstain | false_abstain | The park looks beautiful in the spring. |
| en-es:sentence-veto:match:001 | sentence_veto_v10 | match | positive_abstain | false_abstain | The match ended after extra time. |
| en-es:sentence-veto:board:001 | sentence_veto_v10 | board | positive_abstain | false_abstain | He arranged the pieces on the board before the lesson began. |
| en-es:sentence-veto:table:001 | sentence_veto_v10 | table | positive_abstain | false_abstain | The plates are already on the table. |
| en-es:sentence-veto:branch:001 | sentence_veto_v10 | branch | positive_abstain | false_abstain | The downtown branch closes at five on weekdays. |
| en-es:sentence-veto:park:001 | sentence_veto_v10 | park | positive_abstain | false_abstain | The children ran through the park after school. |
| en-es:sentence-veto:park:002 | sentence_veto_v10 | park | positive_abstain | false_abstain | We met near the fountain in the park. |
| en-es:sentence-veto:play:001 | sentence_veto_v10 | play | positive_abstain | false_abstain | They praised the play in reviews. |
| en-es:sentence-veto:play:002 | sentence_veto_v10 | play | positive_abstain | false_abstain | The play opened last night. |
| en-es:sentence-veto:watch:001 | sentence_veto_v10 | watch | positive_abstain | false_abstain | He adjusted his watch strap before the interview. |
| en-es:sentence-veto:check:001 | sentence_veto_v10 | check | positive_abstain | false_abstain | He signed the check before mailing the rent. |
| en-es:sentence-veto:check:002 | sentence_veto_v10 | check | positive_abstain | false_abstain | The check cleared after the holiday weekend. |
| en-es:sentence-veto:order:001 | sentence_veto_v10 | order | positive_abstain | false_abstain | The order shipped this morning. |
| en-es:sentence-veto:order:002 | sentence_veto_v10 | order | positive_abstain | false_abstain | Your order arrived before noon. |
| en-es:sentence-veto:trip:001 | sentence_veto_v10 | trip | positive_abstain | false_abstain | The trip lasted only two days. |
| en-es:sentence-veto:trip:002 | sentence_veto_v10 | trip | positive_abstain | false_abstain | Their trip ended before sunrise. |
| en-es:sentence-veto:report:001 | sentence_veto_v10 | report | positive_abstain | false_abstain | The report arrived this morning. |
| en-es:sentence-veto:report:002 | sentence_veto_v10 | report | positive_abstain | false_abstain | The report was delayed until Friday. |

## Interpretation

- The measured lanes do not meet the initial product target.
- Use failure rows to decide whether the next work is evidence, scoring, or policy.

## Next Steps

- Inspect failure rows and suite breakdowns before changing thresholds.
- Prefer data/evidence fixes when negative allows cluster by missing phrase or shadow evidence.
- Prefer policy fixes only when score traces already expose the correct no-replace signal.

## Limitations

- `product_metrics_do_not_replace_runtime_validation`
- `stress_lane_is_not_representative_browsing`
- `case_labels_are_inherited_from_source_validation_reports`
- `planned_lanes_unmeasured`
