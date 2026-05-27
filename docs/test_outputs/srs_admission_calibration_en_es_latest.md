# SRS Admission Calibration - en-es

- Status: WARN
- Findings: pass=6 warn=1 fail=0
- Admission budget: 10
- Top-k window: 60
- Weighted seeds: 11, 23, 37
- Source rows: 4123

## How To Read

- Ranked share is the deterministic topic-matching share of the preview admission batch.
- Full-pool weighted share samples from the whole candidate pool and is diagnostic only.
- Top-k weighted share samples from the ranked window, preserving variety without using the whole pool.
- Reserved lane share uses the real profile-bootstrap policy with topic slots plus general slots.
- Reserved lane expected count is derived from topic strength, lane cap, and ranked-window topic capacity.
- These values are calibration diagnostics, not hard product guarantees.

## Ranked Admission Batch Shares

| Scenario | Active topics | Topic share | Topic count | Avg difficulty | Avg readiness | Top lemmas |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| neutral | none | 0.000 | 0 | 0.000 | 1.000 | como, este, sobre, dos, bien, hacer, nada, parte |
| animals_interest | animals | 1.000 | 10 | 0.034 | 1.000 | perro, ganado, animal, gato, pollo, toro, lobo, pez |
| animals_light_weight | animals | 0.500 | 5 | 0.010 | 1.000 | perro, ganado, animal, gato, reina, como, este, sobre |
| plants_nature_interest | plants_nature | 1.000 | 10 | 0.056 | 1.000 | haya, árbol, flor, hierba, col, pino, parra, plátano |
| food_cooking_interest | food_cooking | 1.000 | 10 | 0.021 | 1.000 | agua, comida, carne, pan, leche, cerveza, huevo, aceite |
| medicine_health_interest | medicine_health | 1.000 | 10 | 0.011 | 1.000 | mano, cabeza, cara, media, boca, vía, simple, miembro |
| finance_business_interest | finance_business | 1.000 | 10 | 0.007 | 1.000 | punto, derecho, seguro, tierra, capital, plaza, valor, interés |
| sports_fitness_interest | sports_fitness | 1.000 | 10 | 0.009 | 1.000 | final, largo, escuela, serie, campo, resultado, puerta, defensa |
| games_interest | games | 1.000 | 10 | 0.019 | 1.000 | juego, rey, comer, color, muerto, copa, torre, columna |
| music_media_entertainment_interest | music_media_entertainment | 1.000 | 10 | 0.012 | 1.000 | bajo, grupo, música, película, canción, natural, televisión, accidente |
| law_politics_civics_interest | law_politics_civics | 1.000 | 10 | 0.004 | 1.000 | parte, general, ley, sistema, número, cuerpo, proceso, orden |
| science_technology_interest | science_technology | 1.000 | 10 | 0.021 | 1.000 | vida, salida, función, cadena, plataforma, cliente, motor, ventana |
| travel_places_transport_interest | travel_places_transport | 1.000 | 10 | 0.012 | 1.000 | país, ciudad, camino, calle, viaje, hotel, aeropuerto, frontera |
| animals_high_proficiency | animals | 0.000 | 0 | 0.646 | 0.999 | oh, hola, ésa, nabab, vos, debacle, según, pues |
| animals_plants_interest | animals, plants_nature | 1.000 | 10 | 0.026 | 1.000 | haya, perro, ganado, animal, gato, árbol, flor, pollo |
| weighted_plants_over_animals | animals, plants_nature | 1.000 | 10 | 0.056 | 1.000 | haya, árbol, flor, hierba, col, pino, parra, plátano |

## Weighted Admission Batch Shares

| Scenario | Mean topic share | Range | Mean topic count | Frequent lemmas |
| --- | ---: | --- | ---: | --- |
| animals_high_proficiency | 0.000 | 0.000-0.000 | 0.000 | para(2), mudez(2), informador(2), siempre(2), femineidad(1), mazurca(1), monoclonal(1), fríamente(1) |
| animals_interest | 0.000 | 0.000-0.000 | 0.000 | invierno(1), caudillo(1), hindú(1), arado(1), urraca(1), protocolo(1), solo(1), dorsal(1) |
| animals_light_weight | 0.000 | 0.000-0.000 | 0.000 | fotografía(1), oasis(1), protestante(1), abreviatura(1), trombón(1), realista(1), péndulo(1), evidente(1) |
| animals_plants_interest | 0.000 | 0.000-0.000 | 0.000 | deuda(1), camarero(1), demolición(1), recado(1), finlandés(1), jurisdicción(1), potasio(1), hall(1) |
| finance_business_interest | 0.000 | 0.000-0.000 | 0.000 | moneda(1), calabaza(1), tranvía(1), cesto(1), indonesio(1), leña(1), pecador(1), horrible(1) |
| food_cooking_interest | 0.000 | 0.000-0.000 | 0.000 | cliente(1), escopeta(1), zinc(1), urraca(1), rezagado(1), realista(1), fuero(1), evidente(1) |
| games_interest | 0.033 | 0.000-0.100 | 0.333 | correr(1), notario(1), abeja(1), argelino(1), fisonomía(1), fluido(1), interferencia(1), cargar(1) |
| law_politics_civics_interest | 0.000 | 0.000-0.000 | 0.000 | agencia(1), asma(1), grieta(1), romería(1), farsante(1), pensador(1), lagarto(1), delantera(1) |
| medicine_health_interest | 0.033 | 0.000-0.100 | 0.333 | ayuntamiento(1), caucho(1), sintomático(1), propulsión(1), avispa(1), humano(1), arquero(1), divertido(1) |
| music_media_entertainment_interest | 0.000 | 0.000-0.000 | 0.000 | cliente(1), calabaza(1), reja(1), cándido(1), merluza(1), peste(1), temática(1), reflector(1) |
| neutral | 0.000 | 0.000-0.000 | 0.000 | rostro(1), celo(1), pleito(1), frontón(1), faisán(1), superioridad(1), caldera(1), ladrido(1) |
| plants_nature_interest | 0.000 | 0.000-0.000 | 0.000 | motor(1), patriarca(1), abeja(1), cantábrico(1), rezagado(1), ácido(1), guaraní(1), evidente(1) |
| science_technology_interest | 0.000 | 0.000-0.000 | 0.000 | toque(1), patriarca(1), escultor(1), finlandés(1), fisonomía(1), oponente(1), pecador(1), profundo(1) |
| sports_fitness_interest | 0.000 | 0.000-0.000 | 0.000 | miércoles(1), asma(1), garra(1), reparo(1), cándido(1), motivación(1), prólogo(1), flagelo(1) |
| travel_places_transport_interest | 0.000 | 0.000-0.000 | 0.000 | tío(1), escopeta(1), zinc(1), abreviatura(1), neerlandés(1), amplitud(1), tal(1), vello(1) |
| weighted_plants_over_animals | 0.000 | 0.000-0.000 | 0.000 | cerebro(1), mostrador(1), cilindro(1), cándido(1), merluza(1), leña(1), mismo(1), magnetismo(1) |

## Top-K Weighted Admission Shares

| Scenario | Mean topic share | Range | Mean topic count | Frequent lemmas |
| --- | ---: | --- | ---: | --- |
| animals_high_proficiency | 0.000 | 0.000-0.000 | 0.000 | ucraniano(3), parpadeante(2), cosmogonía(2), repelar(2), ávidamente(2), húngara(1), neerlandesa(1), oficializar(1) |
| animals_interest | 1.000 | 1.000-1.000 | 10.000 | cuervo(2), sapo(2), faisán(2), atún(2), insecto(2), oveja(2), rana(1), tigre(1) |
| animals_light_weight | 0.033 | 0.000-0.100 | 0.333 | gobierno(3), caso(2), fin(2), hecho(2), bueno(2), contra(1), bien(1), país(1) |
| animals_plants_interest | 1.000 | 1.000-1.000 | 10.000 | pino(2), parra(2), gaviota(2), cabra(2), gata(2), elefante(2), araña(1), lobo(1) |
| finance_business_interest | 0.767 | 0.700-0.800 | 7.667 | propulsión(3), cargo(2), revés(2), día(2), radio(2), ejercicio(2), red(1), siete(1) |
| food_cooking_interest | 0.600 | 0.500-0.700 | 6.000 | tomate(3), uva(2), menú(2), contra(2), sobre(2), maíz(2), patata(1), queso(1) |
| games_interest | 0.767 | 0.700-0.800 | 7.667 | león(3), túnel(2), plancha(2), año(2), penal(2), palo(2), muerto(2), sencillo(1) |
| law_politics_civics_interest | 1.000 | 1.000-1.000 | 10.000 | naranja(3), instrumento(2), caballería(2), metal(2), perla(2), protesta(1), acción(1), anillo(1) |
| medicine_health_interest | 1.000 | 1.000-1.000 | 10.000 | arteria(3), faz(2), costilla(2), labio(2), ataque(2), mejilla(1), cerebro(1), frente(1) |
| music_media_entertainment_interest | 0.767 | 0.700-0.800 | 7.667 | ronda(3), trombón(2), sencillo(2), año(2), accidental(2), orquesta(2), canción(2), metal(1) |
| neutral | 0.000 | 0.000-0.000 | 0.000 | momento(3), poder(2), lado(2), país(2), historia(2), casa(1), día(1), bueno(1) |
| plants_nature_interest | 0.367 | 0.300-0.500 | 3.667 | nada(2), nuevo(2), granado(2), sobre(2), tiempo(2), dos(2), manzano(1), calabaza(1) |
| science_technology_interest | 0.367 | 0.300-0.500 | 3.667 | este(3), menú(2), hacer(2), caso(2), parte(2), plataforma(2), controlador(1), mandato(1) |
| sports_fitness_interest | 1.000 | 1.000-1.000 | 10.000 | ataque(3), carrera(2), guardia(2), volante(2), cuadro(2), relevo(1), deporte(1), registro(1) |
| travel_places_transport_interest | 0.433 | 0.400-0.500 | 4.333 | como(3), tranvía(2), casa(2), nada(2), billete(2), viaje(2), dos(1), visado(1) |
| weighted_plants_over_animals | 0.900 | 0.800-1.000 | 9.000 | gato(3), manzano(2), como(2), granado(2), pez(2), col(2), perro(1), calabaza(1) |

## Reserved Topic-Lane Policy

| Scenario | Active topics | Topic share | Topic count | Expected | Window topic candidates | Status | Top lemmas |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| neutral | none | 0.000 | 0 | 0 | 0 | matches | como, este, sobre, dos, bien, hacer, nada, parte |
| animals_interest | animals | 0.500 | 5 | 5 | 60 | matches | perro, ganado, animal, gato, pollo, como, este, sobre |
| animals_light_weight | animals | 0.100 | 1 | 1 | 5 | matches | perro, como, este, sobre, dos, bien, hacer, nada |
| plants_nature_interest | plants_nature | 0.500 | 5 | 5 | 27 | matches | haya, árbol, flor, hierba, col, como, este, sobre |
| food_cooking_interest | food_cooking | 0.500 | 5 | 5 | 33 | matches | agua, comida, carne, pan, leche, como, este, sobre |
| medicine_health_interest | medicine_health | 0.500 | 5 | 5 | 60 | matches | mano, cabeza, cara, media, boca, como, este, sobre |
| finance_business_interest | finance_business | 0.500 | 5 | 5 | 46 | matches | punto, derecho, seguro, tierra, capital, como, este, sobre |
| sports_fitness_interest | sports_fitness | 0.500 | 5 | 5 | 60 | matches | final, largo, escuela, serie, campo, como, este, sobre |
| games_interest | games | 0.500 | 5 | 5 | 41 | matches | juego, rey, comer, color, muerto, como, este, sobre |
| music_media_entertainment_interest | music_media_entertainment | 0.500 | 5 | 5 | 41 | matches | bajo, grupo, música, película, canción, como, este, sobre |
| law_politics_civics_interest | law_politics_civics | 0.500 | 5 | 5 | 60 | matches | parte, general, ley, sistema, número, como, este, sobre |
| science_technology_interest | science_technology | 0.500 | 5 | 5 | 28 | matches | vida, salida, función, cadena, plataforma, como, este, sobre |
| travel_places_transport_interest | travel_places_transport | 0.500 | 5 | 5 | 29 | matches | país, ciudad, camino, calle, viaje, como, este, sobre |
| animals_high_proficiency | animals | 0.000 | 0 | 0 | 0 | matches | oh, hola, ésa, nabab, vos, debacle, según, pues |
| animals_plants_interest | animals, plants_nature | 0.500 | 5 | 5 | 60 | matches | haya, perro, ganado, animal, gato, como, este, sobre |
| weighted_plants_over_animals | animals, plants_nature | 0.500 | 5 | 5 | 55 | matches | haya, árbol, flor, hierba, col, como, este, sobre |

## Topic Support

### animals_interest
- animals: candidates=80, support_mass=68.106, examples=perro, ganado, animal, gato, pollo

### animals_light_weight
- animals: candidates=80, support_mass=68.106, examples=perro, ganado, animal, gato, pollo

### plants_nature_interest
- plants_nature: candidates=28, support_mass=23.447, examples=haya, árbol, flor, hierba, col

### food_cooking_interest
- food_cooking: candidates=35, support_mass=31.306, examples=agua, comida, carne, pan, leche

### medicine_health_interest
- medicine_health: candidates=90, support_mass=71.477, examples=mano, cabeza, cara, media, boca

### finance_business_interest
- finance_business: candidates=51, support_mass=42.412, examples=punto, derecho, seguro, tierra, capital

### sports_fitness_interest
- sports_fitness: candidates=103, support_mass=73.061, examples=final, largo, escuela, serie, campo

### games_interest
- games: candidates=56, support_mass=37.551, examples=juego, rey, comer, color, muerto

### music_media_entertainment_interest
- music_media_entertainment: candidates=44, support_mass=35.955, examples=bajo, grupo, música, película, canción

### law_politics_civics_interest
- law_politics_civics: candidates=108, support_mass=84.074, examples=parte, general, ley, sistema, número

### science_technology_interest
- science_technology: candidates=39, support_mass=30.814, examples=vida, salida, función, cadena, plataforma

### travel_places_transport_interest
- travel_places_transport: candidates=30, support_mass=27.727, examples=país, ciudad, camino, calle, viaje

### animals_high_proficiency
- animals: candidates=80, support_mass=68.106, examples=perro, ganado, animal, gato, pollo

### animals_plants_interest
- animals: candidates=80, support_mass=68.106, examples=perro, ganado, animal, gato, pollo
- plants_nature: candidates=28, support_mass=23.447, examples=haya, árbol, flor, hierba, col

### weighted_plants_over_animals
- plants_nature: candidates=28, support_mass=23.447, examples=haya, árbol, flor, hierba, col
- animals: candidates=80, support_mass=68.106, examples=perro, ganado, animal, gato, pollo

## Findings

- PASS: `CALIBRATION_PREVIEWS_HAVE_NO_FAILURES` - Ranked and weighted admission previews completed without FAIL findings.
- PASS: `RANKED_TOPIC_STRENGTH_MONOTONIC` - Ranked animals topic share is monotonic from neutral to light to strong.
- WARN: `WEIGHTED_TOPIC_STRENGTH_MONOTONIC` - Weighted animals topic share did not become visible in the seeded samples; the full-pool weighted policy may be too diffuse for topic preferences.
- PASS: `TOP_K_WEIGHTED_TOPIC_SIGNAL_VISIBLE` - Top-k weighted sampling makes the animals preference visible.
- PASS: `RESERVED_TOPIC_LANE_PRODUCES_MIXED_TOPIC_BATCH` - Reserved topic-lane policy produces a meaningful but mixed animals batch.
- PASS: `RESERVED_TOPIC_LANE_MATCHES_EXPECTED_CAPACITY` - Reserved topic-lane observed counts match the policy expectation derived from topic strength and ranked-window topic capacity.
- PASS: `HIGH_PROFICIENCY_TRADEOFF_VISIBLE` - High-proficiency animals calibration exposes whether readiness suppresses too-easy topic items.
