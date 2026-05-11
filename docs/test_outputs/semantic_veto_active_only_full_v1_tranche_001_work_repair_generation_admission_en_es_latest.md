# en-es Semantic Veto Evidence-Gap Generation Admission

- Status: `review`
- Decision: `generated_items_need_repair`
- Generated: `2026-05-11T22:38:36Z`
- Requests: `docs/test_outputs/semantic_veto_active_only_full_generation_plan_en_es_latest.json`
- Generated responses: `docs/test_outputs/semantic_veto_active_only_full_v1_tranche_001_work_repair_generated_responses_en_es_latest.json`
- Generated responses present: `True`

## Summary

- Expected requests: `1`
- Generated responses: `1`
- Expected items: `2`
- Admitted items: `1`
- Rejected items: `1`
- Waived items: `0`
- Coverage shortfall: `1`

## Alignment

- Matched expected requests: `1`
- Missing expected requests: `0`
- Unexpected response requests: `0`

## Arm Summary

| Arm | Expected requests | Expected items | Admitted | Rejected | Waived | Shortfall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `P0_exposure_first` | 1 | 2 | 1 | 1 | 0 | 1 |

## Slot Summary

| Slot type | Expected requests | Expected items | Admitted | Rejected | Waived | Shortfall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `active_evidence_expansion` | 1 | 2 | 1 | 1 | 0 | 1 |

## Rejection Reasons

| Reason | Count |
| --- | ---: |
| `source_phrase_missing_or_not_runtime_like` | 1 |

## Coverage Samples

| Request | Arm | Slot | Expected | Admitted | Waived | Shortfall |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `semantic_veto_active_only_full_en_es_v1:en-es:srs-source-target:work:trabajar:41fc059d:active_evidence_expansion` | `P0_exposure_first` | `active_evidence_expansion` | 2 | 1 | 0 | 1 |

## Next Steps

- Repair and rerender the generation request packet before any LLM spend.
- Do not admit generated outputs against a non-ok request packet.

## Limitations

- `research-only generated-response admission lane`
- `no LLM call is made by this script`
- `no generated item is source evidence until a later explicit promotion step`
- `no runtime policy or threshold changes are made`
- `semantic correctness of generated text still needs scoring and spot review`
