# en-es Animals/Plants Existing Signal Audit

- Status: `ok`
- Decision: `animals_plants_existing_signal_audit_completed`
- Generated: `2026-05-16T22:48:32+00:00`
- Rows measured: `10000`

## Findings

- `PASS` `existing_sources_loaded`: Frequency and Kaikki DBs are available.
- `PASS` `animals_plants_split_enforced`: Botany/plants evidence is reported separately from animal evidence.
- `PASS` `animal_evidence_found`: Existing sources contain animal evidence.
- `PASS` `plants_nature_evidence_found`: Existing sources contain plants/nature evidence.

## Family Summary

| Family | Candidates | Share | Tiers | Confidence Bands | Review Required |
| --- | ---: | ---: | --- | --- | ---: |
| `animals` | 172 | 1.7% | A=14, B=48, C=88, D=22 | high=42, medium=76, review=45, inventory=9 | 52 |
| `plants_nature` | 138 | 1.4% | A=24, B=13, C=93, D=8 | high=22, medium=85, review=28, inventory=3 | 30 |

## `animals` Top Candidates

| Lemma | Confidence | Band | Tier | Evidence |
| --- | ---: | --- | --- | --- |
| `dinosaurio` | 0.9 | `high` | `A` | `sense_topics:zoology` |
| `manada` | 0.9 | `high` | `A` | `sense_topics:zoology` |
| `morena` | 0.9 | `high` | `A` | `sense_topics:zoology` |
| `potro` | 0.9 | `high` | `A` | `sense_topics:zoology` |
| `araña` | 0.855 | `high` | `B` | `translation:primary_translation:spider` |
| `asno` | 0.855 | `high` | `B` | `translation:primary_translation:donkey` |
| `ave` | 0.855 | `high` | `B` | `translation:primary_translation:bird` |
| `ballena` | 0.855 | `high` | `B` | `translation:primary_translation:whale` |
| `bestia` | 0.855 | `high` | `B` | `translation:primary_translation:beast` |
| `burro` | 0.855 | `high` | `B` | `translation:primary_translation:donkey` |
| `can` | 0.855 | `high` | `B` | `translation:primary_translation:dog` |
| `carnero` | 0.855 | `high` | `B` | `translation:primary_translation:sheep` |

## `plants_nature` Top Candidates

| Lemma | Confidence | Band | Tier | Evidence |
| --- | ---: | --- | --- | --- |
| `brote` | 0.9 | `high` | `A` | `sense_topics:botany` |
| `espiga` | 0.9 | `high` | `A` | `sense_topics:botany` |
| `espino` | 0.9 | `high` | `A` | `sense_topics:botany` |
| `fruto` | 0.9 | `high` | `A` | `sense_topics:botany` |
| `goma` | 0.9 | `high` | `A` | `sense_topics:botany` |
| `invernadero` | 0.9 | `high` | `A` | `sense_topics:botany` |
| `planta` | 0.9 | `high` | `A` | `sense_topics:botany` |
| `polen` | 0.9 | `high` | `A` | `sense_topics:botany` |
| `vaina` | 0.9 | `high` | `A` | `sense_topics:botany` |
| `cebada` | 0.855 | `high` | `B` | `translation:primary_translation:barley` |
| `flor` | 0.855 | `high` | `B` | `translation:primary_translation:flower` |
| `hierba` | 0.855 | `high` | `B` | `translation:primary_translation:grass` |

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
