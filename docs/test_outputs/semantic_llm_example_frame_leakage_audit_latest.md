# en-es LLM Example-Frame Leakage Audit

- Status: `review`
- Generated: `2026-04-24T22:58:19Z`
- Batch: `en-es:example-frame-missing-rows:example-frame-remediation-v1-20260425a`
- Filtered batch: `en-es:example-frame-missing-rows:example-frame-remediation-v1-20260425a:filtered`

## Summary

- Input rows: `8`
- Leakage hits: `1`
- Kept rows: `7`
- Jaccard threshold: `0.75`
- Min contained tokens: `5`

## Leakage Rows

| Row | Family | Evidence | Matched Case | Reason | Jaccard |
| --- | --- | --- | --- | --- | ---: |
| `en-es-sentence-veto-plant-planta:llm:active:missing:v1` | `en-es:sentence-veto:plant:planta` | She watered the plant on the windowsill every morning. | `en-es:sentence-veto:plant:001` | `benchmark_token_sequence_contained` | 0.75 |

## Recommendation

- Use the filtered batch for downstream prototype reads, and regenerate or replace the removed rows before any promotion claim.
