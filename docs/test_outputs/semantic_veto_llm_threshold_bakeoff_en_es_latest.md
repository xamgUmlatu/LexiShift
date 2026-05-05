# en-es Semantic Veto LLM Threshold Bakeoff

- Status: `ok`
- Decision: `separate_threshold_discovery_candidate_found`
- Generated: `2026-05-04T23:42:23Z`
- Selection lane: `llm_discovery`
- Candidate rows: `121`
- All-lane pass rows: `2`

## E2E Checks

| Check | Value |
| --- | --- |
| `calculus_source` | `scripts/testing/semantic_veto_product_quality_en_es.py::score_product_outcome_counts` |
| `llm_case_rows_read` | `72` |
| `llm_discovery_rows_read` | `56` |
| `llm_locked_eval_rows_read` | `16` |
| `validation_reports_read` | `2` |
| `manual_stress_rows_read` | `48` |
| `candidate_rows_emitted` | `121` |
| `shadow_lead_grid` | `-0.1, -0.075, -0.05, -0.025, 0.0, 0.025, 0.05, 0.075, 0.1, 0.125, 0.15` |
| `phrase_lead_grid` | `-0.1, -0.075, -0.05, -0.025, 0.0, 0.025, 0.05, 0.075, 0.1, 0.125, 0.15` |

## Selected Discovery Candidate

| Candidate | Shadow | Phrase | Disc pos | Disc neg | Locked pos | Locked neg | Stress pos | Stress neg | Stress utility |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| separate_thresholds\|shadow=-0.05\|phrase=-0.025 | -0.05 | -0.025 | 80.8% | 83.3% | 80.0% | 83.3% | 12.5% | 100.0% | 22.0 |

## Incumbent

| Candidate | Shadow | Phrase | Disc pos | Disc neg | Locked pos | Locked neg | Stress pos | Stress neg | Stress utility |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| separate_thresholds\|shadow=0.05\|phrase=0.05 | 0.05 | 0.05 | 84.6% | 50.0% | 100.0% | 66.7% | 81.2% | 75.0% | 26.2 |

## Top Discovery Rows

| Candidate | Shadow | Phrase | Disc pos | Disc neg | Locked pos | Locked neg | Stress pos | Stress neg | Stress utility |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| separate_thresholds\|shadow=-0.05\|phrase=-0.025 | -0.05 | -0.025 | 80.8% | 83.3% | 80.0% | 83.3% | 12.5% | 100.0% | 22.0 |
| separate_thresholds\|shadow=-0.05\|phrase=0.0 | -0.05 | 0.0 | 80.8% | 83.3% | 90.0% | 83.3% | 12.5% | 100.0% | 22.0 |
| separate_thresholds\|shadow=-0.05\|phrase=0.025 | -0.05 | 0.025 | 80.8% | 80.0% | 90.0% | 83.3% | 18.8% | 100.0% | 23.4 |
| separate_thresholds\|shadow=-0.05\|phrase=0.05 | -0.05 | 0.05 | 80.8% | 80.0% | 90.0% | 83.3% | 25.0% | 100.0% | 24.8 |
| separate_thresholds\|shadow=-0.05\|phrase=0.075 | -0.05 | 0.075 | 80.8% | 80.0% | 90.0% | 83.3% | 25.0% | 100.0% | 24.8 |
| separate_thresholds\|shadow=-0.05\|phrase=0.1 | -0.05 | 0.1 | 80.8% | 80.0% | 90.0% | 83.3% | 25.0% | 100.0% | 24.8 |
| separate_thresholds\|shadow=-0.05\|phrase=0.125 | -0.05 | 0.125 | 80.8% | 80.0% | 90.0% | 83.3% | 25.0% | 100.0% | 24.8 |
| separate_thresholds\|shadow=-0.05\|phrase=0.15 | -0.05 | 0.15 | 80.8% | 80.0% | 90.0% | 83.3% | 25.0% | 100.0% | 24.8 |
| separate_thresholds\|shadow=-0.025\|phrase=0.075 | -0.025 | 0.075 | 84.6% | 73.3% | 90.0% | 83.3% | 37.5% | 93.8% | 24.8 |
| separate_thresholds\|shadow=-0.025\|phrase=0.1 | -0.025 | 0.1 | 84.6% | 73.3% | 90.0% | 83.3% | 37.5% | 93.8% | 24.8 |
| separate_thresholds\|shadow=-0.025\|phrase=0.125 | -0.025 | 0.125 | 84.6% | 73.3% | 90.0% | 83.3% | 37.5% | 93.8% | 24.8 |
| separate_thresholds\|shadow=-0.025\|phrase=0.15 | -0.025 | 0.15 | 84.6% | 73.3% | 90.0% | 83.3% | 37.5% | 93.8% | 24.8 |

## Top All-Lane Rows

| Candidate | Shadow | Phrase | Disc pos | Disc neg | Locked pos | Locked neg | Stress pos | Stress neg | Stress utility |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| separate_thresholds\|shadow=0.05\|phrase=0.075 | 0.05 | 0.075 | 96.2% | 50.0% | 100.0% | 66.7% | 81.2% | 68.8% | 23.4 |
| separate_thresholds\|shadow=0.05\|phrase=0.05 | 0.05 | 0.05 | 84.6% | 50.0% | 100.0% | 66.7% | 81.2% | 75.0% | 26.2 |
| separate_thresholds\|shadow=-0.05\|phrase=0.05 | -0.05 | 0.05 | 80.8% | 80.0% | 90.0% | 83.3% | 25.0% | 100.0% | 24.8 |
| separate_thresholds\|shadow=-0.05\|phrase=0.075 | -0.05 | 0.075 | 80.8% | 80.0% | 90.0% | 83.3% | 25.0% | 100.0% | 24.8 |
| separate_thresholds\|shadow=-0.05\|phrase=0.1 | -0.05 | 0.1 | 80.8% | 80.0% | 90.0% | 83.3% | 25.0% | 100.0% | 24.8 |
| separate_thresholds\|shadow=-0.05\|phrase=0.125 | -0.05 | 0.125 | 80.8% | 80.0% | 90.0% | 83.3% | 25.0% | 100.0% | 24.8 |
| separate_thresholds\|shadow=-0.05\|phrase=0.15 | -0.05 | 0.15 | 80.8% | 80.0% | 90.0% | 83.3% | 25.0% | 100.0% | 24.8 |
| separate_thresholds\|shadow=-0.025\|phrase=0.075 | -0.025 | 0.075 | 84.6% | 73.3% | 90.0% | 83.3% | 37.5% | 93.8% | 24.8 |
| separate_thresholds\|shadow=-0.025\|phrase=0.1 | -0.025 | 0.1 | 84.6% | 73.3% | 90.0% | 83.3% | 37.5% | 93.8% | 24.8 |
| separate_thresholds\|shadow=-0.025\|phrase=0.125 | -0.025 | 0.125 | 84.6% | 73.3% | 90.0% | 83.3% | 37.5% | 93.8% | 24.8 |
| separate_thresholds\|shadow=-0.025\|phrase=0.15 | -0.025 | 0.15 | 84.6% | 73.3% | 90.0% | 83.3% | 37.5% | 93.8% | 24.8 |
| separate_thresholds\|shadow=-0.05\|phrase=0.025 | -0.05 | 0.025 | 80.8% | 80.0% | 90.0% | 83.3% | 18.8% | 100.0% | 23.4 |

## Validation Sources

| Report | Cases | Status | Decision | Path |
| --- | ---: | --- | --- | --- |
| semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout_validation_latest | 32 | review | heldout_review | docs/test_outputs/semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout_validation_latest.json |
| semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase_validation_latest | 16 | review | heldout_review | docs/test_outputs/semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase_validation_latest.json |

## Recommendation

- A discovery-selected separate-threshold candidate exists; evaluate it as research-only.
- Do not promote it from this report alone because selection used LLM discovery data.
- The discovery-selected candidate overblocks manual/stress positives relative to the incumbent.
- At least one row passes discovery, locked-eval, and combined manual/stress targets; inspect source breakdowns before considering a follow-up candidate-selection harness.
