# en-es Semantic LLM Prompt Preflight

- Status: `ready`
- Generated: `2026-05-09T20:27:27Z`
- Queue: `semantic_prompt_bakeoff_en_es_v10`
- Prompt spec: `semantic_prompt_spec_en_es_v10`
- Prompt version: `semantic_prompt_bakeoff_v3`
- Stage: `proxy`
- Selected model: `gpt-5.4-mini`
- Temperature: `0.2`

## Summary

- Selected requests: `12`
- Selected families: `6`
- Active slots represented: `4`
- Current shell ready: `True`
- Sourced shell ready: `True`
- Any safe local path ready: `True`
- Live spend blocked by default: `True`

## Environment Checks

| Check | Status | Notes |
| --- | --- | --- |
| `current_python_openai_sdk_installed` | `ok` | The current Python environment used by this command must import `openai` for direct live execution. |
| `current_shell_openai_api_key_visible` | `ok` | The current shell must expose `OPENAI_API_KEY`; this preflight does not source shell rc files automatically. |
| `repo_venv_openai_sdk_installed` | `ok` | Checks whether the repo venv at `.venv/bin/python` can import `openai`. |
| `shell_rc_mentions_openai_api_key` | `ok` | Checks whether `/Users/takeyayuki/.zshrc` appears to export `OPENAI_API_KEY` without printing the key. |
| `quota_not_checked` | `warn` | This no-spend preflight does not make a live API call, so quota/billing remains unverified here. |

## Planned Artifacts

- Journal: `docs/test_outputs/experiments/semantic_llm_prompt_batches/en-es-proxy-run-id_journal.jsonl`
- Raw responses: `docs/test_outputs/experiments/semantic_llm_prompt_batches/en-es-proxy-run-id_raw_responses.json`
- Intake batch: `docs/test_outputs/experiments/semantic_llm_prompt_batches/en-es-proxy-run-id_intake_batch.json`
- Normalized batch: `docs/test_outputs/experiments/semantic_llm_prompt_batches/en-es-proxy-run-id_normalized_evidence.json`

## Selected Requests

| Request | Slot | Family | Trigger | Active -> Candidate |
| --- | --- | --- | --- | --- |
| `en-es:proxy:cue-contrastive-general-v1:plant:fabrica` | `cue_contrastive_general_v1` | `en-es:sentence-veto:plant:planta` | `plant` | `planta` -> `fábrica` |
| `en-es:proxy:cue-contrastive-general-v1:drink:beber` | `cue_contrastive_general_v1` | `en-es:sentence-veto:drink:bebida` | `drink` | `bebida` -> `beber` |
| `en-es:proxy:cue-contrastive-overlap-v1:plant:fabrica` | `cue_contrastive_overlap_v1` | `en-es:sentence-veto:plant:planta` | `plant` | `planta` -> `fábrica` |
| `en-es:proxy:cue-contrastive-overlap-v1:drink:beber` | `cue_contrastive_overlap_v1` | `en-es:sentence-veto:drink:bebida` | `drink` | `bebida` -> `beber` |
| `en-es:proxy:cue-cross-pos-frame-v1:check:revisar` | `cue_cross_pos_frame_v1` | `en-es:sentence-veto:check:cheque` | `check` | `cheque` -> `revisar` |
| `en-es:proxy:cue-cross-pos-frame-v1:order:ordenar` | `cue_cross_pos_frame_v1` | `en-es:sentence-veto:order:pedido` | `order` | `pedido` -> `ordenar` |
| `en-es:proxy:cue-cross-pos-frame-v1:trip:tropezar` | `cue_cross_pos_frame_v1` | `en-es:sentence-veto:trip:viaje` | `trip` | `viaje` -> `tropezar` |
| `en-es:proxy:cue-cross-pos-frame-v1:report:informar` | `cue_cross_pos_frame_v1` | `en-es:sentence-veto:report:informe` | `report` | `informe` -> `informar` |
| `en-es:proxy:cue-cross-pos-overlap-v1:check:revisar` | `cue_cross_pos_overlap_v1` | `en-es:sentence-veto:check:cheque` | `check` | `cheque` -> `revisar` |
| `en-es:proxy:cue-cross-pos-overlap-v1:order:ordenar` | `cue_cross_pos_overlap_v1` | `en-es:sentence-veto:order:pedido` | `order` | `pedido` -> `ordenar` |
| `en-es:proxy:cue-cross-pos-overlap-v1:trip:tropezar` | `cue_cross_pos_overlap_v1` | `en-es:sentence-veto:trip:viaje` | `trip` | `viaje` -> `tropezar` |
| `en-es:proxy:cue-cross-pos-overlap-v1:report:informar` | `cue_cross_pos_overlap_v1` | `en-es:sentence-veto:report:informe` | `report` | `informe` -> `informar` |

## Live Command

```bash
PYTHONPATH=apps/gui/src:core .venv/bin/python scripts/testing/semantic_llm_prompt_bakeoff_en_es.py --stage proxy --execute-live --request-id en-es:proxy:cue-contrastive-general-v1:plant:fabrica --request-id en-es:proxy:cue-contrastive-general-v1:drink:beber --request-id en-es:proxy:cue-contrastive-overlap-v1:plant:fabrica --request-id en-es:proxy:cue-contrastive-overlap-v1:drink:beber --request-id en-es:proxy:cue-cross-pos-frame-v1:check:revisar --request-id en-es:proxy:cue-cross-pos-frame-v1:order:ordenar --request-id en-es:proxy:cue-cross-pos-frame-v1:trip:tropezar --request-id en-es:proxy:cue-cross-pos-frame-v1:report:informar --request-id en-es:proxy:cue-cross-pos-overlap-v1:check:revisar --request-id en-es:proxy:cue-cross-pos-overlap-v1:order:ordenar --request-id en-es:proxy:cue-cross-pos-overlap-v1:trip:tropezar --request-id en-es:proxy:cue-cross-pos-overlap-v1:report:informar --run-id <RUN_ID> --require-selected-request-count 12 --input-rate-per-1m <INPUT_RATE> --output-rate-per-1m <OUTPUT_RATE> --max-estimated-cost-ceiling-usd <USD_CAP>
```
