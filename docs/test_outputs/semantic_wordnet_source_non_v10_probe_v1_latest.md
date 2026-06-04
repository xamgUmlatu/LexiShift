# en-es WordNet Example-Frame Batch

- Status: `ok`
- Generated: `2026-04-26T03:20:39Z`
- Batch: `en-es:wordnet-example-frames:wordnet-source-non-v10-probe-v1-20260426a`
- Source: `wordnet_example_frames` / `external_sense_graph`
- Scope: `all_dataset_families`
- Rows: `18`
- Min link score: `0.12`
- Evidence mode: `example_preferred`

## Coverage

- Queue families: `8`
- Source families: `8`
- Target families: `8`
- Target families with active WordNet rows: `8`
- Target families with shadow WordNet rows: `8`
- Families with phrase-control examples: `0`

| Family | Role | Active | Shadow | Phrase | Rows | Best Links |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `en-es:sentence-veto:rock:roca` | `target` | 1 | 1 | 0 | 2 | `roca:09438954-n@0.7143`<br>`sacudir:01880021-v@0.5556` |
| `en-es:sentence-veto:draft:borrador` | `target` | 1 | 1 | 0 | 2 | `borrador:06402605-n@0.5556`<br>`reclutar:01099911-v@0.375` |
| `en-es:sentence-veto:case:caso` | `target` | 1 | 2 | 0 | 3 | `caso:01185144-n@0.4`<br>`estuche:02978156-n@0.7143`<br>`vigilar:02170426-v@0.3333` |
| `en-es:sentence-veto:scale:escala` | `target` | 1 | 1 | 0 | 2 | `escala:13872501-n@0.6667`<br>`escalar:02211818-v@0.1667` |
| `en-es:sentence-veto:line:linea` | `target` | 1 | 1 | 0 | 2 | `linea:07025650-n@0.5`<br>`forrar:01273348-v@0.2857` |
| `en-es:sentence-veto:point:punto` | `target` | 1 | 1 | 0 | 2 | `punto:06619161-n@0.2222`<br>`senalar:00925764-v@0.6667` |
| `en-es:sentence-veto:ring:anillo` | `target` | 1 | 1 | 0 | 2 | `anillo:04099721-n@0.6667`<br>`sonar:02185344-v@0.5714` |
| `en-es:sentence-veto:date:fecha` | `target` | 1 | 2 | 0 | 3 | `fecha:15185626-n@0.5556`<br>`datil:07781049-n@0.7143`<br>`fechar:00620873-v@0.4444` |

## Recommendation

- This adapter is a real local source pass for active/shadow semantic evidence, but it intentionally does not solve phrase containment. Run the source-admission cycle before using it as a challenger, and treat missing/low-score links as source gaps rather than generated coverage.
