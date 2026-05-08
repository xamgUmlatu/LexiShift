# en-es Semantic Veto Evidence-Gap Generation Admission

- Status: `ok`
- Decision: `ready_for_generated_response_admission`
- Generated: `2026-05-08T03:10:13Z`
- Requests: `docs/test_outputs/semantic_veto_evidence_gap_generation_requests_en_es_latest.json`
- Generated responses: ``
- Generated responses present: `False`

## Summary

- Expected requests: `72`
- Generated responses: `0`
- Expected items: `120`
- Admitted items: `0`
- Rejected items: `0`
- Coverage shortfall: `120`

## Alignment

- Matched expected requests: `0`
- Missing expected requests: `0`
- Unexpected response requests: `0`

## Arm Summary

| Arm | Expected requests | Expected items | Admitted | Rejected | Shortfall |
| --- | ---: | ---: | ---: | ---: | ---: |
| `high_need` | 24 | 40 | 0 | 0 | 40 |
| `low_control` | 24 | 40 | 0 | 0 | 40 |
| `middle_control` | 24 | 40 | 0 | 0 | 40 |

## Slot Summary

| Slot type | Expected requests | Expected items | Admitted | Rejected | Shortfall |
| --- | ---: | ---: | ---: | ---: | ---: |
| `active_evidence_expansion` | 24 | 48 | 0 | 0 | 48 |
| `no_winner_context_probe` | 24 | 24 | 0 | 0 | 24 |
| `shadow_or_competitor_evidence_probe` | 24 | 48 | 0 | 0 | 48 |

## Rejection Reasons

_None._

## Coverage Samples

| Request | Arm | Slot | Expected | Admitted | Shortfall |
| --- | --- | --- | ---: | ---: | ---: |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:acceptable:razonable:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | 2 | 0 | 2 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:acceptable:razonable:no_winner_context_probe` | `middle_control` | `no_winner_context_probe` | 1 | 0 | 1 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:acceptable:razonable:shadow_or_competitor_evidence_probe` | `middle_control` | `shadow_or_competitor_evidence_probe` | 2 | 0 | 2 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:adjoining:vecino:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | 2 | 0 | 2 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:adjoining:vecino:no_winner_context_probe` | `high_need` | `no_winner_context_probe` | 1 | 0 | 1 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:adjoining:vecino:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | 2 | 0 | 2 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:american:americano:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | 2 | 0 | 2 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:american:americano:no_winner_context_probe` | `high_need` | `no_winner_context_probe` | 1 | 0 | 1 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:american:americano:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | 2 | 0 | 2 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:among:entre:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | 2 | 0 | 2 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:among:entre:no_winner_context_probe` | `high_need` | `no_winner_context_probe` | 1 | 0 | 1 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:among:entre:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | 2 | 0 | 2 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:bar:cercar:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | 2 | 0 | 2 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:bar:cercar:no_winner_context_probe` | `low_control` | `no_winner_context_probe` | 1 | 0 | 1 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:bar:cercar:shadow_or_competitor_evidence_probe` | `low_control` | `shadow_or_competitor_evidence_probe` | 2 | 0 | 2 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:begin:comenzar:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | 2 | 0 | 2 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:begin:comenzar:no_winner_context_probe` | `high_need` | `no_winner_context_probe` | 1 | 0 | 1 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:begin:comenzar:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | 2 | 0 | 2 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:bouillon:caldo:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | 2 | 0 | 2 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:bouillon:caldo:no_winner_context_probe` | `high_need` | `no_winner_context_probe` | 1 | 0 | 1 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:bouillon:caldo:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | 2 | 0 | 2 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:break:quebrar:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | 2 | 0 | 2 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:break:quebrar:no_winner_context_probe` | `low_control` | `no_winner_context_probe` | 1 | 0 | 1 |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:break:quebrar:shadow_or_competitor_evidence_probe` | `low_control` | `shadow_or_competitor_evidence_probe` | 2 | 0 | 2 |

## Next Steps

- Review the request packet, then run the bounded LLM generation batch.
- Run this admission harness on the generated response objects before rescoring.
- Keep high, middle, and low arms under the same response and admission contract.

## Limitations

- `research-only generated-response admission lane`
- `no LLM call is made by this script`
- `no generated item is source evidence until a later explicit promotion step`
- `no runtime policy or threshold changes are made`
- `semantic correctness of generated text still needs scoring and spot review`
