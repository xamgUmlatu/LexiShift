# en-es LLM Example-Frame Leakage Audit

- Status: `review`
- Generated: `2026-04-30T03:35:13Z`
- Batch: `en-es:wordnet-alternate-sense-phrase:wordnet-alternate-sense-phrase-non-v10-wave6-wiktextract-supported-v1-latest`
- Filtered batch: `en-es:wordnet-alternate-sense-phrase:wordnet-alternate-sense-phrase-non-v10-wave6-wiktextract-supported-v1-latest:filtered`

## Summary

- Input rows: `189`
- Leakage hits: `0`
- Duplicate hits: `9`
- Rejected rows: `9`
- Kept rows: `180`
- Jaccard threshold: `0.75`
- Duplicate jaccard threshold: `0.92`
- Min contained tokens: `5`
- Min duplicate tokens: `4`

## Leakage Rows

| Row | Family | Evidence | Matched Case | Reason | Jaccard |
| --- | --- | --- | --- | --- | ---: |
| `none` | `n/a` | n/a | `n/a` | `n/a` | 0 |

## Duplicate Rows

| Row | Family | Evidence | Matched Row | Reason | Jaccard |
| --- | --- | --- | --- | --- | ---: |
| `en-es-sentence-veto-leave-permiso:phrase-control-wordnet-alt-02361226-v` | `en-es:sentence-veto:leave:permiso` | put into the care or protection of someone example: He left the decision to his deputy | `en-es-sentence-veto-leave-permiso:phrase-control-wordnet-alt-00615374-v` | `source_duplicate_token_sequence_contained` | 0.1852 |
| `en-es-sentence-veto-part-parte:phrase-control-wordnet-alt-13306199-n` | `en-es:sentence-veto:part:parte` | assets belonging to or due to or contributed by an individual person or group example:... | `en-es-sentence-veto-part-parte:phrase-control-wordnet-alt-00721817-n` | `source_duplicate_token_sequence_contained` | 0.2308 |
| `en-es-sentence-veto-feel-talento:phrase-control-wordnet-alt-02115034-v` | `en-es:sentence-veto:feel:talento` | undergo passive experience of example: We felt the effects of inflation | `en-es-sentence-veto-feel-talento:phrase-control-wordnet-alt-02110460-v` | `source_duplicate_token_sequence_contained` | 0.1818 |
| `en-es-sentence-veto-throw-lanzamiento:phrase-control-wordnet-alt-01636439-v` | `en-es:sentence-veto:throw:lanzamiento` | put or send forth example: She threw the flashlight beam into the corner | `en-es-sentence-veto-throw-lanzamiento:phrase-control-wordnet-alt-01501904-v` | `source_duplicate_token_sequence_contained` | 0.3158 |
| `en-es-sentence-veto-piece-trozo:phrase-control-wordnet-alt-07324075-n` | `en-es:sentence-veto:piece:trozo` | an instance of some kind example: it was a nice piece of work | `en-es-sentence-veto-piece-trozo:phrase-control-wordnet-alt-03938737-n` | `source_duplicate_token_sequence_contained` | 0.3333 |
| `en-es-sentence-veto-show-espect-culo:phrase-control-wordnet-alt-00945869-v` | `en-es:sentence-veto:show:espect-culo` | give expression to example: She showed her disappointment | `en-es-sentence-veto-show-espect-culo:phrase-control-wordnet-alt-02141597-v` | `source_duplicate_token_sequence_contained` | 0.2667 |
| `en-es-sentence-veto-show-espect-culo:phrase-control-wordnet-alt-00925764-v` | `en-es:sentence-veto:show:espect-culo` | indicate a place, direction, person, or thing; either spatially or figuratively example... | `en-es-sentence-veto-show-espect-culo:phrase-control-wordnet-alt-02141597-v` | `source_duplicate_token_sequence_contained` | 0.2273 |
| `en-es-sentence-veto-show-espect-culo:phrase-control-wordnet-alt-02144017-v` | `en-es:sentence-veto:show:espect-culo` | be or become visible or noticeable example: His good upbringing really shows | `en-es-sentence-veto-show-espect-culo:phrase-control-wordnet-alt-02141597-v` | `source_duplicate_token_sequence_contained` | 0.2941 |
| `en-es-sentence-veto-rank-rancio:phrase-control-wordnet-alt-08417922-n` | `en-es:sentence-veto:rank:rancio` | the body of members of an organization or group example: they polled their membership | `en-es-sentence-veto-rank-rancio:phrase-control-wordnet-alt-08415136-n` | `source_duplicate_token_sequence_contained` | 0.2 |

## Recommendation

- Use the filtered batch for downstream prototype reads, and replace the source-duplicate rows before any promotion claim.
