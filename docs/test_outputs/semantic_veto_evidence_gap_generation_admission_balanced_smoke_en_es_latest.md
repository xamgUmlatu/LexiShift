# en-es Semantic Veto Evidence-Gap Generation Admission

- Status: `ok`
- Decision: `generated_items_admitted_for_pilot_rescoring`
- Generated: `2026-05-08T19:36:01Z`
- Requests: `docs/test_outputs/semantic_veto_evidence_gap_generation_requests_en_es_latest.json`
- Generated responses: `docs/test_outputs/semantic_veto_evidence_gap_generated_responses_balanced_smoke_en_es_latest.json`
- Generated responses present: `True`

## Summary

- Expected requests: `9`
- Generated responses: `9`
- Expected items: `15`
- Admitted items: `13`
- Rejected items: `0`
- Waived items: `2`
- Coverage shortfall: `0`

## Alignment

- Matched expected requests: `9`
- Missing expected requests: `0`
- Unexpected response requests: `0`

## Arm Summary

| Arm | Expected requests | Expected items | Admitted | Rejected | Waived | Shortfall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `high_need` | 3 | 5 | 3 | 0 | 2 | 0 |
| `low_control` | 3 | 5 | 5 | 0 | 0 | 0 |
| `middle_control` | 3 | 5 | 5 | 0 | 0 | 0 |

## Slot Summary

| Slot type | Expected requests | Expected items | Admitted | Rejected | Waived | Shortfall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `active_evidence_expansion` | 3 | 6 | 6 | 0 | 0 | 0 |
| `no_winner_context_probe` | 3 | 3 | 3 | 0 | 0 | 0 |
| `shadow_or_competitor_evidence_probe` | 3 | 6 | 4 | 0 | 2 | 0 |

## Rejection Reasons

_None._

## Coverage Samples

| Request | Arm | Slot | Expected | Admitted | Waived | Shortfall |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:brother:hermano:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:brother:hermano:no_winner_context_probe` | `middle_control` | `no_winner_context_probe` | 1 | 1 | 0 | 0 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:brother:hermano:shadow_or_competitor_evidence_probe` | `middle_control` | `shadow_or_competitor_evidence_probe` | 2 | 2 | 0 | 0 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:entirely:enteramente:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:entirely:enteramente:no_winner_context_probe` | `high_need` | `no_winner_context_probe` | 1 | 1 | 0 | 0 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:entirely:enteramente:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | 2 | 0 | 2 | 0 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:smile:sonre-r:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:smile:sonre-r:no_winner_context_probe` | `low_control` | `no_winner_context_probe` | 1 | 1 | 0 | 0 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:smile:sonre-r:shadow_or_competitor_evidence_probe` | `low_control` | `shadow_or_competitor_evidence_probe` | 2 | 2 | 0 | 0 |

## Next Steps

- Run the downstream evidence-application/rescoring harness on admitted generated items.
- Compare improvement by high_need, middle_control, and low_control arms.
- Treat this as heuristic validation, not runtime promotion.

## Limitations

- `research-only generated-response admission lane`
- `no LLM call is made by this script`
- `no generated item is source evidence until a later explicit promotion step`
- `no runtime policy or threshold changes are made`
- `semantic correctness of generated text still needs scoring and spot review`
