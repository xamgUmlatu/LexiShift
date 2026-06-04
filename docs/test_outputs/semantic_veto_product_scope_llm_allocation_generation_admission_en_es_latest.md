# en-es Semantic Veto Evidence-Gap Generation Admission

- Status: `review`
- Decision: `generated_responses_need_repair`
- Generated: `2026-05-09T05:27:39Z`
- Requests: `docs/test_outputs/semantic_veto_product_scope_llm_allocation_generation_requests_en_es_latest.json`
- Generated responses: `docs/test_outputs/semantic_veto_product_scope_llm_allocation_generated_responses_en_es_latest.json`
- Generated responses present: `True`

## Summary

- Expected requests: `60`
- Generated responses: `60`
- Expected items: `100`
- Admitted items: `84`
- Rejected items: `4`
- Waived items: `10`
- Coverage shortfall: `6`

## Alignment

- Matched expected requests: `60`
- Missing expected requests: `0`
- Unexpected response requests: `0`

## Arm Summary

| Arm | Expected requests | Expected items | Admitted | Rejected | Waived | Shortfall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `high_need` | 24 | 40 | 38 | 2 | 0 | 2 |
| `low_control` | 24 | 40 | 28 | 2 | 8 | 4 |
| `middle_control` | 12 | 20 | 18 | 0 | 2 | 0 |

## Slot Summary

| Slot type | Expected requests | Expected items | Admitted | Rejected | Waived | Shortfall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `active_evidence_expansion` | 20 | 40 | 40 | 0 | 0 | 0 |
| `no_winner_context_probe` | 20 | 20 | 20 | 0 | 0 | 0 |
| `shadow_or_competitor_evidence_probe` | 20 | 40 | 24 | 4 | 10 | 6 |

## Rejection Reasons

| Reason | Count |
| --- | ---: |
| `active_mismatch_note_declares_competitor_wrong` | 4 |
| `active_mismatch_note_missing_active_target_lemma` | 2 |
| `duplicate_sentence` | 1 |
| `missing_competitor_target_lemma` | 1 |

## Coverage Samples

| Request | Arm | Slot | Expected | Admitted | Waived | Shortfall |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:acceptable:razonable:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:acceptable:razonable:no_winner_context_probe` | `high_need` | `no_winner_context_probe` | 1 | 1 | 0 | 0 |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:acceptable:razonable:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | 2 | 2 | 0 | 0 |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:adder:v-bora:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:adder:v-bora:no_winner_context_probe` | `middle_control` | `no_winner_context_probe` | 1 | 1 | 0 | 0 |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:adder:v-bora:shadow_or_competitor_evidence_probe` | `middle_control` | `shadow_or_competitor_evidence_probe` | 2 | 2 | 0 | 0 |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:adjoining:contiguo:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:adjoining:contiguo:no_winner_context_probe` | `low_control` | `no_winner_context_probe` | 1 | 1 | 0 | 0 |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:adjoining:contiguo:shadow_or_competitor_evidence_probe` | `low_control` | `shadow_or_competitor_evidence_probe` | 2 | 0 | 2 | 0 |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:adjoining:vecino:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:adjoining:vecino:no_winner_context_probe` | `low_control` | `no_winner_context_probe` | 1 | 1 | 0 | 0 |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:adjoining:vecino:shadow_or_competitor_evidence_probe` | `low_control` | `shadow_or_competitor_evidence_probe` | 2 | 2 | 0 | 0 |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:begin:comenzar:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:begin:comenzar:no_winner_context_probe` | `low_control` | `no_winner_context_probe` | 1 | 1 | 0 | 0 |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:begin:comenzar:shadow_or_competitor_evidence_probe` | `low_control` | `shadow_or_competitor_evidence_probe` | 2 | 0 | 0 | 2 |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:billow:oleaje:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:billow:oleaje:no_winner_context_probe` | `high_need` | `no_winner_context_probe` | 1 | 1 | 0 | 0 |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:billow:oleaje:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | 2 | 0 | 0 | 2 |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:bouillon:caldo:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:bouillon:caldo:no_winner_context_probe` | `low_control` | `no_winner_context_probe` | 1 | 1 | 0 | 0 |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:bouillon:caldo:shadow_or_competitor_evidence_probe` | `low_control` | `shadow_or_competitor_evidence_probe` | 2 | 0 | 2 | 0 |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:bridle:reprimir:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:bridle:reprimir:no_winner_context_probe` | `high_need` | `no_winner_context_probe` | 1 | 1 | 0 | 0 |
| `semantic_veto_product_scope_llm_allocation_pilot_en_es_v1:en-es:full-family-repaired-full:bridle:reprimir:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | 2 | 2 | 0 | 0 |

## Next Steps

- Repair request_id, family_id, slot_id, slot_type, and target_lemma alignment.
- Regenerate only the failed request objects rather than changing the pilot design.

## Limitations

- `research-only generated-response admission lane`
- `no LLM call is made by this script`
- `no generated item is source evidence until a later explicit promotion step`
- `no runtime policy or threshold changes are made`
- `semantic correctness of generated text still needs scoring and spot review`
