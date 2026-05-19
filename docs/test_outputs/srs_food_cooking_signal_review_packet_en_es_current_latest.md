# en-es Food/Cooking Signal Review Packet

- Status: `ok`
- Decision: `srs_food_cooking_signal_review_packet_ready`
- Generated: `2026-05-19T00:51:53+00:00`
- Candidate universe: `46`
- Review rows: `46`
- Review cells covered: `16` / `16`
- Labeled rows: `0`

## Manual Decisions

- `accept_strong_topic`: `0`
- `accept_light_topic`: `0`
- `reject_wrong_topic`: `0`
- `reject_secondary_or_obscure_sense`: `0`
- `uncertain_needs_source_check`: `0`

## Cell Coverage

| Cell | Candidates | Selected |
| --- | ---: | ---: |
| `food_cooking|tier=D|band=review|review=True|source=food_gloss_pattern` | 4 | 4 |
| `food_cooking|tier=D|band=review|review=True|source=food_translation_pattern` | 3 | 3 |
| `food_cooking|tier=C|band=review|review=True|source=foods` | 1 | 1 |
| `food_cooking|tier=C|band=review|review=True|source=meats` | 1 | 1 |
| `food_cooking|tier=D|band=inventory|review=True|source=food_gloss_pattern` | 10 | 10 |
| `food_cooking|tier=C|band=medium|review=True|source=foods` | 6 | 6 |
| `food_cooking|tier=C|band=medium|review=True|source=fruits` | 3 | 3 |
| `food_cooking|tier=C|band=medium|review=True|source=legumes` | 1 | 1 |
| `food_cooking|tier=C|band=medium|review=True|source=meats` | 5 | 5 |
| `food_cooking|tier=C|band=medium|review=True|source=seafood` | 3 | 3 |
| `food_cooking|tier=C|band=medium|review=True|source=soups` | 2 | 2 |
| `food_cooking|tier=C|band=medium|review=True|source=spices` | 1 | 1 |
| `food_cooking|tier=C|band=medium|review=True|source=vegetables` | 2 | 2 |
| `food_cooking|tier=A|band=medium|review=False|source=cooking` | 2 | 2 |
| `food_cooking|tier=B|band=high|review=False|source=primary_translation:cereal` | 1 | 1 |
| `food_cooking|tier=B|band=high|review=False|source=primary_translation:tea` | 1 | 1 |

## Manual Review Queue

| ID | Lemma | Tier | Band | Source | Score | Review? | Evidence | Decision | Notes |
| --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- |
| `srs-food-001` | `frutar` | `D` | `review` | `gloss_or_translation:food_gloss_pattern` | 0.527 | `True` | `to fruit; bear fruit` |  |  |
| `srs-food-002` | `panadero` | `D` | `review` | `gloss_or_translation:food_gloss_pattern` | 0.527 | `True` | `baker (a person who bakes and sells bread, etc)` |  |  |
| `srs-food-003` | `piltrafa` | `D` | `review` | `gloss_or_translation:food_gloss_pattern` | 0.527 | `True` | `scrap of meat` |  |  |
| `srs-food-004` | `ronda` | `D` | `review` | `gloss_or_translation:food_gloss_pattern` | 0.527 | `True` | `round, iteration (of drinks, golf, elections, cards, etc.)` |  |  |
| `srs-food-005` | `pelotazo` | `D` | `review` | `translation:food_translation_pattern` | 0.4536 | `True` | `drink` |  |  |
| `srs-food-006` | `chica` | `D` | `review` | `translation:food_translation_pattern` | 0.4536 | `True` | `a spice made from the sobralia orchid.` |  |  |
| `srs-food-007` | `pote` | `D` | `review` | `translation:food_translation_pattern` | 0.4536 | `True` | `stew` |  |  |
| `srs-food-008` | `tamal` | `C` | `review` | `entry_categories:foods` | 0.5719 | `True` | allowlisted_category_or_tag |  |  |
| `srs-food-009` | `lomo` | `C` | `review` | `entry_categories:meats` | 0.5054 | `True` | allowlisted_category_or_tag |  |  |
| `srs-food-010` | `farsa` | `D` | `inventory` | `gloss_or_translation:food_gloss_pattern` | 0.3689 | `True` | `farce (in gastronomy: forcemeat, stuffing, seasoned stuffing, ground meat fil...` |  |  |
| `srs-food-011` | `morocho` | `D` | `inventory` | `gloss_or_translation:food_gloss_pattern` | 0.3689 | `True` | `dark yellow and hard grain (colombia, ecuador, peru, chile, of corn) dark yel...` |  |  |
| `srs-food-012` | `picante` | `D` | `inventory` | `gloss_or_translation:food_gloss_pattern` | 0.3689 | `True` | `hot sauce or any hot or spicy condiment or ingredient` |  |  |
| `srs-food-013` | `sacar` | `D` | `inventory` | `gloss_or_translation:food_gloss_pattern` | 0.3689 | `True` | `to scoop (e.g. fruit, flour, sugar, salt, sand) (transitive) to scoop (e.g. f...` |  |  |
| `srs-food-014` | `corazón` | `D` | `inventory` | `gloss_or_translation:food_gloss_pattern` | 0.3689 | `True` | `core (of a fruit)` |  |  |
| `srs-food-015` | `puerco` | `D` | `inventory` | `gloss_or_translation:food_gloss_pattern` | 0.3689 | `True` | `pork (the meat of a pig)` |  |  |
| `srs-food-016` | `acompañamiento` | `D` | `inventory` | `gloss_or_translation:food_gloss_pattern` | 0.3689 | `True` | `side dish` |  |  |
| `srs-food-017` | `dulce` | `D` | `inventory` | `gloss_or_translation:food_gloss_pattern` | 0.3689 | `True` | `sweet food, dessert` |  |  |
| `srs-food-018` | `falda` | `D` | `inventory` | `gloss_or_translation:food_gloss_pattern` | 0.3689 | `True` | `brisket (a cut of meat) (butchery) brisket (a cut of meat)` |  |  |
| `srs-food-019` | `fonda` | `D` | `inventory` | `gloss_or_translation:food_gloss_pattern` | 0.3689 | `True` | `boarding house, inn, or tavern providing lodging and meals` |  |  |
| `srs-food-020` | `empanada` | `C` | `medium` | `entry_categories:foods` | 0.817 | `True` | allowlisted_category_or_tag |  |  |
| `srs-food-021` | `jalea` | `C` | `medium` | `entry_categories:foods` | 0.817 | `True` | allowlisted_category_or_tag |  |  |
| `srs-food-022` | `ensalada` | `C` | `medium` | `entry_categories:foods` | 0.817 | `True` | allowlisted_category_or_tag |  |  |
| `srs-food-023` | `pincho` | `C` | `medium` | `entry_categories:foods` | 0.817 | `True` | allowlisted_category_or_tag |  |  |
| `srs-food-024` | `tortilla` | `C` | `medium` | `entry_categories:foods` | 0.817 | `True` | allowlisted_category_or_tag |  |  |
| `srs-food-025` | `chipa` | `C` | `medium` | `entry_categories:foods` | 0.817 | `True` | allowlisted_category_or_tag |  |  |
| `srs-food-026` | `papaya` | `C` | `medium` | `entry_categories:fruits` | 0.722 | `True` | allowlisted_category_or_tag |  |  |
| `srs-food-027` | `naranja` | `C` | `medium` | `entry_categories:fruits` | 0.722 | `True` | allowlisted_category_or_tag |  |  |
| `srs-food-028` | `damasco` | `C` | `medium` | `entry_categories:fruits` | 0.722 | `True` | allowlisted_category_or_tag |  |  |
| `srs-food-029` | `mariposa` | `C` | `medium` | `entry_categories:legumes` | 0.741 | `True` | allowlisted_category_or_tag |  |  |
| `srs-food-030` | `ave` | `C` | `medium` | `entry_categories:meats` | 0.722 | `True` | allowlisted_category_or_tag |  |  |
| `srs-food-031` | `chancho` | `C` | `medium` | `entry_categories:meats` | 0.722 | `True` | allowlisted_category_or_tag |  |  |
| `srs-food-032` | `picadillo` | `C` | `medium` | `entry_categories:meats` | 0.722 | `True` | allowlisted_category_or_tag |  |  |
| `srs-food-033` | `pichón` | `C` | `medium` | `entry_categories:meats` | 0.722 | `True` | allowlisted_category_or_tag |  |  |
| `srs-food-034` | `magro` | `C` | `medium` | `entry_categories:meats` | 0.722 | `True` | allowlisted_category_or_tag |  |  |
| `srs-food-035` | `erizo` | `C` | `medium` | `entry_categories:seafood` | 0.779 | `True` | allowlisted_category_or_tag |  |  |
| `srs-food-036` | `mejillón` | `C` | `medium` | `entry_categories:seafood` | 0.779 | `True` | allowlisted_category_or_tag |  |  |
| `srs-food-037` | `langostino` | `C` | `medium` | `sense_categories:seafood` | 0.779 | `True` | allowlisted_category_or_tag |  |  |
| `srs-food-038` | `caldo` | `C` | `medium` | `entry_categories:soups` | 0.798 | `True` | allowlisted_category_or_tag |  |  |
| `srs-food-039` | `puchero` | `C` | `medium` | `entry_categories:soups` | 0.798 | `True` | allowlisted_category_or_tag |  |  |
| `srs-food-040` | `pimienta` | `C` | `medium` | `sense_categories:spices` | 0.798 | `True` | allowlisted_category_or_tag |  |  |
| `srs-food-041` | `cogollo` | `C` | `medium` | `entry_categories:vegetables` | 0.722 | `True` | allowlisted_category_or_tag |  |  |
| `srs-food-042` | `canónigo` | `C` | `medium` | `entry_categories:vegetables` | 0.722 | `True` | allowlisted_category_or_tag |  |  |
| `srs-food-043` | `careta` | `A` | `medium` | `sense_topics:cooking` | 0.665 | `False` | explicit_sense_topic |  |  |
| `srs-food-044` | `batido` | `A` | `medium` | `sense_topics:cooking` | 0.665 | `False` | explicit_sense_topic |  |  |
| `srs-food-045` | `cereal` | `B` | `high` | `translation:primary_translation:cereal` | 0.855 | `False` | `cereal (type of grass cultivated for edible grains)` |  |  |
| `srs-food-046` | `té` | `B` | `high` | `translation:primary_translation:tea` | 0.855 | `False` | `tea` |  |  |

## Limitations

- The packet reviews existing audit candidates only; it does not collect new food data.
- The current food/cooking audit is intentionally conservative and not a final recall target.
- Rows are selected deterministically by review cell and stable hash, not by model judgment.
- Pending or agent labels are QA surfaces and must not be treated as approved overlay data.
