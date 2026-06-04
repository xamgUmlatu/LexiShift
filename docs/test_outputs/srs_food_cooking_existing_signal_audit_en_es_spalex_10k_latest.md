# en-es Food/Cooking Existing Signal Audit

- Status: `ok`
- Decision: `food_cooking_existing_signal_audit_completed`
- Generated: `2026-05-19T02:52:37+00:00`
- Candidate lemmas measured: `10000`
- Food/cooking candidates: `265`
- Review-required candidates: `219`

## Findings

- `PASS` `existing_sources_loaded`: Frequency and Kaikki DBs are available.
- `PASS` `food_cooking_overlap_allowed`: Food/cooking evidence may overlap animals or plants; overlap is a topic-membership feature, not a conflict.
- `PASS` `food_cooking_evidence_found`: Existing sources contain food/cooking evidence beyond direct sense topics.

## Coverage

- Candidate share: `0.0265`
- Tier counts: `{'A': 15, 'B': 31, 'C': 122, 'D': 97}`
- Confidence bands: `{'high': 39, 'medium': 117, 'review': 51, 'inventory': 58}`

## Top Source Labels

- `food_gloss_pattern`: 78
- `foods`: 24
- `food_translation_pattern`: 19
- `cooking`: 16
- `meats`: 14
- `fish`: 11
- `vegetables`: 10
- `fruits`: 9
- `seafood`: 8
- `spices_and_herbs`: 6
- `beverages`: 5
- `alcoholic_beverages`: 5
- `soups`: 4
- `food`: 4
- `spices`: 3
- `breads`: 3
- `grains`: 3
- `desserts`: 3
- `sauces`: 3
- `herbs`: 2

## Top Candidates

- `cepa`: `high` 0.95 via `A`
- `leche`: `high` 0.95 via `A`
- `masa`: `high` 0.95 via `A`
- `aceite`: `high` 0.855 via `B`
- `ajo`: `high` 0.855 via `B`
- `alimento`: `high` 0.855 via `B`
- `azúcar`: `high` 0.855 via `B`
- `bebida`: `high` 0.855 via `B`
- `cebolla`: `high` 0.855 via `B`
- `cereal`: `high` 0.855 via `B`
- `cerveza`: `high` 0.855 via `B`
- `cocina`: `high` 0.855 via `C`
- `cocinar`: `high` 0.855 via `C`
- `cocinero`: `high` 0.855 via `C`
- `comida`: `high` 0.855 via `B`
- `fruta`: `high` 0.855 via `B`
- `fría`: `high` 0.855 via `B`
- `harina`: `high` 0.855 via `C`
- `horno`: `high` 0.855 via `C`
- `huevo`: `high` 0.855 via `B`

## Broad Exclusions Sample

- `luz`: anatomy, medicine
- `estilo`: biology, botany
- `sol`: chemistry
- `jefe`: hobbies
- `reunión`: hobbies
- `rostro`: anatomy, medicine
- `piel`: anatomy
- `entrada`: hobbies
- `marcar`: hobbies
- `luchar`: hobbies
- `órgano`: anatomy, biology, medicine
- `creciente`: hobbies
- `cargar`: hobbies
- `estadio`: medicine
- `pista`: hobbies
- `palo`: hobbies
- `titular`: chemistry, hobbies
- `oreja`: anatomy, medicine
- `placa`: medicine
- `calentar`: hobbies
- `garganta`: anatomy, medicine
- `barrera`: hobbies
- `retener`: chemistry
- `campesino`: agriculture

## Limitations

- This audit uses only existing local frequency and Kaikki/Wiktionary data.
- It does not write overlays, mutate packs, or change admission behavior.
- food/cooking can intentionally overlap animals and plants/nature.
- Category-derived food evidence needs review before product lift because many food labels are sense-specific.
