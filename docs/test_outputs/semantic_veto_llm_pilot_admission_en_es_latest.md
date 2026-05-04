# en-es Semantic Veto LLM Pilot Admission

- Status: `ok`
- Decision: `admitted_for_scoring`
- Generated: `2026-05-04T21:53:16Z`
- Plan: `docs/test_inputs/semantic_veto_llm_pilot_plan_en_es.json`
- Generation requests: `docs/test_outputs/semantic_veto_llm_pilot_generation_requests_en_es_latest.json`
- Generated rows: `docs/test_outputs/semantic_veto_llm_pilot_generated_rows_en_es_latest.json`
- Candidate: `control_st_masked_all_margin_phrase_override|shadow_or_phrase_score|lead=0.05|score=0.0`
- Runtime policy change: `none`

## Strict Flow

| Check | Value |
| --- | --- |
| Runtime policy change | `none` |
| Source evidence promotion | `none` |
| Locked-eval threshold tuning | `False` |
| Required flow steps | `7` |
| Required admission filters | `11` |

## Plan Summary

- Pilot families: `12`
- Planned rows: `72`
- Planned rows by type: `phrase_no_winner: 12, positive_active: 36, shadow_negative: 24`
- Generation strata axes: `context_distance, difficulty, morphology, register, trigger_position, word_order`

## Admission Summary

- Generated rows present: `True`
- Generated rows: `72`
- Admitted rows: `72`
- Rejected rows: `0`
- Accepted rows by type: `phrase_no_winner: 12, positive_active: 36, shadow_negative: 24`

## Request Alignment

- Request packet present: `True`
- Expected rows: `72`
- Matched rows: `72`
- Missing expected rows: `0`
- Unexpected generated rows: `0`

## Split Summary

- Discovery rows: `56`
- Locked-eval rows: `16`
- Threshold tuning on locked eval: `false`

## Family Coverage

| Family | Trigger | Type | Planned | Admitted | Shortfall |
| --- | --- | --- | ---: | ---: | ---: |
| `pilot:bank:banco` | `bank` | `positive_active` | 3 | 3 | 0 |
| `pilot:bank:banco` | `bank` | `shadow_negative` | 2 | 2 | 0 |
| `pilot:bank:banco` | `bank` | `phrase_no_winner` | 1 | 1 | 0 |
| `pilot:plant:planta` | `plant` | `positive_active` | 3 | 3 | 0 |
| `pilot:plant:planta` | `plant` | `shadow_negative` | 2 | 2 | 0 |
| `pilot:plant:planta` | `plant` | `phrase_no_winner` | 1 | 1 | 0 |
| `pilot:board:tablero` | `board` | `positive_active` | 3 | 3 | 0 |
| `pilot:board:tablero` | `board` | `shadow_negative` | 2 | 2 | 0 |
| `pilot:board:tablero` | `board` | `phrase_no_winner` | 1 | 1 | 0 |
| `pilot:check:cheque` | `check` | `positive_active` | 3 | 3 | 0 |
| `pilot:check:cheque` | `check` | `shadow_negative` | 2 | 2 | 0 |
| `pilot:check:cheque` | `check` | `phrase_no_winner` | 1 | 1 | 0 |
| `pilot:branch:sucursal` | `branch` | `positive_active` | 3 | 3 | 0 |
| `pilot:branch:sucursal` | `branch` | `shadow_negative` | 2 | 2 | 0 |
| `pilot:branch:sucursal` | `branch` | `phrase_no_winner` | 1 | 1 | 0 |
| `pilot:file:archivo` | `file` | `positive_active` | 3 | 3 | 0 |
| `pilot:file:archivo` | `file` | `shadow_negative` | 2 | 2 | 0 |
| `pilot:file:archivo` | `file` | `phrase_no_winner` | 1 | 1 | 0 |
| `pilot:play:obra` | `play` | `positive_active` | 3 | 3 | 0 |
| `pilot:play:obra` | `play` | `shadow_negative` | 2 | 2 | 0 |
| `pilot:play:obra` | `play` | `phrase_no_winner` | 1 | 1 | 0 |
| `pilot:seal:sello` | `seal` | `positive_active` | 3 | 3 | 0 |
| `pilot:seal:sello` | `seal` | `shadow_negative` | 2 | 2 | 0 |
| `pilot:seal:sello` | `seal` | `phrase_no_winner` | 1 | 1 | 0 |
| `pilot:report:informe` | `report` | `positive_active` | 3 | 3 | 0 |
| `pilot:report:informe` | `report` | `shadow_negative` | 2 | 2 | 0 |
| `pilot:report:informe` | `report` | `phrase_no_winner` | 1 | 1 | 0 |
| `pilot:order:pedido` | `order` | `positive_active` | 3 | 3 | 0 |
| `pilot:order:pedido` | `order` | `shadow_negative` | 2 | 2 | 0 |
| `pilot:order:pedido` | `order` | `phrase_no_winner` | 1 | 1 | 0 |
| `pilot:match:partido` | `match` | `positive_active` | 3 | 3 | 0 |
| `pilot:match:partido` | `match` | `shadow_negative` | 2 | 2 | 0 |
| `pilot:match:partido` | `match` | `phrase_no_winner` | 1 | 1 | 0 |
| `pilot:watch:reloj` | `watch` | `positive_active` | 3 | 3 | 0 |
| `pilot:watch:reloj` | `watch` | `shadow_negative` | 2 | 2 | 0 |
| `pilot:watch:reloj` | `watch` | `phrase_no_winner` | 1 | 1 | 0 |

## Rejections

| Row | Family | Type | Reasons |
| --- | --- | --- | --- |
| _None._ |  |  |  |

## Next Steps

- Score admitted discovery and locked-eval rows with the frozen veto-only candidate.
- Compare product metrics against the current candidate-selection and stress lanes.
- Expand breadth only if locked-eval metrics stay near the product acceptance target.

## Limitations

- `research-only lane`
- `runtime policy remains unchanged`
- `generated rows are evaluation data, not source evidence`
- `locked-eval rows cannot be used for threshold selection`
