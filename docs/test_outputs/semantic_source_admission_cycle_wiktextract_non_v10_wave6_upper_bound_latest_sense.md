# en-es LLM Example-Frame Sense-Discrimination Audit

- Status: `review`
- Generated: `2026-04-29T01:18:56Z`
- Batch: `en-es:wiktextract-non-v10-wave6-upper-bound:source-admission-cycle-latest`
- Admitted batch: `en-es:wiktextract-non-v10-wave6-upper-bound:source-admission-cycle-latest:sense-admitted`

## Summary

- Input rows: `28`
- Semantic rows: `28`
- Semantic admitted rows: `21`
- Semantic rejected rows: `7`
- Non-semantic passthrough rows: `0`
- Admitted rows: `21`
- Scorers: `sentence_transformer_cosine`
- Evidence view: `all_evidence_text`
- Min intended score: `0.5`
- Min margin: `0.0`
- Rejection reasons: `{"competitor_sense_not_lower": 5, "weak_intended_similarity": 2}`

## Rejected Rows

| Row | Family | Relation | Intended | Reason | Best Scorer | Intended | Competitor | Margin |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `en-es-sentence-veto-leave-permiso:active-en-es-sentence-veto-leave-permiso-active-wiktextract-example-1` | `en-es:sentence-veto:leave:permiso` | `anchor_cue` | `en-es:sentence-veto:leave:permiso:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.614652 | 0.690764 | -0.076112 |
| `en-es-sentence-veto-part-parte:active-en-es-sentence-veto-part-parte-active-wiktextract-example-2` | `en-es:sentence-veto:part:parte` | `anchor_cue` | `en-es:sentence-veto:part:parte:active` | `weak_intended_similarity` | `sentence_transformer_cosine` | 0.499987 | 0.500847 | -0.00086 |
| `en-es-sentence-veto-feel-talento:active-en-es-sentence-veto-feel-talento-active-wiktextract-example-1` | `en-es:sentence-veto:feel:talento` | `anchor_cue` | `en-es:sentence-veto:feel:talento:active` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.596261 | 0.613261 | -0.017 |
| `en-es-sentence-veto-bear-bajista:shadow-en-es-sentence-veto-bear-bajista-llevar-shadow-wiktextract-example-2` | `en-es:sentence-veto:bear:bajista` | `shadow_candidate` | `en-es:sentence-veto:bear:bajista:llevar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.507502 | 0.549247 | -0.041745 |
| `en-es-sentence-veto-throw-lanzamiento:shadow-en-es-sentence-veto-throw-lanzamiento-lanzar-shadow-wiktextract-example-1` | `en-es:sentence-veto:throw:lanzamiento` | `shadow_candidate` | `en-es:sentence-veto:throw:lanzamiento:lanzar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.736011 | 0.766312 | -0.030301 |
| `en-es-sentence-veto-upset-disgustado:shadow-en-es-sentence-veto-upset-disgustado-trastrocar-shadow-wiktextract-example-2` | `en-es:sentence-veto:upset:disgustado` | `shadow_candidate` | `en-es:sentence-veto:upset:disgustado:trastrocar:shadow` | `competitor_sense_not_lower` | `sentence_transformer_cosine` | 0.572382 | 0.609368 | -0.036986 |
| `en-es-sentence-veto-show-espect-culo:shadow-en-es-sentence-veto-show-espect-culo-demostrar-shadow-wiktextract-example-1` | `en-es:sentence-veto:show:espect-culo` | `shadow_candidate` | `en-es:sentence-veto:show:espect-culo:demostrar:shadow` | `weak_intended_similarity` | `sentence_transformer_cosine` | 0.494388 | 0.510187 | -0.015799 |

## Recommendation

- Use the admitted batch only as an analysis artifact. Replace or quarantine rejected active/shadow rows before any promotion-candidate merge.
