# en-es LLM Example-Frame Sense-Discrimination Audit

- Status: `review`
- Generated: `2026-04-25T02:08:18Z`
- Batch: `en-es:example-frame-composite:reverse-aux-wordnet-all-v10-source-admission-latest`
- Admitted batch: `en-es:example-frame-composite:reverse-aux-wordnet-all-v10-source-admission-latest:sense-admitted`

## Summary

- Input rows: `66`
- Semantic rows: `66`
- Semantic admitted rows: `64`
- Semantic rejected rows: `2`
- Non-semantic passthrough rows: `0`
- Admitted rows: `64`
- Scorers: `sentence_transformer_cosine`
- Evidence view: `all_evidence_text`
- Min intended score: `0.5`
- Min margin: `0.0`
- Rejection reasons: `{"competitor_sense_not_lower": 2}`

## Rejected Rows

| Row | Family | Relation | Intended | Reason | Best Scorer | Intended | Competitor | Margin |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `en-es-sentence-veto-drink-bebida:active-wordnet-example-1` | `en-es:sentence-veto:drink:bebida` | `anchor_cue` | `en-es:sentence-veto:drink:bebida:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.76509 | 0.784039 | -0.018948 |
| `en-es-sentence-veto-play-obra:shadow-en-es-sentence-veto-play-jugar-shadow-wordnet-entry_sentence-1` | `en-es:sentence-veto:play:obra` | `shadow_candidate` | `en-es:sentence-veto:play:jugar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.625639 | 0.701108 | -0.075469 |

## Recommendation

- Use the admitted batch only as an analysis artifact. Replace or quarantine rejected active/shadow rows before any promotion-candidate merge.
