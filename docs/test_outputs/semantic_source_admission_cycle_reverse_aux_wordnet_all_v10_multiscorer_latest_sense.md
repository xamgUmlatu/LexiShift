# en-es LLM Example-Frame Sense-Discrimination Audit

- Status: `review`
- Generated: `2026-04-25T01:44:13Z`
- Batch: `en-es:example-frame-composite:reverse-aux-wordnet-all-v10-multiscorer-source-admission-latest`
- Admitted batch: `en-es:example-frame-composite:reverse-aux-wordnet-all-v10-multiscorer-source-admission-latest:sense-admitted`

## Summary

- Input rows: `66`
- Semantic rows: `66`
- Semantic admitted rows: `62`
- Semantic rejected rows: `4`
- Non-semantic passthrough rows: `0`
- Admitted rows: `62`
- Scorers: `token_jaccard, tfidf_cosine, sentence_transformer_cosine`
- Evidence view: `all_evidence_text`
- Min intended score: `0.5`
- Min margin: `0.0`
- Rejection reasons: `{"competitor_sense_not_lower": 1, "weak_intended_similarity": 3}`

## Rejected Rows

| Row | Family | Relation | Intended | Reason | Best Scorer | Intended | Competitor | Margin |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `en-es-sentence-veto-drink-bebida:active-wordnet-1` | `en-es:sentence-veto:drink:bebida` | `anchor_cue` | `en-es:sentence-veto:drink:bebida:active` | `weak_intended_similarity` | `tfidf_cosine` | 0.101076 | 0.049683 | 0.051393 |
| `en-es-sentence-veto-drink-bebida:shadow-en-es-sentence-veto-drink-beber-shadow-wordnet-1` | `en-es:sentence-veto:drink:bebida` | `shadow_candidate` | `en-es:sentence-veto:drink:beber:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.662433 | 0.694093 | -0.03166 |
| `en-es-sentence-veto-play-obra:shadow-en-es-sentence-veto-play-jugar-shadow-wordnet-1` | `en-es:sentence-veto:play:obra` | `shadow_candidate` | `en-es:sentence-veto:play:jugar:shadow` | `weak_intended_similarity` | `token_jaccard` | 0.0 | 0.0 | 0.0 |
| `en-es-sentence-veto-report-informe:shadow-en-es-sentence-veto-report-informar-shadow-wordnet-1` | `en-es:sentence-veto:report:informe` | `shadow_candidate` | `en-es:sentence-veto:report:informar:shadow` | `weak_intended_similarity` | `token_jaccard` | 0.0 | 0.0 | 0.0 |

## Recommendation

- Use the admitted batch only as an analysis artifact. Replace or quarantine rejected active/shadow rows before any promotion-candidate merge.
