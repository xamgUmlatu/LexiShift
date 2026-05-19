# en-es Food/Cooking Existing Signal Audit

- Status: `ok`
- Decision: `food_cooking_existing_signal_audit_completed`
- Generated: `2026-05-19T02:36:57+00:00`
- Candidate lemmas measured: `1984`
- Food/cooking candidates: `46`
- Review-required candidates: `42`

## Findings

- `PASS` `existing_sources_loaded`: Frequency and Kaikki DBs are available.
- `PASS` `food_cooking_overlap_allowed`: Food/cooking evidence may overlap animals or plants; overlap is a topic-membership feature, not a conflict.
- `PASS` `food_cooking_evidence_found`: Existing sources contain food/cooking evidence beyond direct sense topics.

## Coverage

- Candidate share: `0.023185`
- Tier counts: `{'A': 2, 'B': 2, 'C': 25, 'D': 17}`
- Confidence bands: `{'high': 2, 'medium': 25, 'review': 9, 'inventory': 10}`

## Top Source Labels

- `food_gloss_pattern`: 14
- `foods`: 7
- `meats`: 6
- `food_translation_pattern`: 3
- `fruits`: 3
- `seafood`: 3
- `cooking`: 2
- `soups`: 2
- `vegetables`: 2
- `primary_translation:tea`: 1
- `primary_translation:cereal`: 1
- `spices`: 1
- `legumes`: 1

## Top Candidates

- `cereal`: `high` 0.855 via `B`
- `té`: `high` 0.855 via `B`
- `chipa`: `medium` 0.817 via `C`
- `empanada`: `medium` 0.817 via `C`
- `ensalada`: `medium` 0.817 via `C`
- `jalea`: `medium` 0.817 via `C`
- `pincho`: `medium` 0.817 via `C`
- `tortilla`: `medium` 0.817 via `C`
- `caldo`: `medium` 0.798 via `C`
- `pimienta`: `medium` 0.798 via `C`
- `puchero`: `medium` 0.798 via `C`
- `erizo`: `medium` 0.779 via `C`
- `langostino`: `medium` 0.779 via `C`
- `mejillón`: `medium` 0.779 via `C`
- `mariposa`: `medium` 0.741 via `C`
- `ave`: `medium` 0.722 via `C`
- `canónigo`: `medium` 0.722 via `C`
- `chancho`: `medium` 0.722 via `C`
- `cogollo`: `medium` 0.722 via `C`
- `damasco`: `medium` 0.722 via `C`

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
