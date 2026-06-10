# en-ja Semantic Veto Product Quality

- Status: `review`
- Decision: `stress_lane_product_target_pass_representative_unmeasured`
- Generated: `2026-06-09T18:13:03Z`
- Policy: `docs/test_inputs/semantic_veto_product_quality_policy_en_ja.json`
- Cases: `95`
- Measured lane types: `stress`
- Planned unmeasured lane types: `representative`

## Overall Product Metrics

| Scope | Cases | Positives | Negatives | Pos allow | Pos allow rate | Neg abstain | Neg abstain rate | Neg allow | Utility | Target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| overall | 95 | 38 | 57 | 35 | 92.1% | 57 | 100.0% | 0 | 79.4 | pass |

## Baselines

| Baseline | Utility | Utility/case | Positive allow rate | Negative abstain rate | Delta current utility |
| --- | ---: | ---: | ---: | ---: | ---: |
| lexical_allow_all | 3.8 | 0.04 | 100.0% | 0.0% | 75.6 |
| abstain_all | 30.4 | 0.32 | 0.0% | 100.0% | 49.0 |

## Lanes

| Lane | Type | Cases | Pos allow rate | Neg abstain rate | Utility | Target | Interpretation |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| en_ja_sentence_veto_breadth_v1 | stress | 95 | 92.1% | 100.0% | 79.4 | pass | Useful for scoring and parameter sanity across en-es-style stress breadth; still not representative browsing evidence by itself. |

## Suite Breakdowns

| Scope | Cases | Positives | Negatives | Pos allow | Pos allow rate | Neg abstain | Neg abstain rate | Neg allow | Utility | Target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| en_ja_sentence_veto_breadth_v1 | 95 | 38 | 57 | 35 | 92.1% | 57 | 100.0% | 0 | 79.4 | pass |

## Failure Rows

| Case | Suite | Trigger | Outcome | Error | Sentence |
| --- | --- | --- | --- | --- | --- |
| en-ja:sentence-veto:ball:001 | en_ja_sentence_veto_breadth_v1 | ball | positive_abstain | false_abstain | The goalkeeper punched the ball over the bar. |
| en-ja:sentence-veto:ball:002 | en_ja_sentence_veto_breadth_v1 | ball | positive_abstain | false_abstain | The child kicked the ball into the street. |
| en-ja:sentence-veto:plant:001 | en_ja_sentence_veto_breadth_v1 | plant | positive_abstain | false_abstain | She watered the plant on the windowsill. |

## Interpretation

- The measured stress lane meets the initial product target and beats lexical baseline.
- This is not production evidence because no representative browsing lane has been measured.
- The next useful milestone is to add a representative or LLM-expanded locked lane.

## Next Steps

- Add a representative browsing lane before making a broad product-quality claim.
- Use LLM generation budget to create admitted positive, negative, and phrase/no-winner rows for that lane.
- Keep this stress lane in the report so future candidates cannot hide regressions on known hard cases.

## Limitations

- `product_metrics_do_not_replace_runtime_validation`
- `stress_lane_is_not_representative_browsing`
- `case_labels_are_inherited_from_source_validation_reports`
- `planned_lanes_unmeasured`
