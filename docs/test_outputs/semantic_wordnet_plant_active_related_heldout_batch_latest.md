# en-es WordNet Example-Frame Batch

- Status: `ok`
- Generated: `2026-04-25T03:12:44Z`
- Batch: `en-es:wordnet-example-frames:wordnet-plant-active-related-heldout-v1-20260425a`
- Source: `wordnet_example_frames` / `external_sense_graph`
- Scope: `family_keys`
- Rows: `14`
- Min link score: `0.12`
- Evidence mode: `definition_preferred`

## Coverage

- Queue families: `8`
- Source families: `1`
- Target families: `1`
- Target families with active WordNet rows: `1`
- Target families with shadow WordNet rows: `1`
- Families with phrase-control examples: `0`

| Family | Role | Active | Shadow | Phrase | Rows | Best Links |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `en-es:sentence-veto:plant:planta` | `target` | 12 | 2 | 0 | 14 | `planta:00017402-n@0.2`<br>`fábrica:03963198-n@0.1429` |

## Recommendation

- This adapter is a real local source pass for active/shadow semantic evidence, but it intentionally does not solve phrase containment. Run the source-admission cycle before using it as a challenger, and treat missing/low-score links as source gaps rather than generated coverage.
