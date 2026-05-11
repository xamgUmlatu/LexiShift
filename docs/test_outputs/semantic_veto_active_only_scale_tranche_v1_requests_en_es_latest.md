# en-es Semantic Veto Active-Only Scale Tranche Requests

- Status: `ok`
- Decision: `active_only_scale_tranche_request_packet_ready`
- Generated: `2026-05-09T22:49:26Z`
- Prompt id: `semantic_veto_evidence_gap_generation_v7_shadow_target_correctness`
- Covered families excluded: `33`
- Uncovered candidate families: `16`
- Selected families: `16`
- Requests: `16`
- Expected generated items: `32`
- Estimated input tokens: `7967`
- Expected output-token budget: `4480`

## Arm Summary

| Arm | Families | Requests | Expected items |
| --- | ---: | ---: | ---: |
| `high_need` | 6 | 6 | 12 |
| `middle_control` | 4 | 4 | 8 |
| `low_control` | 6 | 6 | 12 |

## Selected Families

| Arm | Band rank | Family | Trigger | Target | Predicted need |
| --- | ---: | --- | --- | --- | ---: |
| `high_need` | 5 | `en-es:full-family-repaired-full:current:contempor-neo` | `current` | `contemporáneo` | 0.8 |
| `high_need` | 6 | `en-es:full-family-repaired-full:continue:durar` | `continue` | `durar` | 0.7962 |
| `high_need` | 9 | `en-es:full-family-repaired-full:parrot:loro` | `parrot` | `loro` | 0.6885 |
| `high_need` | 11 | `en-es:full-family-repaired-full:recover:sanar` | `recover` | `sanar` | 0.6885 |
| `high_need` | 14 | `en-es:full-family-repaired-full:billow:oleaje` | `billow` | `oleaje` | 0.6615 |
| `high_need` | 15 | `en-es:full-family-repaired-full:stall:cuadra` | `stall` | `cuadra` | 0.75 |
| `middle_control` | 3 | `en-es:full-family-repaired-full:upon:sobre` | `upon` | `sobre` | 0.5077 |
| `middle_control` | 4 | `en-es:full-family-repaired-full:pair:par` | `pair` | `par` | 0.6577 |
| `middle_control` | 13 | `en-es:full-family-repaired-full:health:salud` | `health` | `salud` | 0.4962 |
| `middle_control` | 14 | `en-es:full-family-repaired-full:snore:roncar` | `snore` | `roncar` | 0.6 |
| `low_control` | 5 | `en-es:full-family-repaired-full:handiwork:artesan-a` | `handiwork` | `artesanía` | 0.3 |
| `low_control` | 6 | `en-es:full-family-repaired-full:adjoining:contiguo` | `adjoining` | `contiguo` | 0.4808 |
| `low_control` | 9 | `en-es:full-family-repaired-full:adder:v-bora` | `adder` | `víbora` | 0.4885 |
| `low_control` | 10 | `en-es:full-family-repaired-full:altitude:elevaci-n` | `altitude` | `elevación` | 0.4385 |
| `low_control` | 11 | `en-es:full-family-repaired-full:june:junio` | `june` | `junio` | 0.4154 |
| `low_control` | 13 | `en-es:full-family-repaired-full:emotion:emoci-n` | `emotion` | `emoción` | 0.3808 |

## Next Steps

- Run this active-only request packet with explicit live spend guards.
- Admit generated responses structurally before scoring or packaging.
- Use the no_high_eval_overlap_sentence_only postprocess view unless it regresses.
- Package only admitted active rows as canonical anchor_cue evidence with tranche-specific provenance.

## Limitations

- `active evidence only`
- `request packet makes no LLM call`
- `does not generate shadows or no-winner rows`
- `selected from the current 49-family product-scope denominator only`
- `generated outputs must pass admission, postprocess, packaging, replay, helper smoke, and page review before broader spend`
