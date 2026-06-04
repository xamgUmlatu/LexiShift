# en-es Semantic Veto Evidence-Gap Generation Admission

- Status: `review`
- Decision: `generated_items_need_repair`
- Generated: `2026-05-09T21:50:49Z`
- Requests: `docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generation_requests_en_es_latest.json`
- Generated responses: `docs/test_outputs/semantic_veto_product_scope_band_grading_v1_shadow_mini_high_generated_responses_en_es_latest.json`
- Generated responses present: `True`

## Summary

- Expected requests: `6`
- Generated responses: `6`
- Expected items: `12`
- Admitted items: `10`
- Rejected items: `2`
- Waived items: `0`
- Coverage shortfall: `2`

## Alignment

- Matched expected requests: `6`
- Missing expected requests: `0`
- Unexpected response requests: `0`

## Arm Summary

| Arm | Expected requests | Expected items | Admitted | Rejected | Waived | Shortfall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `high_need` | 6 | 12 | 10 | 2 | 0 | 2 |

## Slot Summary

| Slot type | Expected requests | Expected items | Admitted | Rejected | Waived | Shortfall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `shadow_or_competitor_evidence_probe` | 6 | 12 | 10 | 2 | 0 | 2 |

## Rejection Reasons

| Reason | Count |
| --- | ---: |
| `active_mismatch_note_declares_competitor_wrong` | 2 |
| `active_mismatch_note_missing_active_target_lemma` | 2 |

## Coverage Samples

| Request | Arm | Slot | Expected | Admitted | Waived | Shortfall |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:bar:cercar:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | 2 | 2 | 0 | 0 |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:cite:mencionar:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | 2 | 2 | 0 | 0 |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:control:gobernar:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | 2 | 2 | 0 | 0 |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:except:excepto:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | 2 | 0 | 0 | 2 |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:region:comarca:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | 2 | 2 | 0 | 0 |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:smile:sonre-r:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | 2 | 2 | 0 | 0 |

## Next Steps

- Discard or regenerate rejected generated sentences before rescoring.
- Keep rejection reasons with the batch so failure classes remain auditable.

## Limitations

- `research-only generated-response admission lane`
- `no LLM call is made by this script`
- `no generated item is source evidence until a later explicit promotion step`
- `no runtime policy or threshold changes are made`
- `semantic correctness of generated text still needs scoring and spot review`
