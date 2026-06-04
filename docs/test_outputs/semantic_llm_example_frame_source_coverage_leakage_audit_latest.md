# en-es LLM Example-Frame Leakage Audit

- Status: `review`
- Generated: `2026-04-25T00:40:26Z`
- Batch: `en-es:example-frame-missing-rows:source-coverage-v1-20260425a`
- Filtered batch: `en-es:example-frame-missing-rows:source-coverage-v1-20260425a:filtered`

## Summary

- Input rows: `22`
- Leakage hits: `3`
- Duplicate hits: `0`
- Rejected rows: `3`
- Kept rows: `19`
- Jaccard threshold: `0.75`
- Duplicate jaccard threshold: `0.92`
- Min contained tokens: `5`
- Min duplicate tokens: `4`

## Leakage Rows

| Row | Family | Evidence | Matched Case | Reason | Jaccard |
| --- | --- | --- | --- | --- | ---: |
| `en-es-sentence-veto-ball-pelota:llm:active:missing:v1` | `en-es:sentence-veto:ball:pelota` | He kicked the ball into the net during soccer practice. | `en-es:sentence-veto:ball:002` | `benchmark_token_sequence_overlap` | 0.3636 |
| `en-es-sentence-veto-file-archivo:llm:shadow:en-es-sentence-veto-file-lima-shadow:missing:v1` | `en-es:sentence-veto:file:archivo` | He used a file to smooth the jagged edge of the metal rod. | `en-es:sentence-veto:file:003` | `benchmark_token_sequence_overlap` | 0.6154 |
| `en-es-sentence-veto-board-tablero:llm:shadow:en-es-sentence-veto-board-junta-shadow:missing:v1` | `en-es:sentence-veto:board:tablero` | The board approved the merger after reviewing the quarterly report. | `en-es:sentence-veto:board:003` | `benchmark_token_sequence_overlap` | 0.4 |

## Duplicate Rows

| Row | Family | Evidence | Matched Row | Reason | Jaccard |
| --- | --- | --- | --- | --- | ---: |
| `none` | `n/a` | n/a | `n/a` | `n/a` | 0 |

## Recommendation

- Use the filtered batch for downstream prototype reads, and regenerate or replace the removed leakage or duplicate rows before any promotion claim.
