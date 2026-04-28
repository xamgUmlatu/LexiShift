# en-es LLM Example-Frame Sense-Discrimination Audit

- Status: `review`
- Generated: `2026-04-25T01:44:52Z`
- Batch: `en-es:example-frame-composite:reverse-aux-wordnet-all-v10-multiscorer-low-source-admission-latest`
- Admitted batch: `en-es:example-frame-composite:reverse-aux-wordnet-all-v10-multiscorer-low-source-admission-latest:sense-admitted`

## Summary

- Input rows: `66`
- Semantic rows: `66`
- Semantic admitted rows: `63`
- Semantic rejected rows: `3`
- Non-semantic passthrough rows: `0`
- Admitted rows: `63`
- Scorers: `token_jaccard, tfidf_cosine, sentence_transformer_cosine`
- Evidence view: `all_evidence_text`
- Min intended score: `0.05`
- Min margin: `0.0`
- Rejection reasons: `{"competitor_sense_not_lower": 1, "weak_intended_similarity": 2}`

## Rejected Rows

| Row | Family | Relation | Intended | Reason | Best Scorer | Intended | Competitor | Margin |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `en-es-sentence-veto-drink-bebida:shadow-en-es-sentence-veto-drink-beber-shadow-wordnet-1` | `en-es:sentence-veto:drink:bebida` | `shadow_candidate` | `en-es:sentence-veto:drink:beber:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.662433 | 0.694093 | -0.03166 |
| `en-es-sentence-veto-play-obra:shadow-en-es-sentence-veto-play-jugar-shadow-wordnet-1` | `en-es:sentence-veto:play:obra` | `shadow_candidate` | `en-es:sentence-veto:play:jugar:shadow` | `weak_intended_similarity` | `token_jaccard` | 0.0 | 0.0 | 0.0 |
| `en-es-sentence-veto-report-informe:shadow-en-es-sentence-veto-report-informar-shadow-wordnet-1` | `en-es:sentence-veto:report:informe` | `shadow_candidate` | `en-es:sentence-veto:report:informar:shadow` | `weak_intended_similarity` | `token_jaccard` | 0.0 | 0.0 | 0.0 |

## Recommendation

- Use the admitted batch only as an analysis artifact. Replace or quarantine rejected active/shadow rows before any promotion-candidate merge.
