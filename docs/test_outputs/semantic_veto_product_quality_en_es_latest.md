# en-es Semantic Veto Product Quality

- Status: `review`
- Decision: `product_target_missed`
- Generated: `2026-05-05T18:21:59Z`
- Policy: `docs/test_inputs/semantic_veto_product_quality_policy_en_es.json`
- Cases: `168`
- Measured lane types: `representative, stress`
- Planned unmeasured lane types: `llm_expanded_eval, representative_expanded`

## Overall Product Metrics

| Scope | Cases | Positives | Negatives | Pos allow | Pos allow rate | Neg abstain | Neg abstain rate | Neg allow | Utility | Target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| overall | 168 | 69 | 99 | 27 | 39.1% | 92 | 92.9% | 7 | 79.6 | fail |

## Baselines

| Baseline | Utility | Utility/case | Positive allow rate | Negative abstain rate | Delta current utility |
| --- | ---: | ---: | ---: | ---: | ---: |
| lexical_allow_all | 9.6 | 0.0571 | 100.0% | 0.0% | 70.0 |
| abstain_all | 51.6 | 0.3071 | 0.0% | 100.0% | 28.0 |

## Lanes

| Lane | Type | Cases | Pos allow rate | Neg abstain rate | Utility | Target | Interpretation |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| wave7_phrase_control_triage_stress | stress | 48 | 87.5% | 78.1% | 29.0 | pass | Useful for guarding known hard cases; not representative browsing evidence. |
| sampling_stage1_representative_proxy | representative | 120 | 24.5% | 100.0% | 50.6 | fail | Useful for measuring product-facing recall on the filled 120-row representative proxy; still not a final browsing distribution, and the 25 corpus-like rows need human review. |

## Suite Breakdowns

| Scope | Cases | Positives | Negatives | Pos allow | Pos allow rate | Neg abstain | Neg abstain rate | Neg allow | Utility | Target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| active_shadow | 32 | 16 | 16 | 14 | 87.5% | 15 | 93.8% | 1 | 24.6 | pass |
| phrase_no_winner | 16 | 0 | 16 | 0 | n/a | 10 | 62.5% | 6 | 4.4 | pass |
| sampling_stage1_representative | 120 | 53 | 67 | 13 | 24.5% | 67 | 100.0% | 0 | 50.6 | fail |

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
| en-es:representative-gap:v1:001 | sampling_stage1_representative | ball | positive_abstain | false_abstain | A fan caught the foul ball in the second inning. |
| en-es:sentence-veto:ball:001 | sampling_stage1_representative | ball | positive_abstain | false_abstain | The goalkeeper punched the ball over the bar. |
| en-es:sentence-veto:ball:002 | sampling_stage1_representative | ball | positive_abstain | false_abstain | The child kicked the ball into the street. |
| en-es:representative-gap:v1:003 | sampling_stage1_representative | bank | positive_abstain | false_abstain | The bank froze the card after the suspicious charge. |
| en-es:sentence-veto:bank:001 | sampling_stage1_representative | bank | positive_abstain | false_abstain | She deposited the cash at the bank before lunch. |
| en-es:sentence-veto:bank:002 | sampling_stage1_representative | bank | positive_abstain | false_abstain | The bank approved our mortgage application. |
| en-es:representative-gap:v1:015 | sampling_stage1_representative | board | positive_abstain | false_abstain | The chess board was missing two squares. |
| en-es:sentence-veto:board:001 | sampling_stage1_representative | board | positive_abstain | false_abstain | He arranged the pieces on the board before the lesson began. |
| en-es:representative-gap:v1:019 | sampling_stage1_representative | branch | positive_abstain | false_abstain | The new branch opened beside the train station. |
| en-es:sentence-veto:branch:001 | sampling_stage1_representative | branch | positive_abstain | false_abstain | The downtown branch closes at five on weekdays. |
| en-es:sentence-veto:check:001 | sampling_stage1_representative | check | positive_abstain | false_abstain | He signed the check before mailing the rent. |
| en-es:sentence-veto:check:002 | sampling_stage1_representative | check | positive_abstain | false_abstain | The check cleared after the holiday weekend. |
| en-es:representative-gap:v1:023 | sampling_stage1_representative | drink | positive_abstain | false_abstain | The cold drink helped after the long walk. |
| en-es:sentence-veto:drink:001 | sampling_stage1_representative | drink | positive_abstain | false_abstain | They enjoyed a drink after dinner. |
| en-es:sentence-veto:drink:002 | sampling_stage1_representative | drink | positive_abstain | false_abstain | I ordered a drink at the bar. |
| en-es:representative-gap:v1:012 | sampling_stage1_representative | file | positive_abstain | false_abstain | The file attached to the email contains the receipts. |
| en-es:representative-gap:v1:013 | sampling_stage1_representative | match | positive_abstain | false_abstain | The final match drew a huge crowd downtown. |
| en-es:sentence-veto:match:001 | sampling_stage1_representative | match | positive_abstain | false_abstain | The match ended after extra time. |
| en-es:sentence-veto:order:001 | sampling_stage1_representative | order | positive_abstain | false_abstain | The order shipped this morning. |
| en-es:sentence-veto:order:002 | sampling_stage1_representative | order | positive_abstain | false_abstain | Your order arrived before noon. |
| en-es:representative-gap:v1:021 | sampling_stage1_representative | park | positive_abstain | false_abstain | Families filled the park on Saturday afternoon. |
| en-es:sentence-veto:park:001 | sampling_stage1_representative | park | positive_abstain | false_abstain | The children ran through the park after school. |
| en-es:sentence-veto:park:002 | sampling_stage1_representative | park | positive_abstain | false_abstain | We met near the fountain in the park. |
| en-es:representative-gap:v1:004 | sampling_stage1_representative | plant | positive_abstain | false_abstain | A small plant on the shelf drooped in the heat. |
| en-es:sentence-veto:plant:001 | sampling_stage1_representative | plant | positive_abstain | false_abstain | She watered the plant on the windowsill. |
| en-es:sentence-veto:plant:002 | sampling_stage1_representative | plant | positive_abstain | false_abstain | The plant needs more sunlight in the afternoon. |
| en-es:representative-gap:v1:024 | sampling_stage1_representative | play | positive_abstain | false_abstain | The school play starts at seven tonight. |
| en-es:sentence-veto:play:001 | sampling_stage1_representative | play | positive_abstain | false_abstain | They praised the play in reviews. |
| en-es:sentence-veto:play:002 | sampling_stage1_representative | play | positive_abstain | false_abstain | The play opened last night. |
| en-es:sentence-veto:report:001 | sampling_stage1_representative | report | positive_abstain | false_abstain | The report arrived this morning. |
| en-es:sentence-veto:report:002 | sampling_stage1_representative | report | positive_abstain | false_abstain | The report was delayed until Friday. |
| en-es:representative-gap:v1:010 | sampling_stage1_representative | seal | positive_abstain | false_abstain | The customs seal on the box was still intact. |
| en-es:sentence-veto:spring:001 | sampling_stage1_representative | spring | positive_abstain | false_abstain | Warm rain usually arrives in spring. |
| en-es:sentence-veto:spring:002 | sampling_stage1_representative | spring | positive_abstain | false_abstain | The park looks beautiful in the spring. |
| en-es:representative-gap:v1:017 | sampling_stage1_representative | table | positive_abstain | false_abstain | The table near the window seats four people. |
| en-es:sentence-veto:table:001 | sampling_stage1_representative | table | positive_abstain | false_abstain | The plates are already on the table. |
| en-es:sentence-veto:trip:001 | sampling_stage1_representative | trip | positive_abstain | false_abstain | The trip lasted only two days. |
| en-es:sentence-veto:trip:002 | sampling_stage1_representative | trip | positive_abstain | false_abstain | Their trip ended before sunrise. |
| en-es:representative-gap:v1:025 | sampling_stage1_representative | watch | positive_abstain | false_abstain | His watch stopped just before the meeting. |
| en-es:sentence-veto:watch:001 | sampling_stage1_representative | watch | positive_abstain | false_abstain | He adjusted his watch strap before the interview. |

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
