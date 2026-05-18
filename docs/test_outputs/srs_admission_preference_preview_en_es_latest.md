# SRS Admission Preference Preview - en-es

- Status: PASS
- Findings: pass=5 warn=0 fail=0
- Frequency DB rows: 2000
- Runtime scope: admission_preview_only

## Inputs

- frequency_db: `/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift/frequency_packs/freq-es-cde.sqlite`
- set_top_n: 2000
- initial_active_count: 120
- preview_count: 20

## Scenario Summary

| Scenario | Topic movers | Overlay application | Top lemmas |
| --- | ---: | --- | --- |
| neutral | 0 | n/a | siglo, millón, hora, música, principio, movimiento, luz, mayoría |
| animals_interest | 7 | applied | ave, siglo, cordero, millón, cachorro, hora, víbora, música |
| animals_light_weight | 1 | applied | siglo, millón, hora, música, principio, movimiento, luz, mayoría |
| plants_nature_interest | 2 | applied | siglo, millón, hora, sauce, música, principio, movimiento, luz |
| animals_plants_interest | 8 | applied | ave, siglo, cordero, millón, cachorro, hora, sauce, víbora |
| weighted_plants_over_animals | 2 | applied | siglo, millón, hora, sauce, música, principio, movimiento, luz |
| finance_control | 0 | n/a | siglo, millón, hora, música, principio, movimiento, luz, mayoría |

## Findings

- PASS: `FREQUENCY_DB_READABLE` - Frequency DB has 2000 rows.
- PASS: `ANIMALS_INTEREST_MOVES_ADMISSION` - animals preference produced 7 topic movers in the admission preview.
- PASS: `PLANTS_NATURE_INTEREST_MOVES_ADMISSION` - plants_nature preference produced 2 topic movers in the admission preview.
- PASS: `SCALAR_TOPIC_WEIGHTS_AFFECT_PRIORITY` - Weighted plants-over-animals profile surfaces plants/nature movers.
- PASS: `UNSUPPORTED_TOPIC_CONTROL_STAYS_NEUTRAL` - Finance control remains neutral because current tested metadata has no finance support.

## Top Topic Movers

### animals_interest
- ave: base_rank=91, reranked_rank=1, delta=90, source=topic_hint:animals
- cordero: base_rank=387, reranked_rank=3, delta=384, source=topic_hint:animals
- cachorro: base_rank=429, reranked_rank=5, delta=424, source=topic_hint:animals
- víbora: base_rank=524, reranked_rank=7, delta=517, source=topic_hint:animals
- lagartija: base_rank=727, reranked_rank=13, delta=714, source=topic_hint:animals
- chivo: base_rank=812, reranked_rank=18, delta=794, source=topic_hint:animals
- escarabajo: base_rank=855, reranked_rank=20, delta=835, source=topic_hint:animals

### animals_light_weight
- ave: base_rank=91, reranked_rank=11, delta=80, source=topic_hint:animals

### plants_nature_interest
- sauce: base_rank=578, reranked_rank=4, delta=574, source=topic_hint:plants_nature
- granado: base_rank=909, reranked_rank=11, delta=898, source=topic_hint:plants_nature

### animals_plants_interest
- ave: base_rank=91, reranked_rank=1, delta=90, source=topic_hint:animals
- cordero: base_rank=387, reranked_rank=3, delta=384, source=topic_hint:animals
- cachorro: base_rank=429, reranked_rank=5, delta=424, source=topic_hint:animals
- sauce: base_rank=578, reranked_rank=7, delta=571, source=topic_hint:plants_nature
- víbora: base_rank=524, reranked_rank=8, delta=516, source=topic_hint:animals
- lagartija: base_rank=727, reranked_rank=14, delta=713, source=topic_hint:animals
- granado: base_rank=909, reranked_rank=16, delta=893, source=topic_hint:plants_nature
- chivo: base_rank=812, reranked_rank=20, delta=792, source=topic_hint:animals

### weighted_plants_over_animals
- sauce: base_rank=578, reranked_rank=4, delta=574, source=topic_hint:plants_nature
- granado: base_rank=909, reranked_rank=11, delta=898, source=topic_hint:plants_nature
