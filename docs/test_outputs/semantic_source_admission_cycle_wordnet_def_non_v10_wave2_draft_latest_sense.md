# en-es LLM Example-Frame Sense-Discrimination Audit

- Status: `review`
- Generated: `2026-04-27T22:25:03Z`
- Batch: `en-es:wordnet-def-non-v10-wave2-draft-v1:source-admission-cycle`
- Admitted batch: `en-es:wordnet-def-non-v10-wave2-draft-v1:source-admission-cycle:sense-admitted`

## Summary

- Input rows: `17`
- Semantic rows: `17`
- Semantic admitted rows: `15`
- Semantic rejected rows: `2`
- Non-semantic passthrough rows: `0`
- Admitted rows: `15`
- Scorers: `sentence_transformer_cosine`
- Evidence view: `all_evidence_text`
- Min intended score: `0.5`
- Min margin: `0.0`
- Rejection reasons: `{"competitor_sense_not_lower": 2}`

## Rejected Rows

| Row | Family | Relation | Intended | Reason | Best Scorer | Intended | Competitor | Margin |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `en-es-sentence-veto-look-aspecto:shadow-en-es-sentence-veto-look-aspecto-parecer-shadow-wordnet-definition-1` | `en-es:sentence-veto:look:aspecto` | `shadow_candidate` | `en-es:sentence-veto:look:aspecto:parecer:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.737194 | 0.812901 | -0.075707 |
| `en-es-sentence-veto-end-fin:active-wordnet-definition-1` | `en-es:sentence-veto:end:fin` | `anchor_cue` | `en-es:sentence-veto:end:fin:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.733842 | 0.777175 | -0.043333 |

## Recommendation

- Use the admitted batch only as an analysis artifact. Replace or quarantine rejected active/shadow rows before any promotion-candidate merge.
