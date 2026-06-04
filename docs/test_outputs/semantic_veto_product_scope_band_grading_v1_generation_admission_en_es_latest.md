# en-es Semantic Veto Evidence-Gap Generation Admission

- Status: `review`
- Decision: `generated_responses_need_repair`
- Generated: `2026-05-09T20:30:23Z`
- Requests: `docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generation_requests_en_es_latest.json`
- Generated responses: `docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generated_responses_en_es_latest.json`
- Generated responses present: `True`

## Summary

- Expected requests: `54`
- Generated responses: `54`
- Expected items: `90`
- Admitted items: `67`
- Rejected items: `5`
- Waived items: `10`
- Coverage shortfall: `13`

## Alignment

- Matched expected requests: `54`
- Missing expected requests: `0`
- Unexpected response requests: `0`

## Arm Summary

| Arm | Expected requests | Expected items | Admitted | Rejected | Waived | Shortfall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `high_need` | 18 | 30 | 26 | 4 | 0 | 4 |
| `low_control` | 18 | 30 | 18 | 0 | 6 | 6 |
| `middle_control` | 18 | 30 | 23 | 1 | 4 | 3 |

## Slot Summary

| Slot type | Expected requests | Expected items | Admitted | Rejected | Waived | Shortfall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `active_evidence_expansion` | 18 | 36 | 36 | 0 | 0 | 0 |
| `no_winner_context_probe` | 18 | 18 | 17 | 1 | 0 | 1 |
| `shadow_or_competitor_evidence_probe` | 18 | 36 | 14 | 4 | 10 | 12 |

## Rejection Reasons

| Reason | Count |
| --- | ---: |
| `active_mismatch_note_declares_competitor_wrong` | 3 |
| `active_mismatch_note_missing_active_target_lemma` | 2 |
| `duplicate_sentence` | 1 |
| `missing_competitor_target_lemma` | 3 |
| `proposed_competitor_reuses_active_target_lemma` | 1 |
| `spanish_target_lemma_in_sentence` | 1 |

## Coverage Samples

| Request | Arm | Slot | Expected | Admitted | Waived | Shortfall |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:american:americano:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:american:americano:no_winner_context_probe` | `middle_control` | `no_winner_context_probe` | 1 | 1 | 0 | 0 |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:american:americano:shadow_or_competitor_evidence_probe` | `middle_control` | `shadow_or_competitor_evidence_probe` | 2 | 1 | 0 | 1 |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:argentinean:argentino:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:argentinean:argentino:no_winner_context_probe` | `low_control` | `no_winner_context_probe` | 1 | 1 | 0 | 0 |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:argentinean:argentino:shadow_or_competitor_evidence_probe` | `low_control` | `shadow_or_competitor_evidence_probe` | 2 | 0 | 2 | 0 |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:bar:cercar:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:bar:cercar:no_winner_context_probe` | `high_need` | `no_winner_context_probe` | 1 | 1 | 0 | 0 |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:bar:cercar:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | 2 | 2 | 0 | 0 |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:cite:mencionar:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:cite:mencionar:no_winner_context_probe` | `high_need` | `no_winner_context_probe` | 1 | 1 | 0 | 0 |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:cite:mencionar:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | 2 | 2 | 0 | 0 |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:control:gobernar:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:control:gobernar:no_winner_context_probe` | `high_need` | `no_winner_context_probe` | 1 | 1 | 0 | 0 |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:control:gobernar:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | 2 | 2 | 0 | 0 |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:dentist:dentista:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:dentist:dentista:no_winner_context_probe` | `low_control` | `no_winner_context_probe` | 1 | 1 | 0 | 0 |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:dentist:dentista:shadow_or_competitor_evidence_probe` | `low_control` | `shadow_or_competitor_evidence_probe` | 2 | 0 | 2 | 0 |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:endure:durar:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:endure:durar:no_winner_context_probe` | `middle_control` | `no_winner_context_probe` | 1 | 1 | 0 | 0 |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:endure:durar:shadow_or_competitor_evidence_probe` | `middle_control` | `shadow_or_competitor_evidence_probe` | 2 | 2 | 0 | 0 |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:except:excepto:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:except:excepto:no_winner_context_probe` | `high_need` | `no_winner_context_probe` | 1 | 1 | 0 | 0 |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:except:excepto:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | 2 | 0 | 0 | 2 |

## Next Steps

- Repair request_id, family_id, slot_id, slot_type, and target_lemma alignment.
- Regenerate only the failed request objects rather than changing the pilot design.

## Limitations

- `research-only generated-response admission lane`
- `no LLM call is made by this script`
- `no generated item is source evidence until a later explicit promotion step`
- `no runtime policy or threshold changes are made`
- `semantic correctness of generated text still needs scoring and spot review`
