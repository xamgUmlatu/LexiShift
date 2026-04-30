# en-es LLM Example-Frame Leakage Audit

- Status: `review`
- Generated: `2026-04-30T19:16:51Z`
- Batch: `en-es:wordnet-alternate-sense-phrase:wordnet-alternate-sense-phrase-non-v10-wave7-source-class-breadth-v1-triage-latest`
- Filtered batch: `en-es:wordnet-alternate-sense-phrase:wordnet-alternate-sense-phrase-non-v10-wave7-source-class-breadth-v1-triage-latest:filtered`

## Summary

- Input rows: `179`
- Leakage hits: `0`
- Duplicate hits: `6`
- Rejected rows: `6`
- Kept rows: `173`
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
| `en-es-sentence-veto-fix-aprieto:phrase-control-wordnet-alt-00487934-v` | `en-es:sentence-veto:fix:aprieto` | make fixed, stable or stationary example: let's fix the picture to the frame | `en-es-sentence-veto-fix-aprieto:phrase-control-wordnet-alt-01651085-v` | `source_duplicate_token_sequence_contained` | 0.2778 |
| `en-es-sentence-veto-full-lleno:phrase-control-wordnet-alt-00434478-v` | `en-es:sentence-veto:full:lleno` | increase in phase example: the moon is waxing | `en-es-sentence-veto-full-lleno:phrase-control-wordnet-alt-15232352-n` | `source_duplicate_token_sequence_contained` | 0.2857 |
| `en-es-sentence-veto-wrong-incorrecto:phrase-control-wordnet-alt-00636618-a` | `en-es:sentence-veto:wrong:incorrecto` | based on or acting or judging in error example: it is wrong to think that way | `en-es-sentence-veto-wrong-incorrecto:phrase-control-wordnet-alt-02042744-a` | `source_duplicate_token_sequence_contained` | 0.28 |
| `en-es-sentence-veto-score-tantos:phrase-control-wordnet-alt-00187483-n` | `en-es:sentence-veto:score:tantos` | the act of scoring in a game or sport example: the winning score came with less than a... | `en-es-sentence-veto-score-tantos:phrase-control-wordnet-alt-13615828-n` | `source_duplicate_token_sequence_contained` | 0.2857 |
| `en-es-sentence-veto-crash-choque:phrase-control-wordnet-alt-01564990-v` | `en-es:sentence-veto:crash:choque` | cause to crash example: The terrorists crashed the plane into the palace | `en-es-sentence-veto-crash-choque:phrase-control-wordnet-alt-02023134-v` | `source_duplicate_token_sequence_contained` | 0.25 |
| `en-es-sentence-veto-trim-compensador:phrase-control-wordnet-alt-01265128-v` | `en-es:sentence-veto:trim:compensador` | remove the edges from and cut down to the desired size example: pare one's fingernails | `en-es-sentence-veto-trim-compensador:phrase-control-wordnet-alt-00360729-n` | `source_duplicate_token_sequence_contained` | 0.2941 |

## Recommendation

- Use the filtered batch for downstream prototype reads, and replace the source-duplicate rows before any promotion claim.
