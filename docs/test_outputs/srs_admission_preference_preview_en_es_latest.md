# SRS Admission Preference Preview - en-es

- Status: PASS
- Findings: pass=16 warn=0 fail=0
- Frequency DB rows: 4123
- Base frequency DB rows: 2000
- Runtime scope: admission_preview_only

## Inputs

- frequency_db: `/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift/frequency_packs/freq-es-cde.sqlite`
- preview_frequency_db: `/var/folders/4d/050gvyq54p97jbx1nh5rlhk00000gn/T/lexishift-srs-pref-preview-jwajd3w0/srs-admission-lab-zipf-augmented.sqlite`
- merged_overlay_source_path: `/var/folders/4d/050gvyq54p97jbx1nh5rlhk00000gn/T/lexishift-srs-pref-preview-jwajd3w0/srs-admission-lab-merged-topic-overlay.json`
- set_top_n: 10000
- initial_active_count: 120
- preview_count: 20

## Source Augmentation

- status: `applied`
- output_row_count: 4123
- added_row_count: 2139
- overlay_topic_lemma_count: 1012
- overlay_missing_without_bridge_count: 489

## Scenario Summary

| Scenario | Topic movers | Overlay application | Top lemmas |
| --- | ---: | --- | --- |
| neutral | 0 | n/a | como, este, sobre, dos, bien, hacer, nada, parte |
| animals_interest | 20 | applied | perro, animal, gato, lobo, pez, vaca, tigre, mono |
| animals_light_weight | 3 | applied | perro, animal, gato, como, este, sobre, dos, bien |
| plants_nature_interest | 17 | applied | árbol, flor, hierba, pino, parra, roble, cebada, planta |
| food_cooking_interest | 20 | applied | agua, comida, carne, pan, leche, cerveza, huevo, aceite |
| medicine_health_interest | 20 | applied | mano, cabeza, cara, media, boca, vía, simple, miembro |
| finance_business_interest | 20 | applied | punto, derecho, seguro, tierra, capital, plaza, valor, interés |
| sports_fitness_interest | 20 | applied | final, largo, escuela, serie, campo, resultado, puerta, defensa |
| games_interest | 20 | applied | juego, rey, comer, color, muerto, copa, reina, torre |
| music_media_entertainment_interest | 20 | applied | bajo, grupo, música, película, canción, natural, televisión, accidente |
| law_politics_civics_interest | 20 | applied | parte, general, ley, sistema, número, cuerpo, proceso, orden |
| science_technology_interest | 20 | applied | vida, salida, función, cadena, plataforma, cliente, motor, ventana |
| travel_places_transport_interest | 20 | applied | país, ciudad, camino, calle, viaje, hotel, aeropuerto, frontera |
| animals_high_proficiency | 0 | applied | oh, hola, ésa, nabab, vos, debacle, según, pues |
| animals_plants_interest | 20 | applied | perro, animal, gato, árbol, flor, lobo, pez, vaca |
| weighted_plants_over_animals | 20 | applied | árbol, flor, hierba, pino, parra, roble, cebada, planta |

## Findings

- PASS: `FREQUENCY_DB_READABLE` - Frequency DB has 4123 rows.
- PASS: `ZIPF_AUGMENTED_LAB_SOURCE_AVAILABLE` - Dev-only Zipf bridge source was applied for the preference preview.
- PASS: `ANIMALS_INTEREST_MOVES_ADMISSION` - animals preference produced 20 topic movers in the admission preview.
- PASS: `PLANTS_NATURE_INTEREST_MOVES_ADMISSION` - plants_nature preference produced 17 topic movers in the admission preview.
- PASS: `FOOD_COOKING_INTEREST_MOVES_ADMISSION` - food_cooking preference produced 20 topic movers in the admission preview.
- PASS: `MEDICINE_HEALTH_INTEREST_MOVES_ADMISSION` - medicine_health preference produced 20 topic movers in the admission preview.
- PASS: `FINANCE_BUSINESS_INTEREST_MOVES_ADMISSION` - finance_business preference produced 20 topic movers in the admission preview.
- PASS: `SPORTS_FITNESS_INTEREST_MOVES_ADMISSION` - sports_fitness preference produced 20 topic movers in the admission preview.
- PASS: `GAMES_INTEREST_MOVES_ADMISSION` - games preference produced 20 topic movers in the admission preview.
- PASS: `MUSIC_MEDIA_ENTERTAINMENT_INTEREST_MOVES_ADMISSION` - music_media_entertainment preference produced 20 topic movers in the admission preview.
- PASS: `LAW_POLITICS_CIVICS_INTEREST_MOVES_ADMISSION` - law_politics_civics preference produced 20 topic movers in the admission preview.
- PASS: `SCIENCE_TECHNOLOGY_INTEREST_MOVES_ADMISSION` - science_technology preference produced 20 topic movers in the admission preview.
- PASS: `TRAVEL_BETA_TOPIC_EXPOSES_LIMIT` - Travel/place/transport preference produced runtime movers.
- PASS: `SCALAR_TOPIC_WEIGHTS_AFFECT_PRIORITY` - Weighted plants-over-animals profile surfaces plants/nature movers.
- PASS: `TOPIC_STRENGTH_IS_MONOTONIC_IN_SMOKE` - Full animals preference produced at least as many topic movers as light animals weight.
- PASS: `HIGH_PROFICIENCY_SUPPRESSES_TOO_EASY_TOPIC_ITEMS` - High-proficiency animals scenario suppressed too-easy animal movers.

## Top Topic Movers

### animals_interest
- perro: base_rank=347, reranked_rank=1, delta=346, source=topic_hint:animals
- animal: base_rank=514, reranked_rank=2, delta=512, source=topic_hint:animals
- gato: base_rank=573, reranked_rank=3, delta=570, source=topic_hint:animals
- lobo: base_rank=966, reranked_rank=4, delta=962, source=topic_hint:animals
- pez: base_rank=976, reranked_rank=5, delta=971, source=topic_hint:animals
- vaca: base_rank=1021, reranked_rank=6, delta=1015, source=topic_hint:animals
- tigre: base_rank=1033, reranked_rank=7, delta=1026, source=topic_hint:animals
- mono: base_rank=1039, reranked_rank=8, delta=1031, source=topic_hint:animals

### animals_light_weight
- perro: base_rank=347, reranked_rank=1, delta=346, source=topic_hint:animals
- animal: base_rank=514, reranked_rank=2, delta=512, source=topic_hint:animals
- gato: base_rank=573, reranked_rank=3, delta=570, source=topic_hint:animals

### plants_nature_interest
- árbol: base_rank=611, reranked_rank=1, delta=610, source=topic_hint:plants_nature
- flor: base_rank=705, reranked_rank=2, delta=703, source=topic_hint:plants_nature
- hierba: base_rank=1137, reranked_rank=3, delta=1134, source=topic_hint:plants_nature
- pino: base_rank=1210, reranked_rank=4, delta=1206, source=topic_hint:plants_nature
- parra: base_rank=1397, reranked_rank=5, delta=1392, source=topic_hint:plants_nature
- roble: base_rank=1488, reranked_rank=6, delta=1482, source=topic_hint:plants_nature
- cebada: base_rank=1636, reranked_rank=7, delta=1629, source=topic_hint:plants_nature
- planta: base_rank=411, reranked_rank=8, delta=403, source=topic_hint:plants_nature

### food_cooking_interest
- agua: base_rank=61, reranked_rank=1, delta=60, source=topic_hint:food_cooking
- comida: base_rank=188, reranked_rank=2, delta=186, source=topic_hint:food_cooking
- carne: base_rank=390, reranked_rank=3, delta=387, source=topic_hint:food_cooking
- pan: base_rank=401, reranked_rank=4, delta=397, source=topic_hint:food_cooking
- leche: base_rank=457, reranked_rank=5, delta=452, source=topic_hint:food_cooking
- cerveza: base_rank=662, reranked_rank=6, delta=656, source=topic_hint:food_cooking
- huevo: base_rank=676, reranked_rank=7, delta=669, source=topic_hint:food_cooking
- aceite: base_rank=707, reranked_rank=8, delta=699, source=topic_hint:food_cooking

### medicine_health_interest
- mano: base_rank=91, reranked_rank=1, delta=90, source=topic_hint:medicine_health
- cabeza: base_rank=105, reranked_rank=2, delta=103, source=topic_hint:medicine_health
- cara: base_rank=132, reranked_rank=3, delta=129, source=topic_hint:medicine_health
- media: base_rank=170, reranked_rank=4, delta=166, source=topic_hint:medicine_health
- boca: base_rank=258, reranked_rank=5, delta=253, source=topic_hint:medicine_health
- vía: base_rank=286, reranked_rank=6, delta=280, source=topic_hint:medicine_health
- simple: base_rank=305, reranked_rank=7, delta=298, source=topic_hint:medicine_health
- miembro: base_rank=364, reranked_rank=8, delta=356, source=topic_hint:medicine_health

### finance_business_interest
- punto: base_rank=60, reranked_rank=1, delta=59, source=topic_hint:finance_business
- derecho: base_rank=75, reranked_rank=2, delta=73, source=topic_hint:finance_business
- seguro: base_rank=88, reranked_rank=3, delta=85, source=topic_hint:finance_business
- tierra: base_rank=101, reranked_rank=4, delta=97, source=topic_hint:finance_business
- capital: base_rank=139, reranked_rank=5, delta=134, source=topic_hint:finance_business
- plaza: base_rank=201, reranked_rank=6, delta=195, source=topic_hint:finance_business
- valor: base_rank=203, reranked_rank=7, delta=196, source=topic_hint:finance_business
- interés: base_rank=217, reranked_rank=8, delta=209, source=topic_hint:finance_business

### sports_fitness_interest
- final: base_rank=58, reranked_rank=1, delta=57, source=topic_hint:sports_fitness
- largo: base_rank=116, reranked_rank=2, delta=114, source=topic_hint:sports_fitness
- escuela: base_rank=136, reranked_rank=3, delta=133, source=topic_hint:sports_fitness
- serie: base_rank=154, reranked_rank=4, delta=150, source=topic_hint:sports_fitness
- campo: base_rank=173, reranked_rank=5, delta=168, source=topic_hint:sports_fitness
- resultado: base_rank=211, reranked_rank=6, delta=205, source=topic_hint:sports_fitness
- puerta: base_rank=239, reranked_rank=7, delta=232, source=topic_hint:sports_fitness
- defensa: base_rank=242, reranked_rank=8, delta=234, source=topic_hint:sports_fitness

### games_interest
- juego: base_rank=90, reranked_rank=1, delta=89, source=topic_hint:games
- rey: base_rank=149, reranked_rank=2, delta=147, source=topic_hint:games
- comer: base_rank=226, reranked_rank=3, delta=223, source=topic_hint:games
- color: base_rank=241, reranked_rank=4, delta=237, source=topic_hint:games
- muerto: base_rank=319, reranked_rank=5, delta=314, source=topic_hint:games
- copa: base_rank=381, reranked_rank=6, delta=375, source=topic_hint:games
- reina: base_rank=423, reranked_rank=7, delta=416, source=topic_hint:games
- torre: base_rank=666, reranked_rank=8, delta=658, source=topic_hint:games

### music_media_entertainment_interest
- bajo: base_rank=44, reranked_rank=1, delta=43, source=topic_hint:music_media_entertainment
- grupo: base_rank=45, reranked_rank=2, delta=43, source=topic_hint:music_media_entertainment
- música: base_rank=147, reranked_rank=3, delta=144, source=topic_hint:music_media_entertainment
- película: base_rank=178, reranked_rank=4, delta=174, source=topic_hint:music_media_entertainment
- canción: base_rank=240, reranked_rank=5, delta=235, source=topic_hint:music_media_entertainment
- natural: base_rank=261, reranked_rank=6, delta=255, source=topic_hint:music_media_entertainment
- televisión: base_rank=284, reranked_rank=7, delta=277, source=topic_hint:music_media_entertainment
- accidente: base_rank=497, reranked_rank=8, delta=489, source=topic_hint:music_media_entertainment

### law_politics_civics_interest
- parte: base_rank=8, reranked_rank=1, delta=7, source=topic_hint:law_politics_civics
- general: base_rank=38, reranked_rank=2, delta=36, source=topic_hint:law_politics_civics
- ley: base_rank=41, reranked_rank=3, delta=38, source=topic_hint:law_politics_civics
- sistema: base_rank=50, reranked_rank=4, delta=46, source=topic_hint:law_politics_civics
- número: base_rank=71, reranked_rank=5, delta=66, source=topic_hint:law_politics_civics
- cuerpo: base_rank=102, reranked_rank=6, delta=96, source=topic_hint:law_politics_civics
- proceso: base_rank=112, reranked_rank=7, delta=105, source=topic_hint:law_politics_civics
- orden: base_rank=117, reranked_rank=8, delta=109, source=topic_hint:law_politics_civics

### science_technology_interest
- vida: base_rank=11, reranked_rank=1, delta=10, source=topic_hint:science_technology
- salida: base_rank=367, reranked_rank=2, delta=365, source=topic_hint:science_technology
- función: base_rank=369, reranked_rank=3, delta=366, source=topic_hint:science_technology
- cadena: base_rank=449, reranked_rank=4, delta=445, source=topic_hint:science_technology
- plataforma: base_rank=524, reranked_rank=5, delta=519, source=topic_hint:science_technology
- cliente: base_rank=589, reranked_rank=6, delta=583, source=topic_hint:science_technology
- motor: base_rank=594, reranked_rank=7, delta=587, source=topic_hint:science_technology
- ventana: base_rank=649, reranked_rank=8, delta=641, source=topic_hint:science_technology

### travel_places_transport_interest
- país: base_rank=27, reranked_rank=1, delta=26, source=topic_hint:travel_places_transport
- ciudad: base_rank=33, reranked_rank=2, delta=31, source=topic_hint:travel_places_transport
- camino: base_rank=123, reranked_rank=3, delta=120, source=topic_hint:travel_places_transport
- calle: base_rank=131, reranked_rank=4, delta=127, source=topic_hint:travel_places_transport
- viaje: base_rank=214, reranked_rank=5, delta=209, source=topic_hint:travel_places_transport
- hotel: base_rank=414, reranked_rank=6, delta=408, source=topic_hint:travel_places_transport
- aeropuerto: base_rank=447, reranked_rank=7, delta=440, source=topic_hint:travel_places_transport
- frontera: base_rank=456, reranked_rank=8, delta=448, source=topic_hint:travel_places_transport

### animals_plants_interest
- perro: base_rank=347, reranked_rank=1, delta=346, source=topic_hint:animals
- animal: base_rank=514, reranked_rank=2, delta=512, source=topic_hint:animals
- gato: base_rank=573, reranked_rank=3, delta=570, source=topic_hint:animals
- árbol: base_rank=611, reranked_rank=4, delta=607, source=topic_hint:plants_nature
- flor: base_rank=705, reranked_rank=5, delta=700, source=topic_hint:plants_nature
- lobo: base_rank=966, reranked_rank=6, delta=960, source=topic_hint:animals
- pez: base_rank=976, reranked_rank=7, delta=969, source=topic_hint:animals
- vaca: base_rank=1021, reranked_rank=8, delta=1013, source=topic_hint:animals

### weighted_plants_over_animals
- árbol: base_rank=611, reranked_rank=1, delta=610, source=topic_hint:plants_nature
- flor: base_rank=705, reranked_rank=2, delta=703, source=topic_hint:plants_nature
- hierba: base_rank=1137, reranked_rank=3, delta=1134, source=topic_hint:plants_nature
- pino: base_rank=1210, reranked_rank=4, delta=1206, source=topic_hint:plants_nature
- parra: base_rank=1397, reranked_rank=5, delta=1392, source=topic_hint:plants_nature
- roble: base_rank=1488, reranked_rank=6, delta=1482, source=topic_hint:plants_nature
- cebada: base_rank=1636, reranked_rank=7, delta=1629, source=topic_hint:plants_nature
- planta: base_rank=411, reranked_rank=8, delta=403, source=topic_hint:plants_nature
