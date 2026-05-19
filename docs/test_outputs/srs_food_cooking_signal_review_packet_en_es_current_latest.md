# en-es Food/Cooking Signal Review Packet

- Status: `ok`
- Decision: `srs_food_cooking_signal_review_packet_ready`
- Generated: `2026-05-19T01:00:30+00:00`
- Candidate universe: `46`
- Review rows: `46`
- Review cells covered: `16` / `16`
- Labeled rows: `46`

## Manual Decisions

- `accept_strong_topic`: `19`
- `accept_light_topic`: `18`
- `reject_wrong_topic`: `3`
- `reject_secondary_or_obscure_sense`: `6`
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
| `srs-food-001` | `frutar` | `D` | `review` | `gloss_or_translation:food_gloss_pattern` | 0.527 | `True` | `to fruit; bear fruit` | reject_wrong_topic | Fruit-bearing verb; more botany/agriculture than food/cooking vocabulary. |
| `srs-food-002` | `panadero` | `D` | `review` | `gloss_or_translation:food_gloss_pattern` | 0.527 | `True` | `baker (a person who bakes and sells bread, etc)` | accept_light_topic | Baker is cooking/food-profession vocabulary, but not a food item. |
| `srs-food-003` | `piltrafa` | `D` | `review` | `gloss_or_translation:food_gloss_pattern` | 0.527 | `True` | `scrap of meat` | accept_light_topic | Scrap of meat is food-related, but low-value and somewhat obscure. |
| `srs-food-004` | `ronda` | `D` | `review` | `gloss_or_translation:food_gloss_pattern` | 0.527 | `True` | `round, iteration (of drinks, golf, elections, cards, etc.)` | reject_secondary_or_obscure_sense | Round of drinks is a secondary collocational sense; dominant meaning is not food/cooking. |
| `srs-food-005` | `pelotazo` | `D` | `review` | `translation:food_translation_pattern` | 0.4536 | `True` | `drink` | reject_secondary_or_obscure_sense | Drink sense is slang/secondary; dominant topic is not food/cooking. |
| `srs-food-006` | `chica` | `D` | `review` | `translation:food_translation_pattern` | 0.4536 | `True` | `a spice made from the sobralia orchid.` | reject_secondary_or_obscure_sense | Spice sense is highly obscure; dominant meaning is not food/cooking. |
| `srs-food-007` | `pote` | `D` | `review` | `translation:food_translation_pattern` | 0.4536 | `True` | `stew` | accept_light_topic | Stew/pot culinary sense is real, but the word is polysemous. |
| `srs-food-008` | `tamal` | `C` | `review` | `entry_categories:foods` | 0.5719 | `True` | allowlisted_category_or_tag | accept_strong_topic | Direct prepared food item. |
| `srs-food-009` | `lomo` | `C` | `review` | `entry_categories:meats` | 0.5054 | `True` | allowlisted_category_or_tag | accept_light_topic | Loin/tenderloin culinary sense is real, but body/back senses compete. |
| `srs-food-010` | `farsa` | `D` | `inventory` | `gloss_or_translation:food_gloss_pattern` | 0.3689 | `True` | `farce (in gastronomy: forcemeat, stuffing, seasoned stuffing, ground meat fil...` | reject_secondary_or_obscure_sense | Gastronomy forcemeat sense is too obscure against the dominant farce/fiction meaning. |
| `srs-food-011` | `morocho` | `D` | `inventory` | `gloss_or_translation:food_gloss_pattern` | 0.3689 | `True` | `dark yellow and hard grain (colombia, ecuador, peru, chile, of corn) dark yel...` | accept_light_topic | Regional corn-grain sense is food-related, but regionally narrow and polysemous. |
| `srs-food-012` | `picante` | `D` | `inventory` | `gloss_or_translation:food_gloss_pattern` | 0.3689 | `True` | `hot sauce or any hot or spicy condiment or ingredient` | accept_strong_topic | Spicy/hot-sauce/condiment vocabulary is directly food-relevant. |
| `srs-food-013` | `sacar` | `D` | `inventory` | `gloss_or_translation:food_gloss_pattern` | 0.3689 | `True` | `to scoop (e.g. fruit, flour, sugar, salt, sand) (transitive) to scoop (e.g. f...` | reject_wrong_topic | Food appears only as example objects for a general verb. |
| `srs-food-014` | `corazón` | `D` | `inventory` | `gloss_or_translation:food_gloss_pattern` | 0.3689 | `True` | `core (of a fruit)` | reject_secondary_or_obscure_sense | Fruit core sense is secondary; dominant meaning is heart/core generally. |
| `srs-food-015` | `puerco` | `D` | `inventory` | `gloss_or_translation:food_gloss_pattern` | 0.3689 | `True` | `pork (the meat of a pig)` | accept_light_topic | Pork sense is food-related, but animal/adjectival senses compete. |
| `srs-food-016` | `acompañamiento` | `D` | `inventory` | `gloss_or_translation:food_gloss_pattern` | 0.3689 | `True` | `side dish` | accept_light_topic | Side-dish sense is useful but competes with broader accompaniment meanings. |
| `srs-food-017` | `dulce` | `D` | `inventory` | `gloss_or_translation:food_gloss_pattern` | 0.3689 | `True` | `sweet food, dessert` | accept_strong_topic | Sweet/candy/dessert vocabulary is directly food-relevant. |
| `srs-food-018` | `falda` | `D` | `inventory` | `gloss_or_translation:food_gloss_pattern` | 0.3689 | `True` | `brisket (a cut of meat) (butchery) brisket (a cut of meat)` | accept_light_topic | Brisket/cut-of-meat sense is real, but skirt/hillside senses compete. |
| `srs-food-019` | `fonda` | `D` | `inventory` | `gloss_or_translation:food_gloss_pattern` | 0.3689 | `True` | `boarding house, inn, or tavern providing lodging and meals` | accept_light_topic | Food-service venue sense is food-adjacent, not a direct food item. |
| `srs-food-020` | `empanada` | `C` | `medium` | `entry_categories:foods` | 0.817 | `True` | allowlisted_category_or_tag | accept_strong_topic | Direct prepared food item. |
| `srs-food-021` | `jalea` | `C` | `medium` | `entry_categories:foods` | 0.817 | `True` | allowlisted_category_or_tag | accept_strong_topic | Jelly/gelatin/dessert vocabulary is directly food-relevant. |
| `srs-food-022` | `ensalada` | `C` | `medium` | `entry_categories:foods` | 0.817 | `True` | allowlisted_category_or_tag | accept_strong_topic | Direct prepared food item. |
| `srs-food-023` | `pincho` | `C` | `medium` | `entry_categories:foods` | 0.817 | `True` | allowlisted_category_or_tag | accept_light_topic | Skewer/tapa sense is useful, but spike/piercing senses compete. |
| `srs-food-024` | `tortilla` | `C` | `medium` | `entry_categories:foods` | 0.817 | `True` | allowlisted_category_or_tag | accept_strong_topic | Direct prepared food item. |
| `srs-food-025` | `chipa` | `C` | `medium` | `entry_categories:foods` | 0.817 | `True` | allowlisted_category_or_tag | accept_strong_topic | Direct prepared food item. |
| `srs-food-026` | `papaya` | `C` | `medium` | `entry_categories:fruits` | 0.722 | `True` | allowlisted_category_or_tag | accept_strong_topic | Direct fruit/food item; vulgar secondary sense should not erase food membership. |
| `srs-food-027` | `naranja` | `C` | `medium` | `entry_categories:fruits` | 0.722 | `True` | allowlisted_category_or_tag | accept_strong_topic | Direct fruit/food item, despite color and political senses. |
| `srs-food-028` | `damasco` | `C` | `medium` | `entry_categories:fruits` | 0.722 | `True` | allowlisted_category_or_tag | accept_light_topic | Apricot sense is food-related, but damask/Damascus senses compete. |
| `srs-food-029` | `mariposa` | `C` | `medium` | `entry_categories:legumes` | 0.741 | `True` | allowlisted_category_or_tag | reject_wrong_topic | Legume category appears incidental; dominant meaning is butterfly, not food/cooking. |
| `srs-food-030` | `ave` | `C` | `medium` | `entry_categories:meats` | 0.722 | `True` | allowlisted_category_or_tag | accept_light_topic | Poultry/meat overlap is real, but the dominant word is animal/bird. |
| `srs-food-031` | `chancho` | `C` | `medium` | `entry_categories:meats` | 0.722 | `True` | allowlisted_category_or_tag | accept_light_topic | Pig/pork overlap is real, but animal and adjectival senses compete. |
| `srs-food-032` | `picadillo` | `C` | `medium` | `entry_categories:meats` | 0.722 | `True` | allowlisted_category_or_tag | accept_strong_topic | Minced meat or prepared dish vocabulary is directly food-relevant. |
| `srs-food-033` | `pichón` | `C` | `medium` | `entry_categories:meats` | 0.722 | `True` | allowlisted_category_or_tag | accept_light_topic | Squab/young pigeon food sense is real, but animal/person senses compete. |
| `srs-food-034` | `magro` | `C` | `medium` | `entry_categories:meats` | 0.722 | `True` | allowlisted_category_or_tag | accept_light_topic | Lean meat sense is real, but adjective/general senses compete. |
| `srs-food-035` | `erizo` | `C` | `medium` | `entry_categories:seafood` | 0.779 | `True` | allowlisted_category_or_tag | accept_light_topic | Seafood/sea-urchin culinary sense is real, but hedgehog/animal senses compete. |
| `srs-food-036` | `mejillón` | `C` | `medium` | `entry_categories:seafood` | 0.779 | `True` | allowlisted_category_or_tag | accept_strong_topic | Direct seafood item. |
| `srs-food-037` | `langostino` | `C` | `medium` | `sense_categories:seafood` | 0.779 | `True` | allowlisted_category_or_tag | accept_strong_topic | Direct seafood item. |
| `srs-food-038` | `caldo` | `C` | `medium` | `entry_categories:soups` | 0.798 | `True` | allowlisted_category_or_tag | accept_strong_topic | Broth/soup vocabulary is directly food-relevant. |
| `srs-food-039` | `puchero` | `C` | `medium` | `entry_categories:soups` | 0.798 | `True` | allowlisted_category_or_tag | accept_strong_topic | Stew/cooking-pot food sense is strong enough for food/cooking. |
| `srs-food-040` | `pimienta` | `C` | `medium` | `sense_categories:spices` | 0.798 | `True` | allowlisted_category_or_tag | accept_strong_topic | Direct spice/food ingredient. |
| `srs-food-041` | `cogollo` | `C` | `medium` | `entry_categories:vegetables` | 0.722 | `True` | allowlisted_category_or_tag | accept_light_topic | Vegetable heart/lettuce sense is food-related, but plant/anatomy senses compete. |
| `srs-food-042` | `canónigo` | `C` | `medium` | `entry_categories:vegetables` | 0.722 | `True` | allowlisted_category_or_tag | reject_secondary_or_obscure_sense | Corn-salad/vegetable sense is too secondary against the dominant clerical/person sense. |
| `srs-food-043` | `careta` | `A` | `medium` | `sense_topics:cooking` | 0.665 | `False` | explicit_sense_topic | accept_light_topic | Pork-cheek cooking sense is real but secondary to face/mask senses. |
| `srs-food-044` | `batido` | `A` | `medium` | `sense_topics:cooking` | 0.665 | `False` | explicit_sense_topic | accept_strong_topic | Batter/smoothie/milkshake cooking and drink senses are directly food/cooking. |
| `srs-food-045` | `cereal` | `B` | `high` | `translation:primary_translation:cereal` | 0.855 | `False` | `cereal (type of grass cultivated for edible grains)` | accept_strong_topic | Direct food/grain/cereal vocabulary. |
| `srs-food-046` | `té` | `B` | `high` | `translation:primary_translation:tea` | 0.855 | `False` | `tea` | accept_strong_topic | Direct drink vocabulary. |

## Limitations

- The packet reviews existing audit candidates only; it does not collect new food data.
- The current food/cooking audit is intentionally conservative and not a final recall target.
- Rows are selected deterministically by review cell and stable hash, not by model judgment.
- Pending or agent labels are QA surfaces and must not be treated as approved overlay data.
