# en-es Semantic Veto Evidence-Gap Generation Requests

- Status: `ok`
- Decision: `evidence_gap_generation_request_packet_ready`
- Generated: `2026-05-09T05:25:32Z`
- Plan: `docs/test_inputs/semantic_veto_product_scope_llm_allocation_pilot_plan_en_es.json`
- Prompt id: `semantic_veto_evidence_gap_generation_v7_shadow_target_correctness`
- Requests rendered: `60`
- Families: `20`
- Expected generated items: `100`
- Expected output-token budget: `14000`

## Contract

- No runtime policy change.
- No threshold tuning from generated outputs.
- Use the same slot contract for high, middle, and low arms.
- Each response must be JSON and must preserve request_id, family_id, slot_id, and slot_type.
- Generated English contexts must contain the English source phrase and must not contain Spanish target lemmas.

## Arm Summary

| Arm | Requests | Families | Expected items |
| --- | ---: | ---: | ---: |
| `high_need` | 24 | 8 | 40 |
| `middle_control` | 12 | 4 | 20 |
| `low_control` | 24 | 8 | 40 |

## Slot Summary

| Slot type | Requests | Expected items |
| --- | ---: | ---: |
| `active_evidence_expansion` | 20 | 40 |
| `shadow_or_competitor_evidence_probe` | 20 | 40 |
| `no_winner_context_probe` | 20 | 20 |

## Request Samples

| arm | rank | trigger | slot | items | prompt chars |
| --- | --- | --- | --- | --- | --- |
| `high_need` | 1 | `acceptable` | `active_evidence_expansion` | 2 | 2084 |
| `high_need` | 1 | `acceptable` | `shadow_or_competitor_evidence_probe` | 2 | 3933 |
| `high_need` | 1 | `acceptable` | `no_winner_context_probe` | 1 | 3213 |
| `high_need` | 2 | `billow` | `active_evidence_expansion` | 2 | 2003 |
| `high_need` | 2 | `billow` | `shadow_or_competitor_evidence_probe` | 2 | 3858 |
| `high_need` | 2 | `billow` | `no_winner_context_probe` | 1 | 3138 |
| `high_need` | 3 | `bridle` | `active_evidence_expansion` | 2 | 2048 |
| `high_need` | 3 | `bridle` | `shadow_or_competitor_evidence_probe` | 2 | 3893 |
| `high_need` | 3 | `bridle` | `no_winner_context_probe` | 1 | 3179 |
| `high_need` | 4 | `current` | `active_evidence_expansion` | 2 | 2111 |
| `high_need` | 4 | `current` | `shadow_or_competitor_evidence_probe` | 2 | 3974 |
| `high_need` | 4 | `current` | `no_winner_context_probe` | 1 | 3232 |

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
