# en-es Semantic Veto Evidence-Gap Generation Requests

- Status: `ok`
- Decision: `evidence_gap_generation_request_packet_ready`
- Generated: `2026-05-09T20:22:46Z`
- Plan: `docs/test_inputs/semantic_veto_product_scope_band_grading_v1_allocation_plan_en_es.json`
- Prompt id: `semantic_veto_evidence_gap_generation_v7_shadow_target_correctness`
- Requests rendered: `54`
- Families: `18`
- Expected generated items: `90`
- Expected output-token budget: `12600`

## Contract

- No runtime policy change.
- No threshold tuning from generated outputs.
- Use the same slot contract for high, middle, and low arms.
- Each response must be JSON and must preserve request_id, family_id, slot_id, and slot_type.
- Generated English contexts must contain the English source phrase and must not contain Spanish target lemmas.

## Arm Summary

| Arm | Requests | Families | Expected items |
| --- | ---: | ---: | ---: |
| `high_need` | 18 | 6 | 30 |
| `middle_control` | 18 | 6 | 30 |
| `low_control` | 18 | 6 | 30 |

## Slot Summary

| Slot type | Requests | Expected items |
| --- | ---: | ---: |
| `active_evidence_expansion` | 18 | 36 |
| `shadow_or_competitor_evidence_probe` | 18 | 36 |
| `no_winner_context_probe` | 18 | 18 |

## Request Samples

| arm | rank | trigger | slot | items | prompt chars |
| --- | --- | --- | --- | --- | --- |
| `high_need` | 1 | `cite` | `active_evidence_expansion` | 2 | 2037 |
| `high_need` | 1 | `cite` | `shadow_or_competitor_evidence_probe` | 2 | 3882 |
| `high_need` | 1 | `cite` | `no_winner_context_probe` | 1 | 3166 |
| `high_need` | 2 | `smile` | `active_evidence_expansion` | 2 | 2049 |
| `high_need` | 2 | `smile` | `shadow_or_competitor_evidence_probe` | 2 | 3900 |
| `high_need` | 2 | `smile` | `no_winner_context_probe` | 1 | 3182 |
| `high_need` | 3 | `bar` | `active_evidence_expansion` | 2 | 2008 |
| `high_need` | 3 | `bar` | `shadow_or_competitor_evidence_probe` | 2 | 3861 |
| `high_need` | 3 | `bar` | `no_winner_context_probe` | 1 | 3143 |
| `high_need` | 4 | `control` | `active_evidence_expansion` | 2 | 2074 |
| `high_need` | 4 | `control` | `shadow_or_competitor_evidence_probe` | 2 | 3923 |
| `high_need` | 4 | `control` | `no_winner_context_probe` | 1 | 3205 |

## Guardrails

| Check | Value |
| --- | --- |
| `request_count_matches_planned_slots` | `True` |
| `unique_request_ids` | `True` |
| `unique_slot_ids` | `True` |
| `all_requests_have_prompt_text` | `True` |
| `all_requests_have_positive_requested_items` | `True` |
| `same_slot_counts_per_arm` | `True` |

## Next Steps

- Review the prompt packet before spending.
- Run the same generation contract for high_need, middle_control, and low_control arms.
- Admit generated outputs with slot-id and family-id checks before any downstream scoring.
- Compare improvement by arm; do not tune thresholds from this generation packet.

## Limitations

- `no LLM call is made by this script`
- `request packet is not generated data`
- `generated output must be admitted and reviewed before scoring claims`
- `the same request schema is used for high, middle, and low arms`
- `runtime policy and scorer thresholds remain unchanged`
