# en-es Semantic Veto Evidence-Gap Generation Requests

- Status: `ok`
- Decision: `evidence_gap_generation_request_packet_ready`
- Generated: `2026-05-08T03:10:13Z`
- Plan: `docs/test_inputs/semantic_veto_evidence_gap_control_pilot_plan_en_es.json`
- Prompt id: `semantic_veto_evidence_gap_generation_v5`
- Requests rendered: `72`
- Families: `24`
- Expected generated items: `120`
- Expected output-token budget: `16800`

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
| `middle_control` | 24 | 8 | 40 |
| `low_control` | 24 | 8 | 40 |

## Slot Summary

| Slot type | Requests | Expected items |
| --- | ---: | ---: |
| `active_evidence_expansion` | 24 | 48 |
| `shadow_or_competitor_evidence_probe` | 24 | 48 |
| `no_winner_context_probe` | 24 | 24 |

## Request Samples

| arm | rank | trigger | slot | items | prompt chars |
| --- | --- | --- | --- | --- | --- |
| `high_need` | 1 | `adjoining` | `active_evidence_expansion` | 2 | 1994 |
| `high_need` | 1 | `adjoining` | `shadow_or_competitor_evidence_probe` | 2 | 3129 |
| `high_need` | 1 | `adjoining` | `no_winner_context_probe` | 1 | 2632 |
| `high_need` | 2 | `entirely` | `active_evidence_expansion` | 2 | 2043 |
| `high_need` | 2 | `entirely` | `shadow_or_competitor_evidence_probe` | 2 | 3168 |
| `high_need` | 2 | `entirely` | `no_winner_context_probe` | 1 | 2671 |
| `high_need` | 3 | `bouillon` | `active_evidence_expansion` | 2 | 1974 |
| `high_need` | 3 | `bouillon` | `shadow_or_competitor_evidence_probe` | 2 | 3111 |
| `high_need` | 3 | `bouillon` | `no_winner_context_probe` | 1 | 2614 |
| `high_need` | 4 | `december` | `active_evidence_expansion` | 2 | 2021 |
| `high_need` | 4 | `december` | `shadow_or_competitor_evidence_probe` | 2 | 3150 |
| `high_need` | 4 | `december` | `no_winner_context_probe` | 1 | 2653 |

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
