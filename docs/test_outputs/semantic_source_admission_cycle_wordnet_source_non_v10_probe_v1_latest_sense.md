# en-es LLM Example-Frame Sense-Discrimination Audit

- Status: `review`
- Generated: `2026-04-26T03:21:02Z`
- Batch: `en-es:source-admission-cycle:wordnet-source-non-v10-probe-v1-20260426a`
- Admitted batch: `en-es:source-admission-cycle:wordnet-source-non-v10-probe-v1-20260426a:sense-admitted`

## Summary

- Input rows: `18`
- Semantic rows: `18`
- Semantic admitted rows: `14`
- Semantic rejected rows: `4`
- Non-semantic passthrough rows: `0`
- Admitted rows: `14`
- Scorers: `sentence_transformer_cosine`
- Evidence view: `all_evidence_text`
- Min intended score: `0.5`
- Min margin: `0.0`
- Rejection reasons: `{"competitor_sense_not_lower": 4}`

## Rejected Rows

| Row | Family | Relation | Intended | Reason | Best Scorer | Intended | Competitor | Margin |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `en-es-sentence-veto-rock-roca:active-wordnet-example-1` | `en-es:sentence-veto:rock:roca` | `anchor_cue` | `en-es:sentence-veto:rock:roca:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.68905 | 0.698032 | -0.008982 |
| `en-es-sentence-veto-case-caso:active-wordnet-example-1` | `en-es:sentence-veto:case:caso` | `anchor_cue` | `en-es:sentence-veto:case:caso:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.638299 | 0.641316 | -0.003017 |
| `en-es-sentence-veto-point-punto:active-wordnet-example-1` | `en-es:sentence-veto:point:punto` | `anchor_cue` | `en-es:sentence-veto:point:punto:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.726964 | 0.727076 | -0.000112 |
| `en-es-sentence-veto-date-fecha:active-wordnet-example-1` | `en-es:sentence-veto:date:fecha` | `anchor_cue` | `en-es:sentence-veto:date:fecha:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.65645 | 0.665607 | -0.009157 |

## Recommendation

- Use the admitted batch only as an analysis artifact. Replace or quarantine rejected active/shadow rows before any promotion-candidate merge.
