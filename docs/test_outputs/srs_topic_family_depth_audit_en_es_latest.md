# en-es SRS Topic Family Depth Audit

- Status: `ok`
- Decision: `srs_topic_family_depth_audit_completed`
- Generated: `2026-05-19T03:41:52+00:00`
- Frontier count: `2`
- Missing optional frontiers: `0`

## Scope

This is a read-only coverage/depth audit for the product-owned SRS topic/register taxonomy. It does not download sources, write overlays, mutate SRS state, or enable admission lift.

## Findings

- `PASS` `kaikki_signal_source_available`: Kaikki/Wiktionary signal DB exists.
- `PASS` `trusted_topic_families_available:current_cde`: At least one topic family has trusted candidate coverage.
- `PASS` `register_review_signals_available:current_cde`: Register/style has review-only candidate signals.
- `PASS` `trusted_topic_families_available:spalex_10k_research`: At least one topic family has trusted candidate coverage.
- `PASS` `register_review_signals_available:spalex_10k_research`: Register/style has review-only candidate signals.

## Frontier Coverage

### `current_cde`

- exists: `True`
- status: `ok`
- seeds measured: `2000`
- unique lemmas: `1984`

| Family | Axis | State | Trusted Rows | Bands | Max Difficulty | Review-Only Rows | Posture |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| `science_technology` | `topic` | `source_ready` | 120 | 4 | 0.837 | 0 | `measurable_trusted_coverage` |
| `medicine_health` | `topic` | `source_ready` | 43 | 4 | 0.837 | 0 | `measurable_trusted_coverage` |
| `law_politics_civics` | `topic` | `source_ready` | 38 | 3 | 0.876 | 0 | `measurable_trusted_coverage` |
| `sports_fitness` | `topic` | `source_ready` | 33 | 3 | 0.867 | 0 | `measurable_trusted_coverage` |
| `music_media_entertainment` | `topic` | `source_ready` | 28 | 4 | 0.824 | 0 | `measurable_trusted_coverage` |
| `travel_places_transport` | `topic` | `partial` | 27 | 2 | 0.786 | 0 | `measurable_trusted_coverage` |
| `finance_business` | `topic` | `source_ready` | 25 | 4 | 0.828 | 0 | `measurable_trusted_coverage` |
| `games` | `topic` | `source_ready` | 24 | 3 | 0.867 | 0 | `measurable_trusted_coverage` |
| `arts_literature_humanities` | `topic` | `partial` | 23 | 4 | 0.818 | 0 | `measurable_trusted_coverage` |
| `plants_nature` | `topic` | `p0_enrichment` | 5 | 2 | 0.789 | 0 | `thin_trusted_coverage` |
| `food_cooking` | `topic` | `p0_enrichment` | 2 | 2 | 0.821 | 0 | `thin_trusted_coverage` |
| `animals` | `topic` | `p0_enrichment` | 1 | 1 | 0.630 | 0 | `thin_trusted_coverage` |
| `anime_manga_pop_culture` | `topic` | `p0_enrichment` | 0 | 0 | n/a | 0 | `no_trusted_coverage` |
| `hobbies_crafts` | `topic` | `p0_enrichment` | 0 | 0 | n/a | 0 | `no_trusted_coverage` |
| `sat_toefl_exam_prep` | `topic` | `legal_source_gated` | 0 | 0 | n/a | 0 | `no_trusted_coverage` |
| `casual_slang_register` | `register` | `review_only` | 0 | 0 | n/a | 85 | `review_only_signal_available` |
| `formal_professional_register` | `register` | `review_only` | 0 | 0 | n/a | 5 | `review_only_signal_available` |

#### Trusted Examples

- `science_technology`: `entrada` (0.463811), `defecto` (0.55838), `cargar` (0.658392), `quemar` (0.658887), `controlador` (0.72922)
- `medicine_health`: `luz` (0.385492), `corazón` (0.441503), `rostro` (0.447399), `órgano` (0.483237), `estadio` (0.519217)
- `law_politics_civics`: `mayor` (0.427453), `jefe` (0.428496), `demanda` (0.469488), `tropa` (0.478046), `órgano` (0.483237)
- `sports_fitness`: `reunión` (0.437836), `entrada` (0.463811), `pista` (0.523674), `palo` (0.530825), `titular` (0.536097)
- `music_media_entertainment`: `movimiento` (0.383519), `mayor` (0.427453), `orquesta` (0.449716), `órgano` (0.483237), `pista` (0.523674)
- `travel_places_transport`: `mayor` (0.427453), `tren` (0.498631), `derrota` (0.506575), `palo` (0.530825), `bordo` (0.580628)
- `finance_business`: `movimiento` (0.383519), `luz` (0.385492), `capital` (0.414113), `par` (0.467531), `poner` (0.517899)
- `games`: `jefe` (0.428496), `corazón` (0.441503), `entrada` (0.463811), `pista` (0.523674), `palo` (0.530825)
- `arts_literature_humanities`: `auto` (0.507449), `doble` (0.574759), `enano` (0.760857), `sombra` (0.463097), `mosaico` (0.587468)
- `plants_nature`: `estilo` (0.414652), `coral` (0.629617), `vaina` (0.656245), `viudo` (0.716935), `cogollo` (0.789309)
- `food_cooking`: `careta` (0.602102), `batido` (0.820912)
- `animals`: `coral` (0.629617)

#### Register Review-Only Examples

- `casual_slang_register`: `hora` (sense_categories:spanish_colloquialisms, sense_tags:colloquial), `hermano` (sense_categories:spanish_informal_terms, sense_tags:informal), `jefe` (sense_categories:spanish_colloquialisms, sense_tags:colloquial), `cuestión` (sense_categories:spanish_colloquialisms, sense_tags:colloquial), `cuento` (sense_categories:spanish_colloquialisms, sense_tags:colloquial)
- `formal_professional_register`: `mayor` (sense_categories:spanish_literary_terms, sense_tags:literary), `auto` (sense_categories:spanish_formal_terms, sense_tags:formal), `acontecer` (sense_categories:spanish_literary_terms, sense_tags:literary), `revestir` (sense_categories:spanish_formal_terms, sense_tags:formal), `empero` (sense_categories:spanish_formal_terms, sense_tags:formal)

### `spalex_10k_research`

- exists: `True`
- status: `ok`
- seeds measured: `10000`
- unique lemmas: `10000`

| Family | Axis | State | Trusted Rows | Bands | Max Difficulty | Review-Only Rows | Posture |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| `science_technology` | `topic` | `source_ready` | 629 | 4 | 0.609 | 0 | `measurable_trusted_coverage` |
| `law_politics_civics` | `topic` | `source_ready` | 256 | 3 | 0.601 | 0 | `measurable_trusted_coverage` |
| `sports_fitness` | `topic` | `source_ready` | 208 | 3 | 0.601 | 0 | `measurable_trusted_coverage` |
| `music_media_entertainment` | `topic` | `source_ready` | 194 | 2 | 0.315 | 0 | `shallow_difficulty_depth` |
| `medicine_health` | `topic` | `source_ready` | 172 | 2 | 0.308 | 0 | `shallow_difficulty_depth` |
| `arts_literature_humanities` | `topic` | `partial` | 168 | 4 | 0.609 | 0 | `measurable_trusted_coverage` |
| `travel_places_transport` | `topic` | `partial` | 139 | 2 | 0.308 | 0 | `shallow_difficulty_depth` |
| `games` | `topic` | `source_ready` | 109 | 3 | 0.601 | 0 | `measurable_trusted_coverage` |
| `finance_business` | `topic` | `source_ready` | 102 | 2 | 0.314 | 0 | `shallow_difficulty_depth` |
| `plants_nature` | `topic` | `p0_enrichment` | 29 | 1 | 0.151 | 0 | `shallow_difficulty_depth` |
| `animals` | `topic` | `p0_enrichment` | 17 | 2 | 0.306 | 0 | `shallow_difficulty_depth` |
| `food_cooking` | `topic` | `p0_enrichment` | 17 | 2 | 0.312 | 0 | `shallow_difficulty_depth` |
| `anime_manga_pop_culture` | `topic` | `p0_enrichment` | 0 | 0 | n/a | 0 | `no_trusted_coverage` |
| `hobbies_crafts` | `topic` | `p0_enrichment` | 0 | 0 | n/a | 0 | `no_trusted_coverage` |
| `sat_toefl_exam_prep` | `topic` | `legal_source_gated` | 0 | 0 | n/a | 0 | `no_trusted_coverage` |
| `casual_slang_register` | `register` | `review_only` | 0 | 0 | n/a | 488 | `review_only_signal_available` |
| `formal_professional_register` | `register` | `review_only` | 0 | 0 | n/a | 41 | `review_only_signal_available` |

#### Trusted Examples

- `science_technology`: `entrada` (0.000209), `defecto` (0.000641), `controlador` (0.002736), `pincho` (0.003703), `vida` (0.004283)
- `law_politics_civics`: `jefe` (0.000122), `demanda` (0.000228), `tropa` (0.000255), `órgano` (0.000273), `competencia` (0.000275)
- `sports_fitness`: `reunión` (0.000141), `entrada` (0.000209), `pista` (0.000441), `palo` (0.000475), `titular` (0.000504)
- `music_media_entertainment`: `movimiento` (6.2e-05), `orquesta` (0.000168), `órgano` (0.000273), `pista` (0.000441), `palo` (0.000475)
- `medicine_health`: `luz` (6.4e-05), `corazón` (0.000149), `rostro` (0.000163), `órgano` (0.000273), `estadio` (0.000421)
- `arts_literature_humanities`: `auto` (0.000367), `pie` (0.005291), `género` (0.005341), `concepto` (0.005438), `metro` (0.006482)
- `travel_places_transport`: `tren` (0.000333), `derrota` (0.000363), `palo` (0.000475), `bordo` (0.000795), `propulsión` (0.001753)
- `games`: `jefe` (0.000122), `corazón` (0.000149), `entrada` (0.000209), `pista` (0.000441), `palo` (0.000475)
- `finance_business`: `movimiento` (6.2e-05), `luz` (6.4e-05), `capital` (9.7e-05), `par` (0.000219), `pista` (0.000441)
- `plants_nature`: `estilo` (9.9e-05), `coral` (0.001228), `vaina` (0.001547), `cogollo` (0.004054), `planta` (0.00573)
- `animals`: `coral` (0.001228), `artículo` (0.004918), `pico` (0.00772), `reo` (0.010406), `bonito` (0.011618)
- `food_cooking`: `careta` (0.000962), `menudo` (0.005528), `masa` (0.006372), `duro` (0.006955), `leche` (0.007319)

#### Register Review-Only Examples

- `casual_slang_register`: `hora` (sense_categories:spanish_colloquialisms, sense_tags:colloquial), `hermano` (sense_categories:spanish_informal_terms, sense_tags:informal), `jefe` (sense_categories:spanish_colloquialisms, sense_tags:colloquial), `cuestión` (sense_categories:spanish_colloquialisms, sense_tags:colloquial), `cuento` (sense_categories:spanish_colloquialisms, sense_tags:colloquial)
- `formal_professional_register`: `auto` (sense_categories:spanish_formal_terms, sense_tags:formal), `haber` (sense_categories:spanish_formal_terms, sense_tags:formal), `presente` (sense_categories:spanish_formal_terms, sense_tags:formal), `acceso` (sense_categories:spanish_formal_terms, sense_tags:formal), `matrimonio` (sense_categories:spanish_formal_terms, sense_tags:formal)

## Limitations

- This audit is read-only and does not create overlays, mutate packs, or publish SRS sets.
- Trusted family coverage uses explicit sense-topic-style evidence only.
- Register/style rows are inventoried as review-only candidates and are not profile-admission proof.
- Difficulty depth uses the current admission-weight proxy, not a calibrated CEFR or learner-level model.
- Optional research frontiers are reported as unavailable if their local SQLite path is absent; the audit does not download or rebuild them.
