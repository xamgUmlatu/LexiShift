# en-es Semantic Veto Evidence-Gap Generation Run

- Status: `ok`
- Generated: `2026-05-08T03:10:20Z`
- Execution mode: `replay`
- Batch id: `en-es:semantic-veto-evidence-gap-generation:semantic-veto-evidence-gap-smoke-replay-repaired-contract-v5:replay`
- Pilot id: `semantic_veto_evidence_gap_control_pilot_en_es_v1`
- Prompt id: `semantic_veto_evidence_gap_generation_v5`
- Selected model: `gpt-5.4-mini`

## Summary

- Selected requests: `3`
- Accepted responses: `3`
- Accepted generated items: `5`
- API errors: `0`
- Invalid outputs: `0`
- Input tokens: `300`
- Output tokens: `240`
- Accepted responses by arm: `high_need: 3`
- Accepted items by slot: `active_evidence_expansion: 2, no_winner_context_probe: 1, shadow_or_competitor_evidence_probe: 2`

## Admission Preview

- Admission status: `ok`
- Admission decision: `generated_items_admitted_for_pilot_rescoring`
- Admitted items: `5`
- Rejected items: `0`
- Coverage shortfall: `0`

## Artifacts

- Journal: ``
- Raw responses: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-semantic-veto-evidence-gap-smoke-replay-repaired-contract-v5-replay_raw_responses.json`
- Generated responses: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-semantic-veto-evidence-gap-smoke-replay-repaired-contract-v5-replay_generated_responses.json`

## Request Outcomes

| Request | Arm | Slot | Status | Items | Output / Error |
| --- | --- | --- | --- | ---: | --- |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:adjoining:vecino:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | `accepted` | 2 | The adjoining room shares a wall with the kitchen. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:adjoining:vecino:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | `accepted` | 2 | The legal notice used adjoining to classify parcels that touch at one border. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:adjoining:vecino:no_winner_context_probe` | `high_need` | `no_winner_context_probe` | `accepted` | 1 | The template heading "Adjoining" appears before the room list. |
