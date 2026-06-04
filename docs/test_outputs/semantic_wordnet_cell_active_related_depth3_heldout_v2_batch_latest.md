# en-es WordNet Example-Frame Batch

- Status: `ok`
- Generated: `2026-04-25T05:27:50Z`
- Batch: `en-es:wordnet-example-frames:en-es-wordnet-cell-active-related-depth3-heldout-v2-20260425a`
- Source: `wordnet_example_frames` / `external_sense_graph`
- Scope: `family_keys`
- Rows: `86`
- Min link score: `0.12`
- Evidence mode: `example_preferred`

## Coverage

- Queue families: `8`
- Source families: `1`
- Target families: `1`
- Target families with active WordNet rows: `1`
- Target families with shadow WordNet rows: `1`
- Families with phrase-control examples: `0`

| Family | Role | Active | Shadow | Phrase | Rows | Best Links |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `en-es:sentence-veto:cell:celula` | `target` | 80 | 6 | 0 | 86 | `célula:00006484-n@0.3`<br>`celda:02994757-n@0.5` |

## Recommendation

- This adapter is a real local source pass for active/shadow semantic evidence, but it intentionally does not solve phrase containment. Run the source-admission cycle before using it as a challenger, and treat missing/low-score links as source gaps rather than generated coverage.
