# en-es LLM Example-Frame Leakage Audit

- Status: `review`
- Generated: `2026-04-28T21:09:19Z`
- Batch: `en-es:example-frame-missing-rows:source-frame-gap-v2-20260429a`
- Filtered batch: `en-es:example-frame-missing-rows:source-frame-gap-v2-20260429a:filtered`

## Summary

- Input rows: `5`
- Leakage hits: `2`
- Duplicate hits: `1`
- Rejected rows: `2`
- Kept rows: `3`
- Jaccard threshold: `0.75`
- Duplicate jaccard threshold: `0.92`
- Min contained tokens: `5`
- Min duplicate tokens: `4`

## Leakage Rows

| Row | Family | Evidence | Matched Case | Reason | Jaccard |
| --- | --- | --- | --- | --- | ---: |
| `en-es-sentence-veto-board-tablero:aligned-frame:shadow-example:en-es-sentence-veto-board-junta-shadow:candidate-02` | `en-es:sentence-veto:board:tablero` | At Monday's meeting, the board approved the merger after reviewing the audit report. | `en-es:sentence-veto:board:003` | `benchmark_token_sequence_overlap` | 0.3077 |
| `en-es-sentence-veto-board-tablero:aligned-frame:shadow-example:en-es-sentence-veto-board-junta-shadow:candidate-05` | `en-es:sentence-veto:board:tablero` | After the audit, the board approved the merger and appointed a new chief executive. | `en-es:sentence-veto:board:003` | `benchmark_token_sequence_overlap` | 0.2857 |

## Duplicate Rows

| Row | Family | Evidence | Matched Row | Reason | Jaccard |
| --- | --- | --- | --- | --- | ---: |
| `en-es-sentence-veto-board-tablero:aligned-frame:shadow-example:en-es-sentence-veto-board-junta-shadow:candidate-05` | `en-es:sentence-veto:board:tablero` | After the audit, the board approved the merger and appointed a new chief executive. | `en-es-sentence-veto-board-tablero:aligned-frame:shadow-example:en-es-sentence-veto-board-junta-shadow:candidate-02` | `source_duplicate_token_sequence_contained` | 0.375 |

## Recommendation

- Use the filtered batch for downstream prototype reads, and regenerate or replace the removed leakage or duplicate rows before any promotion claim.
