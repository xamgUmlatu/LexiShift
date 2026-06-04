# en-es LLM Example-Frame Sense-Discrimination Audit

- Status: `review`
- Generated: `2026-04-25T03:11:04Z`
- Batch: `en-es:example-frame-composite:reverse-aux-wordnet-wiktextract-wordnet-related-plant-heldout-v1`
- Admitted batch: `en-es:example-frame-composite:reverse-aux-wordnet-wiktextract-wordnet-related-plant-heldout-v1:sense-admitted`

## Summary

- Input rows: `89`
- Semantic rows: `89`
- Semantic admitted rows: `86`
- Semantic rejected rows: `3`
- Non-semantic passthrough rows: `0`
- Admitted rows: `86`
- Scorers: `sentence_transformer_cosine`
- Evidence view: `all_evidence_text`
- Min intended score: `0.5`
- Min margin: `0.0`
- Rejection reasons: `{"competitor_sense_not_lower": 3}`

## Rejected Rows

| Row | Family | Relation | Intended | Reason | Best Scorer | Intended | Competitor | Margin |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `en-es-sentence-veto-plant-planta:shadow-en-es-sentence-veto-plant-fabrica-shadow-wordnet-definition-9` | `en-es:sentence-veto:plant:planta` | `shadow_candidate` | `en-es:sentence-veto:plant:fabrica:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.720713 | 0.740908 | -0.020196 |
| `en-es-sentence-veto-plant-planta:shadow-en-es-sentence-veto-plant-fabrica-shadow-wordnet-definition-11` | `en-es:sentence-veto:plant:planta` | `shadow_candidate` | `en-es:sentence-veto:plant:fabrica:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.694966 | 0.709755 | -0.014789 |
| `en-es-sentence-veto-plant-planta:shadow-en-es-sentence-veto-plant-fabrica-shadow-wordnet-definition-12` | `en-es:sentence-veto:plant:planta` | `shadow_candidate` | `en-es:sentence-veto:plant:fabrica:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.663337 | 0.735862 | -0.072525 |

## Recommendation

- Use the admitted batch only as an analysis artifact. Replace or quarantine rejected active/shadow rows before any promotion-candidate merge.
