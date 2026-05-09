# en-es Semantic Veto Evidence-Gap Generation Admission

- Status: `ok`
- Decision: `generated_items_admitted_for_pilot_rescoring`
- Generated: `2026-05-09T00:15:00Z`
- Requests: `docs/test_inputs/semantic_veto_evidence_gap_prompt_variant_requests_en_es/v6_diversity_only.json`
- Generated responses: `docs/test_outputs/semantic_veto_evidence_gap_generated_responses_prompt_bakeoff_v6_diversity_only_en_es_latest.json`
- Generated responses present: `True`

## Summary

- Expected requests: `24`
- Generated responses: `24`
- Expected items: `48`
- Admitted items: `48`
- Rejected items: `0`
- Waived items: `0`
- Coverage shortfall: `0`

## Alignment

- Matched expected requests: `24`
- Missing expected requests: `0`
- Unexpected response requests: `0`

## Arm Summary

| Arm | Expected requests | Expected items | Admitted | Rejected | Waived | Shortfall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `high_need` | 8 | 16 | 16 | 0 | 0 | 0 |
| `low_control` | 8 | 16 | 16 | 0 | 0 | 0 |
| `middle_control` | 8 | 16 | 16 | 0 | 0 | 0 |

## Slot Summary

| Slot type | Expected requests | Expected items | Admitted | Rejected | Waived | Shortfall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `active_evidence_expansion` | 24 | 48 | 48 | 0 | 0 | 0 |

## Rejection Reasons

_None._

## Coverage Samples

| Request | Arm | Slot | Expected | Admitted | Waived | Shortfall |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:acceptable:razonable:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:adjoining:vecino:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:american:americano:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:among:entre:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:bar:cercar:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:begin:comenzar:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:bouillon:caldo:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:break:quebrar:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:bridle:reprimir:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:brother:hermano:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:chic:elegante:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:control:gobernar:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:december:diciembre:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:dentist:dentista:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:entirely:enteramente:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:german:alem-n:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:govern:gobernar:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:heart:coraz-n:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:offset:distancia:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:rebate:descuento:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:rumanian:rumano:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:salesman:vendedor:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:smile:sonre-r:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:tomorrow:ma-ana:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |

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
