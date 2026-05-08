# en-es Semantic Veto Evidence-Gap Generation Run

- Status: `ok`
- Generated: `2026-05-08T01:35:47Z`
- Execution mode: `live`
- Batch id: `en-es:semantic-veto-evidence-gap-generation:semantic-veto-evidence-gap-live-smoke-20260508-005`
- Pilot id: `semantic_veto_evidence_gap_control_pilot_en_es_v1`
- Prompt id: `semantic_veto_evidence_gap_generation_v4`
- Selected model: `gpt-5.4-mini`

## Summary

- Selected requests: `3`
- Accepted responses: `3`
- Accepted generated items: `5`
- API errors: `0`
- Invalid outputs: `0`
- Input tokens: `1721`
- Output tokens: `697`
- Accepted responses by arm: `high_need: 3`
- Accepted items by slot: `active_evidence_expansion: 2, no_winner_context_probe: 1, shadow_or_competitor_evidence_probe: 2`

## Admission Preview

- Admission status: `ok`
- Admission decision: `generated_items_admitted_for_pilot_rescoring`
- Admitted items: `5`
- Rejected items: `0`
- Coverage shortfall: `0`

## Artifacts

- Journal: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-semantic-veto-evidence-gap-live-smoke-20260508-005_journal.jsonl`
- Raw responses: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-semantic-veto-evidence-gap-live-smoke-20260508-005_raw_responses.json`
- Generated responses: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-semantic-veto-evidence-gap-live-smoke-20260508-005_generated_responses.json`

## Request Outcomes

| Request | Arm | Slot | Status | Items | Output / Error |
| --- | --- | --- | --- | ---: | --- |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:adjoining:vecino:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | `accepted` | 2 | The cafe opened in the adjoining building, right next to the library. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:adjoining:vecino:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | `accepted` | 2 | The report included an adjoining appendix with the raw data. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:adjoining:vecino:no_winner_context_probe` | `high_need` | `no_winner_context_probe` | `accepted` | 1 | Search results for adjoining apartments in the city center. |
