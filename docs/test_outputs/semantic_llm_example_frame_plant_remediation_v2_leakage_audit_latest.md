# en-es LLM Example-Frame Leakage Audit

- Status: `review`
- Generated: `2026-04-24T23:10:45Z`
- Batch: `en-es:example-frame-missing-rows:example-frame-plant-remediation-v2-20260425a`
- Filtered batch: `en-es:example-frame-missing-rows:example-frame-plant-remediation-v2-20260425a:filtered`

## Summary

- Input rows: `1`
- Leakage hits: `1`
- Kept rows: `0`
- Jaccard threshold: `0.75`
- Min contained tokens: `5`

## Leakage Rows

| Row | Family | Evidence | Matched Case | Reason | Jaccard |
| --- | --- | --- | --- | --- | ---: |
| `en-es-sentence-veto-plant-planta:llm:active:remediation-active-001-002:v1` | `en-es:sentence-veto:plant:planta` | The plant on my windowsill drooped until I watered its roots. | `en-es:sentence-veto:plant:001` | `benchmark_canonical_token_sequence_overlap` | 0.4167 |

## Recommendation

- Use the filtered batch for downstream prototype reads, and regenerate or replace the removed rows before any promotion claim.
