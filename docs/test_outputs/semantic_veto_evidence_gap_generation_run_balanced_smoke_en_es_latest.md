# en-es Semantic Veto Evidence-Gap Generation Run

- Status: `ok`
- Generated: `2026-05-08T19:35:47Z`
- Execution mode: `live`
- Batch id: `en-es:semantic-veto-evidence-gap-generation:semantic-veto-evidence-gap-balanced-smoke-20260509-001`
- Pilot id: `semantic_veto_evidence_gap_control_pilot_en_es_v1`
- Prompt id: `semantic_veto_evidence_gap_generation_v5`
- Selected model: `gpt-5.4-mini`

## Summary

- Selected requests: `9`
- Accepted responses: `9`
- Accepted generated items: `13`
- API errors: `0`
- Invalid outputs: `0`
- Input tokens: `5436`
- Output tokens: `1960`
- Accepted responses by arm: `high_need: 3, low_control: 3, middle_control: 3`
- Accepted items by slot: `active_evidence_expansion: 6, no_winner_context_probe: 3, shadow_or_competitor_evidence_probe: 4`

## Admission Preview

- Admission status: `ok`
- Admission decision: `generated_items_admitted_for_pilot_rescoring`
- Admitted items: `13`
- Rejected items: `0`
- Waived items: `2`
- Coverage shortfall: `0`

## Artifacts

- Journal: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-semantic-veto-evidence-gap-balanced-smoke-20260509-001_journal.jsonl`
- Raw responses: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-semantic-veto-evidence-gap-balanced-smoke-20260509-001_raw_responses.json`
- Generated responses: `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-semantic-veto-evidence-gap-balanced-smoke-20260509-001_generated_responses.json`

## Request Outcomes

| Request | Arm | Slot | Status | Items | Output / Error |
| --- | --- | --- | --- | ---: | --- |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:entirely:enteramente:active_evidence_expansion` | `high_need` | `active_evidence_expansion` | `accepted` | 2 | The room was entirely dark after the power went out. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:entirely:enteramente:shadow_or_competitor_evidence_probe` | `high_need` | `shadow_or_competitor_evidence_probe` | `accepted` | 0 | n/a |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:entirely:enteramente:no_winner_context_probe` | `high_need` | `no_winner_context_probe` | `accepted` | 1 | Search results for entirely |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:brother:hermano:active_evidence_expansion` | `middle_control` | `active_evidence_expansion` | `accepted` | 2 | My brother helped me move into my new apartment. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:brother:hermano:shadow_or_competitor_evidence_probe` | `middle_control` | `shadow_or_competitor_evidence_probe` | `accepted` | 2 | The old brother spent the morning copying manuscripts in the monastery library. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:brother:hermano:no_winner_context_probe` | `middle_control` | `no_winner_context_probe` | `accepted` | 1 | Search results for brother |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:smile:sonre-r:active_evidence_expansion` | `low_control` | `active_evidence_expansion` | `accepted` | 2 | She tried to smile after hearing the good news. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:smile:sonre-r:shadow_or_competitor_evidence_probe` | `low_control` | `shadow_or_competitor_evidence_probe` | `accepted` | 2 | Her smile lit up the room during the ceremony. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:smile:sonre-r:no_winner_context_probe` | `low_control` | `no_winner_context_probe` | `accepted` | 1 | Page title: smile — customer feedback dashboard |
