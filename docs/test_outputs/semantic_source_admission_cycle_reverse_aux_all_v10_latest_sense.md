# en-es LLM Example-Frame Sense-Discrimination Audit

- Status: `review`
- Generated: `2026-04-25T01:24:11Z`
- Batch: `en-es:example-frame-composite:reverse-aux-all-v10-source-admission-latest`
- Admitted batch: `en-es:example-frame-composite:reverse-aux-all-v10-source-admission-latest:sense-admitted`

## Summary

- Input rows: `35`
- Semantic rows: `35`
- Semantic admitted rows: `32`
- Semantic rejected rows: `3`
- Non-semantic passthrough rows: `0`
- Admitted rows: `32`
- Scorers: `sentence_transformer_cosine`
- Evidence view: `all_evidence_text`
- Min intended score: `0.5`
- Min margin: `0.0`
- Rejection reasons: `{"competitor_sense_not_lower": 3}`

## Rejected Rows

| Row | Family | Relation | Intended | Reason | Best Scorer | Intended | Competitor | Margin |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `en-es-sentence-veto-cell-celula:active-reverse-aux` | `en-es:sentence-veto:cell:celula` | `anchor_cue` | `en-es:sentence-veto:cell:celula:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.622134 | 0.632833 | -0.010699 |
| `en-es-sentence-veto-check-cheque:active-reverse-aux` | `en-es:sentence-veto:check:cheque` | `anchor_cue` | `en-es:sentence-veto:check:cheque:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.645188 | 0.653943 | -0.008755 |
| `en-es-sentence-veto-report-informe:shadow-en-es-sentence-veto-report-informar-shadow-reverse-aux` | `en-es:sentence-veto:report:informe` | `shadow_candidate` | `en-es:sentence-veto:report:informar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.714239 | 0.739001 | -0.024762 |

## Recommendation

- Use the admitted batch only as an analysis artifact. Replace or quarantine rejected active/shadow rows before any promotion-candidate merge.
