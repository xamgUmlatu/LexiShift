# en-es Semantic Veto Evidence-Gap Generation Admission

- Status: `ok`
- Decision: `generated_items_admitted_for_pilot_rescoring`
- Generated: `2026-05-11T22:43:57Z`
- Requests: `docs/test_outputs/semantic_veto_active_only_full_generation_plan_en_es_latest.json`
- Generated responses: `docs/test_outputs/semantic_veto_active_only_full_v1_tranche_001_work_repair_manual_exact_token_generated_responses_en_es_latest.json`
- Generated responses present: `True`

## Summary

- Expected requests: `1`
- Generated responses: `1`
- Expected items: `2`
- Admitted items: `2`
- Rejected items: `0`
- Waived items: `0`
- Coverage shortfall: `0`

## Alignment

- Matched expected requests: `1`
- Missing expected requests: `0`
- Unexpected response requests: `0`

## Arm Summary

| Arm | Expected requests | Expected items | Admitted | Rejected | Waived | Shortfall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `P0_exposure_first` | 1 | 2 | 2 | 0 | 0 | 0 |

## Slot Summary

| Slot type | Expected requests | Expected items | Admitted | Rejected | Waived | Shortfall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `active_evidence_expansion` | 1 | 2 | 2 | 0 | 0 | 0 |

## Rejection Reasons

_None._

## Coverage Samples

| Request | Arm | Slot | Expected | Admitted | Waived | Shortfall |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:work:trabajar:41fc059d:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |

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
