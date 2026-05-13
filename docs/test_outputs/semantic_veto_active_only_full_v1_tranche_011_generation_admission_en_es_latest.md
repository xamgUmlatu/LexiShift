# en-es Semantic Veto Evidence-Gap Generation Admission

- Status: `ok`
- Decision: `generated_items_admitted_for_pilot_rescoring`
- Generated: `2026-05-13T20:41:32Z`
- Requests: `docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_011_pre_spend_en_es_latest.json`
- Generated responses: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-en-es-active-only-full-v1-tranche-011-approved_generated_responses.json`
- Generated responses present: `True`

## Summary

- Expected requests: `9`
- Generated responses: `9`
- Expected items: `18`
- Admitted items: `18`
- Rejected items: `0`
- Waived items: `0`
- Coverage shortfall: `0`

## Alignment

- Matched expected requests: `9`
- Missing expected requests: `0`
- Unexpected response requests: `0`

## Arm Summary

| Arm | Expected requests | Expected items | Admitted | Rejected | Waived | Shortfall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `P3_exposure_first` | 9 | 18 | 18 | 0 | 0 | 0 |

## Slot Summary

| Slot type | Expected requests | Expected items | Admitted | Rejected | Waived | Shortfall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `active_evidence_expansion` | 9 | 18 | 18 | 0 | 0 | 0 |

## Rejection Reasons

_None._

## Coverage Samples

| Request | Arm | Slot | Expected | Admitted | Waived | Shortfall |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `en-es-active-only-full-v1-tranche-011:en-es:srs-source-target:abate:decrecer:a89e2928:active_evidence_expansion` | `P3_exposure_first` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `en-es-active-only-full-v1-tranche-011:en-es:srs-source-target:aberration:yerro:4e3d998f:active_evidence_expansion` | `P3_exposure_first` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `en-es-active-only-full-v1-tranche-011:en-es:srs-source-target:admonition:exhortacion:d75f45fe:active_evidence_expansion` | `P3_exposure_first` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `en-es-active-only-full-v1-tranche-011:en-es:srs-source-target:confiscate:confiscar:6016e741:active_evidence_expansion` | `P3_exposure_first` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `en-es-active-only-full-v1-tranche-011:en-es:srs-source-target:exhortation:exhortacion:219d6592:active_evidence_expansion` | `P3_exposure_first` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `en-es-active-only-full-v1-tranche-011:en-es:srs-source-target:laggard:rezagado:59ff6b32:active_evidence_expansion` | `P3_exposure_first` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `en-es-active-only-full-v1-tranche-011:en-es:srs-source-target:straggler:rezagado:e9269d35:active_evidence_expansion` | `P3_exposure_first` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `en-es-active-only-full-v1-tranche-011:en-es:srs-source-target:transitive:transitivo:08c49e29:active_evidence_expansion` | `P3_exposure_first` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `en-es-active-only-full-v1-tranche-011:en-es:srs-source-target:wrangle:renir:2f7db0f0:active_evidence_expansion` | `P3_exposure_first` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |

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
