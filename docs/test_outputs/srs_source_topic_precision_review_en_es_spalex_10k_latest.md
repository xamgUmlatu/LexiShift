# en-es Source Topic Precision Review

- Status: `review`
- Decision: `srs_source_topic_precision_review_needs_review`
- Generated: `2026-05-19T22:11:28.208248+00:00`
- Reviewed rows: `91`
- Accepted rows: `49` (53.8%)
- Rejected rows: `3` (3.3%)
- Pending rows: `39`

## Findings

- `PASS` `frontier_available`: Depth-audit frontier exists.
- `PASS` `release_topics_selected`: Release-candidate topics were selected.
- `PASS` `review_rows_present`: Review rows were generated.
- `PASS` `manual_labels_applied`: Manual labels applied.
- `FAIL` `review_rows_unlabeled`: Some review rows are unlabeled.

## Precision By Family

| Label | Rows | Accepted | Strong | Light | Rejected | Reject Rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `science_technology` | 12 | 11 | 5 | 6 | 1 | 8.3% |
| `music_media_entertainment` | 11 | 0 | 0 | 0 | 0 | 0.0% |
| `arts_literature_humanities` | 10 | 10 | 3 | 7 | 0 | 0.0% |
| `finance_business` | 10 | 0 | 0 | 0 | 0 | 0.0% |
| `games` | 10 | 8 | 0 | 8 | 2 | 20.0% |
| `law_politics_civics` | 10 | 10 | 3 | 7 | 0 | 0.0% |
| `sports_fitness` | 10 | 10 | 0 | 10 | 0 | 0.0% |
| `medicine_health` | 9 | 0 | 0 | 0 | 0 | 0.0% |
| `travel_places_transport` | 9 | 0 | 0 | 0 | 0 | 0.0% |

## Notable Source Labels

| Label | Rows | Accepted | Strong | Light | Rejected | Reject Rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `sciences` | 12 | 11 | 5 | 6 | 1 | 8.3% |
| `business` | 10 | 0 | 0 | 0 | 0 | 0.0% |
| `finance` | 10 | 0 | 0 | 0 | 0 | 0.0% |
| `games` | 10 | 8 | 0 | 8 | 2 | 20.0% |
| `mathematics` | 10 | 10 | 4 | 6 | 0 | 0.0% |
| `sports` | 10 | 10 | 0 | 10 | 0 | 0.0% |
| `engineering` | 9 | 9 | 4 | 5 | 0 | 0.0% |
| `entertainment` | 9 | 0 | 0 | 0 | 0 | 0.0% |
| `medicine` | 9 | 0 | 0 | 0 | 0 | 0.0% |
| `natural_sciences` | 9 | 9 | 4 | 5 | 0 | 0.0% |
| `physical_sciences` | 9 | 9 | 4 | 5 | 0 | 0.0% |
| `computing` | 8 | 8 | 3 | 5 | 0 | 0.0% |
| `law` | 8 | 8 | 3 | 5 | 0 | 0.0% |
| `music` | 6 | 0 | 0 | 0 | 0 | 0.0% |
| `card_games` | 5 | 4 | 0 | 4 | 1 | 20.0% |
| `transport` | 5 | 0 | 0 | 0 | 0 | 0.0% |
| `anatomy` | 4 | 0 | 0 | 0 | 0 | 0.0% |
| `ball_games` | 4 | 4 | 0 | 4 | 0 | 0.0% |
| `geography` | 4 | 0 | 0 | 0 | 0 | 0.0% |
| `literature` | 4 | 4 | 1 | 3 | 0 | 0.0% |
| `nautical` | 4 | 0 | 0 | 0 | 0 | 0.0% |
| `soccer` | 4 | 4 | 0 | 4 | 0 | 0.0% |
| `government` | 3 | 3 | 0 | 3 | 0 | 0.0% |
| `linguistics` | 3 | 3 | 2 | 1 | 0 | 0.0% |

## Rejected Rows

- `games` `levantar`: `reject_secondary_or_obscure_sense` - Game/card sense is too weak compared with the broad general verb.
- `games` `bailar`: `reject_secondary_or_obscure_sense` - Could occur in games, but the source relation is too indirect for game-topic evidence.
- `science_technology` `regir`: `reject_secondary_or_obscure_sense` - Scientific or mathematical governing sense is too broad for release evidence.

## Review Queue

| ID | Family | Lemma | Sample | Difficulty | Source Labels | Decision | Notes |
| --- | --- | --- | --- | ---: | --- | --- | --- |
| `srs-src-topic-001` | `medicine_health` | `luz` | `top_example` | 6.4e-05 | anatomy, medicine |  |  |
| `srs-src-topic-002` | `medicine_health` | `corazón` | `top_example` | 0.000149 | anatomy, medicine |  |  |
| `srs-src-topic-003` | `medicine_health` | `rostro` | `top_example` | 0.000163 | anatomy, medicine |  |  |
| `srs-src-topic-004` | `medicine_health` | `órgano` | `top_example` | 0.000273 | anatomy, medicine |  |  |
| `srs-src-topic-005` | `medicine_health` | `enconar` | `band_example` | 0.302479 | medicine |  |  |
| `srs-src-topic-006` | `medicine_health` | `responder` | `band_example` | 0.304614 | medicine |  |  |
| `srs-src-topic-007` | `medicine_health` | `dormir` | `hardest_example` | 0.305559 | medicine |  |  |
| `srs-src-topic-008` | `medicine_health` | `indicar` | `hardest_example` | 0.306076 | medicine |  |  |
| `srs-src-topic-009` | `medicine_health` | `liberar` | `hardest_example` | 0.307503 | medicine, physiology |  |  |
| `srs-src-topic-010` | `finance_business` | `movimiento` | `top_example` | 6.2e-05 | banking, business, finance |  |  |
| `srs-src-topic-011` | `finance_business` | `luz` | `top_example` | 6.4e-05 | business, finance |  |  |
| `srs-src-topic-012` | `finance_business` | `capital` | `top_example` | 9.7e-05 | business, finance |  |  |
| `srs-src-topic-013` | `finance_business` | `par` | `top_example` | 0.000219 | business, finance |  |  |
| `srs-src-topic-014` | `finance_business` | `poner` | `band_example` | 0.300013 | business, finance |  |  |
| `srs-src-topic-015` | `finance_business` | `conectar` | `band_example` | 0.300306 | business, finance |  |  |
| `srs-src-topic-016` | `finance_business` | `campear` | `hardest_example` | 0.302028 | business, finance |  |  |
| `srs-src-topic-017` | `finance_business` | `zurcir` | `hardest_example` | 0.302302 | business, finance |  |  |
| `srs-src-topic-018` | `finance_business` | `ascender` | `hardest_example` | 0.310088 | business, finance |  |  |
| `srs-src-topic-019` | `finance_business` | `cancelar` | `hardest_example` | 0.314492 | business, finance |  |  |
| `srs-src-topic-020` | `sports_fitness` | `entrada` | `top_example` | 0.000209 | ball_games, soccer, sports | accept_light_topic | Tackle/ticket/entry sports senses exist, but the lemma is highly polysemous. |
| `srs-src-topic-021` | `sports_fitness` | `pista` | `top_example` | 0.000441 | sports | accept_light_topic | Track/court sense is useful for sports, but clue/trail senses compete. |
| `srs-src-topic-022` | `sports_fitness` | `palo` | `top_example` | 0.000475 | sports | accept_light_topic | Stick/post sports senses are real, but the word is broad. |
| `srs-src-topic-023` | `sports_fitness` | `titular` | `top_example` | 0.000504 | sports | accept_light_topic | Starter/headline sports sense is useful, but headline/title senses are broad. |
| `srs-src-topic-024` | `sports_fitness` | `sacar` | `band_example` | 0.300049 | ball_games, soccer, sports | accept_light_topic | Serve/kick-off use is real, but the general verb is very broad. |
| `srs-src-topic-025` | `sports_fitness` | `marcar` | `band_example` | 0.300149 | sports | accept_light_topic | Score/mark is common sports vocabulary, but the non-sports senses are broad. |
| `srs-src-topic-026` | `sports_fitness` | `recortar` | `hardest_example` | 0.313105 | ball_games, soccer, sports | accept_light_topic | Cut back/change direction is useful sports vocabulary, but broad. |
| `srs-src-topic-027` | `sports_fitness` | `remontar` | `hardest_example` | 0.313915 | sports | accept_light_topic | Comeback sense is common in sports, but the verb also has general senses. |
| `srs-src-topic-028` | `sports_fitness` | `fichar` | `hardest_example` | 0.314717 | sports | accept_light_topic | Player-signing sense is useful, but hiring/registering senses compete. |
| `srs-src-topic-029` | `sports_fitness` | `despejar` | `hardest_example` | 0.315153 | ball_games, soccer, sports | accept_light_topic | Clear-the-ball sense is real, but the verb is not sports-exclusive. |
| `srs-src-topic-030` | `games` | `jefe` | `top_example` | 0.000122 | games, video_games | accept_light_topic | Boss-enemy sense is real in games, but chief/boss senses dominate generally. |
| `srs-src-topic-031` | `games` | `corazón` | `top_example` | 0.000149 | card_games, games | accept_light_topic | Card-suit and game-life senses are useful, but heart/body senses compete. |
| `srs-src-topic-032` | `games` | `pista` | `top_example` | 0.000441 | games | accept_light_topic | Clue/hint sense is useful for games, but non-game senses compete. |
| `srs-src-topic-033` | `games` | `palo` | `top_example` | 0.000475 | card_games, games | accept_light_topic | Card-suit or game-piece sense is useful, but stick/club senses compete. |
| `srs-src-topic-034` | `games` | `cargar` | `band_example` | 0.30027 | games | accept_light_topic | Load-game sense is real, but charge/load senses are broad. |
| `srs-src-topic-035` | `games` | `descartar` | `band_example` | 0.30042 | card_games, games | accept_light_topic | Discard is direct card/game vocabulary, but also a general verb. |
| `srs-src-topic-036` | `games` | `levantar` | `hardest_example` | 0.306012 | card_games, games | reject_secondary_or_obscure_sense | Game/card sense is too weak compared with the broad general verb. |
| `srs-src-topic-037` | `games` | `bailar` | `hardest_example` | 0.308534 | games | reject_secondary_or_obscure_sense | Could occur in games, but the source relation is too indirect for game-topic evidence. |
| `srs-src-topic-038` | `games` | `apuntar` | `hardest_example` | 0.311802 | card_games, games | accept_light_topic | Aim/point is common gameplay vocabulary, but the verb is broad. |
| `srs-src-topic-039` | `games` | `despejar` | `hardest_example` | 0.315153 | games | accept_light_topic | Clear-board or clear-area gameplay sense is real, but broad. |
| `srs-src-topic-040` | `music_media_entertainment` | `movimiento` | `top_example` | 6.2e-05 | entertainment, music |  |  |
| `srs-src-topic-041` | `music_media_entertainment` | `orquesta` | `top_example` | 0.000168 | entertainment, music |  |  |
| `srs-src-topic-042` | `music_media_entertainment` | `órgano` | `top_example` | 0.000273 | entertainment, music |  |  |
| `srs-src-topic-043` | `music_media_entertainment` | `pista` | `top_example` | 0.000441 | entertainment, music |  |  |
| `srs-src-topic-044` | `music_media_entertainment` | `espacio` | `band_example` | 0.000105 | media, publishing |  |  |
| `srs-src-topic-045` | `music_media_entertainment` | `transportar` | `band_example` | 0.300284 | entertainment, music |  |  |
| `srs-src-topic-046` | `music_media_entertainment` | `pinchar` | `band_example` | 0.301313 | entertainment, music |  |  |
| `srs-src-topic-047` | `music_media_entertainment` | `brindar` | `hardest_example` | 0.310931 | entertainment |  |  |
| `srs-src-topic-048` | `music_media_entertainment` | `apuntar` | `hardest_example` | 0.311802 | entertainment, theater |  |  |
| `srs-src-topic-049` | `music_media_entertainment` | `encerrar` | `hardest_example` | 0.314254 | media, publishing |  |  |
| `srs-src-topic-050` | `music_media_entertainment` | `lidiar` | `hardest_example` | 0.315177 | entertainment |  |  |
| `srs-src-topic-051` | `law_politics_civics` | `jefe` | `top_example` | 0.000122 | government, politics | accept_light_topic | Leader/chief is civics-adjacent, but the lemma is broad. |
| `srs-src-topic-052` | `law_politics_civics` | `demanda` | `top_example` | 0.000228 | law | accept_strong_topic | Direct legal vocabulary for claim/lawsuit. |
| `srs-src-topic-053` | `law_politics_civics` | `tropa` | `top_example` | 0.000255 | government, politics | accept_light_topic | Military/government vocabulary is relevant, but not strictly civics. |
| `srs-src-topic-054` | `law_politics_civics` | `órgano` | `top_example` | 0.000273 | law | accept_light_topic | Institutional body sense is relevant, but body-organ sense competes. |
| `srs-src-topic-055` | `law_politics_civics` | `presentar` | `band_example` | 0.30003 | government, law | accept_light_topic | File/submit a legal or government document is relevant, but broad. |
| `srs-src-topic-056` | `law_politics_civics` | `recurrir` | `band_example` | 0.30034 | law | accept_strong_topic | Appeal/legal recourse sense is direct legal vocabulary. |
| `srs-src-topic-057` | `law_politics_civics` | `comparecer` | `hardest_example` | 0.312796 | law | accept_strong_topic | Appear before court or authority is direct legal/civics vocabulary. |
| `srs-src-topic-058` | `law_politics_civics` | `alzar` | `hardest_example` | 0.313297 | law | accept_light_topic | Legal or political uprising/appeal senses are relevant, but broad. |
| `srs-src-topic-059` | `law_politics_civics` | `fallar` | `hardest_example` | 0.314114 | law | accept_light_topic | Rule/decide in court is relevant, but fail/misfire senses compete. |
| `srs-src-topic-060` | `law_politics_civics` | `reivindicar` | `hardest_example` | 0.31484 | law | accept_light_topic | Claim/assert-rights sense is relevant, but not exclusively legal. |
| `srs-src-topic-061` | `science_technology` | `entrada` | `top_example` | 0.000209 | computing, engineering, mathematics, natural_sciences, physical_sciences, sciences | accept_light_topic | Input/entry sense is useful in computing, but the lemma is broad. |
| `srs-src-topic-062` | `science_technology` | `defecto` | `top_example` | 0.000641 | computing, engineering, mathematics, natural_sciences, physical_sciences, sciences | accept_light_topic | Defect/fault is useful in engineering and technology, but broad. |
| `srs-src-topic-063` | `science_technology` | `controlador` | `top_example` | 0.002736 | computing, engineering, mathematics, natural_sciences, physical_sciences, sciences | accept_strong_topic | Direct controller/driver technical vocabulary. |
| `srs-src-topic-064` | `science_technology` | `vida` | `top_example` | 0.004283 | computing, engineering, mathematics, natural_sciences, physical_sciences, sciences | accept_light_topic | Life is relevant to biology/science, but the word is very broad. |
| `srs-src-topic-065` | `science_technology` | `luz` | `band_example` | 6.4e-05 | engineering, natural_sciences, physical_sciences, physics, sciences | accept_strong_topic | Direct physics/science vocabulary. |
| `srs-src-topic-066` | `science_technology` | `área` | `band_example` | 9.3e-05 | mathematics, sciences | accept_strong_topic | Direct mathematics/science vocabulary. |
| `srs-src-topic-067` | `science_technology` | `trasladar` | `band_example` | 0.300196 | mathematics, sciences | accept_light_topic | Translate/transfer sense is relevant in math or engineering, but broad. |
| `srs-src-topic-068` | `science_technology` | `cargar` | `band_example` | 0.30027 | computing, engineering, mathematics, natural_sciences, physical_sciences, sciences | accept_light_topic | Load/charge is useful computing and engineering vocabulary, but broad. |
| `srs-src-topic-069` | `science_technology` | `actualizar` | `hardest_example` | 0.313111 | computing, engineering, mathematics, natural_sciences, physical_sciences, sciences | accept_strong_topic | Direct computing/technology vocabulary. |
| `srs-src-topic-070` | `science_technology` | `regir` | `hardest_example` | 0.315195 | sciences | reject_secondary_or_obscure_sense | Scientific or mathematical governing sense is too broad for release evidence. |
| `srs-src-topic-071` | `science_technology` | `colgar` | `hardest_example` | 0.315571 | computing, engineering, mathematics, natural_sciences, physical_sciences, sciences | accept_light_topic | Hang/freeze computing sense is useful, but the word is broad. |
| `srs-src-topic-072` | `science_technology` | `programar` | `hardest_example` | 0.316254 | computing, engineering, mathematics, natural_sciences, physical_sciences, sciences | accept_strong_topic | Direct computing/technology vocabulary. |
| `srs-src-topic-073` | `travel_places_transport` | `tren` | `top_example` | 0.000333 | transport |  |  |
| `srs-src-topic-074` | `travel_places_transport` | `derrota` | `top_example` | 0.000363 | nautical, transport |  |  |
| `srs-src-topic-075` | `travel_places_transport` | `palo` | `top_example` | 0.000475 | nautical, transport |  |  |
| `srs-src-topic-076` | `travel_places_transport` | `bordo` | `top_example` | 0.000795 | nautical, transport |  |  |
| `srs-src-topic-077` | `travel_places_transport` | `etapa` | `band_example` | 0.000217 | geography |  |  |
| `srs-src-topic-078` | `travel_places_transport` | `reclamar` | `band_example` | 0.30812 | nautical, transport |  |  |
| `srs-src-topic-079` | `travel_places_transport` | `sísmico` | `hardest_example` | 0.151413 | geography |  |  |
| `srs-src-topic-080` | `travel_places_transport` | `paleolítico` | `hardest_example` | 0.166346 | geography |  |  |
| `srs-src-topic-081` | `travel_places_transport` | `antártico` | `hardest_example` | 0.167956 | geography |  |  |
| `srs-src-topic-082` | `arts_literature_humanities` | `pie` | `top_example` | 0.005291 | arts, literature | accept_light_topic | Verse/footnote/text sense is relevant, but body-part sense dominates. |
| `srs-src-topic-083` | `arts_literature_humanities` | `género` | `top_example` | 0.005341 | linguistics, literature | accept_strong_topic | Direct genre/linguistics/literature vocabulary. |
| `srs-src-topic-084` | `arts_literature_humanities` | `concepto` | `top_example` | 0.005438 | literature | accept_light_topic | Useful humanities vocabulary, but broad. |
| `srs-src-topic-085` | `arts_literature_humanities` | `metro` | `top_example` | 0.006482 | literature | accept_light_topic | Metre/meter is relevant to poetry and humanities, but transit/measurement senses compete. |
| `srs-src-topic-086` | `arts_literature_humanities` | `luz` | `band_example` | 6.4e-05 | architecture | accept_light_topic | Light is relevant to architecture/arts, but the word is broad. |
| `srs-src-topic-087` | `arts_literature_humanities` | `sombra` | `band_example` | 0.000207 | art, arts | accept_light_topic | Shadow/shading is useful in art vocabulary, but broad. |
| `srs-src-topic-088` | `arts_literature_humanities` | `afrodita` | `band_example` | 0.608917 | philosophy | accept_light_topic | Mythology/culture relevance is real, but proper-noun policy should stay light. |
| `srs-src-topic-089` | `arts_literature_humanities` | `paleolítico` | `hardest_example` | 0.166346 | history | accept_strong_topic | Direct history/humanities vocabulary. |
| `srs-src-topic-090` | `arts_literature_humanities` | `neutro` | `hardest_example` | 0.168765 | linguistics | accept_light_topic | Neutral/neuter grammar and humanities sense is relevant, but broad. |
| `srs-src-topic-091` | `arts_literature_humanities` | `reflexivo` | `hardest_example` | 0.169514 | linguistics | accept_strong_topic | Direct linguistics/grammar vocabulary. |

## Limitations

- This packet samples compact evidence retained by the depth audit, not every source row.
- Agent labels are pending user approval and do not promote runtime topic truth by themselves.
- Rejects in this sample should tighten release guidance before default-visible topics are accepted.
