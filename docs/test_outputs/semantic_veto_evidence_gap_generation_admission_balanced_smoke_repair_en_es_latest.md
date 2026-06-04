# en-es Semantic Veto Evidence-Gap Generation Admission

- Status: `ok`
- Decision: `generated_items_admitted_for_pilot_rescoring`
- Generated: `2026-05-08T03:11:11Z`
- Requests: `docs/test_outputs/semantic_veto_evidence_gap_generation_requests_en_es_latest.json`
- Generated responses: `docs/test_outputs/semantic_veto_evidence_gap_generated_responses_balanced_smoke_repair_en_es_latest.json`
- Generated responses present: `True`

## Summary

- Expected requests: `1`
- Generated responses: `1`
- Expected items: `2`
- Admitted items: `2`
- Rejected items: `0`
- Coverage shortfall: `0`

## Alignment

- Matched expected requests: `1`
- Missing expected requests: `0`
- Unexpected response requests: `0`

## Arm Summary

| Arm | Expected requests | Expected items | Admitted | Rejected | Shortfall |
| --- | ---: | ---: | ---: | ---: | ---: |
| `low_control` | 1 | 2 | 2 | 0 | 0 |

## Slot Summary

| Slot type | Expected requests | Expected items | Admitted | Rejected | Shortfall |
| --- | ---: | ---: | ---: | ---: | ---: |
| `shadow_or_competitor_evidence_probe` | 1 | 2 | 2 | 0 | 0 |

## Rejection Reasons

_None._

## Coverage Samples

| Request | Arm | Slot | Expected | Admitted | Shortfall |
| --- | --- | --- | ---: | ---: | ---: |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:smile:sonre-r:shadow_or_competitor_evidence_probe` | `low_control` | `shadow_or_competitor_evidence_probe` | 2 | 2 | 0 |

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
