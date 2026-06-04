# en-es Animals/Plants Existing Signal Audit

- Status: `ok`
- Decision: `animals_plants_existing_signal_audit_completed`
- Generated: `2026-05-16T22:48:21+00:00`
- Rows measured: `1984`

## Findings

- `PASS` `existing_sources_loaded`: Frequency and Kaikki DBs are available.
- `PASS` `animals_plants_split_enforced`: Botany/plants evidence is reported separately from animal evidence.
- `PASS` `animal_evidence_found`: Existing sources contain animal evidence.
- `PASS` `plants_nature_evidence_found`: Existing sources contain plants/nature evidence.

## Family Summary

| Family | Candidates | Share | Tiers | Confidence Bands | Review Required |
| --- | ---: | ---: | --- | --- | ---: |
| `animals` | 38 | 1.9% | A=1, B=10, C=24, D=3 | high=8, medium=21, review=7, inventory=2 | 9 |
| `plants_nature` | 22 | 1.1% | A=3, B=1, C=17, D=1 | high=2, medium=16, review=3, inventory=1 | 3 |

## `animals` Top Candidates

| Lemma | Confidence | Band | Tier | Evidence |
| --- | ---: | --- | --- | --- |
| `ave` | 0.855 | `high` | `B` | `translation:primary_translation:bird` |
| `chancho` | 0.855 | `high` | `B` | `translation:primary_translation:pig` |
| `ciervo` | 0.855 | `high` | `B` | `translation:primary_translation:deer` |
| `escarabajo` | 0.855 | `high` | `B` | `translation:primary_translation:beetle` |
| `lagarto` | 0.855 | `high` | `B` | `translation:primary_translation:lizard` |
| `lobo` | 0.855 | `high` | `B` | `translation:primary_translation:wolf` |
| `loro` | 0.855 | `high` | `B` | `translation:primary_translation:parrot` |
| `puerco` | 0.855 | `high` | `B` | `translation:primary_translation:pig` |
| `avispa` | 0.798 | `medium` | `C` | `entry_categories:insects` |
| `chacal` | 0.798 | `medium` | `C` | `entry_categories:canids` |
| `cordero` | 0.798 | `medium` | `C` | `sense_categories:sheep` |
| `cormorán` | 0.798 | `medium` | `C` | `sense_categories:birds` |

## `plants_nature` Top Candidates

| Lemma | Confidence | Band | Tier | Evidence |
| --- | ---: | --- | --- | --- |
| `vaina` | 0.9 | `high` | `A` | `sense_topics:botany` |
| `sauce` | 0.855 | `high` | `B` | `translation:primary_translation:willow` |
| `añil` | 0.779 | `medium` | `C` | `entry_categories:plants` |
| `cacao` | 0.779 | `medium` | `C` | `entry_categories:trees` |
| `cocotero` | 0.779 | `medium` | `C` | `entry_categories:trees` |
| `granado` | 0.779 | `medium` | `C` | `entry_categories:trees` |
| `jacinto` | 0.779 | `medium` | `C` | `sense_categories:flowers` |
| `morera` | 0.779 | `medium` | `C` | `sense_categories:plants` |
| `nodo` | 0.779 | `medium` | `C` | `sense_categories:botany` |
| `vera` | 0.779 | `medium` | `C` | `entry_categories:trees` |
| `estilo` | 0.76 | `medium` | `C` | `entry_categories:plant_anatomy` |
| `canónigo` | 0.741 | `medium` | `C` | `entry_categories:vegetables` |

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
