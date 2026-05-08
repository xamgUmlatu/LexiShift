# en-es Semantic Veto Evidence-Gap Generation Admission

- Status: `ok`
- Decision: `generated_items_admitted_for_pilot_rescoring`
- Generated: `2026-05-08T03:10:27Z`
- Requests: `docs/test_outputs/semantic_veto_evidence_gap_generation_requests_en_es_latest.json`
- Generated responses: `docs/test_outputs/semantic_veto_evidence_gap_generated_responses_smoke_replay_en_es_latest.json`
- Generated responses present: `True`

## Summary

- Expected requests: `3`
- Generated responses: `3`
- Expected items: `5`
- Admitted items: `5`
- Rejected items: `0`
- Coverage shortfall: `0`

## Alignment

- Matched expected requests: `3`
- Missing expected requests: `0`
- Unexpected response requests: `0`

## Arm Summary

| Arm | Expected requests | Expected items | Admitted | Rejected | Shortfall |
| --- | ---: | ---: | ---: | ---: | ---: |
| `high_need` | 3 | 5 | 5 | 0 | 0 |

## Slot Summary

| Slot type | Expected requests | Expected items | Admitted | Rejected | Shortfall |
| --- | ---: | ---: | ---: | ---: | ---: |
| `active_evidence_expansion` | 1 | 2 | 2 | 0 | 0 |
| `no_winner_context_probe` | 1 | 1 | 1 | 0 | 0 |
| `shadow_or_competitor_evidence_probe` | 1 | 2 | 2 | 0 | 0 |

## Rejection Reasons

_None._

## Coverage Samples

| Request | Arm | Slot | Expected | Admitted | Shortfall |
| --- | --- | --- | ---: | ---: | ---: |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:adjoining:vecino:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | 2 | 2 | 0 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:adjoining:vecino:no_winner_context_probe` | `high_need` | `no_winner_context_probe` | 1 | 1 | 0 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:adjoining:vecino:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | 2 | 2 | 0 |

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
