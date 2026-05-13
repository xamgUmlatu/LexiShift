# en-es Semantic Veto Evidence-Gap Generation Admission

- Status: `review`
- Decision: `generated_items_need_repair`
- Generated: `2026-05-13T05:08:50Z`
- Requests: `docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_005_pre_spend_en_es_latest.json`
- Generated responses: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-en-es-active-only-full-v1-tranche-005-approved_generated_responses.json`
- Generated responses present: `True`

## Summary

- Expected requests: `37`
- Generated responses: `37`
- Expected items: `74`
- Admitted items: `73`
- Rejected items: `1`
- Waived items: `0`
- Coverage shortfall: `1`

## Alignment

- Matched expected requests: `37`
- Missing expected requests: `0`
- Unexpected response requests: `0`

## Arm Summary

| Arm | Expected requests | Expected items | Admitted | Rejected | Waived | Shortfall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `P1_exposure_first` | 27 | 54 | 53 | 1 | 0 | 1 |
| `P2_exposure_first` | 10 | 20 | 20 | 0 | 0 | 0 |

## Slot Summary

| Slot type | Expected requests | Expected items | Admitted | Rejected | Waived | Shortfall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `active_evidence_expansion` | 37 | 74 | 73 | 1 | 0 | 1 |

## Rejection Reasons

| Reason | Count |
| --- | ---: |
| `source_phrase_missing_or_not_runtime_like` | 1 |

## Coverage Samples

| Request | Arm | Slot | Expected | Admitted | Waived | Shortfall |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `en-es-active-only-full-v1-tranche-005:en-es:srs-source-target:adjacent:adyacente:4d8b8ba6:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `en-es-active-only-full-v1-tranche-005:en-es:srs-source-target:afar:lejos:b001ef21:active_evidence_expansion` | `P1_exposure_first` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `en-es-active-only-full-v1-tranche-005:en-es:srs-source-target:african:africano:bffdb36a:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `en-es-active-only-full-v1-tranche-005:en-es:srs-source-target:anonymous:anonimo:fa0192c0:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `en-es-active-only-full-v1-tranche-005:en-es:srs-source-target:australian:australiano:a28c76bb:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `en-es-active-only-full-v1-tranche-005:en-es:srs-source-target:back:reverso:16db1377:active_evidence_expansion` | `P1_exposure_first` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `en-es-active-only-full-v1-tranche-005:en-es:srs-source-target:baker:panadero:7cede4ac:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `en-es-active-only-full-v1-tranche-005:en-es:srs-source-target:bar:taberna:c8ebdb94:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `en-es-active-only-full-v1-tranche-005:en-es:srs-source-target:base:basar:4d72460f:active_evidence_expansion` | `P1_exposure_first` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `en-es-active-only-full-v1-tranche-005:en-es:srs-source-target:basket:cesto:267cb6a1:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `en-es-active-only-full-v1-tranche-005:en-es:srs-source-target:bed:cauce:35138744:active_evidence_expansion` | `P1_exposure_first` | `active_evidence_expansion` | 2 | 1 | 0 | 1 |
| `en-es-active-only-full-v1-tranche-005:en-es:srs-source-target:bee:abeja:e7913c38:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `en-es-active-only-full-v1-tranche-005:en-es:srs-source-target:blow:soplar:80e76972:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `en-es-active-only-full-v1-tranche-005:en-es:srs-source-target:book:reservar:de7e11a6:active_evidence_expansion` | `P1_exposure_first` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `en-es-active-only-full-v1-tranche-005:en-es:srs-source-target:brush:cepillo:02913134:active_evidence_expansion` | `P2_exposure_first` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `en-es-active-only-full-v1-tranche-005:en-es:srs-source-target:check:reprimir:56a101ec:active_evidence_expansion` | `P1_exposure_first` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `en-es-active-only-full-v1-tranche-005:en-es:srs-source-target:commencement:principio:f4eeec84:active_evidence_expansion` | `P1_exposure_first` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `en-es-active-only-full-v1-tranche-005:en-es:srs-source-target:commonplace:comun:9a2ae8bf:active_evidence_expansion` | `P1_exposure_first` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `en-es-active-only-full-v1-tranche-005:en-es:srs-source-target:cover:forrar:79548204:active_evidence_expansion` | `P1_exposure_first` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `en-es-active-only-full-v1-tranche-005:en-es:srs-source-target:cross:atravesar:37f67d2d:active_evidence_expansion` | `P1_exposure_first` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `en-es-active-only-full-v1-tranche-005:en-es:srs-source-target:diminutive:pequeno:c72bf9f8:active_evidence_expansion` | `P1_exposure_first` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `en-es-active-only-full-v1-tranche-005:en-es:srs-source-target:drive:propulsion:fd0fa8d5:active_evidence_expansion` | `P1_exposure_first` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `en-es-active-only-full-v1-tranche-005:en-es:srs-source-target:envelope:sobre:cf91b697:active_evidence_expansion` | `P1_exposure_first` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |
| `en-es-active-only-full-v1-tranche-005:en-es:srs-source-target:figure:calcular:710b79be:active_evidence_expansion` | `P1_exposure_first` | `active_evidence_expansion` | 2 | 2 | 0 | 0 |

## Next Steps

- Discard or regenerate rejected generated sentences before rescoring.
- Keep rejection reasons with the batch so failure classes remain auditable.

## Limitations

- `research-only generated-response admission lane`
- `no LLM call is made by this script`
- `no generated item is source evidence until a later explicit promotion step`
- `no runtime policy or threshold changes are made`
- `semantic correctness of generated text still needs scoring and spot review`
