# en-es LLM Example-Frame Generation Run

- Status: `ok`
- Generated: `2026-04-24T22:42:27Z`
- Execution mode: `replay`
- Batch id: `en-es:example-frame-missing-rows:example-frame-balanced-remediation-v1-20260425a-rekeyed:replay`
- Source id: `llm_example_frame_residual_remediation`
- Prompt version: `example-frame-residual-remediation-v1`
- Selected model: `gpt-5.4-mini`

## Summary

- Selected requests: `6`
- Accepted items: `6`
- API errors: `0`
- Invalid outputs: `0`
- Normalized rows: `6`
- Input tokens: `2182`
- Output tokens: `198`

## Artifacts

- Journal: ``
- Raw responses: `docs/test_outputs/experiments/semantic_example_frame_batches/en-es-example-frame-missing-rows-example-frame-balanced-remediation-v1-20260425a-rekeyed-replay_raw_responses.json`
- Intake batch: `docs/test_outputs/experiments/semantic_example_frame_batches/en-es-example-frame-missing-rows-example-frame-balanced-remediation-v1-20260425a-rekeyed-replay_intake_batch.json`
- Normalized batch: `docs/test_outputs/experiments/semantic_example_frame_batches/en-es-example-frame-missing-rows-example-frame-balanced-remediation-v1-20260425a-rekeyed-replay_normalized_evidence.json`

## Request Outcomes

| Request | Target | Family | Status | Output |
| --- | --- | --- | --- | --- |
| `en-es:example-frame-remediation:active:en-es-sentence-veto-check-cheque` | `remediation_active_example` | `en-es:sentence-veto:check:cheque` | `accepted` | She mailed the rent check with the signed lease yesterday. |
| `en-es:example-frame-remediation:active:en-es-sentence-veto-order-pedido` | `remediation_active_example` | `en-es:sentence-veto:order:pedido` | `accepted` | I placed an order for two laptops and extra chargers online. |
| `en-es:example-frame-remediation:active:en-es-sentence-veto-plant-planta` | `remediation_active_example` | `en-es:sentence-veto:plant:planta` | `accepted` | I watered the plant on the windowsill every morning. |
| `en-es:example-frame-remediation:active:en-es-sentence-veto-play-obra` | `remediation_active_example` | `en-es:sentence-veto:play:obra` | `accepted` | The school play opened to a full house on Friday night. |
| `en-es:example-frame-remediation:active:en-es-sentence-veto-report-informe` | `remediation_active_example` | `en-es:sentence-veto:report:informe` | `accepted` | The final report summarized the survey results and recommendations. |
| `en-es:example-frame-remediation:shadow:en-es-sentence-veto-report-informe:en-es-sentence-veto-report-informar-shadow` | `remediation_shadow_example` | `en-es:sentence-veto:report:informe` | `accepted` | Please report the delay to the manager before noon. |
