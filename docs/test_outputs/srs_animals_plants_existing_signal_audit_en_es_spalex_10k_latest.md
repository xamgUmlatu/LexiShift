# en-es Animals/Plants Existing Signal Audit

- Status: `ok`
- Decision: `animals_plants_existing_signal_audit_completed`
- Generated: `2026-05-16T21:55:55+00:00`
- Rows measured: `10000`

## Findings

- `PASS` `existing_sources_loaded`: Frequency and Kaikki DBs are available.
- `PASS` `animals_plants_split_enforced`: Botany/plants evidence is reported separately from animal evidence.
- `PASS` `animal_evidence_found`: Existing sources contain animal evidence.
- `PASS` `plants_nature_evidence_found`: Existing sources contain plants/nature evidence.

## Family Summary

| Family | Candidates | Share | Tiers | Confidence Bands | Review Required |
| --- | ---: | ---: | --- | --- | ---: |
| `animals` | 126 | 1.3% | A=14, C=65, D=47 | high=12, medium=57, review=54, inventory=3 | 57 |
| `plants_nature` | 92 | 0.9% | A=29, C=54, D=9 | high=27, medium=53, review=12, inventory=0 | 12 |

## `animals` Top Candidates

| Lemma | Confidence | Band | Tier | Evidence |
| --- | ---: | --- | --- | --- |
| `acompañante` | 0.9 | `high` | `A` | `sense_topics:zoology` |
| `artículo` | 0.9 | `high` | `A` | `sense_topics:zoology` |
| `bonito` | 0.9 | `high` | `A` | `sense_topics:zoology` |
| `broma` | 0.9 | `high` | `A` | `sense_topics:zoology` |
| `cubrir` | 0.9 | `high` | `A` | `sense_topics:zoology` |
| `dinosaurio` | 0.9 | `high` | `A` | `sense_topics:zoology` |
| `listado` | 0.9 | `high` | `A` | `sense_topics:zoology` |
| `manada` | 0.9 | `high` | `A` | `sense_topics:zoology` |
| `manta` | 0.9 | `high` | `A` | `sense_topics:zoology` |
| `morena` | 0.9 | `high` | `A` | `sense_topics:zoology` |
| `potro` | 0.9 | `high` | `A` | `sense_topics:zoology` |
| `reo` | 0.9 | `high` | `A` | `sense_topics:zoology` |

## `plants_nature` Top Candidates

| Lemma | Confidence | Band | Tier | Evidence |
| --- | ---: | --- | --- | --- |
| `brote` | 0.9 | `high` | `A` | `sense_topics:botany` |
| `campanilla` | 0.9 | `high` | `A` | `sense_topics:botany` |
| `cima` | 0.9 | `high` | `A` | `sense_topics:botany` |
| `cogollo` | 0.9 | `high` | `A` | `sense_topics:botany` |
| `cono` | 0.9 | `high` | `A` | `sense_topics:botany` |
| `cultivar` | 0.9 | `high` | `A` | `sense_topics:botany` |
| `cáliz` | 0.9 | `high` | `A` | `sense_topics:botany` |
| `espiga` | 0.9 | `high` | `A` | `sense_topics:botany` |
| `espino` | 0.9 | `high` | `A` | `sense_topics:botany` |
| `estilo` | 0.9 | `high` | `A` | `sense_topics:botany` |
| `fruto` | 0.9 | `high` | `A` | `sense_topics:botany` |
| `goma` | 0.9 | `high` | `A` | `sense_topics:botany` |

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
