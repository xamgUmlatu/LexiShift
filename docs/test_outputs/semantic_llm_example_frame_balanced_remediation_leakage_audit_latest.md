# en-es LLM Example-Frame Leakage Audit

- Status: `review`
- Generated: `2026-04-24T23:09:37Z`
- Batch: `en-es:example-frame-missing-rows:example-frame-balanced-remediation-v1-20260425a-rekeyed:replay`
- Filtered batch: `en-es:example-frame-missing-rows:example-frame-balanced-remediation-v1-20260425a-rekeyed:replay:filtered`

## Summary

- Input rows: `6`
- Leakage hits: `1`
- Kept rows: `5`
- Jaccard threshold: `0.75`
- Min contained tokens: `5`

## Leakage Rows

| Row | Family | Evidence | Matched Case | Reason | Jaccard |
| --- | --- | --- | --- | --- | ---: |
| `en-es-sentence-veto-plant-planta:llm:active:remediation-active-001-002:v1` | `en-es:sentence-veto:plant:planta` | I watered the plant on the windowsill every morning. | `en-es:sentence-veto:plant:001` | `benchmark_canonical_token_sequence_contained` | 0.5556 |

## Recommendation

- Use the filtered batch for downstream prototype reads, and regenerate or replace the removed rows before any promotion claim.
