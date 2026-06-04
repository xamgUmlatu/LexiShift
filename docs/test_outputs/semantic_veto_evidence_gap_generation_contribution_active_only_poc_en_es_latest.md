# en-es Semantic Veto Evidence-Gap Generated Contribution

- Status: `ok`
- Decision: `generated_contribution_review_queue_ready`
- Generated: `2026-05-08T20:36:34Z`
- Admitted items: `48`
- Review-required items: `0`
- Possible active-role pollution: `0`
- Metadata active overlap: `0`
- New competitor target items: `0`

## Slot Summary

| Slot | Items | Review required | Possible active pollution |
| --- | ---: | ---: | ---: |
| `active_evidence_expansion` | 48 | 0 | 0 |

## Review Queue

| Item | Slot | Action | TF-IDF active sim | Jaccard active sim | Sentence |
| --- | --- | --- | ---: | ---: | --- |
| _None._ |  |  |  |  |  |

## Next Steps

- Run the downstream score-contribution harness on reviewed generated items.
- Compare high/middle/low improvement only after full-batch admission and role review.

## Limitations

- `no runtime policy change`
- `no source evidence promotion`
- `active-pollution similarity flags use generated sentences, not explanatory metadata`
- `metadata-overlap counts are reported separately because notes may contain contrast language`
- `similarity scores are diagnostics, not final semantic judgments`
- `shadow and no-winner rows still need review or downstream score contribution checks`
