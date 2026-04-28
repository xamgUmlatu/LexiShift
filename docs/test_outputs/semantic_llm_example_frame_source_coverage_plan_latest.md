# en-es LLM Example-Frame Generation Plan

- Status: `ready`
- Generated: `2026-04-25T00:00:32Z`
- Dataset: `en_es_sentence_veto_v10`
- Required families: `en_es_sentence_veto_v10`
- Base batch: `en-es:example-frame-composite:reverse-aux-plus-llm-missing-rows-plus-balanced-remediation-latest`
- Prompt version: `example-frame-missing-rows-v1`
- Selected model: `gpt-5.4-mini`
- Decision contract: `binary_replace_or_abstain`
- Review leakage policy: `do_not_include_sentence_veto_case_sentences_in_prompts`
- Generation targets: `active_example, shadow_example`

## Summary

- Requests: `22`
- Families: `11`
- Estimated input tokens: `6567`
- Expected output tokens: `1100`
- Max output tokens: `3960`
- Requests by target: `{"active_example": 11, "shadow_example": 11}`

## Request Rows

| Request | Target | Family | Candidate | Input Tokens |
| --- | --- | --- | --- | ---: |
| `en-es:example-frame-missing:active:en-es-sentence-veto-ball-pelota` | `active_example` | `en-es:sentence-veto:ball:pelota` | `pelota` | 293 |
| `en-es:example-frame-missing:shadow:en-es-sentence-veto-ball-pelota:en-es-sentence-veto-ball-baile-shadow` | `shadow_example` | `en-es:sentence-veto:ball:pelota` | `baile` | 312 |
| `en-es:example-frame-missing:active:en-es-sentence-veto-bank-banco` | `active_example` | `en-es:sentence-veto:bank:banco` | `banco` | 287 |
| `en-es:example-frame-missing:shadow:en-es-sentence-veto-bank-banco:en-es-sentence-veto-bank-orilla-shadow` | `shadow_example` | `en-es:sentence-veto:bank:banco` | `orilla` | 302 |
| `en-es:example-frame-missing:active:en-es-sentence-veto-cell-celula` | `active_example` | `en-es:sentence-veto:cell:celula` | `célula` | 285 |
| `en-es:example-frame-missing:shadow:en-es-sentence-veto-cell-celula:en-es-sentence-veto-cell-celda-shadow` | `shadow_example` | `en-es:sentence-veto:cell:celula` | `celda` | 301 |
| `en-es:example-frame-missing:active:en-es-sentence-veto-spring-primavera` | `active_example` | `en-es:sentence-veto:spring:primavera` | `primavera` | 290 |
| `en-es:example-frame-missing:shadow:en-es-sentence-veto-spring-primavera:en-es-sentence-veto-spring-resorte-shadow` | `shadow_example` | `en-es:sentence-veto:spring:primavera` | `resorte` | 313 |
| `en-es:example-frame-missing:active:en-es-sentence-veto-seal-sello` | `active_example` | `en-es:sentence-veto:seal:sello` | `sello` | 286 |
| `en-es:example-frame-missing:shadow:en-es-sentence-veto-seal-sello:en-es-sentence-veto-seal-foca-shadow` | `shadow_example` | `en-es:sentence-veto:seal:sello` | `foca` | 302 |
| `en-es:example-frame-missing:active:en-es-sentence-veto-file-archivo` | `active_example` | `en-es:sentence-veto:file:archivo` | `archivo` | 287 |
| `en-es:example-frame-missing:shadow:en-es-sentence-veto-file-archivo:en-es-sentence-veto-file-lima-shadow` | `shadow_example` | `en-es:sentence-veto:file:archivo` | `lima` | 309 |
| `en-es:example-frame-missing:active:en-es-sentence-veto-match-partido` | `active_example` | `en-es:sentence-veto:match:partido` | `partido` | 287 |
| `en-es:example-frame-missing:shadow:en-es-sentence-veto-match-partido:en-es-sentence-veto-match-cerilla-shadow` | `shadow_example` | `en-es:sentence-veto:match:partido` | `cerilla` | 304 |
| `en-es:example-frame-missing:active:en-es-sentence-veto-board-tablero` | `active_example` | `en-es:sentence-veto:board:tablero` | `tablero` | 297 |
| `en-es:example-frame-missing:shadow:en-es-sentence-veto-board-tablero:en-es-sentence-veto-board-junta-shadow` | `shadow_example` | `en-es:sentence-veto:board:tablero` | `junta` | 322 |
| `en-es:example-frame-missing:active:en-es-sentence-veto-table-mesa` | `active_example` | `en-es:sentence-veto:table:mesa` | `mesa` | 290 |
| `en-es:example-frame-missing:shadow:en-es-sentence-veto-table-mesa:en-es-sentence-veto-table-tabla-shadow` | `shadow_example` | `en-es:sentence-veto:table:mesa` | `tabla` | 309 |
| `en-es:example-frame-missing:active:en-es-sentence-veto-branch-sucursal` | `active_example` | `en-es:sentence-veto:branch:sucursal` | `sucursal` | 288 |
| `en-es:example-frame-missing:shadow:en-es-sentence-veto-branch-sucursal:en-es-sentence-veto-branch-rama-shadow` | `shadow_example` | `en-es:sentence-veto:branch:sucursal` | `rama` | 306 |
| `en-es:example-frame-missing:active:en-es-sentence-veto-park-parque` | `active_example` | `en-es:sentence-veto:park:parque` | `parque` | 288 |
| `en-es:example-frame-missing:shadow:en-es-sentence-veto-park-parque:en-es-sentence-veto-park-aparcar-shadow` | `shadow_example` | `en-es:sentence-veto:park:parque` | `aparcar` | 309 |

## Recommendation

- Execute only these selected missing-row requests, then merge accepted rows with the base evidence batch and rerun the contract plus prototype-admission ablation matrix.
