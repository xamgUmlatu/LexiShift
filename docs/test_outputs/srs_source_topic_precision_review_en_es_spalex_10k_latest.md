# en-es Source Topic Precision Review

- Status: `ok`
- Decision: `srs_source_topic_precision_review_ready`
- Generated: `2026-05-19T04:54:43.644770+00:00`
- Reviewed rows: `54`
- Accepted rows: `32` (59.3%)
- Rejected rows: `22` (40.7%)
- Pending rows: `0`

## Findings

- `PASS` `frontier_available`: Depth-audit frontier exists.
- `PASS` `release_topics_selected`: Release-candidate topics were selected.
- `PASS` `review_rows_present`: Review rows were generated.
- `PASS` `manual_labels_applied`: Manual labels applied.
- `PASS` `accepted_majority`: Accepted rows outnumber rejects in the reviewed sample.
- `WARN` `source_false_positive_classes_present`: Rejects identify source-label false-positive classes before promotion.
- `WARN` `family_precision_review_needed`: High sample reject rates need review for: arts_literature_humanities, science_technology, games

## Precision By Family

| Label | Rows | Accepted | Strong | Light | Rejected | Reject Rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `arts_literature_humanities` | 12 | 5 | 1 | 4 | 7 | 58.3% |
| `science_technology` | 12 | 6 | 3 | 3 | 6 | 50.0% |
| `games` | 10 | 5 | 0 | 5 | 5 | 50.0% |
| `law_politics_civics` | 10 | 8 | 2 | 6 | 2 | 20.0% |
| `sports_fitness` | 10 | 8 | 0 | 8 | 2 | 20.0% |

## Notable Source Labels

| Label | Rows | Accepted | Strong | Light | Rejected | Reject Rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `sciences` | 11 | 6 | 3 | 3 | 5 | 45.5% |
| `games` | 10 | 5 | 0 | 5 | 5 | 50.0% |
| `sports` | 10 | 8 | 0 | 8 | 2 | 20.0% |
| `law` | 8 | 6 | 2 | 4 | 2 | 25.0% |
| `mathematics` | 8 | 5 | 2 | 3 | 3 | 37.5% |
| `engineering` | 6 | 4 | 2 | 2 | 2 | 33.3% |
| `natural_sciences` | 6 | 4 | 2 | 2 | 2 | 33.3% |
| `physical_sciences` | 6 | 4 | 2 | 2 | 2 | 33.3% |
| `ball_games` | 4 | 3 | 0 | 3 | 1 | 25.0% |
| `computing` | 4 | 3 | 1 | 2 | 1 | 25.0% |
| `linguistics` | 4 | 1 | 1 | 0 | 3 | 75.0% |
| `literature` | 4 | 3 | 1 | 2 | 1 | 25.0% |
| `government` | 3 | 3 | 0 | 3 | 0 | 0.0% |
| `philosophy` | 3 | 1 | 0 | 1 | 2 | 66.7% |
| `soccer` | 3 | 3 | 0 | 3 | 0 | 0.0% |
| `architecture` | 2 | 1 | 0 | 1 | 1 | 50.0% |
| `physics` | 2 | 1 | 1 | 0 | 1 | 50.0% |
| `politics` | 2 | 2 | 0 | 2 | 0 | 0.0% |
| `arts` | 1 | 1 | 0 | 1 | 0 | 0.0% |
| `baseball` | 1 | 0 | 0 | 0 | 1 | 100.0% |
| `card_games` | 1 | 1 | 0 | 1 | 0 | 0.0% |
| `video_games` | 1 | 1 | 0 | 1 | 0 | 0.0% |

## Rejected Rows

- `sports_fitness` `reunión`: `reject_secondary_or_obscure_sense` - Meeting is too broad; sports relevance is not learner-facing topic evidence.
- `sports_fitness` `center`: `reject_wrong_topic` - English artifact, not a Spanish learner-facing sports lemma.
- `games` `entrada`: `reject_secondary_or_obscure_sense` - Game relevance is too generic without a stronger source label.
- `games` `sacar`: `reject_secondary_or_obscure_sense` - Game-card draw or play sense is too weak for release evidence.
- `games` `center`: `reject_wrong_topic` - English artifact, not a Spanish learner-facing games lemma.
- `games` `recortar`: `reject_secondary_or_obscure_sense` - No clear game-topic sense for user-facing preference evidence.
- `games` `encerrar`: `reject_secondary_or_obscure_sense` - Possible gameplay action is too generic to count as topic evidence.
- `law_politics_civics` `apartar`: `reject_secondary_or_obscure_sense` - Legal removal/disqualification sense is too narrow without corroboration.
- `law_politics_civics` `duplicar`: `reject_wrong_topic` - Duplicate/double does not provide clear law or civics topic evidence.
- `science_technology` `pincho`: `reject_secondary_or_obscure_sense` - Possible technical accessory sense is too regional/polysemous for release evidence.
- `science_technology` `poner`: `reject_secondary_or_obscure_sense` - General verb is too broad for topic evidence despite source labels.
- `science_technology` `más`: `reject_secondary_or_obscure_sense` - Function word/math operator sense is not useful topic evidence.
- `science_technology` `activamente`: `reject_secondary_or_obscure_sense` - Adverbial scientific-context use is too indirect.
- `science_technology` `por`: `reject_secondary_or_obscure_sense` - Function word/math operator sense is not useful topic evidence.
- `science_technology` `venus`: `reject_secondary_or_obscure_sense` - Proper-noun planet sense is too source-fragile under generic science labels.
- `arts_literature_humanities` `auto`: `reject_secondary_or_obscure_sense` - Literary auto sense is narrow and car/auto senses dominate.
- `arts_literature_humanities` `falta`: `reject_secondary_or_obscure_sense` - Linguistic use is too indirect for learner-facing humanities evidence.
- `arts_literature_humanities` `cerrar`: `reject_secondary_or_obscure_sense` - Linguistic close-vowel sense is too technical and broad.
- `arts_literature_humanities` `situar`: `reject_secondary_or_obscure_sense` - Architecture or composition sense is too broad for topic evidence.
- `arts_literature_humanities` `activamente`: `reject_secondary_or_obscure_sense` - Possible grammar relation is too indirect.
- `arts_literature_humanities` `venus`: `reject_secondary_or_obscure_sense` - Proper-noun mythology/art relevance is too source-fragile under philosophy.
- `arts_literature_humanities` `rea`: `reject_secondary_or_obscure_sense` - Proper-noun mythology relevance is too source-fragile under philosophy.

## Review Queue

| ID | Family | Lemma | Sample | Difficulty | Source Labels | Decision | Notes |
| --- | --- | --- | --- | ---: | --- | --- | --- |
| `srs-src-topic-001` | `sports_fitness` | `reunión` | `top_example` | 0.000141 | sports | reject_secondary_or_obscure_sense | Meeting is too broad; sports relevance is not learner-facing topic evidence. |
| `srs-src-topic-002` | `sports_fitness` | `entrada` | `top_example` | 0.000209 | ball_games, soccer, sports | accept_light_topic | Tackle/ticket/entry sports senses exist, but the lemma is highly polysemous. |
| `srs-src-topic-003` | `sports_fitness` | `pista` | `top_example` | 0.000441 | sports | accept_light_topic | Track/court sense is useful for sports, but clue/trail senses compete. |
| `srs-src-topic-004` | `sports_fitness` | `palo` | `top_example` | 0.000475 | sports | accept_light_topic | Stick/post sports senses are real, but the word is broad. |
| `srs-src-topic-005` | `sports_fitness` | `sacar` | `band_example` | 0.300049 | ball_games, soccer, sports | accept_light_topic | Serve/kick-off use is real, but the general verb is very broad. |
| `srs-src-topic-006` | `sports_fitness` | `marcar` | `band_example` | 0.300149 | sports | accept_light_topic | Score/mark is common sports vocabulary, but the non-sports senses are broad. |
| `srs-src-topic-007` | `sports_fitness` | `center` | `band_example` | 0.600677 | ball_games, baseball, sports | reject_wrong_topic | English artifact, not a Spanish learner-facing sports lemma. |
| `srs-src-topic-008` | `sports_fitness` | `remontar` | `hardest_example` | 0.313915 | sports | accept_light_topic | Comeback sense is common in sports, but the verb also has general senses. |
| `srs-src-topic-009` | `sports_fitness` | `fichar` | `hardest_example` | 0.314717 | sports | accept_light_topic | Player-signing sense is useful, but hiring/registering senses compete. |
| `srs-src-topic-010` | `sports_fitness` | `despejar` | `hardest_example` | 0.315153 | ball_games, soccer, sports | accept_light_topic | Clear-the-ball sense is real, but the verb is not sports-exclusive. |
| `srs-src-topic-011` | `games` | `jefe` | `top_example` | 0.000122 | games, video_games | accept_light_topic | Boss-enemy sense is real in games, but chief/boss senses dominate generally. |
| `srs-src-topic-012` | `games` | `corazón` | `top_example` | 0.000149 | card_games, games | accept_light_topic | Card-suit and game-life senses are useful, but heart/body senses compete. |
| `srs-src-topic-013` | `games` | `entrada` | `top_example` | 0.000209 | games | reject_secondary_or_obscure_sense | Game relevance is too generic without a stronger source label. |
| `srs-src-topic-014` | `games` | `pista` | `top_example` | 0.000441 | games | accept_light_topic | Clue/hint sense is useful for games, but non-game senses compete. |
| `srs-src-topic-015` | `games` | `sacar` | `band_example` | 0.300049 | games | reject_secondary_or_obscure_sense | Game-card draw or play sense is too weak for release evidence. |
| `srs-src-topic-016` | `games` | `cargar` | `band_example` | 0.30027 | games | accept_light_topic | Load-game sense is real, but charge/load senses are broad. |
| `srs-src-topic-017` | `games` | `center` | `band_example` | 0.600677 | games | reject_wrong_topic | English artifact, not a Spanish learner-facing games lemma. |
| `srs-src-topic-018` | `games` | `recortar` | `hardest_example` | 0.313105 | games | reject_secondary_or_obscure_sense | No clear game-topic sense for user-facing preference evidence. |
| `srs-src-topic-019` | `games` | `encerrar` | `hardest_example` | 0.314254 | games | reject_secondary_or_obscure_sense | Possible gameplay action is too generic to count as topic evidence. |
| `srs-src-topic-020` | `games` | `despejar` | `hardest_example` | 0.315153 | games | accept_light_topic | Clear-board or clear-area gameplay sense is real, but broad. |
| `srs-src-topic-021` | `law_politics_civics` | `jefe` | `top_example` | 0.000122 | government, politics | accept_light_topic | Leader/chief is civics-adjacent, but the lemma is broad. |
| `srs-src-topic-022` | `law_politics_civics` | `demanda` | `top_example` | 0.000228 | law | accept_strong_topic | Direct legal vocabulary for claim/lawsuit. |
| `srs-src-topic-023` | `law_politics_civics` | `tropa` | `top_example` | 0.000255 | government, politics | accept_light_topic | Military/government vocabulary is relevant, but not strictly civics. |
| `srs-src-topic-024` | `law_politics_civics` | `órgano` | `top_example` | 0.000273 | law | accept_light_topic | Institutional body sense is relevant, but body-organ sense competes. |
| `srs-src-topic-025` | `law_politics_civics` | `presentar` | `band_example` | 0.30003 | government, law | accept_light_topic | File/submit a legal or government document is relevant, but broad. |
| `srs-src-topic-026` | `law_politics_civics` | `recurrir` | `band_example` | 0.30034 | law | accept_strong_topic | Appeal/legal recourse sense is direct legal vocabulary. |
| `srs-src-topic-027` | `law_politics_civics` | `apartar` | `band_example` | 0.600822 | law | reject_secondary_or_obscure_sense | Legal removal/disqualification sense is too narrow without corroboration. |
| `srs-src-topic-028` | `law_politics_civics` | `fallar` | `hardest_example` | 0.314114 | law | accept_light_topic | Rule/decide in court is relevant, but fail/misfire senses compete. |
| `srs-src-topic-029` | `law_politics_civics` | `reivindicar` | `hardest_example` | 0.31484 | law | accept_light_topic | Claim/assert-rights sense is relevant, but not exclusively legal. |
| `srs-src-topic-030` | `law_politics_civics` | `duplicar` | `hardest_example` | 0.315088 | law | reject_wrong_topic | Duplicate/double does not provide clear law or civics topic evidence. |
| `srs-src-topic-031` | `science_technology` | `entrada` | `top_example` | 0.000209 | computing, engineering, mathematics, natural_sciences, physical_sciences, sciences | accept_light_topic | Input/entry sense is useful in computing, but the lemma is broad. |
| `srs-src-topic-032` | `science_technology` | `defecto` | `top_example` | 0.000641 | computing, engineering, mathematics, natural_sciences, physical_sciences, sciences | accept_light_topic | Defect/fault is useful in engineering and technology, but broad. |
| `srs-src-topic-033` | `science_technology` | `controlador` | `top_example` | 0.002736 | computing, engineering, mathematics, natural_sciences, physical_sciences, sciences | accept_strong_topic | Direct controller/driver technical vocabulary. |
| `srs-src-topic-034` | `science_technology` | `pincho` | `top_example` | 0.003703 | computing, engineering, mathematics, natural_sciences, physical_sciences, sciences | reject_secondary_or_obscure_sense | Possible technical accessory sense is too regional/polysemous for release evidence. |
| `srs-src-topic-035` | `science_technology` | `luz` | `band_example` | 6.4e-05 | engineering, natural_sciences, physical_sciences, physics, sciences | accept_strong_topic | Direct physics/science vocabulary. |
| `srs-src-topic-036` | `science_technology` | `área` | `band_example` | 9.3e-05 | mathematics, sciences | accept_strong_topic | Direct mathematics/science vocabulary. |
| `srs-src-topic-037` | `science_technology` | `poner` | `band_example` | 0.300013 | engineering, natural_sciences, physical_sciences, physics | reject_secondary_or_obscure_sense | General verb is too broad for topic evidence despite source labels. |
| `srs-src-topic-038` | `science_technology` | `trasladar` | `band_example` | 0.300196 | mathematics, sciences | accept_light_topic | Translate/transfer sense is relevant in math or engineering, but broad. |
| `srs-src-topic-039` | `science_technology` | `más` | `band_example` | 0.450002 | mathematics, sciences | reject_secondary_or_obscure_sense | Function word/math operator sense is not useful topic evidence. |
| `srs-src-topic-040` | `science_technology` | `activamente` | `band_example` | 0.455584 | sciences | reject_secondary_or_obscure_sense | Adverbial scientific-context use is too indirect. |
| `srs-src-topic-041` | `science_technology` | `por` | `band_example` | 0.601681 | mathematics, sciences | reject_secondary_or_obscure_sense | Function word/math operator sense is not useful topic evidence. |
| `srs-src-topic-042` | `science_technology` | `venus` | `band_example` | 0.604191 | sciences | reject_secondary_or_obscure_sense | Proper-noun planet sense is too source-fragile under generic science labels. |
| `srs-src-topic-043` | `arts_literature_humanities` | `auto` | `top_example` | 0.000367 | literature | reject_secondary_or_obscure_sense | Literary auto sense is narrow and car/auto senses dominate. |
| `srs-src-topic-044` | `arts_literature_humanities` | `pie` | `top_example` | 0.005291 | arts, literature | accept_light_topic | Verse/footnote/text sense is relevant, but body-part sense dominates. |
| `srs-src-topic-045` | `arts_literature_humanities` | `género` | `top_example` | 0.005341 | linguistics, literature | accept_strong_topic | Direct genre/linguistics/literature vocabulary. |
| `srs-src-topic-046` | `arts_literature_humanities` | `concepto` | `top_example` | 0.005438 | literature | accept_light_topic | Useful humanities vocabulary, but broad. |
| `srs-src-topic-047` | `arts_literature_humanities` | `luz` | `band_example` | 6.4e-05 | architecture | accept_light_topic | Light is relevant to architecture/arts, but the word is broad. |
| `srs-src-topic-048` | `arts_literature_humanities` | `falta` | `band_example` | 0.000112 | linguistics | reject_secondary_or_obscure_sense | Linguistic use is too indirect for learner-facing humanities evidence. |
| `srs-src-topic-049` | `arts_literature_humanities` | `cerrar` | `band_example` | 0.305356 | linguistics | reject_secondary_or_obscure_sense | Linguistic close-vowel sense is too technical and broad. |
| `srs-src-topic-050` | `arts_literature_humanities` | `situar` | `band_example` | 0.309134 | architecture | reject_secondary_or_obscure_sense | Architecture or composition sense is too broad for topic evidence. |
| `srs-src-topic-051` | `arts_literature_humanities` | `activamente` | `band_example` | 0.455584 | linguistics | reject_secondary_or_obscure_sense | Possible grammar relation is too indirect. |
| `srs-src-topic-052` | `arts_literature_humanities` | `venus` | `band_example` | 0.604191 | philosophy | reject_secondary_or_obscure_sense | Proper-noun mythology/art relevance is too source-fragile under philosophy. |
| `srs-src-topic-053` | `arts_literature_humanities` | `rea` | `band_example` | 0.604397 | philosophy | reject_secondary_or_obscure_sense | Proper-noun mythology relevance is too source-fragile under philosophy. |
| `srs-src-topic-054` | `arts_literature_humanities` | `afrodita` | `hardest_example` | 0.608917 | philosophy | accept_light_topic | Mythology/culture relevance is real, but proper-noun policy should stay light. |

## Limitations

- This packet samples compact evidence retained by the depth audit, not every source row.
- Agent labels are pending user approval and do not promote runtime topic truth by themselves.
- Rejects in this sample should tighten release guidance before default-visible topics are accepted.
