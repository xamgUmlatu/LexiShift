# en-es Semantic Veto Evidence-Gap Generation Admission

- Status: `ok`
- Decision: `generated_items_admitted_for_pilot_rescoring`
- Generated: `2026-05-09T22:52:30Z`
- Requests: `docs/test_outputs/semantic_veto_active_only_scale_tranche_v1_requests_en_es_latest.json`
- Generated responses: `docs/test_outputs/semantic_veto_active_only_scale_tranche_v1_generated_responses_repaired_en_es_latest.json`
- Generated responses present: `True`

## Summary

- Expected requests: `16`
- Generated responses: `16`
- Expected items: `32`
- Admitted items: `32`
- Rejected items: `0`
- Waived items: `0`
- Coverage shortfall: `0`

## Alignment

- Matched expected requests: `16`
- Missing expected requests: `0`
- Unexpected response requests: `0`

## Arm Summary

| Arm | Expected requests | Expected items | Admitted | Rejected | Waived | Shortfall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `high_need` | 6 | 12 | 12 | 0 | 0 | 0 |
| `low_control` | 6 | 12 | 12 | 0 | 0 | 0 |
| `middle_control` | 4 | 8 | 8 | 0 | 0 | 0 |

## Slot Summary

| Slot type | Expected requests | Expected items | Admitted | Rejected | Waived | Shortfall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `active_evidence_expansion` | 16 | 32 | 32 | 0 | 0 | 0 |

## Rejection Reasons

_None._

## Coverage Samples

| Request | Arm | Slot | Expected | Admitted | Waived | Shortfall |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `semantic_veto_active_only_scale_tranche_v1_en_es:en-es:full-family-repaired-full:adder:v-bora:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_active_only_scale_tranche_v1_en_es:en-es:full-family-repaired-full:adjoining:contiguo:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_active_only_scale_tranche_v1_en_es:en-es:full-family-repaired-full:altitude:elevaci-n:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_active_only_scale_tranche_v1_en_es:en-es:full-family-repaired-full:billow:oleaje:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_active_only_scale_tranche_v1_en_es:en-es:full-family-repaired-full:continue:durar:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_active_only_scale_tranche_v1_en_es:en-es:full-family-repaired-full:current:contempor-neo:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_active_only_scale_tranche_v1_en_es:en-es:full-family-repaired-full:emotion:emoci-n:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_active_only_scale_tranche_v1_en_es:en-es:full-family-repaired-full:handiwork:artesan-a:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_active_only_scale_tranche_v1_en_es:en-es:full-family-repaired-full:health:salud:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_active_only_scale_tranche_v1_en_es:en-es:full-family-repaired-full:june:junio:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_active_only_scale_tranche_v1_en_es:en-es:full-family-repaired-full:pair:par:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_active_only_scale_tranche_v1_en_es:en-es:full-family-repaired-full:parrot:loro:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_active_only_scale_tranche_v1_en_es:en-es:full-family-repaired-full:recover:sanar:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_active_only_scale_tranche_v1_en_es:en-es:full-family-repaired-full:snore:roncar:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_active_only_scale_tranche_v1_en_es:en-es:full-family-repaired-full:stall:cuadra:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_active_only_scale_tranche_v1_en_es:en-es:full-family-repaired-full:upon:sobre:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |

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
