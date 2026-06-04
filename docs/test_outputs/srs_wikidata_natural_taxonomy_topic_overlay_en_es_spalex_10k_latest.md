# en-es Wikidata Natural Taxonomy Topic Overlay

- Status: `ok`
- Decision: `srs_wikidata_natural_taxonomy_topic_overlay_ready`
- Rows: `39`
- Skipped: `1`

## Topic Counts

| Topic | Rows |
| --- | ---: |
| `animals` | 20 |
| `plants_nature` | 19 |

## Rows

| Topic | Lemma | Confidence | Membership | Roots | Match |
| --- | --- | --- | ---: | --- | --- |
| `animals` | `abeja` | `strong` | 1.0 | animal, insect | label, alias |
| `animals` | `atún` | `strong` | 1.0 | fish | alias |
| `animals` | `caracol` | `strong` | 1.0 | animal, mollusk | label |
| `animals` | `cerda` | `strong` | 1.0 | animal | label |
| `animals` | `cucaracha` | `strong` | 1.0 | insect, animal | label |
| `animals` | `elefante` | `strong` | 1.0 | animal, mammal | label |
| `animals` | `ganado` | `strong` | 1.0 | animal | label |
| `animals` | `ganso` | `strong` | 1.0 | animal, bird | label |
| `animals` | `gata` | `strong` | 1.0 | animal | label |
| `animals` | `gaviota` | `strong` | 1.0 | bird, animal | label |
| `animals` | `gorrión` | `strong` | 1.0 | bird | alias |
| `animals` | `hormiga` | `strong` | 1.0 | insect, animal | label |
| `animals` | `mariposa` | `strong` | 1.0 | insect | alias |
| `animals` | `mosca` | `strong` | 1.0 | animal, insect | label |
| `animals` | `ostra` | `strong` | 1.0 | animal, mollusk | label |
| `animals` | `perdiz` | `strong` | 1.0 | animal, bird | label |
| `animals` | `pollo` | `strong` | 1.0 | animal, bird | label, alias |
| `animals` | `reina` | `strong` | 1.0 | animal, insect | label |
| `animals` | `salmón` | `strong` | 1.0 | animal, fish | label |
| `animals` | `toro` | `strong` | 1.0 | animal | label |
| `plants_nature` | `arroz` | `strong` | 1.0 | grass, plant | label |
| `plants_nature` | `calabaza` | `strong` | 1.0 | plant | label |
| `plants_nature` | `caña` | `strong` | 1.0 | plant | label |
| `plants_nature` | `cebolla` | `strong` | 1.0 | plant, vegetable | label |
| `plants_nature` | `centeno` | `strong` | 1.0 | plant | label |
| `plants_nature` | `col` | `strong` | 1.0 | plant, vegetable | label |
| `plants_nature` | `haya` | `strong` | 1.0 | plant, tree | label |
| `plants_nature` | `lima` | `light` | 0.65 | fruit | label |
| `plants_nature` | `limón` | `light` | 0.65 | fruit | alias, label |
| `plants_nature` | `manzana` | `light` | 0.65 | fruit | label |
| `plants_nature` | `marrón` | `light` | 0.65 | fruit | label |
| `plants_nature` | `naranja` | `light` | 0.65 | fruit | label |
| `plants_nature` | `nuez` | `light` | 0.65 | fruit | label |
| `plants_nature` | `patata` | `light` | 0.65 | vegetable | alias |
| `plants_nature` | `pera` | `light` | 0.65 | fruit | label |
| `plants_nature` | `perejil` | `strong` | 1.0 | plant, herb | label |
| `plants_nature` | `plátano` | `strong` | 1.0 | plant, fruit, tree | label |
| `plants_nature` | `tomate` | `strong` | 1.0 | plant, vegetable, fruit | label |
| `plants_nature` | `uva` | `light` | 0.65 | fruit | label |

## Limitations

- This overlay internalizes reviewed source candidates; it does not make Wikidata a runtime dependency.
- Rows are useful for admission-preview/topic preference testing, but natural taxonomy coverage is intentionally incomplete.
- Polysemic labels are retained when the source candidate packet judged them acceptable enough for topic preference use.
