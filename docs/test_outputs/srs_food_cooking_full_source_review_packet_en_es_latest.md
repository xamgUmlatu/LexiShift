# en-es Food/Cooking Full-Source Review Packet

- Status: `ok`
- Decision: `srs_food_cooking_full_source_review_packet_ready`
- Generated: `2026-05-19T02:38:12+00:00`
- Candidate universe: `2076`
- Review rows: `96`
- Review cells covered: `80` / `80`
- Labeled rows: `96`

## Source Scope

- Scope: `full_local_kaikki_minus_current_frontier`
- Source candidates: `2122`
- Excluded current-frontier candidates: `46`
- Expansion candidates sampled from: `2076`

## Review Interpretation

- Accepted rows: `91` / `96`
- Strong accepts: `54`
- Light accepts: `37`
- Rejected rows: `5`

Rejected rows:
- `maní forrajero`: `reject_wrong_topic` (C/legumes)
- `artrodiro`: `reject_wrong_topic` (C/fish)
- `pavía`: `reject_secondary_or_obscure_sense` (C/fruits)
- `carnívoro`: `reject_wrong_topic` (D/food_gloss_pattern)
- `reo`: `reject_secondary_or_obscure_sense` (C/fish)

## Manual Decisions

- `accept_strong_topic`: `54`
- `accept_light_topic`: `37`
- `reject_wrong_topic`: `3`
- `reject_secondary_or_obscure_sense`: `2`
- `uncertain_needs_source_check`: `0`

## Cell Coverage

| Cell | Candidates | Selected |
| --- | ---: | ---: |
| `food_cooking|tier=D|band=review|review=True|source=food_gloss_pattern` | 432 | 2 |
| `food_cooking|tier=D|band=review|review=True|source=food_translation_pattern` | 144 | 2 |
| `food_cooking|tier=C|band=review|review=True|source=alcoholic_beverages` | 1 | 1 |
| `food_cooking|tier=C|band=review|review=True|source=beverages` | 3 | 2 |
| `food_cooking|tier=C|band=review|review=True|source=cooking` | 1 | 1 |
| `food_cooking|tier=C|band=review|review=True|source=desserts` | 2 | 2 |
| `food_cooking|tier=C|band=review|review=True|source=fish` | 8 | 2 |
| `food_cooking|tier=C|band=review|review=True|source=foods` | 2 | 2 |
| `food_cooking|tier=C|band=review|review=True|source=fruits` | 10 | 2 |
| `food_cooking|tier=C|band=review|review=True|source=herbs` | 3 | 2 |
| `food_cooking|tier=C|band=review|review=True|source=legumes` | 2 | 2 |
| `food_cooking|tier=C|band=review|review=True|source=meats` | 2 | 2 |
| `food_cooking|tier=C|band=review|review=True|source=sauces` | 1 | 1 |
| `food_cooking|tier=C|band=review|review=True|source=spices` | 2 | 2 |
| `food_cooking|tier=C|band=review|review=True|source=spices_and_herbs` | 11 | 2 |
| `food_cooking|tier=C|band=review|review=True|source=vegetables` | 10 | 2 |
| `food_cooking|tier=B|band=review|review=True|source=primary_translation:beer` | 4 | 2 |
| `food_cooking|tier=B|band=review|review=True|source=primary_translation:food` | 1 | 1 |
| `food_cooking|tier=B|band=review|review=True|source=primary_translation:tomato` | 1 | 1 |
| `food_cooking|tier=D|band=inventory|review=True|source=food_gloss_pattern` | 164 | 2 |
| `food_cooking|tier=C|band=inventory|review=True|source=fish` | 5 | 2 |
| `food_cooking|tier=C|band=medium|review=True|source=alcoholic_beverages` | 32 | 1 |
| `food_cooking|tier=C|band=medium|review=True|source=beverages` | 48 | 1 |
| `food_cooking|tier=C|band=medium|review=True|source=breads` | 29 | 1 |
| `food_cooking|tier=C|band=medium|review=True|source=cheeses` | 18 | 1 |
| `food_cooking|tier=C|band=medium|review=True|source=dairy_products` | 6 | 1 |
| `food_cooking|tier=C|band=medium|review=True|source=desserts` | 40 | 1 |
| `food_cooking|tier=C|band=medium|review=True|source=fish` | 97 | 1 |
| `food_cooking|tier=C|band=medium|review=True|source=foods` | 255 | 1 |
| `food_cooking|tier=C|band=medium|review=True|source=fruits` | 121 | 1 |
| `food_cooking|tier=C|band=medium|review=True|source=grains` | 21 | 1 |
| `food_cooking|tier=C|band=medium|review=True|source=herbs` | 28 | 1 |
| `food_cooking|tier=C|band=medium|review=True|source=legumes` | 66 | 1 |
| `food_cooking|tier=C|band=medium|review=True|source=meats` | 64 | 1 |
| `food_cooking|tier=C|band=medium|review=True|source=nuts` | 9 | 1 |
| `food_cooking|tier=C|band=medium|review=True|source=sauces` | 71 | 1 |
| `food_cooking|tier=C|band=medium|review=True|source=seafood` | 38 | 1 |
| `food_cooking|tier=C|band=medium|review=True|source=soups` | 24 | 1 |
| `food_cooking|tier=C|band=medium|review=True|source=spices` | 14 | 1 |
| `food_cooking|tier=C|band=medium|review=True|source=spices_and_herbs` | 31 | 1 |
| `food_cooking|tier=C|band=medium|review=True|source=vegetables` | 74 | 1 |
| `food_cooking|tier=C|band=high|review=True|source=cooking` | 35 | 1 |
| `food_cooking|tier=A|band=medium|review=False|source=cooking` | 25 | 1 |
| `food_cooking|tier=A|band=medium|review=False|source=food` | 6 | 1 |
| `food_cooking|tier=B|band=high|review=False|source=primary_translation:apple` | 1 | 1 |
| `food_cooking|tier=B|band=high|review=False|source=primary_translation:banana` | 6 | 1 |
| `food_cooking|tier=B|band=high|review=False|source=primary_translation:bean` | 2 | 1 |
| `food_cooking|tier=B|band=high|review=False|source=primary_translation:beef` | 2 | 1 |
| `food_cooking|tier=B|band=high|review=False|source=primary_translation:beer` | 7 | 1 |
| `food_cooking|tier=B|band=high|review=False|source=primary_translation:bread` | 1 | 1 |
| `food_cooking|tier=B|band=high|review=False|source=primary_translation:butter` | 1 | 1 |
| `food_cooking|tier=B|band=high|review=False|source=primary_translation:cheese` | 2 | 1 |
| `food_cooking|tier=B|band=high|review=False|source=primary_translation:chicken` | 3 | 1 |
| `food_cooking|tier=B|band=high|review=False|source=primary_translation:coffee` | 2 | 1 |
| `food_cooking|tier=B|band=high|review=False|source=primary_translation:corn` | 2 | 1 |
| `food_cooking|tier=B|band=high|review=False|source=primary_translation:dessert` | 1 | 1 |
| `food_cooking|tier=B|band=high|review=False|source=primary_translation:dish` | 1 | 1 |
| `food_cooking|tier=B|band=high|review=False|source=primary_translation:drink` | 3 | 1 |
| `food_cooking|tier=B|band=high|review=False|source=primary_translation:egg` | 1 | 1 |
| `food_cooking|tier=B|band=high|review=False|source=primary_translation:fish` | 2 | 1 |
| `food_cooking|tier=B|band=high|review=False|source=primary_translation:food` | 4 | 1 |
| `food_cooking|tier=B|band=high|review=False|source=primary_translation:fruit` | 1 | 1 |
| `food_cooking|tier=B|band=high|review=False|source=primary_translation:garlic` | 1 | 1 |
| `food_cooking|tier=B|band=high|review=False|source=primary_translation:grape` | 1 | 1 |
| `food_cooking|tier=B|band=high|review=False|source=primary_translation:lemon` | 1 | 1 |
| `food_cooking|tier=B|band=high|review=False|source=primary_translation:maize` | 1 | 1 |
| `food_cooking|tier=B|band=high|review=False|source=primary_translation:meat` | 3 | 1 |
| `food_cooking|tier=B|band=high|review=False|source=primary_translation:oil` | 2 | 1 |
| `food_cooking|tier=B|band=high|review=False|source=primary_translation:onion` | 1 | 1 |
| `food_cooking|tier=B|band=high|review=False|source=primary_translation:pepper` | 3 | 1 |
| `food_cooking|tier=B|band=high|review=False|source=primary_translation:potato` | 2 | 1 |
| `food_cooking|tier=B|band=high|review=False|source=primary_translation:salt` | 1 | 1 |
| `food_cooking|tier=B|band=high|review=False|source=primary_translation:sauce` | 2 | 1 |
| `food_cooking|tier=B|band=high|review=False|source=primary_translation:soup` | 2 | 1 |
| `food_cooking|tier=B|band=high|review=False|source=primary_translation:sugar` | 3 | 1 |
| `food_cooking|tier=B|band=high|review=False|source=primary_translation:tomato` | 1 | 1 |
| `food_cooking|tier=B|band=high|review=False|source=primary_translation:vegetable` | 1 | 1 |
| `food_cooking|tier=B|band=high|review=False|source=primary_translation:wheat` | 1 | 1 |
| `food_cooking|tier=A|band=high|review=False|source=cooking` | 38 | 1 |
| `food_cooking|tier=A|band=high|review=False|source=food` | 9 | 1 |

## Manual Review Queue

| ID | Lemma | Tier | Band | Source | Score | Review? | Evidence | Decision | Notes |
| --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- |
| `srs-food-001` | `plato` | `D` | `review` | `gloss_or_translation:food_gloss_pattern` | 0.527 | `True` | `plate, dish (crockery)` | accept_light_topic | Dish/plate is dining vocabulary, but this row is crockery rather than a food item. |
| `srs-food-002` | `achojcha` | `D` | `review` | `translation:food_translation_pattern` | 0.4536 | `True` | `fruit of the achojcha itself` | accept_light_topic | Edible fruit/vegetable sense is real, but the term is specialized and uncommon. |
| `srs-food-003` | `sangría` | `C` | `review` | `entry_categories:alcoholic_beverages` | 0.5586 | `True` | allowlisted_category_or_tag | accept_strong_topic | Direct alcoholic drink vocabulary. |
| `srs-food-004` | `cola` | `C` | `review` | `entry_categories:beverages` | 0.5586 | `True` | allowlisted_category_or_tag | accept_light_topic | Soft-drink sense is real, but tail, glue, and queue senses compete. |
| `srs-food-005` | `jengibre` | `C` | `review` | `sense_categories:cooking` | 0.5985 | `True` | allowlisted_category_or_tag | accept_strong_topic | Direct spice/ingredient vocabulary. |
| `srs-food-006` | `bombón` | `C` | `review` | `entry_categories:desserts` | 0.5586 | `True` | allowlisted_category_or_tag | accept_strong_topic | Direct candy/sweet vocabulary. |
| `srs-food-007` | `bagre` | `C` | `review` | `sense_categories:fish` | 0.4921 | `True` | allowlisted_category_or_tag | accept_light_topic | Catfish can be culinary vocabulary, but the animal sense dominates. |
| `srs-food-008` | `loche` | `C` | `review` | `entry_categories:foods` | 0.5719 | `True` | allowlisted_category_or_tag | accept_light_topic | Edible squash/pumpkin sense is food-related, but regionally narrow. |
| `srs-food-009` | `chocho` | `C` | `review` | `entry_categories:fruits` | 0.5054 | `True` | allowlisted_category_or_tag | accept_light_topic | Lupin bean/sweet senses are food-related, but slang/person senses compete. |
| `srs-food-010` | `hisopo` | `C` | `review` | `entry_categories:herbs` | 0.4788 | `True` | allowlisted_category_or_tag | accept_light_topic | Herb sense is relevant, but tool/religious senses compete. |
| `srs-food-011` | `legumbre` | `C` | `review` | `entry_categories:legumes` | 0.5187 | `True` | allowlisted_category_or_tag | accept_strong_topic | Direct food/ingredient vocabulary. |
| `srs-food-012` | `callo` | `C` | `review` | `entry_categories:meats` | 0.5054 | `True` | allowlisted_category_or_tag | accept_light_topic | Tripe/meat sense is real, but callus and other senses compete. |
| `srs-food-013` | `pipián` | `C` | `review` | `entry_categories:sauces` | 0.5586 | `True` | allowlisted_category_or_tag | accept_strong_topic | Direct sauce/dish vocabulary. |
| `srs-food-014` | `cúrcuma` | `C` | `review` | `entry_categories:spices` | 0.5586 | `True` | allowlisted_category_or_tag | accept_strong_topic | Direct spice/ingredient vocabulary. |
| `srs-food-015` | `cebolleta` | `C` | `review` | `entry_categories:spices_and_herbs` | 0.5187 | `True` | allowlisted_category_or_tag | accept_strong_topic | Direct vegetable/ingredient vocabulary. |
| `srs-food-016` | `lenteja` | `C` | `review` | `sense_categories:vegetables` | 0.5054 | `True` | allowlisted_category_or_tag | accept_strong_topic | Direct food/ingredient vocabulary. |
| `srs-food-017` | `pilsen` | `B` | `review` | `translation:primary_translation:beer` | 0.5985 | `True` | `beer` | accept_strong_topic | Direct beer/drink vocabulary. |
| `srs-food-018` | `morfi` | `B` | `review` | `translation:primary_translation:food` | 0.5985 | `True` | `food` | accept_light_topic | Food sense is direct but slang/register-specific. |
| `srs-food-019` | `jitomate` | `B` | `review` | `translation:primary_translation:tomato` | 0.5985 | `True` | `tomato (usually red)` | accept_strong_topic | Direct tomato/food vocabulary. |
| `srs-food-020` | `posta` | `D` | `inventory` | `gloss_or_translation:food_gloss_pattern` | 0.3689 | `True` | `slice of meat or fish` | accept_light_topic | Slice of meat or fish is food-related, but the word is polysemous and regional. |
| `srs-food-021` | `panga` | `C` | `inventory` | `sense_categories:fish` | 0.34447 | `True` | allowlisted_category_or_tag | accept_light_topic | Fish sense can be culinary, but boat and animal senses compete. |
| `srs-food-022` | `canelazo` | `C` | `medium` | `sense_categories:alcoholic_beverages` | 0.798 | `True` | allowlisted_category_or_tag | accept_strong_topic | Direct alcoholic drink vocabulary. |
| `srs-food-023` | `agua` | `C` | `medium` | `entry_categories:beverages` | 0.798 | `True` | allowlisted_category_or_tag | accept_strong_topic | Direct drink vocabulary. |
| `srs-food-024` | `bagel` | `C` | `medium` | `sense_categories:breads` | 0.798 | `True` | allowlisted_category_or_tag | accept_strong_topic | Direct bread/food item. |
| `srs-food-025` | `semicurado` | `C` | `medium` | `sense_categories:cheeses` | 0.798 | `True` | allowlisted_category_or_tag | accept_light_topic | Cheese-aging adjective is food-related, but not itself a food item. |
| `srs-food-026` | `natilla` | `C` | `medium` | `entry_categories:dairy_products` | 0.779 | `True` | allowlisted_category_or_tag | accept_strong_topic | Direct custard/dessert vocabulary. |
| `srs-food-027` | `poleada` | `C` | `medium` | `sense_categories:desserts` | 0.798 | `True` | allowlisted_category_or_tag | accept_strong_topic | Direct dessert/dish vocabulary. |
| `srs-food-028` | `trilla` | `C` | `medium` | `entry_categories:fish` | 0.703 | `True` | allowlisted_category_or_tag | accept_light_topic | Fish sense exists, but threshing and other senses compete. |
| `srs-food-029` | `manjar real` | `C` | `medium` | `sense_categories:foods` | 0.817 | `True` | allowlisted_category_or_tag | accept_strong_topic | Direct food/dish phrase. |
| `srs-food-030` | `acerola` | `C` | `medium` | `entry_categories:fruits` | 0.722 | `True` | allowlisted_category_or_tag | accept_strong_topic | Direct fruit vocabulary. |
| `srs-food-031` | `granza` | `C` | `medium` | `sense_categories:grains` | 0.741 | `True` | allowlisted_category_or_tag | accept_light_topic | Grain/chaff food-adjacent sense is real, but agricultural/non-food senses compete. |
| `srs-food-032` | `muña` | `C` | `medium` | `sense_categories:herbs` | 0.684 | `True` | allowlisted_category_or_tag | accept_light_topic | Herb/tea use is food-related, but regionally narrow. |
| `srs-food-033` | `maní forrajero` | `C` | `medium` | `sense_categories:legumes` | 0.741 | `True` | allowlisted_category_or_tag | reject_wrong_topic | Pinto peanut/forage crop is botanical or fodder vocabulary here, not learner-facing food/cooking vocabulary. |
| `srs-food-034` | `anticucho` | `C` | `medium` | `sense_categories:meats` | 0.722 | `True` | allowlisted_category_or_tag | accept_strong_topic | Direct prepared food item. |
| `srs-food-035` | `anacardo` | `C` | `medium` | `entry_categories:nuts` | 0.741 | `True` | allowlisted_category_or_tag | accept_strong_topic | Direct nut/food vocabulary. |
| `srs-food-036` | `guasacaca` | `C` | `medium` | `sense_categories:sauces` | 0.798 | `True` | allowlisted_category_or_tag | accept_strong_topic | Direct sauce vocabulary. |
| `srs-food-037` | `picoroco` | `C` | `medium` | `sense_categories:seafood` | 0.779 | `True` | allowlisted_category_or_tag | accept_light_topic | Seafood sense is real, but animal and regional specificity keep it light. |
| `srs-food-038` | `birria` | `C` | `medium` | `entry_categories:soups` | 0.798 | `True` | allowlisted_category_or_tag | accept_strong_topic | Direct stew/soup/dish vocabulary. |
| `srs-food-039` | `azafrán` | `C` | `medium` | `entry_categories:spices` | 0.798 | `True` | allowlisted_category_or_tag | accept_strong_topic | Direct spice/ingredient vocabulary. |
| `srs-food-040` | `cedrón` | `C` | `medium` | `sense_categories:spices_and_herbs` | 0.741 | `True` | allowlisted_category_or_tag | accept_light_topic | Herb/tea sense is food-related, but plant sense and regionality keep it light. |
| `srs-food-041` | `ajo chalote` | `C` | `medium` | `sense_categories:vegetables` | 0.722 | `True` | allowlisted_category_or_tag | accept_strong_topic | Direct ingredient phrase. |
| `srs-food-042` | `rebozar` | `C` | `high` | `entry_categories:cooking` | 0.855 | `True` | allowlisted_category_or_tag | accept_strong_topic | Direct cooking-preparation verb. |
| `srs-food-043` | `piragua` | `A` | `medium` | `sense_topics:cooking` | 0.665 | `False` | explicit_sense_topic | accept_light_topic | Frozen-dessert sense is real, but canoe is the dominant non-food sense. |
| `srs-food-044` | `untable` | `A` | `medium` | `sense_topics:food` | 0.665 | `False` | explicit_sense_topic | accept_light_topic | Spread/spreadable food sense is real, but adjectival usage keeps it light. |
| `srs-food-045` | `manzana` | `B` | `high` | `translation:primary_translation:apple` | 0.855 | `False` | `apple` | accept_strong_topic | Direct fruit/food vocabulary. |
| `srs-food-046` | `banana` | `B` | `high` | `translation:primary_translation:banana` | 0.855 | `False` | `banana (fruit)` | accept_strong_topic | Direct fruit/food vocabulary. |
| `srs-food-047` | `poroto` | `B` | `high` | `translation:primary_translation:bean` | 0.855 | `False` | `bean` | accept_strong_topic | Direct bean/food vocabulary. |
| `srs-food-048` | `carne de res` | `B` | `high` | `translation:primary_translation:beef` | 0.855 | `False` | `beef` | accept_strong_topic | Direct meat phrase. |
| `srs-food-049` | `cerve` | `B` | `high` | `translation:primary_translation:beer` | 0.855 | `False` | `beer` | accept_light_topic | Beer clipping is direct drink vocabulary, but slang/informal. |
| `srs-food-050` | `pan` | `B` | `high` | `translation:primary_translation:bread` | 0.855 | `False` | `bread (food made by baking cereal dough)` | accept_strong_topic | Direct bread/food vocabulary. |
| `srs-food-051` | `mantequilla` | `B` | `high` | `translation:primary_translation:butter` | 0.855 | `False` | `butter` | accept_strong_topic | Direct dairy/ingredient vocabulary. |
| `srs-food-052` | `formaje` | `B` | `high` | `translation:primary_translation:cheese` | 0.855 | `False` | `cheese` | accept_light_topic | Cheese sense is direct, but dated/rare. |
| `srs-food-053` | `pollo` | `B` | `high` | `translation:primary_translation:chicken` | 0.855 | `False` | `chicken (meat)` | accept_light_topic | Chicken meat sense is food-related, but animal/person senses compete. |
| `srs-food-054` | `tintico` | `B` | `high` | `translation:primary_translation:coffee` | 0.855 | `False` | `coffee` | accept_light_topic | Coffee sense is direct, but regionally narrow. |
| `srs-food-055` | `maíz` | `B` | `high` | `translation:primary_translation:corn` | 0.855 | `False` | `corn, maize` | accept_strong_topic | Direct grain/food vocabulary. |
| `srs-food-056` | `postre` | `B` | `high` | `translation:primary_translation:dessert` | 0.855 | `False` | `dessert; sweet` | accept_strong_topic | Direct dessert vocabulary. |
| `srs-food-057` | `dulcera` | `B` | `high` | `translation:primary_translation:dish` | 0.855 | `False` | `a dish, often of crystal, for storing or serving syrupy sweets, honey, etc.` | accept_light_topic | Sweet-serving dish/container is food-adjacent, not a food item. |
| `srs-food-058` | `bebienda` | `B` | `high` | `translation:primary_translation:drink` | 0.855 | `False` | `drink, beverage; liquid that is drunk` | accept_light_topic | Drink sense is direct, but the form is uncommon/nonstandard. |
| `srs-food-059` | `huevo` | `B` | `high` | `translation:primary_translation:egg` | 0.855 | `False` | `egg` | accept_strong_topic | Direct food/ingredient vocabulary. |
| `srs-food-060` | `pez` | `B` | `high` | `translation:primary_translation:fish` | 0.855 | `False` | `fish (especially while alive)` | accept_light_topic | Fish can be food vocabulary, but this row is primarily animal vocabulary. |
| `srs-food-061` | `vianda` | `B` | `high` | `translation:primary_translation:food` | 0.855 | `False` | `food, viands (items of food served as a meal)` | accept_strong_topic | Direct food/meal vocabulary. |
| `srs-food-062` | `fruta` | `B` | `high` | `translation:primary_translation:fruit` | 0.855 | `False` | `fruit (the seed-bearing part of a plant)` | accept_strong_topic | Direct fruit/food vocabulary. |
| `srs-food-063` | `ajo` | `B` | `high` | `translation:primary_translation:garlic` | 0.855 | `False` | `garlic` | accept_strong_topic | Direct ingredient vocabulary. |
| `srs-food-064` | `uva` | `B` | `high` | `translation:primary_translation:grape` | 0.855 | `False` | `grape` | accept_strong_topic | Direct fruit/food vocabulary. |
| `srs-food-065` | `limón` | `B` | `high` | `translation:primary_translation:lemon` | 0.855 | `False` | `lemon (fruit)` | accept_strong_topic | Direct lemon fruit vocabulary. |
| `srs-food-066` | `millo` | `B` | `high` | `translation:primary_translation:maize` | 0.855 | `False` | `maize, corn (also the plant)` | accept_light_topic | Maize/corn sense is food-related, but regional and plant-overlapping. |
| `srs-food-067` | `chicha` | `B` | `high` | `translation:primary_translation:meat` | 0.855 | `False` | `meat; flesh (culinary term)` | accept_light_topic | Drink/meat senses are food-related, but regional, colloquial, and polysemous. |
| `srs-food-068` | `aceite` | `B` | `high` | `translation:primary_translation:oil` | 0.855 | `False` | `oil` | accept_strong_topic | Direct cooking oil/ingredient vocabulary. |
| `srs-food-069` | `cebolla` | `B` | `high` | `translation:primary_translation:onion` | 0.855 | `False` | `onion` | accept_strong_topic | Direct vegetable/ingredient vocabulary. |
| `srs-food-070` | `pimiento` | `B` | `high` | `translation:primary_translation:pepper` | 0.855 | `False` | `pepper (fruit of the capsicum)` | accept_strong_topic | Direct pepper/vegetable vocabulary. |
| `srs-food-071` | `patata` | `B` | `high` | `translation:primary_translation:potato` | 0.855 | `False` | `potato` | accept_strong_topic | Direct vegetable/food vocabulary. |
| `srs-food-072` | `sal` | `B` | `high` | `translation:primary_translation:salt` | 0.855 | `False` | `salt; table salt` | accept_strong_topic | Direct seasoning/ingredient vocabulary. |
| `srs-food-073` | `refrito` | `B` | `high` | `translation:primary_translation:sauce` | 0.855 | `False` | `sauce` | accept_strong_topic | Direct sauce/cooking-preparation vocabulary. |
| `srs-food-074` | `sopa negra` | `B` | `high` | `translation:primary_translation:soup` | 0.855 | `False` | `a soup, commonly found in costa rica, made with black beans and other ingredi...` | accept_strong_topic | Direct soup/dish phrase. |
| `srs-food-075` | `sucra` | `B` | `high` | `translation:primary_translation:sugar` | 0.855 | `False` | `sugar` | accept_light_topic | Sugar sense is direct, but the term appears regional/rare. |
| `srs-food-076` | `tomate` | `B` | `high` | `translation:primary_translation:tomato` | 0.855 | `False` | `tomato (plant)` | accept_strong_topic | Direct tomato/food vocabulary. |
| `srs-food-077` | `verdura` | `B` | `high` | `translation:primary_translation:vegetable` | 0.855 | `False` | `vegetable` | accept_strong_topic | Direct vegetable/food vocabulary. |
| `srs-food-078` | `trigo` | `B` | `high` | `translation:primary_translation:wheat` | 0.855 | `False` | `wheat` | accept_strong_topic | Direct grain/food vocabulary. |
| `srs-food-079` | `gofio` | `A` | `high` | `sense_topics:cooking` | 0.95 | `False` | explicit_sense_topic | accept_strong_topic | Direct prepared grain/flour food vocabulary. |
| `srs-food-080` | `desmechado` | `A` | `high` | `sense_topics:food` | 0.95 | `False` | explicit_sense_topic | accept_light_topic | Food-specific shredded/pulled adjective is useful, but adjectival and preparation-specific. |
| `srs-food-081` | `cenar` | `D` | `review` | `gloss_or_translation:food_gloss_pattern` | 0.527 | `True` | `to dine; to have supper; to have a lavish meal` | accept_strong_topic | Direct dining/eating verb. |
| `srs-food-082` | `macedonia` | `D` | `review` | `translation:food_translation_pattern` | 0.4536 | `True` | `fruit salad` | accept_light_topic | Fruit-salad sense is real, but proper-name/geographic senses compete. |
| `srs-food-083` | `coca` | `C` | `review` | `entry_categories:beverages` | 0.5586 | `True` | allowlisted_category_or_tag | accept_light_topic | Coke/soft-drink and coca-leaf beverage senses are real, but plant/drug senses compete. |
| `srs-food-084` | `chongo` | `C` | `review` | `entry_categories:desserts` | 0.5586 | `True` | allowlisted_category_or_tag | accept_light_topic | Dessert sense is real, but the word is regional/polysemous. |
| `srs-food-085` | `artrodiro` | `C` | `review` | `sense_categories:fish` | 0.4921 | `True` | allowlisted_category_or_tag | reject_wrong_topic | Extinct zoological fish term, not food/cooking vocabulary. |
| `srs-food-086` | `arroz` | `C` | `review` | `entry_categories:foods` | 0.5719 | `True` | allowlisted_category_or_tag | accept_strong_topic | Direct staple food vocabulary. |
| `srs-food-087` | `pavía` | `C` | `review` | `sense_categories:fruits` | 0.5054 | `True` | allowlisted_category_or_tag | reject_secondary_or_obscure_sense | Fruit-variety sense exists, but dominant entries are Italian place names and the food sense is too secondary. |
| `srs-food-088` | `manzanilla` | `C` | `review` | `entry_categories:herbs` | 0.4788 | `True` | allowlisted_category_or_tag | accept_strong_topic | Direct tea/herb/drink vocabulary. |
| `srs-food-089` | `cacahuete` | `C` | `review` | `sense_categories:legumes` | 0.5187 | `True` | allowlisted_category_or_tag | accept_strong_topic | Direct peanut/food vocabulary. |
| `srs-food-090` | `quijada` | `C` | `review` | `entry_categories:meats` | 0.5054 | `True` | allowlisted_category_or_tag | accept_light_topic | Jowl/meat sense is real, but jaw/anatomy and instrument senses compete. |
| `srs-food-091` | `chile` | `C` | `review` | `entry_categories:spices` | 0.5586 | `True` | allowlisted_category_or_tag | accept_strong_topic | Direct pepper/spice vocabulary. |
| `srs-food-092` | `angélica` | `C` | `review` | `entry_categories:spices_and_herbs` | 0.5187 | `True` | allowlisted_category_or_tag | accept_light_topic | Herb sense is food-related, but name/plant senses compete. |
| `srs-food-093` | `cidracayote` | `C` | `review` | `sense_categories:vegetables` | 0.5054 | `True` | allowlisted_category_or_tag | accept_light_topic | Rare watermelon/vegetable sense is food-related, but too rare for strong lift. |
| `srs-food-094` | `chela` | `B` | `review` | `translation:primary_translation:beer` | 0.5985 | `True` | `beer` | accept_light_topic | Beer sense is real food/drink vocabulary, but regional slang keeps it light. |
| `srs-food-095` | `carnívoro` | `D` | `inventory` | `gloss_or_translation:food_gloss_pattern` | 0.3689 | `True` | `carnivore (meat-eating animal)` | reject_wrong_topic | Meat-eating animal/person vocabulary, not food or cooking vocabulary. |
| `srs-food-096` | `reo` | `C` | `inventory` | `sense_categories:fish` | 0.34447 | `True` | allowlisted_category_or_tag | reject_secondary_or_obscure_sense | Sea-trout sense exists, but legal/criminal senses dominate and the fish sense is too secondary for food lift. |

## Limitations

- This packet samples installed local Kaikki/Wiktionary candidates only; it does not download sources.
- Current-frontier candidates are excluded by default because they were already reviewed in the 46-row packet.
- The packet calibrates broader food/cooking source policy quality; it is not an installed overlay or runtime admission change.
- Rows are selected deterministically by review cell and stable hash, not by model judgment.
