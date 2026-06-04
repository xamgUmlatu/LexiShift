# en-es Semantic Veto Evidence-Gap Generation Run

- Status: `error`
- Generated: `2026-05-09T22:51:25Z`
- Execution mode: `live`
- Batch id: `en-es:semantic-veto-evidence-gap-generation:active-only-scale-tranche-v1-continue-repair-20260510-001`
- Pilot id: `semantic_veto_active_only_scale_tranche_v1_en_es`
- Prompt id: `semantic_veto_evidence_gap_generation_v7_shadow_target_correctness`
- Selected model: `gpt-5.4-mini`

## Summary

- Selected requests: `1`
- Accepted responses: `0`
- Accepted generated items: `0`
- API errors: `0`
- Invalid outputs: `1`
- Input tokens: `463`
- Output tokens: `158`
- Accepted responses by arm: `none`
- Accepted items by slot: `none`

## Admission Preview

- Admission status: `review`
- Admission decision: `generated_responses_need_repair`
- Admitted items: `0`
- Rejected items: `0`
- Waived items: `0`
- Coverage shortfall: `2`

## Artifacts

- Journal: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-active-only-scale-tranche-v1-continue-repair-20260510-001_journal.jsonl`
- Raw responses: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-active-only-scale-tranche-v1-continue-repair-20260510-001_raw_responses.json`
- Generated responses: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-active-only-scale-tranche-v1-continue-repair-20260510-001_generated_responses.json`

## Request Outcomes

| Request | Arm | Slot | Status | Items | Output / Error |
| --- | --- | --- | --- | ---: | --- |
| `semantic_veto_active_only_scale_tranche_v1_en_es:en-es:full-family-repaired-full:continue:durar:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | `invalid_output` | 0 | ValueError: request_id did not match request packet |
