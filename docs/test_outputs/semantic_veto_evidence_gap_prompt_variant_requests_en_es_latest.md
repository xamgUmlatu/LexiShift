# en-es Semantic Veto Active-Only Prompt Variant Requests

- Status: `ok`
- Decision: `prompt_variant_request_packets_ready`
- Generated: `2026-05-09T00:09:46Z`
- Variants: `4`
- Requests per variant: `24`
- Total requests if all variants run: `96`
- Total expected generated items if all variants run: `192`

## Variants

| Variant | Requests | Families | Items | Input tokens | Output budget | Packet |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `v5_refresh_control` | 24 | 24 | 48 | 12110 | 6720 | `docs/test_inputs/semantic_veto_evidence_gap_prompt_variant_requests_en_es/v5_refresh_control.json` |
| `v6_pos_only` | 24 | 24 | 48 | 16638 | 8160 | `docs/test_inputs/semantic_veto_evidence_gap_prompt_variant_requests_en_es/v6_pos_only.json` |
| `v6_diversity_only` | 24 | 24 | 48 | 17165 | 8160 | `docs/test_inputs/semantic_veto_evidence_gap_prompt_variant_requests_en_es/v6_diversity_only.json` |
| `v6_pos_diversity` | 24 | 24 | 48 | 18371 | 8160 | `docs/test_inputs/semantic_veto_evidence_gap_prompt_variant_requests_en_es/v6_pos_diversity.json` |

## Methodology

- `runtime_policy_change`: none
- `llm_call`: none
- `threshold_tuning`: none
- `same_family_denominator`: all variants use the frozen 24 active-only PoC families
- `primary_later_comparison`: postprocess no_high_eval_overlap_sentence_only view

## Next Steps

- Run each variant packet with the existing generation runner and explicit spend guards.
- Admit each variant response bundle against the matching variant request packet.
- Run the generated-evidence postprocess report for each variant.
- Compare variants on the no_high_eval_overlap_sentence_only view before scaling.
