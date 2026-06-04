# en-es LLM Example-Frame Sense-Discrimination Audit

- Status: `review`
- Generated: `2026-04-25T00:54:22Z`
- Batch: `en-es:example-frame-composite:balanced-plus-source-coverage-filtered-safe-v2-20260425a`
- Admitted batch: `en-es:example-frame-composite:balanced-plus-source-coverage-filtered-safe-v2-20260425a:sense-admitted`

## Summary

- Input rows: `60`
- Semantic rows: `52`
- Semantic admitted rows: `50`
- Semantic rejected rows: `2`
- Non-semantic passthrough rows: `8`
- Admitted rows: `58`
- Scorers: `sentence_transformer_cosine`
- Evidence view: `all_evidence_text`
- Min intended score: `0.5`
- Min margin: `0.0`
- Rejection reasons: `{"competitor_sense_not_lower": 2}`

## Rejected Rows

| Row | Family | Relation | Intended | Reason | Best Scorer | Intended | Competitor | Margin |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `en-es-sentence-veto-check-cheque:active-reverse-aux` | `en-es:sentence-veto:check:cheque` | `anchor_cue` | `en-es:sentence-veto:check:cheque:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.645188 | 0.653943 | -0.008755 |
| `en-es-sentence-veto-report-informe:shadow-en-es-sentence-veto-report-informar-shadow-reverse-aux` | `en-es:sentence-veto:report:informe` | `shadow_candidate` | `en-es:sentence-veto:report:informar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.714239 | 0.739001 | -0.024762 |

## Recommendation

- Use the admitted batch only as an analysis artifact. Replace or quarantine rejected active/shadow rows before any promotion-candidate merge.
