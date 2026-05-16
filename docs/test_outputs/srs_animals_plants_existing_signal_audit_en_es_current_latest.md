# en-es Animals/Plants Existing Signal Audit

- Status: `ok`
- Decision: `animals_plants_existing_signal_audit_completed`
- Generated: `2026-05-16T21:24:10+00:00`
- Rows measured: `1984`

## Findings

- `PASS` `existing_sources_loaded`: Frequency and Kaikki DBs are available.
- `PASS` `animals_plants_split_enforced`: Botany/plants evidence is reported separately from animal evidence.
- `PASS` `animal_evidence_found`: Existing sources contain animal evidence.
- `PASS` `plants_nature_evidence_found`: Existing sources contain plants/nature evidence.

## Family Summary

| Family | Candidates | Share | Tiers | Confidence Bands | Review Required |
| --- | ---: | ---: | --- | --- | ---: |
| `animals` | 26 | 1.3% | A=1, C=16, D=9 | high=0, medium=13, review=12, inventory=1 | 13 |
| `plants_nature` | 16 | 0.8% | A=5, C=10, D=1 | high=4, medium=9, review=3, inventory=0 | 3 |

## `animals` Top Candidates

| Lemma | Confidence | Band | Tier | Evidence |
| --- | ---: | --- | --- | --- |
| `ave` | 0.798 | `medium` | `C` | `entry_categories:birds` |
| `cordero` | 0.798 | `medium` | `C` | `sense_categories:sheep` |
| `cormorán` | 0.798 | `medium` | `C` | `sense_categories:birds` |
| `desmán` | 0.798 | `medium` | `C` | `entry_categories:animals` |
| `galgo` | 0.798 | `medium` | `C` | `entry_categories:dogs` |
| `ganso` | 0.798 | `medium` | `C` | `entry_categories:birds` |
| `labrador` | 0.798 | `medium` | `C` | `entry_categories:dogs` |
| `lazarillo` | 0.798 | `medium` | `C` | `entry_categories:dogs` |
| `pichón` | 0.798 | `medium` | `C` | `entry_categories:birds` |
| `semental` | 0.798 | `medium` | `C` | `entry_categories:horses` |
| `cachorro` | 0.779 | `medium` | `C` | `entry_categories:baby_animals` |
| `erizo` | 0.779 | `medium` | `C` | `entry_categories:mammals` |

## `plants_nature` Top Candidates

| Lemma | Confidence | Band | Tier | Evidence |
| --- | ---: | --- | --- | --- |
| `cogollo` | 0.9 | `high` | `A` | `sense_topics:botany` |
| `estilo` | 0.9 | `high` | `A` | `sense_topics:botany` |
| `vaina` | 0.9 | `high` | `A` | `sense_topics:botany` |
| `viudo` | 0.9 | `high` | `A` | `sense_topics:botany` |
| `añil` | 0.779 | `medium` | `C` | `entry_categories:plants` |
| `cacao` | 0.779 | `medium` | `C` | `entry_categories:trees` |
| `cocotero` | 0.779 | `medium` | `C` | `entry_categories:trees` |
| `granado` | 0.779 | `medium` | `C` | `entry_categories:trees` |
| `jacinto` | 0.779 | `medium` | `C` | `sense_categories:flowers` |
| `morera` | 0.779 | `medium` | `C` | `sense_categories:plants` |
| `nodo` | 0.779 | `medium` | `C` | `sense_categories:botany` |
| `sauce` | 0.779 | `medium` | `C` | `sense_categories:trees` |

## Broad Exclusions Sample

| Lemma | Excluded Labels |
| --- | --- |
| `más` | `sciences` |
| `poner` | `natural_sciences` |
| `mayor` | `lifestyle` |
| `movimiento` | `lifestyle` |
| `luz` | `natural_sciences, sciences` |
| `sacar` | `hobbies, lifestyle` |
| `área` | `sciences` |
| `resto` | `sciences` |
| `sol` | `natural_sciences` |
| `falta` | `sciences` |
| `jefe` | `hobbies, lifestyle` |
| `reunión` | `hobbies, lifestyle` |

## Limitations

- This audit uses only existing local frequency and Kaikki/Wiktionary data.
- It does not write overlays, mutate packs, or change admission behavior.
- Tier C category allowlists are intentionally narrow.
- Tier D gloss/translation evidence is review-gated and should be sampled before product lift.
