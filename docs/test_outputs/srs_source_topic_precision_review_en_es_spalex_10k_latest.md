# en-es Source Topic Precision Review

- Status: `ok`
- Decision: `srs_source_topic_precision_review_ready`
- Generated: `2026-05-19T22:39:49.721800+00:00`
- Reviewed rows: `85`
- Accepted rows: `81` (95.3%)
- Rejected rows: `4` (4.7%)
- Pending rows: `0`

## Findings

- `PASS` `frontier_available`: Depth-audit frontier exists.
- `PASS` `release_topics_selected`: Release-candidate topics were selected.
- `PASS` `review_rows_present`: Review rows were generated.
- `PASS` `manual_labels_applied`: Manual labels applied.
- `PASS` `accepted_majority`: Accepted rows outnumber rejects in the reviewed sample.
- `WARN` `source_false_positive_classes_present`: Rejects identify source-label false-positive classes before promotion.

## Precision By Family

| Label | Rows | Accepted | Strong | Light | Rejected | Reject Rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `science_technology` | 12 | 12 | 5 | 7 | 0 | 0.0% |
| `arts_literature_humanities` | 10 | 10 | 3 | 7 | 0 | 0.0% |
| `games` | 10 | 10 | 0 | 10 | 0 | 0.0% |
| `law_politics_civics` | 10 | 10 | 3 | 7 | 0 | 0.0% |
| `sports_fitness` | 10 | 10 | 0 | 10 | 0 | 0.0% |
| `travel_places_transport` | 9 | 7 | 2 | 5 | 2 | 22.2% |
| `finance_business` | 8 | 6 | 3 | 3 | 2 | 25.0% |
| `medicine_health` | 8 | 8 | 4 | 4 | 0 | 0.0% |
| `music_media_entertainment` | 8 | 8 | 4 | 4 | 0 | 0.0% |

## Notable Source Labels

| Label | Rows | Accepted | Strong | Light | Rejected | Reject Rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `sciences` | 11 | 11 | 5 | 6 | 0 | 0.0% |
| `games` | 10 | 10 | 0 | 10 | 0 | 0.0% |
| `mathematics` | 10 | 10 | 4 | 6 | 0 | 0.0% |
| `natural_sciences` | 10 | 10 | 4 | 6 | 0 | 0.0% |
| `physical_sciences` | 10 | 10 | 4 | 6 | 0 | 0.0% |
| `sports` | 10 | 10 | 0 | 10 | 0 | 0.0% |
| `engineering` | 9 | 9 | 4 | 5 | 0 | 0.0% |
| `computing` | 8 | 8 | 3 | 5 | 0 | 0.0% |
| `entertainment` | 8 | 8 | 4 | 4 | 0 | 0.0% |
| `finance` | 8 | 6 | 3 | 3 | 2 | 25.0% |
| `law` | 8 | 8 | 3 | 5 | 0 | 0.0% |
| `medicine` | 8 | 8 | 4 | 4 | 0 | 0.0% |
| `business` | 7 | 5 | 2 | 3 | 2 | 28.6% |
| `music` | 7 | 7 | 4 | 3 | 0 | 0.0% |
| `transport` | 6 | 5 | 2 | 3 | 1 | 16.7% |
| `nautical` | 5 | 4 | 1 | 3 | 1 | 20.0% |
| `anatomy` | 4 | 4 | 3 | 1 | 0 | 0.0% |
| `ball_games` | 4 | 4 | 0 | 4 | 0 | 0.0% |
| `card_games` | 4 | 4 | 0 | 4 | 0 | 0.0% |
| `literature` | 4 | 4 | 1 | 3 | 0 | 0.0% |
| `soccer` | 4 | 4 | 0 | 4 | 0 | 0.0% |
| `geography` | 3 | 2 | 0 | 2 | 1 | 33.3% |
| `government` | 3 | 3 | 0 | 3 | 0 | 0.0% |
| `linguistics` | 3 | 3 | 2 | 1 | 0 | 0.0% |

## Rejected Rows

- `finance_business` `silicio`: `reject_secondary_or_obscure_sense` - Silicon business/finance relation is source-fragile and primarily science/technology vocabulary.
- `finance_business` `raso`: `reject_secondary_or_obscure_sense` - The business/finance relation is too weak compared with the broad adjective.
- `travel_places_transport` `plutón`: `reject_secondary_or_obscure_sense` - Planet/geography evidence is not useful travel or transport preference evidence.
- `travel_places_transport` `bonanza`: `reject_secondary_or_obscure_sense` - Nautical fair-weather sense is too narrow compared with common prosperity/good-fortune senses.

## Review Queue

| ID | Family | Lemma | Sample | Difficulty | Source Labels | Decision | Notes |
| --- | --- | --- | --- | ---: | --- | --- | --- |
| `srs-src-topic-001` | `medicine_health` | `corazón` | `top_example` | 0.000149 | anatomy, medicine | accept_strong_topic | Direct anatomy and health vocabulary. |
| `srs-src-topic-002` | `medicine_health` | `rostro` | `top_example` | 0.000163 | anatomy, medicine | accept_light_topic | Body/anatomy vocabulary is health-relevant, but the lemma is broad and basic. |
| `srs-src-topic-003` | `medicine_health` | `órgano` | `top_example` | 0.000273 | anatomy, medicine | accept_strong_topic | Direct anatomy and medicine vocabulary despite nonmedical senses. |
| `srs-src-topic-004` | `medicine_health` | `estadio` | `top_example` | 0.000421 | medicine | accept_light_topic | Disease stage is a real medicine sense, but the lemma is broad. |
| `srs-src-topic-005` | `medicine_health` | `enconar` | `band_example` | 0.302479 | medicine | accept_light_topic | The inflame/fester sense is medical, but specialized. |
| `srs-src-topic-006` | `medicine_health` | `dormir` | `band_example` | 0.305559 | medicine | accept_light_topic | Sleep is health-relevant, but the verb remains very general. |
| `srs-src-topic-007` | `medicine_health` | `renal` | `hardest_example` | 0.167056 | anatomy, medicine | accept_strong_topic | Direct kidney/anatomy and health vocabulary. |
| `srs-src-topic-008` | `medicine_health` | `inmune` | `hardest_example` | 0.168217 | medicine | accept_strong_topic | Direct immune/health vocabulary. |
| `srs-src-topic-009` | `finance_business` | `capital` | `top_example` | 9.7e-05 | business, finance | accept_strong_topic | Direct finance and business vocabulary. |
| `srs-src-topic-010` | `finance_business` | `par` | `top_example` | 0.000219 | business, finance | accept_light_topic | Par value and market senses are real, but the lemma is broad. |
| `srs-src-topic-011` | `finance_business` | `fusión` | `top_example` | 0.000595 | economics, finance | accept_strong_topic | Merger/fusion is direct finance and business vocabulary. |
| `srs-src-topic-012` | `finance_business` | `silicio` | `top_example` | 0.001459 | business, finance | reject_secondary_or_obscure_sense | Silicon business/finance relation is source-fragile and primarily science/technology vocabulary. |
| `srs-src-topic-013` | `finance_business` | `cancelar` | `band_example` | 0.314492 | business, finance | accept_light_topic | Cancel/pay off debt or invoice senses are finance-relevant, but the lemma is broad. |
| `srs-src-topic-014` | `finance_business` | `auxiliar` | `hardest_example` | 0.151433 | accounting, business, finance | accept_light_topic | Accounting or business assistant/subledger senses are useful, but the lemma is broad. |
| `srs-src-topic-015` | `finance_business` | `raso` | `hardest_example` | 0.15161 | business, finance | reject_secondary_or_obscure_sense | The business/finance relation is too weak compared with the broad adjective. |
| `srs-src-topic-016` | `finance_business` | `acreedor` | `hardest_example` | 0.15334 | business, finance | accept_strong_topic | Direct creditor/finance vocabulary. |
| `srs-src-topic-017` | `sports_fitness` | `entrada` | `top_example` | 0.000209 | ball_games, soccer, sports | accept_light_topic | Tackle/ticket/entry sports senses exist, but the lemma is highly polysemous. |
| `srs-src-topic-018` | `sports_fitness` | `pista` | `top_example` | 0.000441 | sports | accept_light_topic | Track/court sense is useful for sports, but clue/trail senses compete. |
| `srs-src-topic-019` | `sports_fitness` | `palo` | `top_example` | 0.000475 | sports | accept_light_topic | Stick/post sports senses are real, but the word is broad. |
| `srs-src-topic-020` | `sports_fitness` | `titular` | `top_example` | 0.000504 | sports | accept_light_topic | Starter/headline sports sense is useful, but headline/title senses are broad. |
| `srs-src-topic-021` | `sports_fitness` | `sacar` | `band_example` | 0.300049 | ball_games, soccer, sports | accept_light_topic | Serve/kick-off use is real, but the general verb is very broad. |
| `srs-src-topic-022` | `sports_fitness` | `marcar` | `band_example` | 0.300149 | sports | accept_light_topic | Score/mark is common sports vocabulary, but the non-sports senses are broad. |
| `srs-src-topic-023` | `sports_fitness` | `recortar` | `hardest_example` | 0.313105 | ball_games, soccer, sports | accept_light_topic | Cut back/change direction is useful sports vocabulary, but broad. |
| `srs-src-topic-024` | `sports_fitness` | `remontar` | `hardest_example` | 0.313915 | sports | accept_light_topic | Comeback sense is common in sports, but the verb also has general senses. |
| `srs-src-topic-025` | `sports_fitness` | `fichar` | `hardest_example` | 0.314717 | sports | accept_light_topic | Player-signing sense is useful, but hiring/registering senses compete. |
| `srs-src-topic-026` | `sports_fitness` | `despejar` | `hardest_example` | 0.315153 | ball_games, soccer, sports | accept_light_topic | Clear-the-ball sense is real, but the verb is not sports-exclusive. |
| `srs-src-topic-027` | `games` | `jefe` | `top_example` | 0.000122 | games, video_games | accept_light_topic | Boss-enemy sense is real in games, but chief/boss senses dominate generally. |
| `srs-src-topic-028` | `games` | `corazón` | `top_example` | 0.000149 | card_games, games | accept_light_topic | Card-suit and game-life senses are useful, but heart/body senses compete. |
| `srs-src-topic-029` | `games` | `pista` | `top_example` | 0.000441 | games | accept_light_topic | Clue/hint sense is useful for games, but non-game senses compete. |
| `srs-src-topic-030` | `games` | `palo` | `top_example` | 0.000475 | card_games, games | accept_light_topic | Card-suit or game-piece sense is useful, but stick/club senses compete. |
| `srs-src-topic-031` | `games` | `cargar` | `band_example` | 0.30027 | games | accept_light_topic | Load-game sense is real, but charge/load senses are broad. |
| `srs-src-topic-032` | `games` | `descartar` | `band_example` | 0.30042 | card_games, games | accept_light_topic | Discard is direct card/game vocabulary, but also a general verb. |
| `srs-src-topic-033` | `games` | `tocar` | `hardest_example` | 0.305131 | games | accept_light_topic | Turn/play/touch senses can be useful in games, but the verb is very broad. |
| `srs-src-topic-034` | `games` | `lanzar` | `hardest_example` | 0.305905 | games | accept_light_topic | Throw/launch is useful in games, but also broad. |
| `srs-src-topic-035` | `games` | `apuntar` | `hardest_example` | 0.311802 | card_games, games | accept_light_topic | Aim/point is common gameplay vocabulary, but the verb is broad. |
| `srs-src-topic-036` | `games` | `despejar` | `hardest_example` | 0.315153 | games | accept_light_topic | Clear-board or clear-area gameplay sense is real, but broad. |
| `srs-src-topic-037` | `music_media_entertainment` | `movimiento` | `top_example` | 6.2e-05 | entertainment, music | accept_light_topic | Musical movement is a real sense, but the lemma is broad. |
| `srs-src-topic-038` | `music_media_entertainment` | `orquesta` | `top_example` | 0.000168 | entertainment, music | accept_strong_topic | Direct music vocabulary. |
| `srs-src-topic-039` | `music_media_entertainment` | `órgano` | `top_example` | 0.000273 | entertainment, music | accept_strong_topic | Musical instrument sense is direct and learner-useful. |
| `srs-src-topic-040` | `music_media_entertainment` | `pista` | `top_example` | 0.000441 | entertainment, music | accept_light_topic | Track/media sense is useful, but the lemma is highly polysemous. |
| `srs-src-topic-041` | `music_media_entertainment` | `pinchar` | `band_example` | 0.301313 | entertainment, music | accept_light_topic | DJ/play-record sense is entertainment-relevant, but broad and colloquial. |
| `srs-src-topic-042` | `music_media_entertainment` | `interpretar` | `band_example` | 0.306597 | entertainment, music, theater | accept_strong_topic | Direct perform/interpret vocabulary for music, theater, and entertainment. |
| `srs-src-topic-043` | `music_media_entertainment` | `trágico` | `hardest_example` | 0.160962 | broadcasting, entertainment, film, media, television, theater | accept_light_topic | Tragic drama/film/theater usage is entertainment-relevant, but the adjective is broad. |
| `srs-src-topic-044` | `music_media_entertainment` | `presto` | `hardest_example` | 0.163157 | entertainment, music | accept_strong_topic | Direct music tempo vocabulary. |
| `srs-src-topic-045` | `law_politics_civics` | `jefe` | `top_example` | 0.000122 | government, politics | accept_light_topic | Leader/chief is civics-adjacent, but the lemma is broad. |
| `srs-src-topic-046` | `law_politics_civics` | `demanda` | `top_example` | 0.000228 | law | accept_strong_topic | Direct legal vocabulary for claim/lawsuit. |
| `srs-src-topic-047` | `law_politics_civics` | `tropa` | `top_example` | 0.000255 | government, politics | accept_light_topic | Military/government vocabulary is relevant, but not strictly civics. |
| `srs-src-topic-048` | `law_politics_civics` | `órgano` | `top_example` | 0.000273 | law | accept_light_topic | Institutional body sense is relevant, but body-organ sense competes. |
| `srs-src-topic-049` | `law_politics_civics` | `presentar` | `band_example` | 0.30003 | government, law | accept_light_topic | File/submit a legal or government document is relevant, but broad. |
| `srs-src-topic-050` | `law_politics_civics` | `recurrir` | `band_example` | 0.30034 | law | accept_strong_topic | Appeal/legal recourse sense is direct legal vocabulary. |
| `srs-src-topic-051` | `law_politics_civics` | `comparecer` | `hardest_example` | 0.312796 | law | accept_strong_topic | Appear before court or authority is direct legal/civics vocabulary. |
| `srs-src-topic-052` | `law_politics_civics` | `alzar` | `hardest_example` | 0.313297 | law | accept_light_topic | Legal or political uprising/appeal senses are relevant, but broad. |
| `srs-src-topic-053` | `law_politics_civics` | `fallar` | `hardest_example` | 0.314114 | law | accept_light_topic | Rule/decide in court is relevant, but fail/misfire senses compete. |
| `srs-src-topic-054` | `law_politics_civics` | `reivindicar` | `hardest_example` | 0.31484 | law | accept_light_topic | Claim/assert-rights sense is relevant, but not exclusively legal. |
| `srs-src-topic-055` | `science_technology` | `entrada` | `top_example` | 0.000209 | computing, engineering, mathematics, natural_sciences, physical_sciences, sciences | accept_light_topic | Input/entry sense is useful in computing, but the lemma is broad. |
| `srs-src-topic-056` | `science_technology` | `defecto` | `top_example` | 0.000641 | computing, engineering, mathematics, natural_sciences, physical_sciences, sciences | accept_light_topic | Defect/fault is useful in engineering and technology, but broad. |
| `srs-src-topic-057` | `science_technology` | `controlador` | `top_example` | 0.002736 | computing, engineering, mathematics, natural_sciences, physical_sciences, sciences | accept_strong_topic | Direct controller/driver technical vocabulary. |
| `srs-src-topic-058` | `science_technology` | `vida` | `top_example` | 0.004283 | computing, engineering, mathematics, natural_sciences, physical_sciences, sciences | accept_light_topic | Life is relevant to biology/science, but the word is very broad. |
| `srs-src-topic-059` | `science_technology` | `luz` | `band_example` | 6.4e-05 | engineering, natural_sciences, physical_sciences, physics, sciences | accept_strong_topic | Direct physics/science vocabulary. |
| `srs-src-topic-060` | `science_technology` | `área` | `band_example` | 9.3e-05 | mathematics, sciences | accept_strong_topic | Direct mathematics/science vocabulary. |
| `srs-src-topic-061` | `science_technology` | `trasladar` | `band_example` | 0.300196 | mathematics, sciences | accept_light_topic | Translate/transfer sense is relevant in math or engineering, but broad. |
| `srs-src-topic-062` | `science_technology` | `cargar` | `band_example` | 0.30027 | computing, engineering, mathematics, natural_sciences, physical_sciences, sciences | accept_light_topic | Load/charge is useful computing and engineering vocabulary, but broad. |
| `srs-src-topic-063` | `science_technology` | `activar` | `hardest_example` | 0.3127 | chemistry, natural_sciences, physical_sciences, physics | accept_light_topic | Activation is useful technical vocabulary, but the verb is broad. |
| `srs-src-topic-064` | `science_technology` | `actualizar` | `hardest_example` | 0.313111 | computing, engineering, mathematics, natural_sciences, physical_sciences, sciences | accept_strong_topic | Direct computing/technology vocabulary. |
| `srs-src-topic-065` | `science_technology` | `colgar` | `hardest_example` | 0.315571 | computing, engineering, mathematics, natural_sciences, physical_sciences, sciences | accept_light_topic | Hang/freeze computing sense is useful, but the word is broad. |
| `srs-src-topic-066` | `science_technology` | `programar` | `hardest_example` | 0.316254 | computing, engineering, mathematics, natural_sciences, physical_sciences, sciences | accept_strong_topic | Direct computing/technology vocabulary. |
| `srs-src-topic-067` | `travel_places_transport` | `tren` | `top_example` | 0.000333 | transport | accept_strong_topic | Direct transport vocabulary. |
| `srs-src-topic-068` | `travel_places_transport` | `bordo` | `top_example` | 0.000795 | nautical, transport | accept_light_topic | Aboard/ship-side travel expressions are relevant, but the lemma is specialized. |
| `srs-src-topic-069` | `travel_places_transport` | `propulsión` | `top_example` | 0.001753 | aeronautics, aerospace, aviation, nautical, transport | accept_strong_topic | Direct propulsion/transport vocabulary. |
| `srs-src-topic-070` | `travel_places_transport` | `quilla` | `top_example` | 0.002597 | nautical, transport | accept_light_topic | Keel is direct nautical/transport vocabulary, but specialized. |
| `srs-src-topic-071` | `travel_places_transport` | `etapa` | `band_example` | 0.000217 | geography | accept_light_topic | Trip stage or leg is travel-relevant, but the lemma is broad. |
| `srs-src-topic-072` | `travel_places_transport` | `plutón` | `hardest_example` | 0.023268 | geography | reject_secondary_or_obscure_sense | Planet/geography evidence is not useful travel or transport preference evidence. |
| `srs-src-topic-073` | `travel_places_transport` | `bonanza` | `hardest_example` | 0.0233 | nautical, transport | reject_secondary_or_obscure_sense | Nautical fair-weather sense is too narrow compared with common prosperity/good-fortune senses. |
| `srs-src-topic-074` | `travel_places_transport` | `naval` | `hardest_example` | 0.150515 | nautical, transport | accept_light_topic | Naval/maritime adjective is transport-adjacent, but not ordinary travel vocabulary. |
| `srs-src-topic-075` | `travel_places_transport` | `antártico` | `hardest_example` | 0.167956 | geography | accept_light_topic | Place/geography adjective is useful for travel and places, but narrow. |
| `srs-src-topic-076` | `arts_literature_humanities` | `pie` | `top_example` | 0.005291 | arts, literature | accept_light_topic | Verse/footnote/text sense is relevant, but body-part sense dominates. |
| `srs-src-topic-077` | `arts_literature_humanities` | `género` | `top_example` | 0.005341 | linguistics, literature | accept_strong_topic | Direct genre/linguistics/literature vocabulary. |
| `srs-src-topic-078` | `arts_literature_humanities` | `concepto` | `top_example` | 0.005438 | literature | accept_light_topic | Useful humanities vocabulary, but broad. |
| `srs-src-topic-079` | `arts_literature_humanities` | `metro` | `top_example` | 0.006482 | literature | accept_light_topic | Metre/meter is relevant to poetry and humanities, but transit/measurement senses compete. |
| `srs-src-topic-080` | `arts_literature_humanities` | `luz` | `band_example` | 6.4e-05 | architecture | accept_light_topic | Light is relevant to architecture/arts, but the word is broad. |
| `srs-src-topic-081` | `arts_literature_humanities` | `sombra` | `band_example` | 0.000207 | art, arts | accept_light_topic | Shadow/shading is useful in art vocabulary, but broad. |
| `srs-src-topic-082` | `arts_literature_humanities` | `afrodita` | `band_example` | 0.608917 | philosophy | accept_light_topic | Mythology/culture relevance is real, but proper-noun policy should stay light. |
| `srs-src-topic-083` | `arts_literature_humanities` | `paleolítico` | `hardest_example` | 0.166346 | history | accept_strong_topic | Direct history/humanities vocabulary. |
| `srs-src-topic-084` | `arts_literature_humanities` | `neutro` | `hardest_example` | 0.168765 | linguistics | accept_light_topic | Neutral/neuter grammar and humanities sense is relevant, but broad. |
| `srs-src-topic-085` | `arts_literature_humanities` | `reflexivo` | `hardest_example` | 0.169514 | linguistics | accept_strong_topic | Direct linguistics/grammar vocabulary. |

## Limitations

- This packet samples compact evidence retained by the depth audit, not every source row.
- Agent labels are pending user approval and do not promote runtime topic truth by themselves.
- Rejects in this sample should tighten release guidance before default-visible topics are accepted.
