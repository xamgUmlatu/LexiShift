# en-es Food/Cooking Source Capacity Audit

- Status: `ok`
- Decision: `food_cooking_source_capacity_audit_completed`
- Generated: `2026-05-19T01:00:38+00:00`
- Full local Kaikki food-signal lemmas: `2129`
- Current frequency frontier food-signal lemmas: `46`
- Outside current frontier: `2083`

## Findings

- `PASS` `full_source_food_signals_present`: Local Kaikki has food/cooking signal supply.
- `PASS` `frontier_is_primary_recall_bottleneck`: Full local source has far more food/cooking candidates than the current SRS frontier.
- `WARN` `common_food_terms_missing_from_current_frontier`: Common food probes missing from the current frontier: comida, cocinar, cocina, agua, vino, pan, arroz, pollo, carne, huevo, leche, queso.

## Source Capacity

- Tier counts: `{'A': 80, 'B': 79, 'C': 1213, 'D': 757}`
- Confidence bands: `{'high': 154, 'inventory': 179, 'medium': 1143, 'review': 653}`

### Top Source Labels

- `food_gloss_pattern`: 610
- `foods`: 264
- `food_translation_pattern`: 147
- `fruits`: 135
- `fish`: 111
- `cooking`: 101
- `vegetables`: 86
- `meats`: 72
- `sauces`: 72
- `legumes`: 70
- `beverages`: 51
- `spices_and_herbs`: 42
- `seafood`: 42
- `desserts`: 42
- `alcoholic_beverages`: 33
- `herbs`: 31
- `breads`: 29
- `soups`: 26
- `grains`: 21
- `cheeses`: 18

## Common Food Probe Coverage

| Lemma | In Current Frontier | Policy Signal | Best Signal |
| --- | --- | --- | --- |
| `comida` | `False` | `True` | `B:high:primary_translation:food` |
| `comer` | `False` | `False` | `` |
| `cocinar` | `False` | `True` | `C:high:cooking` |
| `cocina` | `False` | `True` | `C:high:cooking` |
| `restaurante` | `True` | `False` | `` |
| `agua` | `False` | `True` | `C:medium:beverages` |
| `vino` | `False` | `True` | `C:medium:alcoholic_beverages` |
| `pan` | `False` | `True` | `B:high:primary_translation:bread` |
| `arroz` | `False` | `True` | `C:review:foods` |
| `pollo` | `False` | `True` | `B:high:primary_translation:chicken` |
| `carne` | `False` | `True` | `C:medium:meats` |
| `huevo` | `False` | `True` | `B:high:primary_translation:egg` |
| `leche` | `False` | `True` | `A:high:food` |
| `queso` | `False` | `True` | `B:high:primary_translation:cheese` |
| `tomate` | `False` | `True` | `B:high:primary_translation:tomato` |
| `patata` | `False` | `True` | `B:high:primary_translation:potato` |
| `papa` | `False` | `True` | `C:medium:vegetables` |
| `azúcar` | `False` | `True` | `B:high:primary_translation:sugar` |
| `sal` | `False` | `True` | `B:high:primary_translation:salt` |
| `sopa` | `False` | `True` | `C:medium:soups` |
| `fruta` | `False` | `True` | `B:high:primary_translation:fruit` |
| `verdura` | `False` | `True` | `B:high:primary_translation:vegetable` |
| `pescado` | `False` | `True` | `C:medium:seafood` |
| `cerveza` | `False` | `True` | `B:high:primary_translation:beer` |
| `café` | `False` | `False` | `` |
| `té` | `True` | `True` | `B:high:primary_translation:tea` |

## Outside-Frontier Examples

- `a fuego lento`: `A` `high` via `cooking`
- `a la romana`: `A` `high` via `cooking`
- `achara`: `A` `high` via `cooking`
- `ahumado`: `A` `high` via `cooking`
- `al gusto`: `A` `high` via `cooking`
- `al vapor`: `A` `high` via `cooking`
- `amasado`: `A` `high` via `cooking`
- `brasear`: `A` `high` via `cooking`
- `cebiche`: `A` `high` via `cooking`
- `cepa`: `A` `high` via `food`
- `criadilla`: `A` `high` via `cooking`
- `cuajado`: `A` `high` via `cooking`
- `dar un hervor`: `A` `high` via `cooking`
- `desglasar`: `A` `high` via `cooking`
- `desmechado`: `A` `high` via `food`
- `en juliana`: `A` `high` via `cooking`
- `encocado`: `A` `high` via `food`
- `enmolada`: `A` `high` via `cooking`
- `entibiar`: `A` `high` via `cooking`
- `entrecot`: `A` `high` via `cooking`

## Limitations

- This audit uses installed local Kaikki/Wiktionary rows and the current food/cooking policy only.
- It does not download sources, mutate packs, write overlays, or change admission behavior.
- Full-source capacity is not precision-reviewed; review labels currently apply only to the current CDE packet.
- The common probe list is diagnostic and intentionally small.
